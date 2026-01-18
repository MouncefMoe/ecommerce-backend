"""Tests for auth router."""

import pytest
from httpx import AsyncClient

from tests.conftest import auth_header


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "customer"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, test_user):
    """Test registration with duplicate email fails."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": test_user.email,
            "password": "password123",
            "full_name": "Another User",
        },
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user):
    """Test successful login."""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "testpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_user):
    """Test login with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": test_user.email,
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user, user_token):
    """Test get current user profile."""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_header(user_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.asyncio
async def test_get_current_user_unauthorized(client: AsyncClient):
    """Test get current user without token fails."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, test_user, user_token):
    """Test update user profile."""
    response = await client.patch(
        "/api/v1/auth/me",
        headers=auth_header(user_token),
        json={
            "full_name": "Updated Name",
            "phone": "1234567890",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["phone"] == "1234567890"


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, test_user, user_token):
    """Test change password."""
    response = await client.post(
        "/api/v1/auth/change-password",
        headers=auth_header(user_token),
        json={
            "current_password": "testpassword123",
            "new_password": "newpassword456",
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, test_user, user_token):
    """Test change password with wrong current password."""
    response = await client.post(
        "/api/v1/auth/change-password",
        headers=auth_header(user_token),
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        },
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_admin_list_users(client: AsyncClient, test_admin, admin_token):
    """Test admin can list users."""
    response = await client.get(
        "/api/v1/auth/users",
        headers=auth_header(admin_token),
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_non_admin_cannot_list_users(client: AsyncClient, test_user, user_token):
    """Test non-admin cannot list users."""
    response = await client.get(
        "/api/v1/auth/users",
        headers=auth_header(user_token),
    )
    assert response.status_code == 403
