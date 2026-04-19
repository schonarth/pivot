import re
import sys
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.core.management import call_command
from django.utils import timezone
import pytest

from ai.models import AIAuth
from ai.services import AIService
from markets.models import Asset, NewsItem, OHLCV, TechnicalIndicators


def make_asset(symbol: str, *, market: str = "US", sector: str = "", industry: str = ""):
    return Asset.objects.create(
        display_symbol=symbol,
        provider_symbol=symbol,
        name=f"{symbol} Holdings",
        market=market,
        exchange="XNYS" if market == "US" else "BVMF",
        currency="USD" if market == "US" else "BRL",
        sector=sector or None,
        industry=industry or None,
    )


def make_news(
    asset,
    headline: str,
    *,
    source: str = "yahoo_finance",
    hours_ago: int = 1,
    sentiment_score=None,
):
    slug = re.sub(r"[^a-z0-9]+", "-", headline.lower()).strip("-")
    return NewsItem.objects.create(
        asset=asset,
        headline=headline,
        url=f"https://example.com/{asset.display_symbol.lower()}/{slug}",
        source=source,
        published_at=timezone.now() - timedelta(hours=hours_ago),
        sentiment_score=sentiment_score,
    )


def make_ohlcv(asset, closes: list[Decimal]):
    start_date = timezone.now().date() - timedelta(days=len(closes) - 1)
    for index, close in enumerate(closes):
        OHLCV.objects.create(
            asset=asset,
            date=start_date + timedelta(days=index),
            open=Decimal(str(close)) - Decimal("1.00"),
            high=Decimal(str(close)) + Decimal("1.00"),
            low=Decimal(str(close)) - Decimal("2.00"),
            close=Decimal(str(close)),
            volume=1000 + index,
        )


def make_indicators(asset, *, date=None):
    TechnicalIndicators.objects.create(
        asset=asset,
        date=date or timezone.now().date(),
        rsi_14=Decimal("61.00"),
        macd=Decimal("1.50"),
        macd_signal=Decimal("1.00"),
        macd_histogram=Decimal("0.50"),
        ma_20=Decimal("101.00"),
        ma_50=Decimal("99.00"),
        ma_200=Decimal("95.00"),
        bb_upper=Decimal("110.00"),
        bb_middle=Decimal("100.00"),
        bb_lower=Decimal("90.00"),
        volume_20d_avg=1000,
    )


@pytest.mark.django_db
class TestAssetContextPack:
    def test_build_asset_context_pack_tags_and_deduplicates(self, user):
        asset = make_asset("AAA", sector="Financial", industry="Banks")
        sector_peer = make_asset("BBB", sector="Financial", industry="Banks")
        macro_peer = make_asset("CCC", sector="Utilities", industry="Electric Utilities")

        make_news(asset, "AAA shares rise on earnings beat")
        make_news(asset, "Regional lender raises dividend")
        make_news(sector_peer, "Fed keeps rates higher after inflation data")
        make_news(sector_peer, "Inflation data keeps Fed rates higher", hours_ago=2)
        make_news(macro_peer, "Rates stay higher for longer as inflation cools")

        service = AIService(user)
        service.set_api_key("test-key")

        context_items = service.build_asset_context_pack(asset)
        buckets = [item["bucket"] for item in context_items]

        assert "symbol" in buckets
        assert "company" in buckets
        assert "sector" in buckets
        assert "macro" in buckets
        assert len(context_items) <= 12
        assert max(buckets.count(bucket) for bucket in set(buckets)) <= 2
        assert sum(1 for item in context_items if item["bucket"] == "sector") == 1

    def test_build_asset_context_pack_includes_theme_bucket(self, user):
        asset = make_asset("TCH", sector="Technology", industry="Semiconductors")
        theme_peer = make_asset("UTIL", sector="Utilities", industry="Utilities")

        make_news(asset, "TCH posts steady quarter")
        make_news(theme_peer, "Chip makers rally on AI demand")

        service = AIService(user)
        service.set_api_key("test-key")

        context_items = service.build_asset_context_pack(asset)

        assert any(item["bucket"] == "theme" for item in context_items)
        assert any(item["provenance"] == "theme:semiconductors" for item in context_items)

    def test_build_story_so_far_labels_new_continuing_and_shifted(self, user):
        asset = make_asset("AAA")

        prior = make_news(asset, "AAA beats earnings expectations", hours_ago=72)
        middle = make_news(asset, "AAA shares rally on earnings beat", hours_ago=2)
        current = make_news(asset, "AAA misses earnings expectations", hours_ago=1)

        service = AIService(user)
        service.set_api_key("test-key")

        context_items = [
            {
                "news_item_id": str(prior.id),
                "headline": "AAA beats earnings expectations",
                "source": "yahoo_finance",
                "published_at": timezone.now() - timedelta(hours=72),
                "bucket": "company",
                "provenance": "asset:AAA",
                "relevance_basis": "current asset news",
                "asset_symbol": "AAA",
                "market": "US",
            },
            {
                "news_item_id": str(middle.id),
                "headline": "AAA shares rally on earnings beat",
                "source": "yahoo_finance",
                "published_at": timezone.now() - timedelta(hours=2),
                "bucket": "company",
                "provenance": "asset:AAA",
                "relevance_basis": "current asset news",
                "asset_symbol": "AAA",
                "market": "US",
            },
            {
                "news_item_id": str(current.id),
                "headline": "AAA misses earnings expectations",
                "source": "yahoo_finance",
                "published_at": timezone.now() - timedelta(hours=1),
                "bucket": "company",
                "provenance": "asset:AAA",
                "relevance_basis": "current asset news",
                "asset_symbol": "AAA",
                "market": "US",
            },
        ]

        story = service.build_story_so_far(asset, context_items)

        assert any(item["label"] == "shifted" for item in story)
        assert any(item["label"] == "continuing" for item in story)
        assert any(item["label"] == "new" for item in story)

    def test_build_story_so_far_excludes_items_outside_window(self, user):
        asset = make_asset("AAA")

        make_news(asset, "AAA beats earnings expectations", hours_ago=8 * 24)
        current = make_news(asset, "AAA shares rally on earnings beat", hours_ago=1)

        service = AIService(user)
        service.set_api_key("test-key")

        context_items = [
            {
                "news_item_id": str(current.id),
                "headline": "AAA shares rally on earnings beat",
                "source": "yahoo_finance",
                "published_at": timezone.now() - timedelta(hours=1),
                "bucket": "company",
                "provenance": "asset:AAA",
                "relevance_basis": "current asset news",
                "asset_symbol": "AAA",
                "market": "US",
            }
        ]

        story = service.build_story_so_far(asset, context_items)

        assert story[0]["label"] == "new"


@pytest.mark.django_db
class TestSentimentTrajectory:
    def test_build_sentiment_trajectory_detects_improving(self, user):
        asset = make_asset("AAA")
        make_news(asset, "AAA steady update", hours_ago=3, sentiment_score=0)
        make_news(asset, "AAA positive outlook", hours_ago=2, sentiment_score=0.6)
        make_news(asset, "AAA stronger guidance", hours_ago=1, sentiment_score=0.9)

        service = AIService(user)

        trajectory = service.build_sentiment_trajectory(
            [
                {
                    "headline": "AAA steady update",
                    "published_at": timezone.now() - timedelta(hours=3),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0,
                },
                {
                    "headline": "AAA positive outlook",
                    "published_at": timezone.now() - timedelta(hours=2),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0.6,
                },
                {
                    "headline": "AAA stronger guidance",
                    "published_at": timezone.now() - timedelta(hours=1),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0.9,
                },
            ],
            {"AAA"},
        )

        assert trajectory[0]["state"] == "improving"
        assert "more positive" in trajectory[0]["summary"]

    def test_build_sentiment_trajectory_detects_deteriorating(self, user):
        service = AIService(user)

        trajectory = service.build_sentiment_trajectory(
            [
                {
                    "headline": "AAA steady update",
                    "published_at": timezone.now() - timedelta(hours=3),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0,
                },
                {
                    "headline": "AAA weaker outlook",
                    "published_at": timezone.now() - timedelta(hours=2),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": -0.6,
                },
                {
                    "headline": "AAA worse guidance",
                    "published_at": timezone.now() - timedelta(hours=1),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": -0.9,
                },
            ],
            {"AAA"},
        )

        assert trajectory[0]["state"] == "deteriorating"
        assert "more negative" in trajectory[0]["summary"]

    def test_build_sentiment_trajectory_detects_conflicting(self, user):
        service = AIService(user)

        trajectory = service.build_sentiment_trajectory(
            [
                {
                    "headline": "AAA upbeat view",
                    "published_at": timezone.now() - timedelta(hours=4),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0.7,
                },
                {
                    "headline": "AAA downbeat view",
                    "published_at": timezone.now() - timedelta(hours=3),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": -0.7,
                },
                {
                    "headline": "AAA upbeat follow-up",
                    "published_at": timezone.now() - timedelta(hours=2),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0.7,
                },
                {
                    "headline": "AAA downbeat follow-up",
                    "published_at": timezone.now() - timedelta(hours=1),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": -0.7,
                },
            ],
            {"AAA"},
        )

        assert trajectory[0]["state"] == "conflicting"
        assert "mixed positive and negative" in trajectory[0]["summary"]

    def test_build_sentiment_trajectory_detects_reversal(self, user):
        service = AIService(user)

        trajectory = service.build_sentiment_trajectory(
            [
                {
                    "headline": "AAA upbeat start",
                    "published_at": timezone.now() - timedelta(hours=4),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0.8,
                },
                {
                    "headline": "AAA still upbeat",
                    "published_at": timezone.now() - timedelta(hours=3),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0.7,
                },
                {
                    "headline": "AAA turns negative",
                    "published_at": timezone.now() - timedelta(hours=2),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": -0.7,
                },
                {
                    "headline": "AAA turns sharply negative",
                    "published_at": timezone.now() - timedelta(hours=1),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": -0.9,
                },
            ],
            {"AAA"},
        )

        assert trajectory[0]["state"] == "reversal"
        assert "flipped" in trajectory[0]["summary"]

    def test_build_sentiment_trajectory_ignores_old_items_outside_window(self, user):
        service = AIService(user)

        trajectory = service.build_sentiment_trajectory(
            [
                {
                    "headline": "AAA old negative",
                    "published_at": timezone.now() - timedelta(days=8),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": -0.9,
                },
                {
                    "headline": "AAA recent positive",
                    "published_at": timezone.now() - timedelta(hours=2),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0.7,
                },
                {
                    "headline": "AAA recent stronger positive",
                    "published_at": timezone.now() - timedelta(hours=1),
                    "asset_symbol": "AAA",
                    "provenance": "asset:AAA",
                    "sentiment_score": 0.9,
                },
            ],
            {"AAA"},
        )

        assert trajectory[0]["state"] == "improving"
        assert all("old negative" not in entry["summary"] for entry in trajectory)

    def test_build_sentiment_trajectory_requires_cross_asset_theme_evidence(self, user):
        service = AIService(user)

        single_asset = service.build_sentiment_trajectory(
            [
                {
                    "headline": "AAA semiconductors rally",
                    "published_at": timezone.now() - timedelta(hours=2),
                    "asset_symbol": "AAA",
                    "provenance": "theme:semiconductors",
                    "sentiment_score": 0.8,
                },
                {
                    "headline": "AAA semiconductors extend gains",
                    "published_at": timezone.now() - timedelta(hours=1),
                    "asset_symbol": "AAA",
                    "provenance": "theme:semiconductors",
                    "sentiment_score": 0.7,
                },
            ],
            {"AAA"},
        )

        cross_asset = service.build_sentiment_trajectory(
            [
                {
                    "headline": "AAA semiconductors rally",
                    "published_at": timezone.now() - timedelta(hours=2),
                    "asset_symbol": "AAA",
                    "provenance": "theme:semiconductors",
                    "sentiment_score": 0.8,
                },
                {
                    "headline": "BBB semiconductors extend gains",
                    "published_at": timezone.now() - timedelta(hours=1),
                    "asset_symbol": "BBB",
                    "provenance": "theme:semiconductors",
                    "sentiment_score": 0.7,
                },
            ],
            {"AAA", "BBB"},
        )

        assert single_asset[0]["subject_type"] == "asset"
        assert all(entry["subject_type"] != "theme" for entry in single_asset)
        assert cross_asset[0]["subject_type"] == "theme"
        assert cross_asset[0]["subject"] == "semiconductors"


@pytest.mark.django_db
class TestDivergenceAnalysis:
    def test_build_divergence_analysis_detects_no_divergence(self, user):
        asset = make_asset("AAA")
        make_ohlcv(asset, [Decimal("100.00"), Decimal("101.00"), Decimal("102.00"), Decimal("104.00"), Decimal("106.00")])

        service = AIService(user)
        analysis = service.build_divergence_analysis(
            "asset",
            [asset],
            [
                {
                    "headline": "AAA shares rise on earnings beat",
                    "bucket": "company",
                    "sentiment_score": Decimal("0.7"),
                },
                {
                    "headline": "AAA momentum strengthens",
                    "bucket": "company",
                    "sentiment_score": Decimal("0.8"),
                },
            ],
            [
                {
                    "subject_type": "asset",
                    "subject": "AAA",
                    "state": "improving",
                }
            ],
            indicators={
                "ma_20": Decimal("101.00"),
                "ma_50": Decimal("99.00"),
                "macd": Decimal("1.50"),
                "macd_signal": Decimal("1.00"),
                "rsi_14": Decimal("61.00"),
            },
        )

        assert analysis["label"] == "no_divergence"
        assert analysis["expected_direction"] == "up"
        assert analysis["actual_direction"] == "up"
        assert analysis["macro_confirmation"] is False

    def test_build_divergence_analysis_detects_no_material_follow_through(self, user):
        asset = make_asset("AAA")
        make_ohlcv(asset, [Decimal("100.00"), Decimal("100.20"), Decimal("100.10"), Decimal("100.30"), Decimal("100.40")])

        service = AIService(user)
        analysis = service.build_divergence_analysis(
            "asset",
            [asset],
            [
                {
                    "headline": "AAA shares rise on earnings beat",
                    "bucket": "company",
                    "sentiment_score": Decimal("0.7"),
                },
                {
                    "headline": "AAA momentum strengthens",
                    "bucket": "company",
                    "sentiment_score": Decimal("0.8"),
                },
            ],
            [
                {
                    "subject_type": "asset",
                    "subject": "AAA",
                    "state": "improving",
                }
            ],
            indicators={
                "ma_20": Decimal("101.00"),
                "ma_50": Decimal("99.00"),
                "macd": Decimal("1.50"),
                "macd_signal": Decimal("1.00"),
                "rsi_14": Decimal("61.00"),
            },
        )

        assert analysis["label"] == "no_material_follow_through"
        assert analysis["actual_direction"] == "flat"

    def test_build_divergence_analysis_detects_reversal(self, user):
        asset = make_asset("AAA")
        make_ohlcv(asset, [Decimal("100.00"), Decimal("99.00"), Decimal("98.00"), Decimal("97.00"), Decimal("96.00")])

        service = AIService(user)
        analysis = service.build_divergence_analysis(
            "asset",
            [asset],
            [
                {
                    "headline": "AAA shares rise on earnings beat",
                    "bucket": "company",
                    "sentiment_score": Decimal("0.7"),
                },
                {
                    "headline": "AAA momentum strengthens",
                    "bucket": "company",
                    "sentiment_score": Decimal("0.8"),
                },
            ],
            [
                {
                    "subject_type": "asset",
                    "subject": "AAA",
                    "state": "improving",
                }
            ],
            indicators={
                "ma_20": Decimal("101.00"),
                "ma_50": Decimal("99.00"),
                "macd": Decimal("1.50"),
                "macd_signal": Decimal("1.00"),
                "rsi_14": Decimal("61.00"),
            },
        )

        assert analysis["label"] == "reversal"
        assert analysis["actual_direction"] == "down"

    def test_build_divergence_analysis_detects_competing_macro_priority(self, user):
        asset = make_asset("AAA")
        make_ohlcv(asset, [Decimal("100.00"), Decimal("99.00"), Decimal("98.00"), Decimal("97.00"), Decimal("96.00")])

        service = AIService(user)
        analysis = service.build_divergence_analysis(
            "portfolio",
            [asset],
            [
                {
                    "headline": "AAA shares rise on earnings beat",
                    "bucket": "company",
                    "sentiment_score": Decimal("0.7"),
                },
                {
                    "headline": "AAA momentum strengthens",
                    "bucket": "company",
                    "sentiment_score": Decimal("0.8"),
                },
                {
                    "headline": "Macro risk rises on rates and inflation pressure",
                    "bucket": "macro",
                    "sentiment_score": Decimal("-0.8"),
                },
            ],
            [
                {
                    "subject_type": "asset",
                    "subject": "AAA",
                    "state": "improving",
                }
            ],
            indicators={
                "ma_20": Decimal("101.00"),
                "ma_50": Decimal("99.00"),
                "macd": Decimal("1.50"),
                "macd_signal": Decimal("1.00"),
                "rsi_14": Decimal("61.00"),
            },
        )

        assert analysis["label"] == "competing_macro_priority"
        assert analysis["macro_confirmation"] is True

    def test_build_divergence_analysis_detects_uncertainty_conflict(self, user):
        asset = make_asset("AAA")
        make_ohlcv(asset, [Decimal("100.00"), Decimal("101.00"), Decimal("102.00"), Decimal("103.00"), Decimal("104.00")])

        service = AIService(user)
        analysis = service.build_divergence_analysis(
            "asset",
            [asset],
            [
                {
                    "headline": "AAA shares fall after guidance cut",
                    "bucket": "company",
                    "sentiment_score": Decimal("-0.8"),
                },
                {
                    "headline": "AAA outlook weakens on margin pressure",
                    "bucket": "company",
                    "sentiment_score": Decimal("-0.7"),
                },
            ],
            [
                {
                    "subject_type": "asset",
                    "subject": "AAA",
                    "state": "deteriorating",
                }
            ],
            indicators={
                "ma_20": Decimal("101.00"),
                "ma_50": Decimal("99.00"),
                "macd": Decimal("1.50"),
                "macd_signal": Decimal("1.00"),
                "rsi_14": Decimal("61.00"),
            },
        )

        assert analysis["label"] == "uncertainty_conflict"

    def test_build_divergence_analysis_returns_none_without_recent_move_data(self, user):
        asset = make_asset("AAA")
        service = AIService(user)

        assert service.build_divergence_analysis(
            "asset",
            [asset],
            [],
            [],
            indicators={
                "ma_20": Decimal("101.00"),
                "ma_50": Decimal("99.00"),
                "macd": Decimal("1.50"),
                "macd_signal": Decimal("1.00"),
                "rsi_14": Decimal("61.00"),
            },
        ) is None

    def test_inspect_divergence_command_prints_structured_output(self, user, capsys):
        asset = make_asset("AAA")
        make_ohlcv(asset, [Decimal("100.00"), Decimal("101.00"), Decimal("102.00"), Decimal("103.00"), Decimal("104.00")])
        make_indicators(asset)
        make_news(asset, "AAA shares rise on earnings beat", sentiment_score=0.8)
        make_news(asset, "AAA momentum strengthens", hours_ago=2, sentiment_score=0.7)

        call_command("inspect_divergence", "--asset-id", str(asset.id))

        captured = capsys.readouterr()
        assert "Divergence:" in captured.out
        assert '"label": "no_divergence"' in captured.out
        assert "Disclosure:" in captured.out


@pytest.mark.django_db
class TestAssetInsightPrompt:
    def test_analyze_asset_uses_tagged_context_pack_in_prompt(self, user):
        asset = make_asset("AAA", sector="Financial", industry="Banks")
        peer = make_asset("BBB", sector="Financial", industry="Banks")
        macro_peer = make_asset("CCC", sector="Utilities", industry="Electric Utilities")

        make_news(asset, "AAA shares rise on earnings beat", sentiment_score=0.6)
        make_news(asset, "AAA earnings momentum strengthens", hours_ago=2, sentiment_score=0.8)
        make_news(peer, "Regional banks face deposit pressure", sentiment_score=-0.6)
        make_news(macro_peer, "Fed keeps rates higher for longer", sentiment_score=-0.4)
        make_ohlcv(asset, [Decimal("100.00"), Decimal("101.00"), Decimal("102.00"), Decimal("103.00"), Decimal("104.00")])

        AIAuth.objects.create(user=user, provider_name="openai")
        service = AIService(user)
        service.set_api_key("test-key")

        indicator_payload = {
            "rsi_14": 61.0,
            "macd": 1.5,
            "macd_signal": 1.0,
            "macd_histogram": 0.5,
            "ma_20": 101.0,
            "ma_50": 99.0,
            "ma_200": 95.0,
            "bb_upper": 110.0,
            "bb_middle": 100.0,
            "bb_lower": 90.0,
            "volume_20d_avg": 1000,
        }

        fake_response = SimpleNamespace(
            output_text=(
                '{"recommendation":"HOLD","confidence":55,'
                '"summary":"The setup is balanced.",'
                '"technical_summary":"Trend is steady.",'
                '"news_context":"Rates matter.",'
                '"price_target":null}'
            ),
            usage=SimpleNamespace(input_tokens=111, output_tokens=22),
        )
        recorded_prompt = {}

        fake_openai = SimpleNamespace(
            OpenAI=MagicMock(
                return_value=SimpleNamespace(
                    responses=SimpleNamespace(
                        create=MagicMock(side_effect=lambda **kwargs: recorded_prompt.update(kwargs) or fake_response),
                    )
                )
            )
        )

        with patch("markets.services.NewsService.fetch_and_store_news", return_value=0), patch(
            "trading.technical.IndicatorCalculator.calculate_indicators", return_value=indicator_payload
        ), patch.dict(sys.modules, {"openai": fake_openai}):
            result = service.analyze_asset(asset)

        assert result["news_items"]
        assert all(item["url"] for item in result["news_items"])
        assert any(item["bucket"] in {"symbol", "company", "sector", "macro"} for item in result["news_items"])
        assert "Context pack:" in recorded_prompt["input"]
        assert "Story so far:" in recorded_prompt["input"]
        assert "Sentiment trajectory:" in recorded_prompt["input"]
        assert "Divergence analysis:" in recorded_prompt["input"]
        assert "[symbol]" in recorded_prompt["input"] or "[company]" in recorded_prompt["input"]
        assert result["sentiment_trajectory"]
        assert result["sentiment_trajectory"]["entries"][0]["state"] == "improving"
        assert result["divergence_analysis"]["label"] == "no_divergence"
        assert result["divergence_summary"]

    def test_analyze_asset_returns_cached_result_on_second_call(self, user):
        cache.clear()

        asset = make_asset("AAA", sector="Financial", industry="Banks")
        make_news(asset, "AAA shares rise on earnings beat")

        AIAuth.objects.create(user=user, provider_name="openai")
        service = AIService(user)
        service.set_api_key("test-key")

        indicator_payload = {
            "rsi_14": 61.0,
            "macd": 1.5,
            "macd_signal": 1.0,
            "macd_histogram": 0.5,
            "ma_20": 101.0,
            "ma_50": 99.0,
            "ma_200": 95.0,
            "bb_upper": 110.0,
            "bb_middle": 100.0,
            "bb_lower": 90.0,
            "volume_20d_avg": 1000,
        }

        fake_response = SimpleNamespace(
            output_text=(
                '{"recommendation":"HOLD","confidence":55,'
                '"summary":"The setup is balanced.",'
                '"technical_summary":"Trend is steady.",'
                '"news_context":"Rates matter.",'
                '"price_target":null}'
            ),
            usage=SimpleNamespace(input_tokens=111, output_tokens=22),
        )
        openai_create = MagicMock(return_value=fake_response)
        fake_openai = SimpleNamespace(
            OpenAI=MagicMock(
                return_value=SimpleNamespace(
                    responses=SimpleNamespace(create=openai_create),
                )
            )
        )

        with patch("markets.services.NewsService.fetch_and_store_news", return_value=0), patch(
            "trading.technical.IndicatorCalculator.calculate_indicators", return_value=indicator_payload
        ), patch.dict(sys.modules, {"openai": fake_openai}):
            first = service.analyze_asset(asset)
            second = service.analyze_asset(asset)

        assert first == second
        assert openai_create.call_count == 1


@pytest.mark.django_db
class TestScopeInsightPrompt:
    def test_analyze_scope_uses_monitored_set_context(self, user):
        asset_a = make_asset("AAA", sector="Financial", industry="Banks")
        asset_b = make_asset("BBB", sector="Financial", industry="Banks")

        make_news(asset_a, "AAA shares rise on earnings beat", sentiment_score=0.7)
        make_news(asset_a, "AAA earnings momentum strengthens", hours_ago=2, sentiment_score=0.8)
        make_news(asset_b, "BBB sees steady inflows", sentiment_score=-0.4)
        make_news(asset_b, "BBB outflows accelerate", hours_ago=2, sentiment_score=-0.7)
        make_ohlcv(asset_a, [Decimal("100.00"), Decimal("100.50"), Decimal("101.00"), Decimal("101.50"), Decimal("102.00")])
        make_ohlcv(asset_b, [Decimal("100.00"), Decimal("99.80"), Decimal("99.60"), Decimal("99.40"), Decimal("99.20")])

        AIAuth.objects.create(user=user, provider_name="openai")
        service = AIService(user)
        service.set_api_key("test-key")

        holdings = [
            {
                "asset_id": str(asset_a.id),
                "symbol": asset_a.display_symbol,
                "name": asset_a.name,
                "market": asset_a.market,
                "currency": asset_a.currency,
                "current_price": "10.00",
                "position_detail": "10 @ 10.00 | MV 100.00 | U P&L 5.00",
            },
            {
                "asset_id": str(asset_b.id),
                "symbol": asset_b.display_symbol,
                "name": asset_b.name,
                "market": asset_b.market,
                "currency": asset_b.currency,
                "current_price": "12.00",
                "position_detail": "8 @ 12.00 | MV 96.00 | U P&L 4.00",
            },
        ]

        fake_response = SimpleNamespace(
            output_text=(
                '{"recommendation":"HOLD","confidence":61,'
                '"summary":"The monitored set is balanced.",'
                '"technical_summary":"Momentum is mixed.",'
                '"news_context":"Coverage is constructive."}'
            ),
            usage=SimpleNamespace(input_tokens=88, output_tokens=19),
        )
        recorded_prompt = {}

        fake_openai = SimpleNamespace(
            OpenAI=MagicMock(
                return_value=SimpleNamespace(
                    responses=SimpleNamespace(
                        create=MagicMock(side_effect=lambda **kwargs: recorded_prompt.update(kwargs) or fake_response),
                    )
                )
            )
        )

        with patch.dict(sys.modules, {"openai": fake_openai}):
            result = service.analyze_scope("portfolio", "Core positions", [asset_a, asset_b], holdings)

        assert result["scope_type"] == "portfolio"
        assert result["asset_count"] == 2
        assert result["summary"] == "The monitored set is balanced."
        assert "Type: portfolio" in recorded_prompt["input"]
        assert "Asset count: 2" in recorded_prompt["input"]
        assert "Sentiment trajectory:" in recorded_prompt["input"]
        assert "Divergence analysis:" in recorded_prompt["input"]
        assert "AAA" in recorded_prompt["input"]
        assert "BBB" in recorded_prompt["input"]
        assert result["sentiment_trajectory"]
        assert result["divergence_analysis"]


@pytest.mark.django_db
class TestSharedInstanceKey:
    def test_analyze_news_sentiment_uses_instance_default_key(self, user):
        service = AIService(user)
        service.set_instance_default_api_key("instance-key", allow_other_users=True)

        fake_response = SimpleNamespace(
            output_text='{"Headline One": 0.8}',
            usage=SimpleNamespace(input_tokens=10, output_tokens=5),
        )
        fake_openai = SimpleNamespace(
            OpenAI=MagicMock(
                return_value=SimpleNamespace(
                    responses=SimpleNamespace(
                        create=MagicMock(return_value=fake_response),
                    )
                )
            )
        )

        with patch.dict(sys.modules, {"openai": fake_openai}):
            sentiments = AIService.analyze_news_sentiment(["Headline One"])

        assert sentiments["Headline One"] == Decimal("0.8")
