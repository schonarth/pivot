from datetime import timedelta
from decimal import Decimal
from types import SimpleNamespace
import json
import re
import sys

import pytest
from django.core.cache import cache
from django.utils import timezone

from ai.discovery import OpportunityDiscoveryService
from ai.services import AIService
from markets.models import Asset, NewsItem, OHLCV


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
