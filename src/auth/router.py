"""Authentication API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AdminUser, CurrentUser
from src.auth.models import UserRole
from src.auth.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    RoleUpdateRequest,
    TokenResponse,
    UserAdminResponse,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from src.auth.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
)
from src.auth.service import AuthService
from src.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Register a new user account."""
    service = AuthService(db)
    user = await service.create_user(user_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Login with email and password to get access tokens."""
    service = AuthService(db)
    user = await service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value},
    )
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login/json", response_model=TokenResponse)
async def login_json(
    login_data: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Login with JSON body (alternative to form login)."""
    service = AuthService(db)
    user = await service.authenticate_user(login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value},
    )
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Get new access token using refresh token."""
    user_id = verify_token(token_data.refresh_token, token_type="refresh")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    service = AuthService(db)
    user = await service.get_user_by_id(UUID(user_id))

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.id,
        extra_claims={"role": user.role.value},
    )
    new_refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUser) -> UserResponse:
    """Get current user's profile."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Update current user's profile."""
    service = AuthService(db)
    user = await service.update_user(current_user.id, user_data)
    return UserResponse.model_validate(user)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Change current user's password."""
    service = AuthService(db)
    await service.change_password(
        current_user.id,
        password_data.current_password,
        password_data.new_password,
    )
    return {"message": "Password changed successfully"}


# Admin endpoints for user management
@router.get("/users", response_model=list[UserAdminResponse])
async def list_users(
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    role: UserRole | None = None,
) -> list[UserAdminResponse]:
    """List all users (admin only)."""
    service = AuthService(db)
    users = await service.get_all_users(skip=skip, limit=limit, role=role)
    return [UserAdminResponse.model_validate(user) for user in users]


@router.get("/users/{user_id}", response_model=UserAdminResponse)
async def get_user(
    user_id: UUID,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserAdminResponse:
    """Get user by ID (admin only)."""
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserAdminResponse.model_validate(user)


@router.patch("/users/{user_id}/role", response_model=UserAdminResponse)
async def update_user_role(
    user_id: UUID,
    role_data: RoleUpdateRequest,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserAdminResponse:
    """Update user role (admin only)."""
    service = AuthService(db)
    user = await service.update_user_role(user_id, role_data.role)
    return UserAdminResponse.model_validate(user)


@router.post("/users/{user_id}/deactivate", response_model=UserAdminResponse)
async def deactivate_user(
    user_id: UUID,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserAdminResponse:
    """Deactivate a user account (admin only)."""
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    service = AuthService(db)
    user = await service.deactivate_user(user_id)
    return UserAdminResponse.model_validate(user)


@router.post("/users/{user_id}/activate", response_model=UserAdminResponse)
async def activate_user(
    user_id: UUID,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserAdminResponse:
    """Activate a user account (admin only)."""
    service = AuthService(db)
    user = await service.activate_user(user_id)
    return UserAdminResponse.model_validate(user)
