import pytest
from decimal import Decimal
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestPortfolioEndpoints:
    def test_portfolio_list_requires_auth(self):
        client = APIClient()
        response = client.get("/api/portfolios/")
        assert response.status_code == 403

    def test_portfolio_list_returns_user_portfolios(self, authenticated_client, portfolio):
        response = authenticated_client.get("/api/portfolios/")
        assert response.status_code == 200
        data = response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data
        assert len(data) >= 1
        assert data[0]["name"] == portfolio.name

    def test_portfolio_list_excludes_other_user_portfolios(self, authenticated_client, portfolio, user2, db):
        other_portfolio = pytest.importorskip("conftest").PortfolioFactory(user=user2)
        response = authenticated_client.get("/api/portfolios/")
        assert response.status_code == 200
        data = response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data
        assert all(p["id"] != str(other_portfolio.id) for p in data)

    def test_portfolio_create_succeeds(self, authenticated_client):
        response = authenticated_client.post(
            "/api/portfolios/",
            {"name": "New Portfolio", "market": "US", "initial_capital": "5000.00"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["name"] == "New Portfolio"
        assert response.data["market"] == "US"
        assert response.data["current_cash"] == "5000.00"

    def test_portfolio_detail_retrieves_portfolio(self, authenticated_client, portfolio):
        response = authenticated_client.get(f"/api/portfolios/{portfolio.id}/")
        assert response.status_code == 200
        assert response.data["id"] == str(portfolio.id)
        assert response.data["name"] == portfolio.name

    def test_portfolio_summary_returns_stats(self, authenticated_client, portfolio):
        response = authenticated_client.get(f"/api/portfolios/{portfolio.id}/summary/")
        assert response.status_code == 200
        assert "total_equity" in response.data
        assert "current_cash" in response.data

    def test_portfolio_performance_returns_twr(self, authenticated_client, portfolio):
        response = authenticated_client.get(f"/api/portfolios/{portfolio.id}/performance/")
        assert response.status_code == 200
        assert "twr" in response.data
        assert "snapshots" in response.data

    def test_portfolio_deposit_increases_cash(self, authenticated_client, portfolio):
        original_cash = Decimal(str(portfolio.current_cash))
        response = authenticated_client.post(
            f"/api/portfolios/{portfolio.id}/deposit/",
            {"amount": "1000.00"},
            format="json",
        )
        assert response.status_code == 200
        assert Decimal(response.data["cash"]) == original_cash + Decimal("1000.00")

    def test_portfolio_withdraw_decreases_cash(self, authenticated_client, portfolio):
        original_cash = Decimal(str(portfolio.current_cash))
        response = authenticated_client.post(
            f"/api/portfolios/{portfolio.id}/withdraw/",
            {"amount": "500.00"},
            format="json",
        )
        assert response.status_code == 200
        assert Decimal(response.data["cash"]) == original_cash - Decimal("500.00")

    def test_portfolio_withdraw_clamps_to_available_cash(self, authenticated_client, portfolio):
        response = authenticated_client.post(
            f"/api/portfolios/{portfolio.id}/withdraw/",
            {"amount": "999999.00"},
            format="json",
        )
        assert response.status_code == 200
        assert "warning" in response.data

    def test_portfolio_cash_transactions_lists_transactions(self, authenticated_client, portfolio):
        authenticated_client.post(
            f"/api/portfolios/{portfolio.id}/deposit/",
            {"amount": "1000.00"},
            format="json",
        )
        response = authenticated_client.get(f"/api/portfolios/{portfolio.id}/cash_transactions/")
        assert response.status_code == 200
        assert len(response.data) >= 1

    def test_portfolio_timeline_returns_events(self, authenticated_client, portfolio):
        response = authenticated_client.get(f"/api/portfolios/{portfolio.id}/timeline/")
        assert response.status_code == 200
        assert isinstance(response.data, list)

    def test_portfolio_refresh_prices_with_positions(self, authenticated_client, position):
        response = authenticated_client.post(f"/api/portfolios/{position.portfolio.id}/refresh_prices/")
        assert response.status_code == 200
        assert "refreshed" in response.data
        assert isinstance(response.data["refreshed"], int)

    def test_portfolio_refresh_prices_empty_portfolio(self, authenticated_client, portfolio):
        response = authenticated_client.post(f"/api/portfolios/{portfolio.id}/refresh_prices/")
        assert response.status_code == 200
        assert response.data["refreshed"] == 0
