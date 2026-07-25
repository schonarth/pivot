from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from ai.models import ArtifactReview, FactCorrection, SourceStance, StrategyRecommendation
from markets.models import NewsItem, NewsSource
from mcp.models import AgentToken


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


def make_agent(user, token="assistant-token"):
    return AgentToken.objects.create(
        user=user,
        token=token,
        name="Evidence assistant",
        origin=f"test-{token}",
        llm_provider="openai",
        llm_model="gpt-5.4-mini",
    )


def make_evidence_recommendation(user, portfolio, asset, headline="AAA raises guidance"):
    source, _ = NewsSource.objects.get_or_create(
        feed_url=f"https://example.com/{asset.id}/feed",
        defaults={"institution_name": "Test Source"},
    )
    news_item = NewsItem.objects.create(
        asset=asset,
        headline=headline,
        url=f"https://example.com/{asset.id}/article",
        source="fixture",
        news_source=source,
    )
    recommendation = StrategyRecommendation.objects.create(
        user=user,
        portfolio=portfolio,
        asset=asset,
        action="BUY",
        quantity=1,
        candidate={"asset_symbol": asset.display_symbol},
        technical_inputs={},
        context_inputs={"items": [{"news_item_id": str(news_item.id), "headline": headline}]},
        sentiment_trajectory_inputs={},
        verdict="approve",
        rationale="Stored recommendation.",
    )
    return recommendation, news_item


@pytest.mark.django_db
def test_mcp_evidence_review_is_scoped_audited_and_rejects_forged_original(user, user2, portfolio, asset):
    agent = make_agent(user)
    recommendation, news_item = make_evidence_recommendation(user, portfolio, asset)
    other_portfolio = type(portfolio).objects.create(
        user=user2,
        name="Other",
        market=portfolio.market,
        initial_capital=portfolio.initial_capital,
        current_cash=portfolio.current_cash,
    )
    other_recommendation, other_news_item = make_evidence_recommendation(
        user2, other_portfolio, asset, "AAA cuts guidance"
    )
    client = APIClient()

    created = client.post(
        "/api/mcp/evidence/fact-corrections/",
        {
            "agent_token": agent.token,
            "news_item_id": str(news_item.id),
            "fact_key": "Guidance Update!",
            "corrected_value": "Guidance was withdrawn.",
            "correction_state": "disputed",
            "reason": "Issuer filing.",
            "original_value": "forged",
        },
        format="json",
    )

    assert created.status_code == 400
    assert not FactCorrection.objects.exists()

    created = client.post(
        "/api/mcp/evidence/fact-corrections/",
        {
            "agent_token": agent.token,
            "news_item_id": str(news_item.id),
            "fact_key": "Guidance Update!",
            "corrected_value": "Guidance was withdrawn.",
            "correction_state": "disputed",
            "reason": "Issuer filing.",
        },
        format="json",
    )

    assert created.status_code == 201
    correction = FactCorrection.objects.get()
    assert correction.operator == user
    assert correction.created_by == user
    assert correction.created_by_agent == agent
    assert correction.original_value == news_item.headline
    assert created.data["fact_key"] == "guidance_update"
    assert created.data["created_by_agent"] == {"id": agent.id, "name": agent.name, "origin": agent.origin}

    evidence = client.get(f"/api/mcp/evidence/{recommendation.id}/?agent_token={agent.token}")

    assert evidence.status_code == 200
    assert evidence.data["fact_key_suggestions"] == ["guidance_update"]
    assert evidence.data["is_invalidated"] is True
    assert evidence.data["evidence"][0]["correction_history"][0]["original_value"] == news_item.headline

    other = client.post(
        "/api/mcp/evidence/artifact-reviews/",
        {
            "agent_token": agent.token,
            "news_item_id": str(other_news_item.id),
            "artifact_review_state": "disputed",
            "reason": "Not in this operator scope.",
        },
        format="json",
    )

    assert other.status_code == 404
    assert not ArtifactReview.objects.exists()
    assert other_recommendation.user == user2


@pytest.mark.django_db
def test_mcp_evidence_review_mutations_use_shared_service_lifecycle(user, portfolio, asset):
    agent = make_agent(user)
    _, news_item = make_evidence_recommendation(user, portfolio, asset)
    client = APIClient()

    review = client.post(
        "/api/mcp/evidence/artifact-reviews/",
        {
            "agent_token": agent.token,
            "news_item_id": str(news_item.id),
            "artifact_review_state": "accepted",
            "reason": "Issuer filing.",
        },
        format="json",
    )
    stance = client.post(
        "/api/mcp/evidence/source-stances/",
        {"agent_token": agent.token, "source_id": news_item.news_source_id, "stance": "trusted"},
        format="json",
    )
    cleared = client.post(
        "/api/mcp/evidence/source-stances/",
        {"agent_token": agent.token, "source_id": news_item.news_source_id, "clear": True},
        format="json",
    )

    assert review.status_code == 201
    assert review.data["created_by_agent"]["id"] == agent.id
    assert stance.status_code == 201
    assert stance.data["created_by_agent"]["name"] == agent.name
    assert cleared.status_code == 204
    active_stance = SourceStance.objects.filter(operator=user, superseded_at__isnull=True)
    assert not active_stance.exists()
    assert SourceStance.objects.get().superseded_by_agent == agent
