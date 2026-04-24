import json
import re
import sys
from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from ai.discovery import OpportunityDiscoveryService
from ai.services import AIService
from markets.models import Asset, NewsItem, OHLCV
from portfolios.models import Portfolio
from trading.models import Position


def build_history(asset, start_close: Decimal, step: Decimal = Decimal("1.00")):
    start_date = timezone.now().date() - timedelta(days=199)
    close = start_close
    for offset in range(200):
        OHLCV.objects.create(
            asset=asset,
            date=start_date + timedelta(days=offset),
            open=close - Decimal("1.00"),
            high=close + Decimal("1.00"),
            low=close - Decimal("2.00"),
            close=close,
            volume=60000 + offset,
        )
        close += step


@pytest.mark.django_db
class TestOpportunityDiscovery:
    def test_discovery_endpoint_returns_structured_shortlist(self, authenticated_client, asset):
        build_history(asset, Decimal("100.00"))

        response = authenticated_client.get("/api/ai/discovery/", {"market": "US"})

        assert response.status_code == 200
        assert response.data["market"] == "US"
        assert response.data["universe_size"] == 1
        assert response.data["survivor_count"] == 1
        assert response.data["shortlist_count"] == 1
        assert len(response.data["shortlist"]) == 1
        item = response.data["shortlist"][0]
        assert item["asset_id"] == str(asset.id)
        assert item["symbol"] == asset.display_symbol
        assert item["watch_action_ready"] is True
        assert "technical_signals" in item
        assert "context_summary" in item
        assert "discovery_reason" in item
        assert "score_breakdown" in item

    def test_shortlist_orders_by_context_when_technical_setup_is_equal(self, authenticated_client, asset):
        other_asset = Asset.objects.create(
            display_symbol="ZZZ9",
            provider_symbol="ZZZ9",
            name="Context Asset",
            market="US",
            exchange="XNYS",
            currency="USD",
            sector="Tech",
            industry="Software",
            is_seeded=True,
        )
        build_history(asset, Decimal("100.00"))
        build_history(other_asset, Decimal("100.00"))
        NewsItem.objects.create(
            asset=asset,
            headline="Asset sees strong support from buyers",
            source="Example News",
            url="https://example.com/a",
            sentiment_score=Decimal("0.80"),
            published_at=timezone.now(),
        )

        response = authenticated_client.get("/api/ai/discovery/", {"market": "US"})

        assert response.status_code == 200
        assert response.data["shortlist"][0]["symbol"] == asset.display_symbol
        assert response.data["shortlist"][0]["discovery_reason"].endswith("Context is positive.")

    def test_discovery_excludes_assets_already_held_in_any_user_portfolio(self, authenticated_client, user):
        held_asset = Asset.objects.create(
            display_symbol="HLD1",
            provider_symbol="HLD1",
            name="Held Asset",
            market="US",
            exchange="XNYS",
            currency="USD",
            sector="Tech",
            industry="Software",
            is_seeded=True,
        )
        candidate_asset = Asset.objects.create(
            display_symbol="NEW1",
            provider_symbol="NEW1",
            name="New Candidate",
            market="US",
            exchange="XNYS",
            currency="USD",
            sector="Tech",
            industry="Software",
            is_seeded=True,
        )
        build_history(held_asset, Decimal("100.00"))
        build_history(candidate_asset, Decimal("120.00"))

        first_portfolio = Portfolio.objects.create(
            user=user,
            name="Core",
            market="US",
            initial_capital=Decimal("10000.00"),
            current_cash=Decimal("5000.00"),
        )
        second_portfolio = Portfolio.objects.create(
            user=user,
            name="Satellite",
            market="US",
            initial_capital=Decimal("10000.00"),
            current_cash=Decimal("5000.00"),
        )
        Position.objects.create(
            portfolio=first_portfolio,
            asset=held_asset,
            quantity=10,
            average_cost=Decimal("100.00"),
        )
        Position.objects.create(
            portfolio=second_portfolio,
            asset=held_asset,
            quantity=5,
            average_cost=Decimal("105.00"),
        )

        response = authenticated_client.get("/api/ai/discovery/", {"market": "US"})

        assert response.status_code == 200
        assert response.data["universe_size"] == 1
        assert response.data["shortlist_count"] == 1
        assert response.data["shortlist"][0]["symbol"] == candidate_asset.display_symbol
        assert all(item["symbol"] != held_asset.display_symbol for item in response.data["shortlist"])

    def test_discovery_bulk_loads_technical_inputs(self, user):
        assets = [
            Asset.objects.create(
                display_symbol=f"BULK{index}",
                provider_symbol=f"BULK{index}",
                name=f"Bulk Candidate {index}",
                market="US",
                exchange="XNYS",
                currency="USD",
                sector="Tech",
                industry="Software",
                is_seeded=True,
            )
            for index in range(3)
        ]
        for asset in assets:
            build_history(asset, Decimal("100.00"))

        service = OpportunityDiscoveryService(user)

        with CaptureQueriesContext(connection) as queries:
            service.discover("US")

        ohlcv_queries = [query for query in queries if 'FROM "ohlcv"' in query["sql"]]
        indicator_queries = [query for query in queries if 'FROM "technical_indicators"' in query["sql"]]
        quote_queries = [query for query in queries if 'FROM "asset_quotes"' in query["sql"]]
        news_queries = [query for query in queries if 'FROM "news_items"' in query["sql"]]
        assert len(ohlcv_queries) == 1
        assert len(indicator_queries) == 1
        assert len(quote_queries) == 1
        assert len(news_queries) == 1

    def test_refinement_cache_reuses_and_invalidates_on_shortlist_change(self, user, db, monkeypatch):
        cache.clear()
        AIService(user).set_api_key("test-key")
        service = OpportunityDiscoveryService(user)

        asset_one = Asset.objects.create(
            display_symbol="ALP1",
            provider_symbol="ALP1",
            name="Alpha One",
            market="US",
            exchange="XNYS",
            currency="USD",
            sector="Tech",
            industry="Software",
            is_seeded=True,
        )
        build_history(asset_one, Decimal("100.00"))

        call_count = {"value": 0}

        class FakeResponses:
            def create(self, **kwargs):
                call_count["value"] += 1
                asset_ids = re.findall(r'"asset_id":\s*"([^"]+)"', kwargs["input"])
                refined_items = [
                    {"asset_id": asset_id, "refined_reason": "Refined by cache test."}
                    for asset_id in asset_ids
                ]
                payload = {"items": refined_items}
                return SimpleNamespace(
                    output_text=json.dumps(payload),
                    usage=SimpleNamespace(input_tokens=10, output_tokens=5),
                )

        class FakeOpenAI:
            def __init__(self, api_key):
                self.api_key = api_key
                self.responses = FakeResponses()

        monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))

        first = service.discover("US", refine=True)
        second = service.discover("US", refine=True)

        assert call_count["value"] == 1
        assert first["refinement"]["applied"] is True
        assert second["refinement"]["cache_hit"] is True

        asset_two = Asset.objects.create(
            display_symbol="OME9",
            provider_symbol="OME9",
            name="Omega Nine",
            market="US",
            exchange="XNYS",
            currency="USD",
            sector="Tech",
            industry="Software",
            is_seeded=True,
        )
        build_history(asset_two, Decimal("150.00"))

        third = service.discover("US", refine=True)

        assert call_count["value"] == 2
        assert third["shortlist"][0]["symbol"] in {asset_one.display_symbol, asset_two.display_symbol}
