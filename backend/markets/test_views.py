import pytest
from decimal import Decimal
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestMarketEndpoints:
    def test_asset_list_requires_auth(self):
        client = APIClient()
        response = client.get("/api/assets/")
        assert response.status_code == 401

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
        response = authenticated_client.get("/api/markets/status")
        assert response.status_code == 200
        assert "US" in response.data
        assert all("open" in status for status in response.data.values())

    def test_market_config_list(self, authenticated_client):
        response = authenticated_client.get("/api/markets/")
        assert response.status_code == 200
        data = response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data
        assert isinstance(data, list)
