import logging
from decimal import Decimal
from datetime import datetime, timedelta
import json
from django.db.models import Sum
from django.utils import timezone

from .models import AIAuth, AICost
from .encryption import KeyEncryption

logger = logging.getLogger("paper_trader.ai")


class AIBudgetError(Exception):
    """Raised when AI budget limit is exceeded."""
    pass


class AIService:
    """Manage AI API calls with budget enforcement and usage tracking."""

    def __init__(self, user):
        self.user = user
        self.ai_auth = AIAuth.objects.filter(user=user).first()

    def has_ai_enabled(self) -> bool:
        """Check if user has AI enabled (has API key configured)."""
        return self.ai_auth is not None and self.ai_auth.api_key_encrypted is not None

    def get_monthly_usage_usd(self) -> Decimal:
        """Get total usage for current month in USD."""
        if not self.ai_auth:
            return Decimal("0")

        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        total = AICost.objects.filter(
            ai_auth=self.ai_auth,
            created_at__gte=month_start
        ).aggregate(total=Sum("cost_usd"))["total"]

        return total or Decimal("0")

    def get_monthly_budget_usd(self) -> Decimal:
        """Get monthly budget in USD."""
        if not self.ai_auth:
            return Decimal("0")
        return self.ai_auth.monthly_budget_usd

    def get_remaining_budget_usd(self) -> Decimal:
        """Get remaining budget for this month in USD."""
        budget = self.get_monthly_budget_usd()
        usage = self.get_monthly_usage_usd()
        return max(Decimal("0"), budget - usage)

    def get_budget_percentage_used(self) -> Decimal:
        """Get percentage of monthly budget used (0-100)."""
        budget = self.get_monthly_budget_usd()
        if budget == 0:
            return Decimal("0")
        usage = self.get_monthly_usage_usd()
        return (usage / budget) * 100

    def is_at_budget_limit(self) -> bool:
        """Check if budget limit has been reached."""
        return self.get_remaining_budget_usd() <= 0

    def should_warn(self) -> bool:
        """Check if usage warning should be shown."""
        if not self.ai_auth:
            return False
        pct_used = self.get_budget_percentage_used()
        warn_threshold = 100 - self.ai_auth.alert_threshold_pct
        return pct_used >= warn_threshold

    def check_budget(self) -> None:
        """Raise error if budget limit exceeded."""
        if self.is_at_budget_limit():
            raise AIBudgetError(
                f"AI budget limit reached. "
                f"${self.get_monthly_usage_usd():.2f} of "
                f"${self.get_monthly_budget_usd():.2f} spent this month."
            )

    def log_call(self, model_name: str, prompt_tokens: int, completion_tokens: int,
                 cost_usd: Decimal, task_type: str) -> AICost:
        """Log an AI API call and its cost."""
        if not self.ai_auth:
            raise ValueError("No AI auth configured for this user")

        cost = AICost.objects.create(
            ai_auth=self.ai_auth,
            model_name=model_name,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            task_type=task_type,
        )

        logger.info(
            f"AI call logged: {self.user.username} - {model_name} - "
            f"{prompt_tokens}p+{completion_tokens}c - ${cost_usd} - {task_type}"
        )

        return cost

    def get_api_key(self) -> str | None:
        """Get decrypted API key for current provider."""
        if not self.ai_auth or not self.ai_auth.api_key_encrypted:
            return None
        try:
            return KeyEncryption.decrypt(self.ai_auth.api_key_encrypted)
        except Exception as e:
            logger.exception(f"Failed to decrypt API key for {self.user.username}: {e}")
            return None

    def set_api_key(self, api_key: str) -> None:
        """Store encrypted API key."""
        if not self.ai_auth:
            self.ai_auth = AIAuth.objects.create(user=self.user)

        self.ai_auth.api_key_encrypted = KeyEncryption.encrypt(api_key)
        self.ai_auth.save()
        logger.info(f"API key updated for {self.user.username}")

    def clear_api_key(self) -> None:
        """Remove API key."""
        if self.ai_auth:
            self.ai_auth.api_key_encrypted = None
            self.ai_auth.save()
            logger.info(f"API key removed for {self.user.username}")

    def get_budget_info(self) -> dict:
        """Get budget info for display in header/settings."""
        pct_used = self.get_budget_percentage_used()
        return {
            "enabled": self.has_ai_enabled(),
            "monthly_budget_usd": str(self.get_monthly_budget_usd()),
            "usage_usd": str(self.get_monthly_usage_usd()),
            "remaining_usd": str(self.get_remaining_budget_usd()),
            "percentage_used": f"{pct_used:.0f}",
            "at_limit": self.is_at_budget_limit(),
            "should_warn": self.should_warn(),
        }

    @staticmethod
    def _extract_json_object(text: str) -> dict | None:
        if not text:
            return None

        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if len(lines) >= 3:
                cleaned = "\n".join(lines[1:-1]).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start == -1 or end == -1 or end <= start:
                return None
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                return None

    @staticmethod
    def _estimate_openai_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
        pricing = {
            "gpt-4o-mini": (Decimal("0.00000015"), Decimal("0.00000060")),
            "gpt-4o": (Decimal("0.00000250"), Decimal("0.00001000")),
        }
        prompt_rate, completion_rate = pricing.get(
            model_name,
            pricing["gpt-4o-mini"],
        )
        return (Decimal(prompt_tokens) * prompt_rate) + (Decimal(completion_tokens) * completion_rate)

    @staticmethod
    def test_connection(provider: str, api_key: str, model: str | None = None) -> dict:
        """Validate API credentials with a minimal provider call."""
        if provider == "anthropic":
            import anthropic

            selected_model = model or "claude-haiku-4-5-20251001"
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=selected_model,
                max_tokens=5,
                messages=[{"role": "user", "content": "Reply with OK"}],
            )
            text = message.content[0].text if message.content else ""
            return {"provider": provider, "model": selected_model, "message": text}

        if provider == "openai":
            import openai

            selected_model = model or "gpt-4o-mini"
            client = openai.OpenAI(api_key=api_key)
            response = client.responses.create(
                model=selected_model,
                max_output_tokens=16,
                input="Reply with OK",
            )
            text = response.output_text
            return {"provider": provider, "model": selected_model, "message": text}

        if provider == "google":
            import google.generativeai as genai

            selected_model = model or "gemini-2.0-flash"
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(selected_model)
            response = model_obj.generate_content("Reply with OK")
            return {"provider": provider, "model": selected_model, "message": response.text}

        raise ValueError(f"Unsupported provider: {provider}")

    def analyze_asset(self, asset) -> dict:
        from markets.models import NewsItem
        from markets.services import NewsService
        from trading.technical import IndicatorCalculator

        if not self.ai_auth or not self.get_api_key():
            raise ValueError("AI is not configured for this user")

        self.check_budget()

        indicators = IndicatorCalculator.calculate_indicators(str(asset.id), asset.display_symbol)
        if not indicators:
            raise ValueError("Not enough historical data to generate AI insight")

        NewsService.fetch_and_store_news(asset)
        news_items = list(
            NewsItem.objects.filter(asset=asset)
            .order_by("-published_at", "-fetched_at")[:5]
            .values("headline", "source", "published_at")
        )

        provider = self.ai_auth.provider_name
        model = self.ai_auth.get_model_for_task("indicator_insight")
        api_key = self.get_api_key()

        prompt = f"""You are analyzing one asset for a paper trading app.

Return ONLY valid JSON with this exact shape:
{{
  "recommendation": "BUY" | "HOLD" | "SELL",
  "confidence": integer from 0 to 100,
  "technical_summary": "plain-English paragraph about the technical setup",
  "news_context": "plain-English paragraph about the market or news context, or empty string if there is no meaningful context",
  "price_target": number or null
}}

Asset:
- Symbol: {asset.display_symbol}
- Name: {asset.name}
- Market: {asset.market}
- Currency: {asset.currency}

Technical indicators:
- RSI 14: {indicators.get("rsi_14")}
- MACD: {indicators.get("macd")}
- MACD signal: {indicators.get("macd_signal")}
- MACD histogram: {indicators.get("macd_histogram")}
- MA 20: {indicators.get("ma_20")}
- MA 50: {indicators.get("ma_50")}
- MA 200: {indicators.get("ma_200")}
- Bollinger upper: {indicators.get("bb_upper")}
- Bollinger middle: {indicators.get("bb_middle")}
- Bollinger lower: {indicators.get("bb_lower")}
- 20 day average volume: {indicators.get("volume_20d_avg")}

Recent headlines:
{chr(10).join(f"- {item['headline']} ({item['source']})" for item in news_items) if news_items else "- None"}

Writing rules:
- Be useful to an everyday investor, not only a technical analyst.
- First paragraph: explain what the indicators suggest in plain English.
- Second paragraph: explain what broader news or market context may be influencing the asset right now.
- If the headlines are weak, generic, or missing, set "news_context" to an empty string.
- Do not mention every indicator mechanically.
- No markdown."""

        response_text = ""
        prompt_tokens = 0
        completion_tokens = 0
        cost_usd = Decimal("0")

        if provider == "anthropic":
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model=model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = message.content[0].text if message.content else ""
            if getattr(message, "usage", None):
                prompt_tokens = getattr(message.usage, "input_tokens", 0) or 0
                completion_tokens = getattr(message.usage, "output_tokens", 0) or 0
        elif provider == "openai":
            import openai

            response = openai.OpenAI(api_key=api_key).responses.create(
                model=model,
                max_output_tokens=300,
                input=prompt,
            )
            response_text = response.output_text
            if getattr(response, "usage", None):
                prompt_tokens = getattr(response.usage, "input_tokens", 0) or 0
                completion_tokens = getattr(response.usage, "output_tokens", 0) or 0
                cost_usd = self._estimate_openai_cost(model, prompt_tokens, completion_tokens)
        elif provider == "google":
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            response = genai.GenerativeModel(model).generate_content(prompt)
            response_text = response.text
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        parsed = self._extract_json_object(response_text)
        if not parsed:
            raise ValueError("AI returned an invalid response")

        self.log_call(
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            task_type="indicator_insight",
        )

        return {
            "symbol": asset.display_symbol,
            "market": asset.market,
            "recommendation": parsed.get("recommendation", "HOLD"),
            "confidence": int(parsed.get("confidence", 50)),
            "technical_summary": parsed.get("technical_summary", ""),
            "news_context": parsed.get("news_context", ""),
            "reasoning": "\n\n".join(
                part for part in [
                    parsed.get("technical_summary", ""),
                    parsed.get("news_context", ""),
                ] if part
            ),
            "price_target": parsed.get("price_target"),
            "model_used": model,
            "generated_at": timezone.now().isoformat(),
            "news_items": [
                {
                    "headline": item["headline"],
                    "source": item["source"],
                    "published_at": item["published_at"].isoformat() if item["published_at"] else None,
                }
                for item in news_items
            ],
        }

    @staticmethod
    def analyze_news_sentiment(headlines: list[str], user=None) -> dict[str, Decimal]:
        """Analyze sentiment for news headlines using configured AI provider.

        Returns dict mapping headline to sentiment score (-1.0 to 1.0).
        If API call fails, returns empty dict.
        """
        if not headlines:
            return {}

        if user:
            service = AIService(user)
            api_key = service.get_api_key()
            provider = service.ai_auth.provider_name if service.ai_auth else "anthropic"
            model = service.ai_auth.get_model_for_task("sentiment_analysis") if service.ai_auth else "claude-opus-4-6"
        else:
            from django.conf import settings
            api_key = getattr(settings, "ANTHROPIC_API_KEY", None)
            provider = "anthropic"
            model = "claude-opus-4-6"

        if not api_key:
            logger.warning("No API key available for sentiment analysis")
            return {}

        prompt = f"""Analyze the sentiment of each headline and return a JSON object mapping each headline to a sentiment score from -1.0 (most negative) to 1.0 (most positive).

Headlines:
{chr(10).join(f'- {h}' for h in headlines)}

Return ONLY valid JSON object, e.g. {{"headline1": -0.5, "headline2": 0.3}}"""

        import json
        try:
            if provider == "anthropic":
                import anthropic
                client = anthropic.Anthropic(api_key=api_key)
                message = client.messages.create(
                    model=model,
                    max_tokens=500,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = message.content[0].text
            elif provider == "openai":
                import openai
                client = openai.OpenAI(api_key=api_key)
                response = client.responses.create(
                    model=model,
                    max_output_tokens=500,
                    input=prompt,
                )
                response_text = response.output_text
            elif provider == "google":
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model_obj = genai.GenerativeModel(model)
                response = model_obj.generate_content(prompt)
                response_text = response.text
            else:
                logger.warning(f"Unsupported provider: {provider}")
                return {}

            sentiments = json.loads(response_text)
            return {h: Decimal(str(s)) for h, s in sentiments.items() if h in headlines}
        except Exception as e:
            logger.exception(f"Failed to analyze news sentiment: {e}")
            return {}
