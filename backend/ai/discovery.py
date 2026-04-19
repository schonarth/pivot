import hashlib
import json
import logging
from dataclasses import dataclass
from decimal import Decimal

from django.core.cache import cache
from django.utils import timezone

from .services import AIService, AIBudgetError
from markets.models import Asset, AssetQuote, OHLCV, TechnicalIndicators
from trading.models import Position

logger = logging.getLogger("paper_trader.ai.discovery")

LIQUIDITY_FLOOR = Decimal("50000")
BREAKOUT_DISTANCE_PCT = Decimal("0.025")
SURVIVOR_CAP = 20
SHORTLIST_CAP = 5
REFINED_CACHE_TTL = 86400


@dataclass(slots=True)
class DiscoveryCandidate:
    asset_id: str
    symbol: str
    market: str
    rank_score: Decimal
    technical_score: int
    breakout_score: int
    context_score: int
    freshness_score: int
    technical_signals: dict
    context_summary: dict
    discovery_reason: str
    watch_action_ready: bool = True
    refined_reason: str | None = None

    def as_dict(self, rank: int) -> dict:
        payload = {
            "asset_id": self.asset_id,
            "symbol": self.symbol,
            "market": self.market,
            "rank": rank,
            "score": str(self.rank_score),
            "score_breakdown": {
                "technical_setup": self.technical_score,
                "breakout": self.breakout_score,
                "context_support": self.context_score,
                "freshness": self.freshness_score,
            },
            "technical_signals": self.technical_signals,
            "context_summary": self.context_summary,
            "discovery_reason": self.discovery_reason,
            "watch_action_ready": self.watch_action_ready,
        }
        if self.refined_reason:
            payload["refined_reason"] = self.refined_reason
        return payload


class OpportunityDiscoveryService:
    def __init__(self, user=None):
        self.user = user
        self.ai_service = AIService(user) if user else None

    @staticmethod
    def _decimal(value) -> Decimal:
        return Decimal(str(value))

    @staticmethod
    def _quantize(value: Decimal | None, places: str = "0.01") -> str | None:
        if value is None:
            return None
        return str(value.quantize(Decimal(places)))

    @staticmethod
    def _to_json_safe(value):
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, dict):
            return {key: OpportunityDiscoveryService._to_json_safe(item) for key, item in value.items()}
        if isinstance(value, list):
            return [OpportunityDiscoveryService._to_json_safe(item) for item in value]
        return value

    @staticmethod
    def _median_highest(values: list[Decimal], length: int) -> Decimal | None:
        if len(values) < length:
            return None
        window = values[-length:]
        return sum(window, Decimal("0")) / Decimal(length)

    @staticmethod
    def _latest_quote(asset: Asset) -> AssetQuote | None:
        return AssetQuote.objects.filter(asset=asset).order_by("-fetched_at").first()

    @staticmethod
    def _latest_indicators(asset: Asset) -> TechnicalIndicators | None:
        return TechnicalIndicators.objects.filter(asset=asset).order_by("-date").first()

    @staticmethod
    def _is_enabled_market(market: str) -> bool:
        return market in {"BR", "US", "UK", "EU"}

    def _held_asset_ids(self, market: str) -> set[str]:
        if not self.user:
            return set()

        return {
            str(asset_id)
            for asset_id in Position.objects.filter(
                portfolio__user=self.user,
                asset__market=market,
            ).values_list("asset_id", flat=True)
        }

    @staticmethod
    def _freshness_score(quote: AssetQuote | None, latest_close_date) -> tuple[int, int]:
        if quote:
            as_of = quote.as_of
            if timezone.is_naive(as_of):
                as_of = timezone.make_aware(as_of, timezone=timezone.get_current_timezone())
            hours_old = max(0, int((timezone.now() - as_of).total_seconds() // 3600))
            if hours_old <= 6:
                return 2, hours_old
            if hours_old <= 24:
                return 1, hours_old
            if hours_old <= 72:
                return 0, hours_old
            return 0, hours_old

        if latest_close_date:
            age_days = max(0, (timezone.now().date() - latest_close_date).days)
            if age_days <= 1:
                return 1, age_days * 24

        return 0, 0

    def _context_bundle(self, asset: Asset) -> tuple[dict, int, list[dict]]:
        context_items = AIService.build_asset_context_pack(asset, max_items=5)
        trajectory = AIService.build_sentiment_trajectory(context_items, {asset.display_symbol})
        support = "none"
        if context_items:
            sentiment_scores = [
                self._decimal(item["sentiment_score"])
                for item in context_items
                if item.get("sentiment_score") is not None
            ]
            if sentiment_scores:
                average = sum(sentiment_scores, Decimal("0")) / Decimal(len(sentiment_scores))
                if average >= Decimal("0.15"):
                    support = "positive"
                elif average <= Decimal("-0.15"):
                    support = "negative"
                else:
                    support = "mixed"
            else:
                support = "mixed"

        trajectory_state = trajectory[0]["state"] if trajectory else "none"
        summary = {
            "item_count": len(context_items),
            "support": support,
            "trajectory": trajectory_state,
            "sources": sorted({item["source"] for item in context_items})[:3],
        }
        return summary, len(context_items), context_items

    def _technical_bundle(self, asset: Asset) -> dict | None:
        ohlcv_rows = list(
            OHLCV.objects.filter(asset=asset)
            .order_by("date")
            .values("date", "close", "volume")
        )
        if len(ohlcv_rows) < 200:
            return None

        closes = [self._decimal(row["close"]) for row in ohlcv_rows]
        volumes = [int(row["volume"]) for row in ohlcv_rows]
        latest_row = ohlcv_rows[-1]
        latest_close = self._decimal(latest_row["close"])
        latest_date = latest_row["date"]

        indicators = self._latest_indicators(asset)
        if indicators:
            ma_20 = self._decimal(indicators.ma_20) if indicators.ma_20 is not None else None
            ma_50 = self._decimal(indicators.ma_50) if indicators.ma_50 is not None else None
            ma_200 = self._decimal(indicators.ma_200) if indicators.ma_200 is not None else None
            macd_histogram = self._decimal(indicators.macd_histogram) if indicators.macd_histogram is not None else None
            rsi_14 = self._decimal(indicators.rsi_14) if indicators.rsi_14 is not None else None
            volume_20d_avg = indicators.volume_20d_avg
        else:
            ma_20 = self._median_highest(closes, 20)
            ma_50 = self._median_highest(closes, 50)
            ma_200 = self._median_highest(closes, 200)
            macd_histogram = None
            rsi_14 = None
            volume_20d_avg = int(sum(volumes[-20:]) / 20)

        recent_high = max(closes[-20:])
        breakout_distance_pct = ((recent_high - latest_close) / recent_high) if recent_high else Decimal("0")
        breakout_confirmed = breakout_distance_pct <= BREAKOUT_DISTANCE_PCT
        breakout_score = 0
        if latest_close >= recent_high:
            breakout_score = 4
        elif breakout_distance_pct <= Decimal("0.01"):
            breakout_score = 3
        elif breakout_distance_pct <= BREAKOUT_DISTANCE_PCT:
            breakout_score = 2
        elif breakout_distance_pct <= Decimal("0.05"):
            breakout_score = 1

        trend_intact = bool(
            ma_20 is not None
            and ma_50 is not None
            and ma_200 is not None
            and latest_close >= ma_20 > ma_50 > ma_200
        )
        liquidity_floor_met = Decimal(str(volume_20d_avg or 0)) >= LIQUIDITY_FLOOR
        if not liquidity_floor_met or not trend_intact or not breakout_confirmed:
            return None

        technical_score = 0
        if latest_close >= ma_20:
            technical_score += 1
        if ma_20 and ma_50 and ma_20 > ma_50:
            technical_score += 1
        if ma_50 and ma_200 and ma_50 > ma_200:
            technical_score += 1
        if macd_histogram is not None and macd_histogram > 0:
            technical_score += 1
        if rsi_14 is not None and Decimal("50") <= rsi_14 <= Decimal("70"):
            technical_score += 1

        context_summary, context_items_count, context_items = self._context_bundle(asset)
        context_score = 0
        if context_items_count:
            context_score += 1
        if context_summary["support"] == "positive":
            context_score += 1
        if context_summary["trajectory"] in {"improving", "reversal"}:
            context_score += 1

        freshness_score, freshness_age = self._freshness_score(self._latest_quote(asset), latest_date)

        rank_score = (
            Decimal(technical_score)
            + Decimal(breakout_score)
            + Decimal(context_score)
            + Decimal(freshness_score)
        )

        technical_signals = {
            "liquidity_floor_met": liquidity_floor_met,
            "average_volume_20d": int(volume_20d_avg or 0),
            "latest_close": self._quantize(latest_close),
            "latest_volume": int(volumes[-1]),
            "trend_intact": trend_intact,
            "ma_20": self._quantize(ma_20),
            "ma_50": self._quantize(ma_50),
            "ma_200": self._quantize(ma_200),
            "recent_high": self._quantize(recent_high),
            "breakout_distance_pct": self._quantize(breakout_distance_pct, "0.0001"),
            "breakout_confirmed": breakout_confirmed,
            "freshness_age": freshness_age,
        }

        breakout_direction = "below"
        breakout_distance = breakout_distance_pct
        if breakout_distance_pct < 0:
            breakout_direction = "above"
            breakout_distance = -breakout_distance_pct

        discovery_reason = (
            f"{asset.display_symbol} passed liquidity, trend, and breakout checks; "
            f"close is {self._quantize(breakout_distance, '0.0001')} {breakout_direction} the recent high."
        )
        if context_summary["item_count"]:
            discovery_reason += f" Context is {context_summary['support']}."

        return {
            "asset": asset,
            "rank_score": rank_score,
            "technical_score": technical_score,
            "breakout_score": breakout_score,
            "context_score": context_score,
            "freshness_score": freshness_score,
            "technical_signals": technical_signals,
            "context_summary": context_summary,
            "discovery_reason": discovery_reason,
        }

    @staticmethod
    def _sort_key(candidate: dict) -> tuple:
        return (
            candidate["rank_score"],
            candidate["technical_score"],
            candidate["breakout_score"],
            candidate["context_score"],
            candidate["freshness_score"],
            candidate["asset"].display_symbol.lower(),
        )

    @classmethod
    def _fingerprint(cls, shortlist: list[dict]) -> str:
        payload = [
            {
                "asset_id": item["asset_id"],
                "rank": item["rank"],
                "score": item["score"],
                "score_breakdown": item["score_breakdown"],
                "technical_signals": item["technical_signals"],
                "context_summary": item["context_summary"],
                "watch_action_ready": item["watch_action_ready"],
            }
            for item in shortlist
        ]
        return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()

    @staticmethod
    def _refined_cache_key(user_id: int, market: str, fingerprint: str) -> str:
        return f"ai_discovery_refined:v1:{user_id}:{market}:{fingerprint}"

    @staticmethod
    def _refined_latest_key(user_id: int, market: str) -> str:
        return f"ai_discovery_refined_latest:v1:{user_id}:{market}"

    def _refine_shortlist(self, market: str, shortlist: list[dict], force_refresh: bool) -> tuple[list[dict], dict]:
        if not self.ai_service or not self.ai_service.has_ai_enabled():
            return shortlist, {"requested": True, "applied": False, "cache_hit": False}

        provider, api_key = self.ai_service.get_api_credentials()
        if not provider or not api_key:
            return shortlist, {"requested": True, "applied": False, "cache_hit": False}

        fingerprint = self._fingerprint(shortlist)
        cache_key = self._refined_cache_key(self.user.id, market, fingerprint)
        latest_key = self._refined_latest_key(self.user.id, market)

        if not force_refresh:
            cached = cache.get(cache_key)
            if cached:
                return cached["shortlist"], {
                    "requested": True,
                    "applied": True,
                    "cache_hit": True,
                    "fingerprint": fingerprint,
                }

        if force_refresh:
            cache.delete(cache_key)

        prompt = self._build_refinement_prompt(market, shortlist)
        model = self.ai_service.ai_auth.get_model_for_task("opportunity_discovery")
        response_text = ""
        prompt_tokens = 0
        completion_tokens = 0

        try:
            self.ai_service.check_budget()
        except AIBudgetError:
            return shortlist, {"requested": True, "applied": False, "cache_hit": False}

        if provider == "anthropic":
            import anthropic

            message = anthropic.Anthropic(api_key=api_key).messages.create(
                model=model,
                max_tokens=350,
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
                max_output_tokens=350,
                input=prompt,
            )
            response_text = response.output_text
            if getattr(response, "usage", None):
                prompt_tokens = getattr(response.usage, "input_tokens", 0) or 0
                completion_tokens = getattr(response.usage, "output_tokens", 0) or 0
        elif provider == "google":
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            response_text = genai.GenerativeModel(model).generate_content(prompt).text
        else:
            return shortlist, {"requested": True, "applied": False, "cache_hit": False}

        parsed = AIService._extract_json_object(response_text)
        if not parsed:
            return shortlist, {"requested": True, "applied": False, "cache_hit": False}

        refined_lookup = {
            str(item.get("asset_id")): item.get("refined_reason")
            for item in parsed.get("items", [])
            if item.get("asset_id") and item.get("refined_reason")
        }

        refined_shortlist = []
        for item in shortlist:
            refined_shortlist.append({**item, "refined_reason": refined_lookup.get(item["asset_id"])})

        self.ai_service.log_call(
            model_name=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=self.ai_service._estimate_provider_cost(provider, model, prompt_tokens, completion_tokens),
            task_type="opportunity_discovery",
        )

        previous_fingerprint = cache.get(latest_key)
        if previous_fingerprint and previous_fingerprint != fingerprint:
            cache.delete(self._refined_cache_key(self.user.id, market, previous_fingerprint))

        cache.set(
            cache_key,
            {"shortlist": refined_shortlist},
            timeout=REFINED_CACHE_TTL,
        )
        cache.set(latest_key, fingerprint, timeout=REFINED_CACHE_TTL)

        return refined_shortlist, {
            "requested": True,
            "applied": True,
            "cache_hit": False,
            "fingerprint": fingerprint,
        }

    @staticmethod
    def _build_refinement_prompt(market: str, shortlist: list[dict]) -> str:
        items = []
        for item in shortlist:
            items.append(
                {
                    "asset_id": item["asset_id"],
                    "symbol": item["symbol"],
                    "rank": item["rank"],
                    "score": item["score"],
                    "technical_signals": item["technical_signals"],
                    "context_summary": item["context_summary"],
                    "discovery_reason": item["discovery_reason"],
                }
            )

        return (
            "You are refining a bounded discovery shortlist for a paper trading app.\n\n"
            "Return ONLY valid JSON with this exact shape:\n"
            "{\n"
            '  "items": [\n'
            '    {"asset_id": "uuid", "refined_reason": "one concise sentence"}\n'
            "  ]\n"
            "}\n\n"
            f"Market: {market}\n\n"
            "Shortlist:\n"
            f"{json.dumps(items, indent=2, default=str)}\n\n"
            "Rules:\n"
            "- Keep each refined reason to one or two concise sentences.\n"
            "- The first sentence should summarize the setup clearly.\n"
            "- When supported by the provided inputs, the second sentence should convey "
            "why the asset deserves attention now.\n"
            "- Do not literally start the second sentence with 'Why now:'.\n"
            "- Use only the provided technical signals, context summary, and discovery reason.\n"
            "- Do not change the ranking or imply execution.\n"
            "- Preserve the deterministic shortlist as source of truth.\n"
        )

    def discover(self, market: str, *, refine: bool = False, force_refresh: bool = False) -> dict:
        market = (market or "").strip().upper()
        if not self._is_enabled_market(market):
            raise ValueError("Invalid market")

        held_asset_ids = self._held_asset_ids(market)
        assets = list(
            Asset.objects.filter(market=market)
            .exclude(id__in=held_asset_ids)
            .order_by("display_symbol")
        )
        survivors: list[dict] = []
        for asset in assets:
            bundle = self._technical_bundle(asset)
            if bundle is None:
                continue
            survivors.append(bundle)

        survivors.sort(key=self._sort_key, reverse=True)
        survivors = survivors[:SURVIVOR_CAP]

        shortlist_candidates = []
        for rank, bundle in enumerate(survivors[:SHORTLIST_CAP], start=1):
            asset = bundle["asset"]
            candidate = DiscoveryCandidate(
                asset_id=str(asset.id),
                symbol=asset.display_symbol,
                market=asset.market,
                rank_score=bundle["rank_score"],
                technical_score=bundle["technical_score"],
                breakout_score=bundle["breakout_score"],
                context_score=bundle["context_score"],
                freshness_score=bundle["freshness_score"],
                technical_signals=bundle["technical_signals"],
                context_summary=bundle["context_summary"],
                discovery_reason=bundle["discovery_reason"],
            )
            shortlist_candidates.append(candidate.as_dict(rank))

        refinement = {"requested": refine, "applied": False, "cache_hit": False}
        if refine and shortlist_candidates:
            shortlist_candidates, refinement = self._refine_shortlist(market, shortlist_candidates, force_refresh)
            for index, item in enumerate(shortlist_candidates, start=1):
                item["rank"] = index

        fingerprint = self._fingerprint(shortlist_candidates) if shortlist_candidates else None

        return {
            "market": market,
            "universe_size": len(assets),
            "survivor_count": len(survivors),
            "shortlist_count": len(shortlist_candidates),
            "shortlist": [self._to_json_safe(item) for item in shortlist_candidates],
            "refinement": {
                **refinement,
                "fingerprint": fingerprint,
            },
            "generated_at": timezone.now().isoformat(),
        }
