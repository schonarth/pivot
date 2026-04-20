from unittest.mock import patch

import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_mcp_schema_is_public():
    client = APIClient()
    response = client.get("/api/mcp/schema/")

    assert response.status_code == 200
    assert response.data["authentication"]["agent"] == "Agent token (obtained via OTP exchange)"
    assert any(endpoint["path"] == "/api/mcp/assets/lookup-symbol/" for endpoint in response.data["endpoints"])
    assert any(endpoint["path"] == "/api/ai/discovery/" for endpoint in response.data["endpoints"])


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
            "name": "Gordon",
            "origin": "unknown",
            "llm_provider": "openai",
            "llm_model": "gpt-5.4-mini",
        },
        format="json",
    )

    assert exchange_response.status_code == 201
    assert "token" in exchange_response.data

    agents_response = authenticated_client.get("/api/mcp/agents/")
    assert agents_response.status_code == 200
    assert len(agents_response.data) == 1
    assert agents_response.data[0]["name"] == "Gordon"


@pytest.mark.django_db
def test_mcp_token_exchange_rejects_invalid_metadata_types(authenticated_client, user, monkeypatch):
    monkeypatch.setattr("mcp.views.publish_event", lambda *args, **kwargs: None)

    otp_response = authenticated_client.post("/api/mcp/otp/generate/")

    response = APIClient().post(
        "/api/mcp/token/exchange/",
        {
            "user_id": str(user.api_uuid),
            "otp": otp_response.data["code"],
            "name": 123,
            "origin": "unknown",
            "llm_provider": "openai",
            "llm_model": "gpt-5.4-mini",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "name" in response.data["error"]


@pytest.mark.django_db
def test_mcp_token_exchange_rejects_oversized_metadata(authenticated_client, user, monkeypatch):
    monkeypatch.setattr("mcp.views.publish_event", lambda *args, **kwargs: None)

    otp_response = authenticated_client.post("/api/mcp/otp/generate/")

    response = APIClient().post(
        "/api/mcp/token/exchange/",
        {
            "user_id": str(user.api_uuid),
            "otp": otp_response.data["code"],
            "name": "G" * 256,
            "origin": "unknown",
            "llm_provider": "openai",
            "llm_model": "gpt-5.4-mini",
        },
        format="json",
    )

    assert response.status_code == 400
    assert "name" in response.data["error"]


@pytest.mark.django_db
def test_mcp_asset_lookup_imports_new_asset_from_yahoo_search(authenticated_client, user, monkeypatch):
    monkeypatch.setattr("mcp.views.publish_event", lambda *args, **kwargs: None)

    otp_response = authenticated_client.post("/api/mcp/otp/generate/")
    exchange_client = APIClient()
    exchange_response = exchange_client.post(
        "/api/mcp/token/exchange/",
        {
            "user_id": str(user.api_uuid),
            "otp": otp_response.data["code"],
            "name": "Lookup Agent",
            "origin": "unknown",
            "llm_provider": "openai",
            "llm_model": "gpt-5.4-mini",
        },
        format="json",
    )
    agent_token = exchange_response.data["token"]

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

    with patch("markets.services.requests.get", return_value=mock_response), patch(
        "markets.tasks.backfill_single_asset_ohlcv.delay"
    ) as mock_backfill:
        response = exchange_client.post(
            "/api/mcp/assets/lookup-symbol/",
            {
                "agent_token": agent_token,
                "symbol": "ZETA4",
            },
            format="json",
        )

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]["display_symbol"] == "ZETA4"
    assert response.data[0]["provider_symbol"] == "ZETA4.SA"
    assert response.data[0]["market"] == "BR"
    mock_backfill.assert_called_once()
