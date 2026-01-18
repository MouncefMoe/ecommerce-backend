"""Pytest configuration and fixtures."""

import asyncio
from decimal import Decimal
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.auth.models import User, UserRole
from src.auth.security import hash_password, create_access_token
from src.database import Base, get_db
from src.main import app
from src.products.models import Category, Product

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test customer user."""
    user = User(
        id=uuid4(),
        email="testuser@example.com",
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        role=UserRole.CUSTOMER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_seller(db_session: AsyncSession) -> User:
    """Create a test seller user."""
    user = User(
        id=uuid4(),
        email="seller@example.com",
        hashed_password=hash_password("sellerpassword123"),
        full_name="Test Seller",
        role=UserRole.SELLER,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create a test admin user."""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("adminpassword123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_category(db_session: AsyncSession) -> Category:
    """Create a test category."""
    category = Category(
        name="Test Category",
        slug="test-category",
        description="A test category",
        is_active=True,
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest_asyncio.fixture
async def test_product(
    db_session: AsyncSession, test_seller: User, test_category: Category
) -> Product:
    """Create a test product."""
    product = Product(
        id=uuid4(),
        seller_id=test_seller.id,
        category_id=test_category.id,
        name="Test Product",
        slug="test-product",
        description="A test product description",
        price=Decimal("99.99"),
        stock=100,
        sku="TEST-SKU-001",
        is_active=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest.fixture
def user_token(test_user: User) -> str:
    """Generate JWT token for test user."""
    return create_access_token(
        subject=test_user.id,
        extra_claims={"role": test_user.role.value},
    )


@pytest.fixture
def seller_token(test_seller: User) -> str:
    """Generate JWT token for test seller."""
    return create_access_token(
        subject=test_seller.id,
        extra_claims={"role": test_seller.role.value},
    )


@pytest.fixture
def admin_token(test_admin: User) -> str:
    """Generate JWT token for test admin."""
    return create_access_token(
        subject=test_admin.id,
        extra_claims={"role": test_admin.role.value},
    )


def auth_header(token: str) -> dict:
    """Create authorization header."""
    return {"Authorization": f"Bearer {token}"}
