import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestAuthEndpoints:
    def test_register_creates_user(self):
        client = APIClient()
        response = client.post(
            "/api/auth/register",
            {"username": "newuser", "email": "new@test.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == 201
        assert response.data["user"]["username"] == "newuser"
        assert "access" in response.data
        assert "refresh" in response.data
        assert User.objects.filter(username="newuser").exists()

    def test_register_with_duplicate_username_fails(self, user):
        client = APIClient()
        response = client.post(
            "/api/auth/register",
            {"username": user.username, "email": "other@test.com", "password": "testpass123"},
            format="json",
        )
        assert response.status_code == 400

    def test_login_returns_tokens(self, user):
        client = APIClient()
        response = client.post(
            "/api/auth/login",
            {"username": user.username, "password": "testpass123"},
            format="json",
        )
        assert response.status_code == 200
        assert response.data["user"]["username"] == user.username
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_with_invalid_password_fails(self, user):
        client = APIClient()
        response = client.post(
            "/api/auth/login",
            {"username": user.username, "password": "wrongpass"},
            format="json",
        )
        assert response.status_code == 401
        assert "error" in response.data

    def test_me_returns_authenticated_user(self, authenticated_client, user):
        response = authenticated_client.get("/api/auth/me")
        assert response.status_code == 200
        assert response.data["username"] == user.username
        assert response.data["email"] == user.email

    def test_me_without_auth_fails(self):
        client = APIClient()
        response = client.get("/api/auth/me")
        assert response.status_code == 403

    def test_logout_succeeds(self, authenticated_client):
        response = authenticated_client.post(
            "/api/auth/logout",
            {"refresh": "dummy_token"},
            format="json",
        )
        assert response.status_code == 204

    def test_logout_without_token_succeeds(self, authenticated_client):
        response = authenticated_client.post("/api/auth/logout", {}, format="json")
        assert response.status_code == 204
