import json
from decimal import Decimal
from uuid import UUID

from django.shortcuts import get_object_or_404

from markets.models import Asset, TechnicalIndicators
from markets.quote_provider import get_latest_quote
from portfolios.models import Portfolio

from .models import StrategyRecommendation
from .services import AIBudgetError, AIService


def _json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def _indicator_payload(indicators):
    if not indicators:
        return {}
    return {
        "date": indicators.date,
        "rsi_14": indicators.rsi_14,
        "macd": indicators.macd,
        "macd_signal": indicators.macd_signal,
        "macd_histogram": indicators.macd_histogram,
        "ma_20": indicators.ma_20,
        "ma_50": indicators.ma_50,
        "ma_200": indicators.ma_200,
        "bb_upper": indicators.bb_upper,
        "bb_middle": indicators.bb_middle,
        "bb_lower": indicators.bb_lower,
        "volume_20d_avg": indicators.volume_20d_avg,
    }


def _desired_vote(action: str) -> str:
    return "positive" if action == "BUY" else "negative"


def _opposite_vote(action: str) -> str:
    return "negative" if action == "BUY" else "positive"


def _verdict_for(action: str, technical_vote: str, context_vote: str, trajectory_vote: str) -> tuple[str, str]:
    desired = _desired_vote(action)
    opposite = _opposite_vote(action)

    if technical_vote == opposite:
        return "reject", "Technical evidence conflicts with the candidate direction."
    if context_vote == opposite or trajectory_vote == opposite:
        return "reject", "Context or sentiment evidence conflicts with the candidate direction."
    if technical_vote == "neutral":
        return "defer", "Technical evidence is insufficient for a recommendation."
    if context_vote == desired or trajectory_vote == desired:
        return "approve", "Technical and context evidence support the candidate direction."
    return "defer", "Technical evidence is directional, but context support is insufficient."


def _fallback_rationale(verdict: str) -> str:
    if verdict == "approve":
        return (
            "The current setup supports this trade idea, and the recent market context does not raise a clear warning."
        )
    if verdict == "reject":
        return "This trade idea looks weak right now: the price setup or recent market context is moving against it."
    return "There is not enough clear support right now to make a confident call on this trade idea."


def _compact_news_items(context_record: dict) -> list[dict]:
    return [
        {
            "headline": item.get("headline"),
            "bucket": item.get("bucket"),
            "sentiment_score": item.get("sentiment_score"),
            "published_at": item.get("published_at"),
            "relevance_basis": item.get("relevance_basis"),
        }
        for item in context_record.get("items", [])[:6]
    ]


def _build_rationale_prompt(
    *,
    candidate: dict,
    verdict: str,
    technical_record: dict,
    context_record: dict,
    trajectory_record: dict,
    divergence: dict | None,
) -> str:
    payload = {
        "candidate": _json_safe(candidate),
        "locked_verdict": verdict,
        "technical": {
            "vote": technical_record["vote"],
            "indicators": technical_record["indicators"],
        },
        "context": {
            "vote": context_record["vote"],
            "item_count": context_record["item_count"],
            "items": _compact_news_items(context_record),
        },
        "sentiment_trajectory": trajectory_record,
        "divergence": _json_safe(divergence),
    }
    return (
        "You are writing a friendly recommendation rationale for a paper trading app.\n"
        "The verdict is already determined by deterministic rules. Do not change it, dispute it, "
        "or suggest a different verdict.\n"
        "Use only the provided evidence. Do not add outside market facts.\n"
        "Write 3 to 4 conversational sentences for an end user deciding whether to place this paper trade.\n"
        "Start with the plain trade idea, not with approval mechanics. Do not start with phrases like "
        "\"The paper trade is approved\", \"This decision is supported\", or \"The verdict\".\n"
        "Use concrete company or symbol language instead of abstract labels where possible.\n"
        "Explain what supports the idea, what weakens confidence, and whether the setup is clean or conditional.\n"
        "Prefer natural wording like \"reasonable setup\", \"mildly supportive\", \"fighting the evidence\", "
        "or \"not enough clean evidence\" when accurate.\n"
        "Mention at most two technical details, and translate them into what they mean for the trade.\n"
        "Do not mention internal field names like technical_vote, context_vote, locked verdict, "
        "or macro confirmation.\n"
        "No markdown. Return only the rationale text.\n\n"
        "Style example for tone only, not facts: "
        "\"This buy has a reasonable setup. The chart is leaning in the trade's favor, and the recent news flow "
        "is mildly supportive rather than hostile. It is not a screaming buy, but the pieces are aligned enough "
        "to support the idea.\"\n\n"
        f"{json.dumps(payload, ensure_ascii=True, default=str)}"
    )


class StrategyValidationService:
    def __init__(self, user):
        self.user = user
        self.ai_service = AIService(user)

    def _generate_rationale(
        self,
        *,
        candidate: dict,
        verdict: str,
        technical_record: dict,
        context_record: dict,
        trajectory_record: dict,
        divergence: dict | None,
    ) -> str:
        provider, api_key = self.ai_service.get_api_credentials()
        if not provider or not api_key:
            return _fallback_rationale(verdict)

        try:
            self.ai_service.check_budget()
        except AIBudgetError:
            return _fallback_rationale(verdict)

        model = self.ai_service.ai_auth.get_model_for_task("trade_validation")
        prompt = _build_rationale_prompt(
            candidate=candidate,
            verdict=verdict,
            technical_record=technical_record,
            context_record=context_record,
            trajectory_record=trajectory_record,
            divergence=divergence,
        )

        response_text = ""
        prompt_tokens = 0
        completion_tokens = 0

        if provider == "anthropic":
            import anthropic

            message = anthropic.Anthropic(api_key=api_key).messages.create(
                model=model,
                max_tokens=220,
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
                max_output_tokens=220,
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
            return _fallback_rationale(verdict)

        rationale = response_text.strip()
        if not rationale:
            return _fallback_rationale(verdict)

        self.ai_service.log_call(
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=AIService._estimate_provider_cost(provider, model, prompt_tokens, completion_tokens),
            task_type="trade_validation",
        )
        return rationale

    def validate(self, *, portfolio_id, asset_id, action, quantity, rationale=""):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=self.user)
        asset = get_object_or_404(Asset, id=asset_id)
        if portfolio.market != asset.market:
            raise ValueError("Portfolio and asset markets do not match")

        quote = get_latest_quote(str(asset.id))
        indicators = TechnicalIndicators.objects.filter(asset=asset).order_by("-date").first()
        technical_inputs = _indicator_payload(indicators)
        technical_vote = AIService._technical_vote(technical_inputs, quote.price if quote else None)

        context_items = AIService.build_asset_context_pack(asset)
        sentiment_trajectory = AIService.build_sentiment_trajectory(context_items, {asset.display_symbol})
        trajectory_vote = AIService._trajectory_vote(sentiment_trajectory, {asset.display_symbol})
        context_vote = AIService._context_vote(context_items, trajectory_vote)
        divergence = AIService.build_divergence_analysis(
            "asset",
            [asset],
            context_items,
            sentiment_trajectory,
            indicators=technical_inputs,
        )
        verdict, _ = _verdict_for(action, technical_vote, context_vote, trajectory_vote)

        candidate = {
            "portfolio_id": portfolio.id,
            "asset_id": asset.id,
            "asset_symbol": asset.display_symbol,
            "action": action,
            "quantity": quantity,
            "rationale": rationale,
            "quote": {
                "price": quote.price if quote else None,
                "currency": quote.currency if quote else asset.currency,
                "as_of": quote.as_of if quote else None,
                "fetched_at": quote.fetched_at if quote else None,
                "source": quote.source if quote else None,
                "is_override": quote.is_override if quote else False,
            },
        }
        technical_record = {
            "available": bool(indicators),
            "vote": technical_vote,
            "indicators": technical_inputs,
        }
        context_record = {
            "vote": context_vote,
            "item_count": len(context_items),
            "items": context_items,
        }
        trajectory_record = {
            "vote": trajectory_vote,
            "entries": sentiment_trajectory,
        }
        rationale_text = self._generate_rationale(
            candidate=candidate,
            verdict=verdict,
            technical_record=technical_record,
            context_record=context_record,
            trajectory_record=trajectory_record,
            divergence=divergence,
        )

        return StrategyRecommendation.objects.create(
            user=self.user,
            portfolio=portfolio,
            asset=asset,
            action=action,
            quantity=quantity,
            candidate=_json_safe(candidate),
            technical_inputs=_json_safe(technical_record),
            context_inputs=_json_safe(context_record),
            sentiment_trajectory_inputs=_json_safe(trajectory_record),
            divergence_inputs=_json_safe(divergence) if divergence else None,
            verdict=verdict,
            rationale=rationale_text,
        )
