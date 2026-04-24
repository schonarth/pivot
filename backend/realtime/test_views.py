import pytest
from rest_framework.test import APIClient

from config.query_observability import clear_query_stats


@pytest.mark.django_db
class TestRealtimeEndpoints:
    def test_health_check_public(self):
        client = APIClient()
        response = client.get("/api/health")
        assert response.status_code in [200, 503]
        assert "database" in response.data
        assert "redis" in response.data
        assert response.data["database"] == "ok"
        assert response.data["redis"] == "ok"

    def test_health_check_returns_ok_when_healthy(self):
        client = APIClient()
        response = client.get("/api/health")
        assert response.status_code == 200
        assert all(v == "ok" for v in response.data.values())

    def test_system_stats_requires_auth(self):
        client = APIClient()
        response = client.get("/api/system/stats")
        assert response.status_code == 403

    def test_system_stats_returns_stats(self, authenticated_client):
        response = authenticated_client.get("/api/system/stats")
        assert response.status_code == 200
        assert "portfolios" in response.data
        assert "trades" in response.data
        assert "alerts_active" in response.data
        assert "assets" in response.data
        assert "quotes" in response.data
        assert isinstance(response.data["portfolios"], int)
        assert isinstance(response.data["trades"], int)
        assert isinstance(response.data["alerts_active"], int)
        assert isinstance(response.data["assets"], int)
        assert isinstance(response.data["quotes"], int)

    def test_system_stats_counts_are_correct(self, authenticated_client, portfolio, asset_with_quote, alert):
        response = authenticated_client.get("/api/system/stats")
        assert response.status_code == 200
        assert response.data["portfolios"] >= 1
        assert response.data["assets"] >= 1
        assert response.data["quotes"] >= 1
        assert response.data["alerts_active"] >= 1

    def test_query_stats_requires_auth(self):
        client = APIClient()
        response = client.get("/api/system/query-stats")
        assert response.status_code == 403

    def test_query_stats_returns_global_request_stats(self, authenticated_client, portfolio):
        clear_query_stats()

        authenticated_client.get("/api/system/stats")
        response = authenticated_client.get("/api/system/query-stats")

        assert response.status_code == 200
        assert response.data["total_requests"] >= 1
        assert response.data["total_queries"] >= 1
        assert response.data["retained_requests"] >= 1
        assert response.data["max_retained_requests"] == 100
        assert response.data["requests"][0]["path"] == "/api/system/stats"
        assert response.data["requests"][0]["query_count"] >= 1
        assert "fingerprints" in response.data["requests"][0]
        assert "heavy_paths" in response.data
