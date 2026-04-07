"""Test authentication API endpoints"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user):
    """Test login with wrong password"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "testuser", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "password"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session):
    """Test login with inactive user"""
    from app.models.user import User
    from app.security import get_password_hash

    # Create an inactive user
    user = User(
        username="inactive",
        email="inactive@example.com",
        hashed_password=get_password_hash("password"),
        is_active=False
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "inactive", "password": "password"}
    )
    assert response.status_code == 400
    assert "Inactive user" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_info(client: AsyncClient, auth_headers):
    """Test getting current user info"""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_get_current_user_info_unauthorized(client: AsyncClient):
    """Test getting current user info without authentication"""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code in [401, 403]  # May return either 401 or 403


@pytest.mark.asyncio
async def test_get_current_user_info_invalid_token(client: AsyncClient):
    """Test getting current user info with invalid token"""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
