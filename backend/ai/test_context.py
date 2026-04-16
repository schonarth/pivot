import re
import sys
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from ai.models import AIAuth
from ai.services import AIService
from markets.models import Asset, NewsItem


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


def make_news(asset, headline: str, *, source: str = "yahoo_finance", hours_ago: int = 1):
    slug = re.sub(r"[^a-z0-9]+", "-", headline.lower()).strip("-")
    return NewsItem.objects.create(
        asset=asset,
        headline=headline,
        url=f"https://example.com/{asset.display_symbol.lower()}/{slug}",
        source=source,
        published_at=timezone.now() - timedelta(hours=hours_ago),
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
class TestAssetInsightPrompt:
    def test_analyze_asset_uses_tagged_context_pack_in_prompt(self, user):
        asset = make_asset("AAA", sector="Financial", industry="Banks")
        peer = make_asset("BBB", sector="Financial", industry="Banks")
        macro_peer = make_asset("CCC", sector="Utilities", industry="Electric Utilities")

        make_news(asset, "AAA shares rise on earnings beat")
        make_news(peer, "Regional banks face deposit pressure")
        make_news(macro_peer, "Fed keeps rates higher for longer")

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
        assert any(item["bucket"] in {"symbol", "company", "sector", "macro"} for item in result["news_items"])
        assert "Context pack:" in recorded_prompt["input"]
        assert "Story so far:" in recorded_prompt["input"]
        assert "[symbol]" in recorded_prompt["input"] or "[company]" in recorded_prompt["input"]


@pytest.mark.django_db
class TestScopeInsightPrompt:
    def test_analyze_scope_uses_monitored_set_context(self, user):
        asset_a = make_asset("AAA", sector="Financial", industry="Banks")
        asset_b = make_asset("BBB", sector="Financial", industry="Banks")

        make_news(asset_a, "AAA shares rise on earnings beat")
        make_news(asset_b, "BBB sees steady inflows")

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
        assert "AAA" in recorded_prompt["input"]
        assert "BBB" in recorded_prompt["input"]
