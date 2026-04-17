import hashlib
import json
import logging
import re
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Sum
from django.utils import timezone

from .encryption import KeyEncryption
from .models import AIAuth, AICost
from .news_context_policy import (
    ASSET_METADATA_OVERRIDES,
    BUCKET_LIMITS,
    BUCKET_ORDER,
    CORPORATE_SUFFIXES,
    HEADLINE_STOPWORDS,
    RAW_BUCKET_LIMITS,
    SOURCE_QUALITY,
    THEME_RULES,
    TOTAL_CONTEXT_LIMIT,
)

logger = logging.getLogger("paper_trader.ai")


class AIBudgetError(Exception):
    """Raised when AI budget limit is exceeded."""
    pass


class AIService:
    """Manage AI API calls with budget enforcement and usage tracking."""

    CONTINUITY_LOOKBACK_DAYS = 5
    CONTINUITY_PROMPT_LIMIT = 5
    CONTINUITY_TOPIC_OVERLAP = 2
    CONTINUITY_SENTIMENT_THRESHOLD = Decimal("0.2")
    POSITIVE_HEADLINE_MARKERS = {
        "beats",
        "beat",
        "growth",
        "gains",
        "gain",
        "rises",
        "rise",
        "rally",
        "rallies",
        "raises",
        "raise",
        "approval",
        "approved",
        "expands",
        "expansion",
        "wins",
        "win",
        "upgrade",
        "upgrades",
    }
    NEGATIVE_HEADLINE_MARKERS = {
        "misses",
        "miss",
        "cuts",
        "cut",
        "falls",
        "fall",
        "slump",
        "slumps",
        "drops",
        "drop",
        "lawsuit",
        "probe",
        "probes",
        "downgrade",
        "downgrades",
        "delays",
        "delay",
        "loss",
        "losses",
    }

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
    def build_connection_test_prompt() -> str:
        return "Reply with OK"

    @staticmethod
    def _normalize_text(text: str) -> str:
        cleaned = re.sub(r"[^a-z0-9]+", " ", (text or "").lower())
        return " ".join(cleaned.split())

    @classmethod
    def _headline_signature(cls, text: str) -> str:
        tokens = []
        for token in cls._normalize_text(text).split():
            if token in HEADLINE_STOPWORDS or token in CORPORATE_SUFFIXES:
                continue
            tokens.append(token)
        if not tokens:
            return cls._normalize_text(text)
        return " ".join(sorted(set(tokens)))

    @classmethod
    def _headline_terms(cls, text: str) -> set[str]:
        tokens = set()
        for token in cls._normalize_text(text).split():
            if token in HEADLINE_STOPWORDS or token in CORPORATE_SUFFIXES:
                continue
            if token in cls.POSITIVE_HEADLINE_MARKERS or token in cls.NEGATIVE_HEADLINE_MARKERS:
                continue
            tokens.add(token)
        return tokens

    @classmethod
    def _headline_direction(cls, text: str) -> str:
        normalized = cls._normalize_text(text)
        positive = sum(1 for marker in cls.POSITIVE_HEADLINE_MARKERS if marker in normalized)
        negative = sum(1 for marker in cls.NEGATIVE_HEADLINE_MARKERS if marker in normalized)
        if positive > negative:
            return "positive"
        if negative > positive:
            return "negative"
        return "neutral"

    @classmethod
    def _sentiment_label(cls, sentiment_score) -> str | None:
        if sentiment_score is None:
            return None
        score = Decimal(str(sentiment_score))
        if score >= cls.CONTINUITY_SENTIMENT_THRESHOLD:
            return "positive"
        if score <= -cls.CONTINUITY_SENTIMENT_THRESHOLD:
            return "negative"
        return "neutral"

    @classmethod
    def _continuity_label(cls, current_item: dict, prior_item) -> str:
        current_terms = cls._headline_terms(current_item["headline"])
        prior_terms = cls._headline_terms(prior_item.headline)
        overlap = len(current_terms & prior_terms)
        if overlap < cls.CONTINUITY_TOPIC_OVERLAP:
            return "new"

        current_sentiment = cls._sentiment_label(current_item.get("sentiment_score"))
        prior_sentiment = cls._sentiment_label(prior_item.sentiment_score)
        if current_sentiment and prior_sentiment and current_sentiment != prior_sentiment:
            return "shifted"

        current_direction = cls._headline_direction(current_item["headline"])
        prior_direction = cls._headline_direction(prior_item.headline)
        if current_direction != "neutral" and prior_direction != "neutral" and current_direction != prior_direction:
            return "shifted"

        return "continuing"

    @classmethod
    def _best_prior_continuity_match(cls, asset, current_item: dict):
        from markets.models import NewsItem

        if not current_item.get("published_at"):
            return None

        window_start = current_item["published_at"] - timedelta(days=cls.CONTINUITY_LOOKBACK_DAYS)
        excluded_id = current_item.get("news_item_id")
        prior_items = (
            NewsItem.objects.select_related("asset")
            .filter(
                asset=asset,
                published_at__gte=window_start,
                published_at__lt=current_item["published_at"],
            )
            .order_by("-published_at", "-fetched_at")
        )
        if excluded_id:
            prior_items = prior_items.exclude(id=excluded_id)

        current_terms = cls._headline_terms(current_item["headline"])
        best_item = None
        best_overlap = 0
        for prior_item in prior_items:
            overlap = len(current_terms & cls._headline_terms(prior_item.headline))
            if overlap > best_overlap:
                best_item = prior_item
                best_overlap = overlap
            if best_overlap >= cls.CONTINUITY_TOPIC_OVERLAP and overlap == best_overlap:
                break

        if best_overlap < cls.CONTINUITY_TOPIC_OVERLAP:
            return None

        return best_item

    @classmethod
    def build_story_so_far(cls, asset, context_items: list[dict]) -> list[dict]:
        story_items = []
        for item in context_items:
            prior_item = cls._best_prior_continuity_match(asset, item)
            label = "new" if prior_item is None else cls._continuity_label(item, prior_item)
            story_items.append({
                "label": label,
                "news_item_id": item.get("news_item_id"),
                "headline": item["headline"],
                "source": item["source"],
                "published_at": item.get("published_at"),
                "sentiment": cls._sentiment_label(item.get("sentiment_score")),
            })

        label_rank = {"shifted": 0, "continuing": 1, "new": 2}
        def sort_key(item: dict) -> tuple[int, float, str]:
            published_at = item["published_at"] or timezone.now()
            if timezone.is_naive(published_at):
                published_at = timezone.make_aware(published_at, timezone=timezone.get_current_timezone())
            return (
                label_rank.get(item["label"], 3),
                -published_at.timestamp(),
                item["headline"].lower(),
            )

        ordered = sorted(
            story_items,
            key=sort_key,
        )
        return ordered[:cls.CONTINUITY_PROMPT_LIMIT]

    @classmethod
    def _matches_alias(cls, headline: str, alias: str) -> bool:
        normalized_headline = f" {cls._normalize_text(headline)} "
        normalized_alias = cls._normalize_text(alias)
        if not normalized_alias:
            return False
        return f" {normalized_alias} " in normalized_headline

    @classmethod
    def _asset_aliases(cls, asset) -> list[str]:
        names = [asset.display_symbol, asset.provider_symbol, asset.name]
        base_name = cls._normalize_text(asset.name)
        if base_name:
            stripped_name = " ".join(
                token for token in base_name.split()
                if token not in CORPORATE_SUFFIXES
            )
            if stripped_name and stripped_name != base_name:
                names.append(stripped_name)
        return [name for name in names if name]

    @classmethod
    def _resolved_asset_metadata(cls, asset) -> tuple[str, str]:
        override = ASSET_METADATA_OVERRIDES.get(asset.display_symbol, {})
        sector = asset.sector or override.get("sector") or ""
        industry = asset.industry or override.get("industry") or ""
        return sector, industry

    @staticmethod
    def _source_quality(source: str) -> int:
        return SOURCE_QUALITY.get((source or "").lower(), 1)

    @staticmethod
    def _impact_score(headline: str) -> int:
        impact_keywords = (
            "beats",
            "misses",
            "guidance",
            "raises",
            "cuts",
            "merger",
            "acquisition",
            "lawsuit",
            "tariff",
            "opec",
            "oil",
            "rates",
            "inflation",
            "fed",
            "cpi",
            "earnings",
            "dividend",
        )
        normalized = AIService._normalize_text(headline)
        score = 0
        for keyword in impact_keywords:
            if keyword in normalized:
                score += 2
        if any(char.isdigit() for char in headline):
            score += 1
        if len(normalized.split()) >= 8:
            score += 1
        return score

    @staticmethod
    def _recency_score(published_at) -> int:
        if not published_at:
            return 0
        if timezone.is_naive(published_at):
            published_at = timezone.make_aware(published_at, timezone=timezone.get_current_timezone())
        hours_old = max(0, (timezone.now() - published_at).total_seconds() / 3600)
        if hours_old <= 6:
            return 4
        if hours_old <= 24:
            return 3
        if hours_old <= 72:
            return 2
        if hours_old <= 168:
            return 1
        return 0

    @classmethod
    def _ranking_score(cls, item: dict) -> tuple[int, int, int, int, str]:
        directness = {
            "symbol": 5,
            "company": 4,
            "sector": 3,
            "industry": 3,
            "macro": 2,
            "theme": 2,
        }.get(item["bucket"], 1)
        return (
            directness,
            cls._impact_score(item["headline"]),
            cls._source_quality(item["source"]),
            cls._recency_score(item.get("published_at")),
            item["headline"].lower(),
        )

    @classmethod
    def _theme_match(cls, headline: str, asset_sector: str, asset_industry: str) -> dict | None:
        normalized = cls._normalize_text(headline)
        for rule in THEME_RULES:
            if rule["sector_names"] and asset_sector not in rule["sector_names"]:
                continue
            if rule["industry_names"] and asset_industry not in rule["industry_names"]:
                continue
            if any(keyword in normalized for keyword in rule["keywords"]):
                return rule
        return None

    @classmethod
    def _classify_context_item(cls, item, asset, asset_sector: str, asset_industry: str) -> tuple[str | None, str, str]:
        headline = item.headline or ""
        if item.asset_id == asset.id:
            if any(cls._matches_alias(headline, alias) for alias in (asset.display_symbol, asset.provider_symbol)):
                return "symbol", f"asset:{asset.display_symbol}", "headline explicitly mentions the symbol"
            if any(cls._matches_alias(headline, alias) for alias in cls._asset_aliases(asset)):
                return "company", f"asset:{asset.display_symbol}", "headline explicitly mentions the company"
            return "company", f"asset:{asset.display_symbol}", "current asset news"

        if item.asset and asset_sector and item.asset.sector == asset_sector:
            return "sector", f"sector:{asset_sector}", f"same sector asset: {item.asset.display_symbol}"

        if item.asset and asset_industry and item.asset.industry == asset_industry:
            return "industry", f"industry:{asset_industry}", f"same industry asset: {item.asset.display_symbol}"

        matched_rule = cls._theme_match(headline, asset_sector, asset_industry)
        if matched_rule:
            provenance = f"{matched_rule['bucket']}:{matched_rule['name']}"
            relevance_basis = f"keyword match: {matched_rule['name']}"
            return matched_rule["bucket"], provenance, relevance_basis

        return None, "", ""

    @classmethod
    def build_asset_context_pack(cls, asset, max_items: int = TOTAL_CONTEXT_LIMIT) -> list[dict]:
        from markets.models import NewsItem

        asset_sector, asset_industry = cls._resolved_asset_metadata(asset)
        candidates: list[dict] = []

        news_items = (
            NewsItem.objects.select_related("asset")
            .order_by("-published_at", "-fetched_at")[:200]
        )

        bucket_raw_counts: dict[str, int] = {bucket: 0 for bucket in BUCKET_ORDER}

        for item in news_items:
            bucket, provenance, relevance_basis = cls._classify_context_item(item, asset, asset_sector, asset_industry)
            if bucket is None:
                continue

            if bucket_raw_counts[bucket] >= RAW_BUCKET_LIMITS[bucket]:
                continue
            bucket_raw_counts[bucket] += 1

            candidates.append({
                "news_item_id": str(item.id),
                "headline": item.headline,
                "url": item.url,
                "source": item.source,
                "published_at": item.published_at or item.fetched_at,
                "bucket": bucket,
                "provenance": provenance,
                "relevance_basis": relevance_basis,
                "asset_symbol": item.asset.display_symbol if item.asset_id else None,
                "market": item.asset.market if item.asset_id else None,
                "sentiment_score": item.sentiment_score,
                "dedupe_key": cls._headline_signature(item.headline),
            })

        deduped: dict[str, dict] = {}
        for candidate in candidates:
            key = candidate["dedupe_key"]
            existing = deduped.get(key)
            if existing is None or cls._ranking_score(candidate) > cls._ranking_score(existing):
                deduped[key] = candidate

        selected_by_bucket: dict[str, list[dict]] = {bucket: [] for bucket in BUCKET_ORDER}
        for candidate in deduped.values():
            selected_by_bucket[candidate["bucket"]].append(candidate)

        selected: list[dict] = []
        for bucket in BUCKET_ORDER:
            ranked = sorted(
                selected_by_bucket[bucket],
                key=cls._ranking_score,
                reverse=True,
            )[:BUCKET_LIMITS[bucket]]
            selected.extend(ranked)

        selected = sorted(selected, key=cls._ranking_score, reverse=True)[:max_items]

        return [
            {
                "news_item_id": item["news_item_id"],
                "headline": item["headline"],
                "url": item["url"],
                "source": item["source"],
                "published_at": item["published_at"],
                "bucket": item["bucket"],
                "provenance": item["provenance"],
                "relevance_basis": item["relevance_basis"],
                "asset_symbol": item["asset_symbol"],
                "market": item["market"],
                "sentiment_score": item["sentiment_score"],
            }
            for item in selected
        ]

    @classmethod
    def build_scope_context_pack(cls, assets, max_items: int = TOTAL_CONTEXT_LIMIT) -> list[dict]:
        candidates: list[dict] = []
        for asset in assets:
            candidates.extend(cls.build_asset_context_pack(asset, max_items=max_items))

        deduped: dict[str, dict] = {}
        for candidate in candidates:
            key = cls._headline_signature(candidate["headline"])
            existing = deduped.get(key)
            if existing is None or cls._ranking_score(candidate) > cls._ranking_score(existing):
                deduped[key] = candidate

        return sorted(deduped.values(), key=cls._ranking_score, reverse=True)[:max_items]

    @staticmethod
    def _format_news_line(item: dict) -> str:
        return (
            f"- [{item.get('bucket', 'news')}] {item['headline']} "
            f"({item['source']}; {item.get('provenance', 'unclassified')})"
        )

    @staticmethod
    def build_indicator_insight_prompt(
        asset,
        indicators: dict,
        news_items: list[dict],
        story_so_far: list[dict] | None = None,
    ) -> str:
        if story_so_far:
            story_section = "\n".join(
                "- [{label}] {headline} ({source}{sentiment})".format(
                    label=item["label"],
                    headline=item["headline"],
                    source=item["source"],
                    sentiment=f"; {item['sentiment']}" if item.get("sentiment") else "",
                )
                for item in story_so_far
            )
        else:
            story_section = "- None"

        news_lines = "\n".join(
            AIService._format_news_line(item) for item in news_items
        ) if news_items else "- None"

        return (
            "You are analyzing one asset for a paper trading app.\n\n"
            "Return ONLY valid JSON with this exact shape:\n"
            "{\n"
            '  "recommendation": "BUY" | "HOLD" | "SELL",\n'
            '  "confidence": integer from 0 to 100,\n'
            '  "summary": "plain-English paragraph about the overall setup for an everyday investor",\n'
            '  "technical_summary": "plain-English paragraph about the technical setup",\n'
            '  "news_context": "plain-English paragraph about the market or news context, or '
            'empty string if there is no meaningful context",\n'
            '  "price_target": number or null\n'
            "}\n\n"
            f"Asset:\n"
            f"- Symbol: {asset.display_symbol}\n"
            f"- Name: {asset.name}\n"
            f"- Market: {asset.market}\n"
            f"- Currency: {asset.currency}\n\n"
            "Technical indicators:\n"
            f"- RSI 14: {indicators.get('rsi_14')}\n"
            f"- MACD: {indicators.get('macd')}\n"
            f"- MACD signal: {indicators.get('macd_signal')}\n"
            f"- MACD histogram: {indicators.get('macd_histogram')}\n"
            f"- MA 20: {indicators.get('ma_20')}\n"
            f"- MA 50: {indicators.get('ma_50')}\n"
            f"- MA 200: {indicators.get('ma_200')}\n"
            f"- Bollinger upper: {indicators.get('bb_upper')}\n"
            f"- Bollinger middle: {indicators.get('bb_middle')}\n"
            f"- Bollinger lower: {indicators.get('bb_lower')}\n"
            f"- 20 day average volume: {indicators.get('volume_20d_avg')}\n\n"
            "Context pack:\n"
            f"{news_lines}\n\n"
            "Story so far:\n"
            f"{story_section}\n\n"
            "Writing rules:\n"
            "- Write the summary as the main takeaway for an everyday investor.\n"
            "- Keep the summary free of technical jargon and do not repeat the technical paragraph.\n"
            "- Technical summary should only describe the indicators and chart setup.\n"
            "- News context should only describe the broader news or market context.\n"
            '- If the headlines are weak, generic, or missing, set "news_context" to an empty string.\n'
            "- Do not mention every indicator mechanically.\n"
            "- No markdown."
        )

    @staticmethod
    def build_scope_insight_prompt(
        scope_type: str,
        scope_label: str,
        holdings: list[dict],
        news_items: list[dict],
    ) -> str:
        holdings_lines = "\n".join(
            f"- {item['symbol']} | {item['name']} | {item.get('position_detail', item.get('current_price', '-'))}"
            for item in holdings
        ) if holdings else "- None"
        news_lines = "\n".join(
            AIService._format_news_line(item) for item in news_items
        ) if news_items else "- None"

        return (
            "You are analyzing one monitored set for a paper trading app.\n\n"
            "Return ONLY valid JSON with this exact shape:\n"
            "{\n"
            '  "recommendation": "BUY" | "HOLD" | "SELL",\n'
            '  "confidence": integer from 0 to 100,\n'
            '  "summary": "plain-English paragraph about the monitored set overall",\n'
            '  "technical_summary": "plain-English paragraph about the scope\'s technical posture",\n'
            '  "news_context": "plain-English paragraph about the broader news or market context, or '
            'empty string if there is no meaningful context"\n'
            "}\n\n"
            f"Scope:\n"
            f"- Type: {scope_type}\n"
            f"- Label: {scope_label}\n"
            f"- Asset count: {len(holdings)}\n\n"
            "Holdings:\n"
            f"{holdings_lines}\n\n"
            "Context pack:\n"
            f"{news_lines}\n\n"
            "Writing rules:\n"
            "- Focus on the monitored set as a whole, not one asset at a time.\n"
            "- Explain how the holdings relate to each other and what the combined setup suggests.\n"
            '- If the headlines are weak, generic, or missing, set "news_context" to an empty string.\n'
            "- Do not mention every holding mechanically.\n"
            "- No markdown."
        )

    @staticmethod
    def build_sentiment_prompt(headlines: list[str]) -> str:
        return (
            "Analyze the sentiment of each headline and return a JSON object mapping each headline "
            "to a sentiment score from -1.0 (most negative) to 1.0 (most positive).\n\n"
            "Headlines:\n"
            f"{chr(10).join(f'- {h}' for h in headlines)}\n\n"
            'Return ONLY valid JSON object, e.g. {"headline1": -0.5, "headline2": 0.3}'
        )

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
    def _estimate_anthropic_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
        pricing = {
            "claude-haiku-4-5-20251001": (Decimal("0.00000080"), Decimal("0.00000400")),
            "claude-sonnet-4-6": (Decimal("0.00000300"), Decimal("0.00001500")),
            "claude-opus-4-6": (Decimal("0.00001500"), Decimal("0.00007500")),
        }
        prompt_rate, completion_rate = pricing.get(
            model_name,
            (Decimal("0.00000100"), Decimal("0.00000500")),
        )
        return (Decimal(prompt_tokens) * prompt_rate) + (Decimal(completion_tokens) * completion_rate)

    @staticmethod
    def _estimate_google_cost(model_name: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
        pricing = {
            "gemini-2.0-flash": (Decimal("0.00000035"), Decimal("0.00000105")),
            "gemini-1.5-pro": (Decimal("0.00000125"), Decimal("0.00000500")),
        }
        prompt_rate, completion_rate = pricing.get(
            model_name,
            (Decimal("0.00000100"), Decimal("0.00000500")),
        )
        return (Decimal(prompt_tokens) * prompt_rate) + (Decimal(completion_tokens) * completion_rate)

    @staticmethod
    def _estimate_provider_cost(provider: str, model_name: str, prompt_tokens: int, completion_tokens: int) -> Decimal:
        if provider == "openai":
            return AIService._estimate_openai_cost(model_name, prompt_tokens, completion_tokens)
        elif provider == "anthropic":
            return AIService._estimate_anthropic_cost(model_name, prompt_tokens, completion_tokens)
        elif provider == "google":
            return AIService._estimate_google_cost(model_name, prompt_tokens, completion_tokens)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

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
        from markets.services import NewsService
        from trading.technical import IndicatorCalculator

        if not self.ai_auth or not self.get_api_key():
            raise ValueError("AI is not configured for this user")

        cache_key = f"ai_insight:v2:{self.user.id}:{asset.id}"
        legacy_cache_key = f"ai_insight:{self.user.id}:{asset.id}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        cached = cache.get(legacy_cache_key)
        if cached:
            cache.set(cache_key, cached, timeout=86400)
            return cached

        self.check_budget()

        indicators = IndicatorCalculator.calculate_indicators(str(asset.id), asset.display_symbol)
        if not indicators:
            raise ValueError("Not enough historical data to generate AI insight")

        NewsService.fetch_and_store_news(asset)
        news_items = self.build_asset_context_pack(asset)
        story_so_far = self.build_story_so_far(asset, news_items)

        provider = self.ai_auth.provider_name
        model = self.ai_auth.get_model_for_task("indicator_insight")
        api_key = self.get_api_key()

        prompt = self.build_indicator_insight_prompt(asset, indicators, news_items, story_so_far)

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
        elif provider == "google":
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            response = genai.GenerativeModel(model).generate_content(prompt)
            response_text = response.text
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        cost_usd = self._estimate_provider_cost(provider, model, prompt_tokens, completion_tokens)

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

        result = {
            "symbol": asset.display_symbol,
            "market": asset.market,
            "recommendation": parsed.get("recommendation", "HOLD"),
            "confidence": int(parsed.get("confidence", 50)),
            "summary": parsed.get("summary", parsed.get("reasoning", "")),
            "technical_summary": parsed.get("technical_summary", ""),
            "news_context": parsed.get("news_context", ""),
            "reasoning": parsed.get("reasoning", ""),
            "price_target": parsed.get("price_target"),
            "model_used": model,
            "generated_at": timezone.now().isoformat(),
            "news_items": [
                {
                    "headline": item["headline"],
                    "url": item["url"],
                    "source": item["source"],
                    "published_at": item["published_at"].isoformat() if item["published_at"] else None,
                    "bucket": item["bucket"],
                    "provenance": item["provenance"],
                    "relevance_basis": item["relevance_basis"],
                    "asset_symbol": item["asset_symbol"],
                    "market": item["market"],
                }
                for item in news_items
            ],
        }

        cache.set(cache_key, result, timeout=86400)

        return result

    def analyze_scope(self, scope_type: str, scope_label: str, assets, holdings: list[dict]) -> dict:
        if scope_type not in {"portfolio", "watch"}:
            raise ValueError(f"Unsupported scope type: {scope_type}")
        if not assets:
            raise ValueError("No assets available for monitored set insight")
        if not self.ai_auth or not self.get_api_key():
            raise ValueError("AI is not configured for this user")

        news_items = self.build_scope_context_pack(assets)
        scope_signature = hashlib.sha256(
            json.dumps(
                {
                    "scope_type": scope_type,
                    "scope_label": scope_label,
                    "holdings": holdings,
                    "news_items": news_items,
                },
                sort_keys=True,
                default=str,
            ).encode("utf-8")
        ).hexdigest()
        cache_key = f"ai_scope_insight:v2:{self.user.id}:{scope_type}:{scope_signature}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        self.check_budget()

        provider = self.ai_auth.provider_name
        model = self.ai_auth.get_model_for_task("indicator_insight")
        api_key = self.get_api_key()
        prompt = self.build_scope_insight_prompt(scope_type, scope_label, holdings, news_items)

        response_text = ""
        prompt_tokens = 0
        completion_tokens = 0

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
        elif provider == "google":
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            response = genai.GenerativeModel(model).generate_content(prompt)
            response_text = response.text
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        cost_usd = self._estimate_provider_cost(provider, model, prompt_tokens, completion_tokens)

        parsed = self._extract_json_object(response_text)
        if not parsed:
            raise ValueError("AI returned an invalid response")

        self.log_call(
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=cost_usd,
            task_type=f"{scope_type}_insight",
        )

        result = {
            "scope_type": scope_type,
            "scope_label": scope_label,
            "asset_count": len(holdings),
            "recommendation": parsed.get("recommendation", "HOLD"),
            "confidence": int(parsed.get("confidence", 50)),
            "summary": parsed.get("summary", ""),
            "technical_summary": parsed.get("technical_summary", ""),
            "news_context": parsed.get("news_context", ""),
            "reasoning": parsed.get("reasoning", ""),
            "model_used": model,
            "generated_at": timezone.now().isoformat(),
        }

        cache.set(cache_key, result, timeout=900)
        return result

    @staticmethod
    def analyze_news_sentiment(headlines: list[str], user=None) -> dict[str, Decimal]:
        """Analyze sentiment for news headlines using configured AI provider.

        Returns dict mapping headline to sentiment score (-1.0 to 1.0).
        If API call fails, returns empty dict.
        """
        if not headlines:
            return {}

        headlines_sorted = sorted(headlines)
        cache_key = f"sentiment:{hash(tuple(headlines_sorted))}"
        cached = cache.get(cache_key)
        if cached:
            return cached

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

        prompt = AIService.build_sentiment_prompt(headlines)

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
            result = {h: Decimal(str(s)) for h, s in sentiments.items() if h in headlines}
            cache.set(cache_key, result, timeout=86400)
            return result
        except Exception as e:
            logger.exception(f"Failed to analyze news sentiment: {e}")
            return {}
