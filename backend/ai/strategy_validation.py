import json
import logging
import re
from decimal import Decimal
from uuid import UUID

from django.shortcuts import get_object_or_404

from markets.models import Asset, TechnicalIndicators
from markets.quote_provider import get_latest_quote
from portfolios.models import Portfolio
from trading.models import Position

from .models import StrategyRecommendation, StrategyScenarioFrame
from .services import AIBudgetError, AIService

logger = logging.getLogger("paper_trader.ai")

SCENARIO_CASES = {"base", "bull", "bear"}
CONFIDENCE_BANDS = {"low", "medium", "high"}
DIRECTION_VALUES = {"conditional", "supportive", "adverse"}
SCENARIO_TEMPERATURE = 0.95
SCENARIO_MAX_OUTPUT_TOKENS = 1400
EVIDENCE_SOURCES = {
    "candidate",
    "technical_inputs",
    "context_inputs",
    "sentiment_trajectory_inputs",
    "divergence_inputs",
    "guardrails",
}
TRADE_IDEA_KEYS = {
    "asset",
    "asset_id",
    "action",
    "quantity",
    "trade",
    "order",
    "proposed_action",
    "proposed_quantity",
    "target_quantity",
}
GENERIC_SCENARIO_PHRASES = {
    "market context",
    "recent context",
    "stored context",
    "technical evidence",
    "sentiment trajectory",
    "trade idea",
}


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
    recommendation = AIService.recommendation_from_votes(technical_vote, context_vote, trajectory_vote)
    if recommendation == action:
        return "approve", "The shared evidence recommendation supports the candidate direction."
    if recommendation == "HOLD":
        return "defer", "The shared evidence recommendation is HOLD."
    return "reject", "The shared evidence recommendation conflicts with the candidate direction."


def _fallback_rationale(verdict: str) -> str:
    if verdict == "approve":
        return (
            "The current setup supports this trade, and the recent market context does not raise a clear warning."
        )
    if verdict == "reject":
        return "This trade looks weak right now: the price setup or recent market context is moving against it."
    return "There is not enough clear support right now to make a confident call on this trade."


def _references_supported(items: list[dict]) -> bool:
    if not items:
        return False
    return all(isinstance(item, dict) and item.get("source") in EVIDENCE_SOURCES and item.get("text") for item in items)


def _distinctive_words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) >= 4}


def _leans_on_context_text(risk_notes: str, context_texts: list[str]) -> bool:
    risk_notes_normalized = risk_notes.lower()
    if any(text.lower() in risk_notes_normalized for text in context_texts):
        return True
    risk_words = _distinctive_words(risk_notes)
    for text in context_texts:
        context_words = _distinctive_words(text)
        if context_words and len(risk_words.intersection(context_words)) >= min(2, len(context_words)):
            return True
    return False


def _contains_trade_idea(value) -> bool:
    if isinstance(value, dict):
        if TRADE_IDEA_KEYS.intersection(value.keys()):
            return True
        return any(_contains_trade_idea(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_trade_idea(item) for item in value)
    return False


def validate_scenario_frame_payloads(frames: list[dict], context_texts: list[str] | None = None) -> list[dict]:
    if len(frames) > 3:
        raise ValueError("Scenario frame count exceeds the three-case cap")

    concrete_context_texts = [text for text in context_texts or [] if text]
    seen_cases = set()
    validated = []
    for frame in frames:
        scenario_case = frame.get("scenario_case")
        confidence_band = frame.get("confidence_band")
        catalysts = frame.get("catalysts")
        invalidating_conditions = frame.get("invalidating_conditions")
        risk_notes = frame.get("risk_notes")
        position_size_guidance = frame.get("position_size_guidance")

        if scenario_case not in SCENARIO_CASES:
            raise ValueError("Scenario frame has an invalid case")
        if scenario_case in seen_cases:
            raise ValueError("Scenario frame case is duplicated")
        if confidence_band not in CONFIDENCE_BANDS:
            raise ValueError("Scenario frame has an invalid confidence band")
        if frame.get("direction") not in DIRECTION_VALUES:
            raise ValueError("Scenario frame is missing direction")
        if not _references_supported(catalysts):
            raise ValueError("Scenario frame has unsupported catalysts")
        if not _references_supported(invalidating_conditions):
            raise ValueError("Scenario frame has unsupported invalidating conditions")
        if not isinstance(risk_notes, str) or not risk_notes:
            raise ValueError("Scenario frame is missing risk notes")
        if any(phrase in risk_notes.lower() for phrase in GENERIC_SCENARIO_PHRASES):
            raise ValueError("Scenario frame uses generic risk notes")
        if not isinstance(position_size_guidance, str) or not position_size_guidance:
            raise ValueError("Scenario frame is missing position-size guidance")
        if _contains_trade_idea(frame):
            raise ValueError("Scenario frame cannot create a new trade idea")

        seen_cases.add(scenario_case)
        validated.append(
            {
                "scenario_case": scenario_case,
                "direction": frame["direction"],
                "catalysts": catalysts,
                "invalidating_conditions": invalidating_conditions,
                "confidence_band": confidence_band,
                "risk_notes": risk_notes,
                "position_size_guidance": position_size_guidance,
            }
        )
    if concrete_context_texts and not any(
        _leans_on_context_text(frame["risk_notes"], concrete_context_texts) for frame in validated
    ):
        raise ValueError("Scenario frame risk notes do not use stored context")
    return validated


def _direction_for(action: str, scenario_case: str) -> str:
    if scenario_case == "base":
        return "conditional"
    supports_buy = scenario_case == "bull"
    if action == "BUY":
        return "supportive" if supports_buy else "adverse"
    return "adverse" if supports_buy else "supportive"


def _parse_scenario_response(response_text: str) -> list[dict]:
    text = response_text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    elif not text.startswith("["):
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            text = text[start : end + 1]

    parsed = json.loads(text)
    if not isinstance(parsed, list):
        raise ValueError("Scenario response must be a JSON array")
    return parsed


def _normalize_ai_scenario_payloads(
    frames: list[dict],
    recommendation: StrategyRecommendation,
    position_size_guidance: str,
) -> list[dict]:
    context_texts = _direct_context_texts(recommendation)
    normalized = []
    for frame in frames:
        if not isinstance(frame, dict):
            normalized.append(frame)
            continue

        scenario_case = frame.get("scenario_case")
        next_frame = dict(frame)
        if scenario_case in SCENARIO_CASES:
            next_frame["direction"] = _direction_for(recommendation.action, scenario_case)
        next_frame["catalysts"] = _normalize_reference_sources(next_frame.get("catalysts"))
        next_frame["invalidating_conditions"] = _normalize_reference_sources(
            next_frame.get("invalidating_conditions")
        )
        if not next_frame.get("position_size_guidance"):
            next_frame["position_size_guidance"] = position_size_guidance
        if scenario_case in SCENARIO_CASES and not next_frame.get("catalysts"):
            next_frame["catalysts"] = [
                {
                    "source": "candidate",
                    "text": (
                        f"The model did not provide a concrete {scenario_case} catalyst; "
                        f"treat this as a weak scenario for the submitted {recommendation.action}."
                    ),
                }
            ]
        risk_notes = next_frame.get("risk_notes")
        if (
            not isinstance(risk_notes, str)
            or any(phrase in risk_notes.lower() for phrase in GENERIC_SCENARIO_PHRASES)
            or (context_texts and not _leans_on_context_text(risk_notes, context_texts))
        ):
            next_frame["risk_notes"] = _repair_ai_risk_notes(next_frame, recommendation)
        normalized.append(next_frame)
    return normalized


def _normalize_reference_sources(items) -> list[dict]:
    if isinstance(items, dict):
        items = [items]
    normalized = []
    for item in items or []:
        if not isinstance(item, dict):
            normalized.append(item)
            continue
        next_item = dict(item)
        if next_item.get("source") not in EVIDENCE_SOURCES:
            next_item["source"] = "context_inputs"
        normalized.append(next_item)
    return normalized


def _repair_ai_risk_notes(frame: dict, recommendation: StrategyRecommendation) -> str:
    scenario_case = frame.get("scenario_case")
    candidate_symbol = getattr(recommendation, "candidate", {}).get("asset_symbol") or "this asset"
    event_text = _direct_context_text_for_case(recommendation, scenario_case)
    if not event_text:
        event_text = f"No direct {candidate_symbol} headline is available; treat this as a price-led scenario"
    effect = _trade_effect_for(recommendation.action, scenario_case)
    return f'{event_text}. {effect} Keep the trade conditional unless price action confirms this scenario.'


def _trade_effect_for(action: str, scenario_case: str) -> str:
    if scenario_case == "bull":
        return (
            "That asset-positive path supports the submitted BUY trade."
            if action == "BUY"
            else "That asset-positive path works against the submitted SELL trade."
        )
    if scenario_case == "bear":
        return (
            "That asset-negative path works against the submitted BUY trade."
            if action == "BUY"
            else "That asset-negative path supports the submitted SELL trade."
        )
    return "That evidence keeps the submitted trade conditional rather than decisive."


def _risk_notes(*, portfolio: Portfolio, quantity: int, quote, current_position: Position | None) -> str:
    price = quote.price if quote else Decimal("0")
    gross_value = price * Decimal(quantity)
    position_quantity = current_position.quantity if current_position else 0
    return (
        f"Candidate value {gross_value} {portfolio.base_currency}; available cash {portfolio.current_cash} "
        f"{portfolio.base_currency}; current position {position_quantity} shares."
    )


def _position_size_guidance(*, portfolio: Portfolio, quantity: int, quote, current_position: Position | None) -> str:
    context = _risk_context(portfolio=portfolio, quantity=quantity, quote=quote, current_position=current_position)
    return (
        f"Submitted value is {context['trade_value']} {context['currency']}; "
        f"current position is {context['position_quantity']} shares; "
        f"max-position reference is {context['max_position_size_pct']}%."
    )


def _risk_context(*, portfolio: Portfolio, quantity: int, quote, current_position: Position | None) -> dict:
    try:
        guardrails = portfolio.guardrails
    except Exception:
        guardrails = None
    price = quote.price if quote else Decimal("0")
    trade_value = (price * Decimal(quantity)).quantize(Decimal("0.01"))
    available_cash = portfolio.current_cash.quantize(Decimal("0.01"))
    cash_pct = None
    if available_cash > 0:
        cash_pct = ((trade_value / available_cash) * Decimal("100")).quantize(Decimal("0.1"))
    return {
        "available_cash": available_cash,
        "cash_pct": cash_pct,
        "currency": portfolio.base_currency,
        "guardrails_enabled": bool(guardrails and guardrails.enabled),
        "max_position_size_pct": guardrails.max_position_size_pct if guardrails else Decimal("20.00"),
        "position_quantity": current_position.quantity if current_position else 0,
        "trade_value": trade_value,
    }


def _size_pressure_phrase(context: dict) -> str:
    if context["cash_pct"] is None:
        return "Cash impact cannot be compared because available cash is zero."
    if context["cash_pct"] >= Decimal("75.0"):
        return f"This would use about {context['cash_pct']}% of available cash, so the trade size is heavy."
    if context["cash_pct"] >= Decimal("30.0"):
        return f"This would use about {context['cash_pct']}% of available cash, so the trade size is meaningful."
    return f"This would use about {context['cash_pct']}% of available cash, so the trade size is modest."


def _scenario_phrase(recommendation: StrategyRecommendation, scenario_case: str, phrases: list[str]) -> str:
    offset = {"base": 0, "bull": 1, "bear": 2}[scenario_case]
    return phrases[(recommendation.candidate_id.int + offset) % len(phrases)]


def _headline_context(recommendation: StrategyRecommendation) -> tuple[str, str, bool]:
    context_items = recommendation.context_inputs.get("items", [])
    if not context_items:
        return "No stored headline gives this trade extra support.", "", False
    headline = context_items[0].get("headline") or "Stored news is available, but the headline is missing."
    return headline, f'The stored catalyst is "{headline}".', True


def _fallback_scenario_frames(recommendation: StrategyRecommendation, context: dict) -> list[dict]:
    action_word = "buy" if recommendation.action == "BUY" else "sell"
    supportive_case = "bull" if recommendation.action == "BUY" else "bear"
    adverse_case = "bear" if recommendation.action == "BUY" else "bull"
    adverse_context = "negative" if recommendation.action == "BUY" else "positive"
    context_text, risk_context_sentence, has_context_news = _headline_context(recommendation)
    context_vote = recommendation.context_inputs.get("vote")
    submitted_value = f"{context['trade_value']} {context['currency']}"
    base_open = _scenario_phrase(
        recommendation,
        "base",
        [
            "The middle path is not dramatic:",
            "The plain reading is this:",
            "The default case is measured:",
        ],
    )
    bull_open = _scenario_phrase(
        recommendation,
        "bull",
        [
            "The bull case matters only if the asset can keep improving:",
            "The upside path depends on buyers staying in control:",
            "The asset-positive path needs the good news to keep mattering:",
        ],
    )
    bear_open = _scenario_phrase(
        recommendation,
        "bear",
        [
            "The bear case matters if pressure keeps building:",
            "The downside path depends on sellers staying in control:",
            "The asset-negative path needs the bad news to keep mattering:",
        ],
    )
    base_context_sentence = (
        risk_context_sentence
        if has_context_news
        else "No stored headline explains the move, so this is a chart-led read."
    )
    if has_context_news and context_vote == "positive":
        bull_context_sentence = risk_context_sentence
        bull_effect = "That asset-positive catalyst supports the BUY" if recommendation.action == "BUY" else (
            "That asset-positive catalyst works against the SELL"
        )
        bear_context_sentence = f"{risk_context_sentence} That is not bear evidence."
        bear_effect = (
            "The BUY only weakens if price action breaks despite it"
            if recommendation.action == "BUY"
            else "The SELL only strengthens if price action breaks despite it"
        )
    elif has_context_news and context_vote == "negative":
        bull_context_sentence = f"{risk_context_sentence} That is not bull evidence."
        bull_effect = (
            "The BUY only strengthens if price action recovers despite it"
            if recommendation.action == "BUY"
            else "The SELL only weakens if price action recovers despite it"
        )
        bear_context_sentence = risk_context_sentence
        bear_effect = "That asset-negative catalyst supports the SELL" if recommendation.action == "SELL" else (
            "That asset-negative catalyst works against the BUY"
        )
    else:
        bull_context_sentence = (
            "There is no stored bullish headline, so the asset-positive path needs price confirmation."
        )
        bull_effect = (
            "That path supports the BUY" if recommendation.action == "BUY" else "That path works against the SELL"
        )
        bear_context_sentence = (
            "There is no stored bearish headline, so the asset-negative path needs price confirmation."
        )
        bear_effect = (
            "That path supports the SELL" if recommendation.action == "SELL" else "That path works against the BUY"
        )
    bull_candidate_text = (
        "The asset-bullish path supports the submitted BUY candidate."
        if recommendation.action == "BUY"
        else "The asset-bullish path is adverse to the submitted SELL candidate."
    )
    bear_candidate_text = (
        "The asset-bearish path is adverse to the submitted BUY candidate."
        if recommendation.action == "BUY"
        else "The asset-bearish path supports the submitted SELL candidate."
    )

    return [
        {
            "scenario_case": "base",
            "direction": _direction_for(recommendation.action, "base"),
            "catalysts": [
                {
                    "source": "technical_inputs",
                    "text": (
                        "The setup stays usable while the technical vote remains "
                        f"{recommendation.technical_inputs['vote']}."
                    ),
                },
                {
                    "source": "context_inputs",
                    "text": f"Stored context is currently {recommendation.context_inputs['vote']}.",
                },
            ],
            "invalidating_conditions": [
                {
                    "source": "sentiment_trajectory_inputs",
                    "text": "A sentiment trajectory shift against the candidate would weaken this base case.",
                }
            ],
            "confidence_band": "medium" if recommendation.verdict == "approve" else "low",
            "risk_notes": (
                f"{base_open} treat this as a cautious {action_word}, not a conviction call. "
                f"{base_context_sentence} {_size_pressure_phrase(context)} With {context['position_quantity']} "
                "shares already held, this is worth doing only if you are comfortable with a meaningful trade."
            ),
            "position_size_guidance": "Keep the submitted quantity as the cap for this validation.",
        },
        {
            "scenario_case": "bull",
            "direction": _direction_for(recommendation.action, "bull"),
            "catalysts": [
                {"source": "context_inputs", "text": context_text},
                {
                    "source": "candidate",
                    "text": bull_candidate_text,
                },
            ],
            "invalidating_conditions": [
                {
                    "source": "technical_inputs",
                    "text": "The asset-bullish path breaks if technical evidence stops confirming asset upside.",
                }
            ],
            "confidence_band": "medium" if recommendation.verdict == "approve" else "low",
            "risk_notes": (
                f"{bull_open} {bull_context_sentence} {bull_effect}; if it is not persuasive, avoid treating "
                f"the {submitted_value} trade as high confidence."
            ),
            "position_size_guidance": (
                f"Do not scale up from this case alone; max-position reference is "
                f"{context['max_position_size_pct']}%."
            ),
        },
        {
            "scenario_case": "bear",
            "direction": _direction_for(recommendation.action, "bear"),
            "catalysts": [
                {
                    "source": "divergence_inputs",
                    "text": "Stored divergence or weak evidence belongs in the asset-bearish path.",
                },
                {
                    "source": "candidate",
                    "text": bear_candidate_text,
                },
            ],
            "invalidating_conditions": [
                {
                    "source": "context_inputs",
                    "text": (
                        f"The asset-bearish path fades if stored context moves back toward {adverse_context} "
                        f"evidence for the asset, which is adverse to the submitted {action_word}."
                    ),
                }
            ],
            "confidence_band": "low",
            "risk_notes": (
                f"{bear_open} {bear_context_sentence} {bear_effect}; if the {adverse_case} case feels more "
                f"plausible than the {supportive_case} case, skip or reduce the {action_word}."
            ),
            "position_size_guidance": "Use this as the caution case.",
        },
    ]


def _scenario_prompt(*, recommendation: StrategyRecommendation, risk_notes: str, position_size_guidance: str) -> str:
    context_items = recommendation.context_inputs.get("items", [])
    direct_context_texts = set(_direct_context_texts(recommendation))
    direct_context_items = [
        item
        for item in context_items
        if item.get("headline") in direct_context_texts
    ]
    direct_context_inputs = dict(recommendation.context_inputs)
    direct_context_inputs["items"] = direct_context_items
    direct_context_inputs["item_count"] = len(direct_context_items)
    if not direct_context_items:
        direct_context_inputs["vote"] = "neutral"
    payload = {
        "candidate": recommendation.candidate,
        "technical_inputs": recommendation.technical_inputs,
        "context_inputs": direct_context_inputs,
        "sentiment_trajectory_inputs": recommendation.sentiment_trajectory_inputs,
        "divergence_inputs": recommendation.divergence_inputs,
        "verdict": recommendation.verdict,
        "risk_notes": risk_notes,
        "position_size_guidance": position_size_guidance,
        "allowed_sources": sorted(EVIDENCE_SOURCES),
    }
    return (
        "Generate exactly three compact scenario frames for an investment recommendation.\n"
        "Use only the JSON evidence provided.\n"
        "Cases must be base, bull, and bear. Confidence bands must be low, medium, or high.\n"
        "Each catalyst and invalidating condition must be an object with source and text.\n"
        "Do not propose a different asset, action, quantity, order, or trade.\n"
        "Write the scenarios as if for a user-facing experience, not an internal report. Consider the user is new "
        "to trading and looking for clear guidance on how to interpret the recommendation and its risks. "
        "Use simple terms.\n"
        "Do not reuse stock openings like 'the ordinary case is simple' or 'the favorable case'. Vary wording.\n"
        "Write risk_notes as the user-facing scenario text: 2 or 3 short, assertive sentences with a beginning, "
        "middle, and end. Do not mention internal field names, votes, guardrails, payloads, or validation mechanics. "
        "The context_inputs items include direct asset news only. If context_inputs.items is empty, do not invent "
        "news or use other-symbol read-through; say there is no direct stored headline and make the scenario "
        "price-led. Do not use generic labels like recent context, market context, technical evidence, or "
        "sentiment trajectory. "
        "For SELL, asset-negative or bear evidence supports the trade; asset-positive or bull evidence is adverse. "
        "If a scenario is weak, say plainly that the user should ignore it in favor of the stronger case. "
        "Write position_size_guidance as one terse audit sentence; it will not be shown in the main UI.\n"
        "Direction must be conditional, supportive, or adverse. Do not use BUY or SELL as direction. "
        "Every frame must have non-empty catalysts, invalidating_conditions, and position_size_guidance. "
        "Do not wrap the JSON in markdown fences.\n"
        "Return only a JSON array of objects with scenario_case, direction, catalysts, "
        "invalidating_conditions, confidence_band, risk_notes, and position_size_guidance.\n\n"
        f"{json.dumps(_json_safe(payload), ensure_ascii=True, default=str)}"
    )


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


def _context_texts(recommendation: StrategyRecommendation) -> list[str]:
    return [
        item.get("headline", "")
        for item in getattr(recommendation, "context_inputs", {}).get("items", [])
        if item.get("headline")
    ]


def _direct_context_texts(recommendation: StrategyRecommendation) -> list[str]:
    return [item["headline"] for item in _direct_context_items(recommendation)]


def _direct_context_items(recommendation: StrategyRecommendation) -> list[dict]:
    candidate_symbol = str(getattr(recommendation, "candidate", {}).get("asset_symbol") or "").upper()
    direct_buckets = {"symbol", "company"}
    return [
        item
        for item in getattr(recommendation, "context_inputs", {}).get("items", [])
        if item.get("headline")
        and (
            item.get("bucket") in direct_buckets
            or (candidate_symbol and str(item.get("asset_symbol") or "").upper() == candidate_symbol)
        )
    ]


def _direct_context_text_for_case(recommendation: StrategyRecommendation, scenario_case: str) -> str:
    items = _direct_context_items(recommendation)
    if not items:
        return ""
    if scenario_case == "bull":
        preferred = [item for item in items if _sentiment_score(item) > Decimal("0")]
        return max(preferred or items, key=_sentiment_score)["headline"]
    if scenario_case == "bear":
        preferred = [item for item in items if _sentiment_score(item) < Decimal("0")]
        return min(preferred or items, key=_sentiment_score)["headline"]
    return items[0]["headline"]


def _sentiment_score(item: dict) -> Decimal:
    try:
        return Decimal(str(item.get("sentiment_score") or "0"))
    except Exception:
        return Decimal("0")


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
        "You are writing a friendly recommendation rationale for a trading app.\n"
        "The verdict is already determined by deterministic rules. Do not change it, dispute it, "
        "or suggest a different verdict.\n"
        "Use only the provided evidence. Do not add outside market facts.\n"
        "Write 3 to 4 conversational sentences for an end user deciding whether to place this trade.\n"
        "Start with the plain trade, not with approval mechanics. Do not start with phrases like "
        "\"The trade is approved\", \"This decision is supported\", or \"The verdict\".\n"
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
        logger.info("Strategy validation rationale prompt: %s", prompt)

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

        logger.info("Strategy validation rationale raw response: %s", response_text)
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

    def _generate_scenario_payloads(
        self,
        *,
        recommendation: StrategyRecommendation,
        quote,
        current_position: Position | None,
    ) -> list[dict]:
        risk_notes = _risk_notes(
            portfolio=recommendation.portfolio,
            quantity=recommendation.quantity,
            quote=quote,
            current_position=current_position,
        )
        position_size_guidance = _position_size_guidance(
            portfolio=recommendation.portfolio,
            quantity=recommendation.quantity,
            quote=quote,
            current_position=current_position,
        )
        ai_payloads = self._generate_ai_scenario_payloads(
            recommendation=recommendation,
            risk_notes=risk_notes,
            position_size_guidance=position_size_guidance,
        )
        if ai_payloads is not None:
            return ai_payloads

        context = _risk_context(
            portfolio=recommendation.portfolio,
            quantity=recommendation.quantity,
            quote=quote,
            current_position=current_position,
        )
        return _fallback_scenario_frames(recommendation, context)

    def _generate_ai_scenario_payloads(
        self,
        *,
        recommendation: StrategyRecommendation,
        risk_notes: str,
        position_size_guidance: str,
    ) -> list[dict] | None:
        provider, api_key = self.ai_service.get_api_credentials()
        if not provider or not api_key:
            return None

        try:
            self.ai_service.check_budget()
        except AIBudgetError:
            return None

        model = self.ai_service.ai_auth.get_model_for_task("trade_validation")
        prompt = _scenario_prompt(
            recommendation=recommendation,
            risk_notes=risk_notes,
            position_size_guidance=position_size_guidance,
        )
        logger.info("Strategy validation scenario prompt: %s", prompt)

        response_text = ""
        prompt_tokens = 0
        completion_tokens = 0
        try:
            if provider == "anthropic":
                import anthropic

                message = anthropic.Anthropic(api_key=api_key).messages.create(
                    model=model,
                    max_tokens=SCENARIO_MAX_OUTPUT_TOKENS,
                    temperature=SCENARIO_TEMPERATURE,
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
                    max_output_tokens=SCENARIO_MAX_OUTPUT_TOKENS,
                    temperature=SCENARIO_TEMPERATURE,
                    input=prompt,
                )
                response_text = response.output_text
                if getattr(response, "usage", None):
                    prompt_tokens = getattr(response.usage, "input_tokens", 0) or 0
                    completion_tokens = getattr(response.usage, "output_tokens", 0) or 0
            elif provider == "google":
                import google.generativeai as genai

                genai.configure(api_key=api_key)
                response = genai.GenerativeModel(model).generate_content(
                    prompt,
                    generation_config={"temperature": SCENARIO_TEMPERATURE},
                )
                response_text = response.text
            else:
                return None

            logger.info("Strategy validation scenario raw response: %s", response_text)
            parsed = _parse_scenario_response(response_text)
            parsed = _normalize_ai_scenario_payloads(parsed, recommendation, position_size_guidance)
            validated = validate_scenario_frame_payloads(parsed, context_texts=_direct_context_texts(recommendation))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            logger.warning(
                "Strategy validation scenario generation failed; falling back. error=%s raw_response=%s",
                exc,
                response_text,
            )
            return None

        self.ai_service.log_call(
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=AIService._estimate_provider_cost(provider, model, prompt_tokens, completion_tokens),
            task_type="trade_validation",
        )
        return validated

    def _persist_scenario_frames(
        self,
        *,
        recommendation: StrategyRecommendation,
        quote,
        current_position: Position | None,
    ) -> None:
        frames = validate_scenario_frame_payloads(
            self._generate_scenario_payloads(
                recommendation=recommendation,
                quote=quote,
                current_position=current_position,
            ),
            context_texts=_direct_context_texts(recommendation),
        )
        StrategyScenarioFrame.objects.bulk_create(
            [
                StrategyScenarioFrame(
                    recommendation=recommendation,
                    scenario_case=frame["scenario_case"],
                    direction=frame["direction"],
                    catalysts=frame["catalysts"],
                    invalidating_conditions=frame["invalidating_conditions"],
                    confidence_band=frame["confidence_band"],
                    risk_notes=frame["risk_notes"],
                    position_size_guidance=frame["position_size_guidance"],
                )
                for frame in frames
            ]
        )

    def validate(self, *, portfolio_id, asset_id, action, quantity, rationale=""):
        portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=self.user)
        asset = get_object_or_404(Asset, id=asset_id)
        if portfolio.market != asset.market:
            raise ValueError("Portfolio and asset markets do not match")

        quote = get_latest_quote(str(asset.id))
        indicators = TechnicalIndicators.objects.filter(asset=asset).order_by("-date").first()
        technical_inputs = _indicator_payload(indicators)
        technical_vote = AIService._technical_vote(technical_inputs, quote.price if quote else None)

        context_items = AIService.build_asset_context_pack(asset, operator=self.user)
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

        current_position = Position.objects.filter(portfolio=portfolio, asset=asset).first()
        recommendation = StrategyRecommendation.objects.create(
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
        self._persist_scenario_frames(
            recommendation=recommendation,
            quote=quote,
            current_position=current_position,
        )
        return recommendation
