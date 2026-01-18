"""Authentication service with business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.auth.schemas import UserCreate, UserUpdate
from src.auth.security import hash_password, verify_password
from src.exceptions import BadRequestError, ConflictError, NotFoundError


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Check if email already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ConflictError("Email already registered")

        # Create user
        user = User(
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            phone=user_data.phone,
            role=UserRole.CUSTOMER,
        )

        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user with email and password."""
        user = await self.get_user_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user

    async def update_user(self, user_id: UUID, user_data: UserUpdate) -> User:
        """Update user profile."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def change_password(
        self, user_id: UUID, current_password: str, new_password: str
    ) -> User:
        """Change user password."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        if not verify_password(current_password, user.hashed_password):
            raise BadRequestError("Current password is incorrect")

        user.hashed_password = hash_password(new_password)
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def update_user_role(self, user_id: UUID, role: UserRole) -> User:
        """Update user role (admin only)."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        user.role = role
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def deactivate_user(self, user_id: UUID) -> User:
        """Deactivate a user account."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        user.is_active = False
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def activate_user(self, user_id: UUID) -> User:
        """Activate a user account."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))

        user.is_active = True
        await self.db.flush()
        await self.db.refresh(user)

        return user

    async def get_all_users(
        self, skip: int = 0, limit: int = 100, role: UserRole | None = None
    ) -> list[User]:
        """Get all users with pagination and optional role filter."""
        query = select(User)

        if role:
            query = query.where(User.role == role)

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def count_users(self, role: UserRole | None = None) -> int:
        """Count total users with optional role filter."""
        from sqlalchemy import func

        query = select(func.count(User.id))

        if role:
            query = query.where(User.role == role)

        result = await self.db.execute(query)
        return result.scalar() or 0
