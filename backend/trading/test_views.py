import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from unittest.mock import patch


@pytest.mark.django_db
class TestTradingEndpoints:
    def test_position_list_requires_auth(self):
        client = APIClient()
        response = client.get("/api/portfolios/00000000-0000-0000-0000-000000000000/positions/")
        assert response.status_code == 403

    def test_position_list_returns_positions(self, authenticated_client, position):
        response = authenticated_client.get(f"/api/portfolios/{position.portfolio.id}/positions/")
        assert response.status_code == 200
        data = response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data
        assert len(data) >= 1
        assert data[0]["id"] == str(position.id)

    def test_position_detail_retrieves_position(self, authenticated_client, position):
        response = authenticated_client.get(
            f"/api/portfolios/{position.portfolio.id}/positions/{position.asset.id}/"
        )
        assert response.status_code == 200
        assert response.data["id"] == str(position.id)

    def test_trade_list_requires_auth(self):
        client = APIClient()
        response = client.get("/api/portfolios/00000000-0000-0000-0000-000000000000/trades/")
        assert response.status_code == 403

    def test_trade_list_returns_trades(self, authenticated_client, trade):
        response = authenticated_client.get(f"/api/portfolios/{trade.portfolio.id}/trades/")
        assert response.status_code == 200
        data = response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data
        assert len(data) >= 1
        assert data[0]["id"] == str(trade.id)

    @patch("realtime.services.publish_event")
    def test_buy_trade_creates_position(self, mock_pub, authenticated_client, portfolio_with_cash, asset_with_quote):
        response = authenticated_client.post(
            f"/api/portfolios/{portfolio_with_cash.id}/trades/",
            {
                "asset_id": str(asset_with_quote.id),
                "action": "BUY",
                "quantity": "10.00",
                "rationale": "Test buy",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["trade"]["action"] == "BUY"
        assert response.data["trade"]["quantity"] == 10
        assert "position" in response.data

    @patch("realtime.services.publish_event")
    def test_sell_trade_closes_position(self, mock_pub, authenticated_client, position_with_quote):
        response = authenticated_client.post(
            f"/api/portfolios/{position_with_quote.portfolio.id}/trades/",
            {
                "asset_id": str(position_with_quote.asset.id),
                "action": "SELL",
                "quantity": "5",
                "rationale": "Test sell",
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["trade"]["action"] == "SELL"

    def test_buy_without_sufficient_cash_fails(self, authenticated_client, portfolio, asset_with_quote):
        response = authenticated_client.post(
            f"/api/portfolios/{portfolio.id}/trades/",
            {
                "asset_id": str(asset_with_quote.id),
                "action": "BUY",
                "quantity": "1000.00",
                "rationale": "Test",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "error" in response.data

    def test_sell_without_position_fails(self, authenticated_client, portfolio, asset_with_quote):
        response = authenticated_client.post(
            f"/api/portfolios/{portfolio.id}/trades/",
            {
                "asset_id": str(asset_with_quote.id),
                "action": "SELL",
                "quantity": "10.00",
                "rationale": "Test",
            },
            format="json",
        )
        assert response.status_code == 400
        assert "error" in response.data

    def test_trade_with_mismatched_market_fails(self, authenticated_client, portfolio, db):
        from conftest import AssetFactory
        br_asset = AssetFactory(market="BR")
        response = authenticated_client.post(
            f"/api/portfolios/{portfolio.id}/trades/",
            {
                "asset_id": str(br_asset.id),
                "action": "BUY",
                "quantity": "1.00",
                "rationale": "Test",
            },
            format="json",
        )
        assert response.status_code == 400
