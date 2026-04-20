from datetime import timedelta
from decimal import Decimal
from unittest.mock import ANY, patch

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from ai.services import AIBudgetError
from markets.models import NewsItem, OHLCV


@pytest.mark.django_db
class TestMarketEndpoints:
    def test_asset_list_requires_auth(self):
        client = APIClient()
        response = client.get("/api/assets/")
        assert response.status_code == 403

    def test_asset_list_returns_all_assets(self, authenticated_client, asset):
        response = authenticated_client.get("/api/assets/")
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert any(a["id"] == str(asset.id) for a in response.data)

    def test_asset_list_filters_by_market(self, authenticated_client, asset):
        response = authenticated_client.get("/api/assets/?market=US")
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert all(a["market"] == "US" for a in response.data)

    def test_asset_list_filters_by_search(self, authenticated_client, asset):
        response = authenticated_client.get(f"/api/assets/?q={asset.display_symbol}")
        assert response.status_code == 200
        assert len(response.data) >= 1
        assert asset.display_symbol in [a["display_symbol"] for a in response.data]

    @patch("markets.services.requests.get")
    def test_asset_lookup_symbol_returns_local_exact_match(self, mock_get, authenticated_client, asset):
        response = authenticated_client.post(
            "/api/assets/lookup-symbol/",
            {"symbol": asset.display_symbol},
            format="json",
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["display_symbol"] == asset.display_symbol
        mock_get.assert_not_called()

    @patch("markets.services.requests.get")
    @patch("markets.tasks.backfill_single_asset_ohlcv.delay")
    def test_asset_lookup_symbol_imports_new_asset_from_yahoo_search(self, mock_backfill, mock_get, authenticated_client):
        mock_response = type("Response", (), {})()
        mock_response.raise_for_status = lambda: None
        mock_response.json = lambda: {
            "quotes": [
                {
                    "symbol": "ZETA4.SA",
                    "quoteType": "EQUITY",
                    "shortname": "Zeta Holdings",
                    "exchange": "SAO",
                    "currency": "BRL",
                }
            ]
        }
        mock_get.return_value = mock_response

        response = authenticated_client.post(
            "/api/assets/lookup-symbol/",
            {"symbol": "ZETA4"},
            format="json",
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["display_symbol"] == "ZETA4"
        assert response.data[0]["provider_symbol"] == "ZETA4.SA"
        assert response.data[0]["market"] == "BR"
        mock_backfill.assert_called_once()

    @patch("markets.services.requests.get")
    @patch("markets.tasks.backfill_single_asset_ohlcv.delay", side_effect=RuntimeError("broker down"))
    def test_asset_lookup_symbol_keeps_asset_when_backfill_queue_fails(self, mock_backfill, mock_get, authenticated_client):
        mock_response = type("Response", (), {})()
        mock_response.raise_for_status = lambda: None
        mock_response.json = lambda: {
            "quotes": [
                {
                    "symbol": "ZETA4.SA",
                    "quoteType": "EQUITY",
                    "shortname": "Zeta Holdings",
                    "exchange": "SAO",
                    "currency": "BRL",
                }
            ]
        }
        mock_get.return_value = mock_response

        response = authenticated_client.post(
            "/api/assets/lookup-symbol/",
            {"symbol": "ZETA4"},
            format="json",
        )

        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]["display_symbol"] == "ZETA4"
        mock_backfill.assert_called_once()

    @patch("markets.services.requests.get")
    def test_asset_lookup_symbol_returns_404_when_not_found(self, mock_get, authenticated_client):
        mock_response = type("Response", (), {})()
        mock_response.raise_for_status = lambda: None
        mock_response.json = lambda: {"quotes": []}
        mock_get.return_value = mock_response

        response = authenticated_client.post(
            "/api/assets/lookup-symbol/",
            {"symbol": "NOTREAL"},
            format="json",
        )

        assert response.status_code == 404
        assert response.data["error"]["code"] == "not_found"

    def test_asset_detail_retrieves_asset(self, authenticated_client, asset):
        response = authenticated_client.get(f"/api/assets/{asset.id}/")
        assert response.status_code == 200
        assert response.data["id"] == str(asset.id)
        assert response.data["display_symbol"] == asset.display_symbol

    def test_asset_price_returns_quote(self, authenticated_client, asset_with_quote):
        response = authenticated_client.get(f"/api/assets/{asset_with_quote.id}/price/")
        assert response.status_code == 200
        assert response.data["price"] in ["100.00", "100.0000"]
        assert "market_open" in response.data

    def test_asset_price_without_quote_returns_404(self, authenticated_client, asset):
        response = authenticated_client.get(f"/api/assets/{asset.id}/price/")
        assert response.status_code == 404
        assert "error" in response.data

    def test_market_status_lists_all_markets(self, authenticated_client):
        response = authenticated_client.get("/api/markets/status/")
        assert response.status_code == 200
        assert "US" in response.data
        assert all("open" in status for status in response.data.values())

    def test_market_config_list(self, authenticated_client):
        response = authenticated_client.get("/api/markets/")
        assert response.status_code == 200
        data = (
            response.data["results"]
            if isinstance(response.data, dict) and "results" in response.data
            else response.data
        )
        assert isinstance(data, list)

    def test_asset_refresh_price_returns_quote(self, authenticated_client, asset_with_quote):
        response = authenticated_client.post(f"/api/assets/{asset_with_quote.id}/refresh-price/")
        assert response.status_code == 200
        assert "price" in response.data
        assert "market_open" in response.data

    def test_asset_refresh_price_without_quote_returns_stale(self, authenticated_client, asset):
        response = authenticated_client.post(f"/api/assets/{asset.id}/refresh-price/")
        assert response.status_code == 404
        assert "error" in response.data

    @patch("markets.views.NewsService.fetch_and_store_news")
    def test_asset_news_returns_recent_items_and_average_sentiment(self, mock_fetch_news, authenticated_client, asset):
        NewsItem.objects.create(
            asset=asset,
            headline="Momentum improves after earnings",
            summary="Analysts see better margins.",
            url="https://example.com/news-1",
            source="Example News",
            sentiment_score=Decimal("0.80"),
        )
        NewsItem.objects.create(
            asset=asset,
            headline="Supply chain remains stable",
            summary="Operations remain on track.",
            url="https://example.com/news-2",
            source="Example News",
            sentiment_score=Decimal("0.20"),
        )

        response = authenticated_client.get(f"/api/assets/{asset.id}/news/")

        assert response.status_code == 200
        assert response.data["symbol"] == asset.display_symbol
        assert response.data["average_sentiment"] == 0.5
        assert len(response.data["news_items"]) == 2
        mock_fetch_news.assert_called_once_with(asset)

    def test_asset_indicators_returns_series_for_requested_window(self, authenticated_client, asset):
        start_date = timezone.now().date() - timedelta(days=59)

        for offset in range(60):
            close = Decimal("100.00") + Decimal(str(offset))
            OHLCV.objects.create(
                asset=asset,
                date=start_date + timedelta(days=offset),
                open=close - Decimal("1.00"),
                high=close + Decimal("1.00"),
                low=close - Decimal("2.00"),
                close=close,
                volume=1000 + offset,
            )

        response = authenticated_client.get(f"/api/assets/{asset.id}/indicators/?days=30")

        assert response.status_code == 200
        assert len(response.data) == 31
        assert response.data[-1]["date"] == start_date + timedelta(days=59)
        assert response.data[-1]["ma_20"] is not None

    @patch("ai.services.AIService.analyze_asset")
    def test_asset_ai_insight_returns_generated_analysis(self, mock_analyze_asset, authenticated_client, asset):
        mock_analyze_asset.return_value = {
            "symbol": asset.display_symbol,
            "market": asset.market,
            "recommendation": "BUY",
            "confidence": 78,
            "summary": "Trend remains constructive.",
            "technical_summary": "Trend remains constructive.",
            "news_context": "Recent coverage is supportive.",
            "reasoning": "",
            "price_target": 145.5,
            "model_used": "gpt-4o-mini",
            "generated_at": timezone.now().isoformat(),
            "news_items": [],
        }

        response = authenticated_client.get(f"/api/assets/{asset.id}/ai-insight/")

        assert response.status_code == 200
        assert response.data["recommendation"] == "BUY"
        assert response.data["confidence"] == 78

    @patch("ai.services.AIService.analyze_asset")
    def test_asset_ai_insight_returns_budget_error(self, mock_analyze_asset, authenticated_client, asset):
        mock_analyze_asset.side_effect = AIBudgetError("Budget exceeded")

        response = authenticated_client.get(f"/api/assets/{asset.id}/ai-insight/")

        assert response.status_code == 402
        assert response.data["error"]["code"] == "budget_exceeded"


@pytest.mark.django_db
class TestOhlcvBackfillEndpoints:
    @patch("markets.views.get_backfill_status")
    def test_ohlcv_backfill_status_returns_status(self, mock_status, authenticated_client):
        mock_status.return_value = {
            "state": "running",
            "source": "startup",
            "initiated_by": None,
            "total_assets": 3,
            "processed_assets_count": 1,
            "successful_assets": 1,
            "failed_assets": 0,
            "current_asset": {"symbol": "AAA", "index": 2, "total_assets": 3},
            "processed_assets": [],
            "started_at": "2026-04-16T00:00:00Z",
            "updated_at": "2026-04-16T00:00:01Z",
            "completed_at": None,
        }

        response = authenticated_client.get("/api/markets/ohlcv-backfill/")

        assert response.status_code == 200
        assert response.data["state"] == "running"
        mock_status.assert_called_once()

    @patch("markets.views.queue_ohlcv_backfill")
    def test_ohlcv_backfill_start_queues_task(self, mock_queue, authenticated_client):
        mock_queue.return_value = (True, {
            "state": "queued",
            "source": "manual",
            "initiated_by": "user-id",
            "total_assets": 3,
            "processed_assets_count": 0,
            "successful_assets": 0,
            "failed_assets": 0,
            "current_asset": None,
            "processed_assets": [],
            "started_at": "2026-04-16T00:00:00Z",
            "updated_at": "2026-04-16T00:00:01Z",
            "completed_at": None,
        })

        response = authenticated_client.post("/api/markets/ohlcv-backfill/")

        assert response.status_code == 202
        assert response.data["queued"] is True
        mock_queue.assert_called_once_with(source="manual", initiated_by=ANY)
