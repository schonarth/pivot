import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_mcp_schema_is_public():
    client = APIClient()
    response = client.get("/api/mcp/schema/")

    assert response.status_code == 200
    assert response.data["authentication"]["agent"] == "Agent token (obtained via OTP exchange)"


@pytest.mark.django_db
def test_mcp_otp_exchange_and_agent_listing(authenticated_client, user, monkeypatch):
    monkeypatch.setattr("mcp.views.publish_event", lambda *args, **kwargs: None)

    otp_response = authenticated_client.post("/api/mcp/otp/generate/")
    assert otp_response.status_code == 200

    exchange_client = APIClient()
    exchange_response = exchange_client.post(
        "/api/mcp/token/exchange/",
        {
            "user_id": str(user.api_uuid),
            "otp": otp_response.data["code"],
            "name": "Unknown Agent",
            "origin": "unknown",
        },
        format="json",
    )

    assert exchange_response.status_code == 201
    assert "token" in exchange_response.data

    agents_response = authenticated_client.get("/api/mcp/agents/")
    assert agents_response.status_code == 200
    assert len(agents_response.data) == 1
    assert agents_response.data[0]["name"] == "Unknown Agent"
