import pytest
from decimal import Decimal
from rest_framework.test import APIClient
from unittest.mock import patch


@pytest.mark.django_db
class TestAlertEndpoints:
    def test_alert_list_requires_auth(self):
        client = APIClient()
        response = client.get("/api/portfolios/00000000-0000-0000-0000-000000000000/alerts/")
        assert response.status_code == 403

    def test_alert_list_returns_alerts(self, authenticated_client, alert):
        response = authenticated_client.get(f"/api/portfolios/{alert.portfolio.id}/alerts/")
        assert response.status_code == 200
        data = response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data
        assert len(data) >= 1
        assert data[0]["id"] == str(alert.id)

    @patch("realtime.services.publish_event")
    def test_alert_create_succeeds(self, mock_pub, authenticated_client, portfolio, asset):
        response = authenticated_client.post(
            f"/api/portfolios/{portfolio.id}/alerts/",
            {
                "asset_id": str(asset.id),
                "condition_type": "price_above",
                "threshold": "150.00",
                "notify_enabled": True,
                "auto_trade_enabled": False,
            },
            format="json",
        )
        assert response.status_code == 201
        assert response.data["condition_type"] == "price_above"
        assert response.data["threshold"] in ["150.00", "150.0000"]
        assert response.data["status"] == "active"

    def test_alert_create_with_mismatched_market_fails(self, authenticated_client, portfolio, db):
        from conftest import AssetFactory
        br_asset = AssetFactory(market="BR")
        response = authenticated_client.post(
            f"/api/portfolios/{portfolio.id}/alerts/",
            {
                "asset_id": str(br_asset.id),
                "condition_type": "price_above",
                "threshold": "150.00",
                "notify_enabled": True,
                "auto_trade_enabled": False,
            },
            format="json",
        )
        assert response.status_code == 400
        assert "market_mismatch" in response.data.get("error", {}).get("code", "")

    def test_alert_detail_retrieves_alert(self, authenticated_client, alert):
        response = authenticated_client.get(f"/api/alerts/{alert.id}/")
        assert response.status_code == 200
        assert response.data["id"] == str(alert.id)

    @patch("realtime.services.publish_event")
    def test_alert_update_succeeds(self, mock_pub, authenticated_client, alert):
        response = authenticated_client.patch(
            f"/api/alerts/{alert.id}/",
            {
                "asset_id": str(alert.asset.id),
                "condition_type": "price_below",
                "threshold": "50.00",
                "notify_enabled": True,
                "auto_trade_enabled": False,
            },
            format="json",
        )
        assert response.status_code == 200
        assert response.data["condition_type"] == "price_below"
        assert response.data["threshold"] in ["50.00", "50.0000"]

    def test_alert_pause_succeeds(self, authenticated_client, alert):
        response = authenticated_client.post(f"/api/alerts/{alert.id}/pause/")
        assert response.status_code == 200
        assert response.data["status"] == "paused"

    def test_alert_pause_when_triggered_fails(self, authenticated_client, alert, db):
        alert.status = "triggered"
        alert.save()
        response = authenticated_client.post(f"/api/alerts/{alert.id}/pause/")
        assert response.status_code == 400
        assert "invalid_status" in response.data.get("error", {}).get("code", "")

    def test_alert_resume_succeeds(self, authenticated_client, alert):
        alert.status = "paused"
        alert.save()
        response = authenticated_client.post(f"/api/alerts/{alert.id}/resume/")
        assert response.status_code == 200
        assert response.data["status"] == "active"

    def test_alert_resume_when_active_fails(self, authenticated_client, alert):
        response = authenticated_client.post(f"/api/alerts/{alert.id}/resume/")
        assert response.status_code == 400
        assert "invalid_status" in response.data.get("error", {}).get("code", "")

    def test_alert_trigger_list_requires_auth(self):
        client = APIClient()
        response = client.get("/api/alert-triggers/")
        assert response.status_code == 403

    def test_alert_trigger_list_returns_triggers(self, authenticated_client, alert, db):
        from conftest import AlertTriggerFactory
        trigger = AlertTriggerFactory(alert=alert)
        response = authenticated_client.get("/api/alert-triggers/")
        assert response.status_code == 200
        data = response.data["results"] if isinstance(response.data, dict) and "results" in response.data else response.data
        assert len(data) >= 1
        assert data[0]["id"] == str(trigger.id)
