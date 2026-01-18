"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.config import settings
from src.database import create_tables
from src.exceptions import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
)
from src.common.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware

# Import routers
from src.auth.router import router as auth_router
from src.products.router import router as products_router
from src.cart.router import router as cart_router
from src.orders.router import router as orders_router
from src.payments.router import router as payments_router
from src.reviews.router import router as reviews_router
from src.admin.router import router as admin_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")

    # Create tables in development (use migrations in production)
    if settings.is_development:
        logger.info("Creating database tables...")
        await create_tables()
        logger.info("Database tables created")

    yield

    # Shutdown
    logger.info("Shutting down application...")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="A production-ready E-commerce Backend API",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        openapi_url="/openapi.json" if settings.is_development else None,
        lifespan=lifespan,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # Exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    if not settings.debug:
        app.add_exception_handler(Exception, generic_exception_handler)

    # Include routers
    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(products_router, prefix=api_prefix)
    app.include_router(cart_router, prefix=api_prefix)
    app.include_router(orders_router, prefix=api_prefix)
    app.include_router(payments_router, prefix=api_prefix)
    app.include_router(reviews_router, prefix=api_prefix)
    app.include_router(admin_router, prefix=api_prefix)

    # Mount static files for demo
    try:
        from pathlib import Path
        demo_dir = Path(__file__).parent.parent / "demo"
        if demo_dir.exists():
            app.mount("/demo", StaticFiles(directory=str(demo_dir), html=True), name="demo")
    except Exception:
        pass

    return app


# Create application instance
app = create_application()


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - redirects to demo page."""
    return RedirectResponse(url="/demo/")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
    }


@app.get("/api/v1", tags=["Health"])
async def api_info():
    """API information endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "endpoints": {
            "auth": "/api/v1/auth",
            "products": "/api/v1/products",
            "categories": "/api/v1/categories",
            "tags": "/api/v1/tags",
            "cart": "/api/v1/cart",
            "orders": "/api/v1/orders",
            "payments": "/api/v1/payments",
            "reviews": "/api/v1/reviews",
            "admin": "/api/v1/admin",
        },
    }


@app.post("/seed-demo-data", tags=["Health"])
async def seed_demo_data_endpoint():
    """Seed database with demo data. Only works in production on first run."""
    from decimal import Decimal
    from src.auth.models import User, UserRole
    from src.auth.security import hash_password
    from src.products.models import Category, Product
    from src.database import async_session_maker

    try:
        async with async_session_maker() as session:
            # Check if data already exists
            from sqlalchemy import select
            result = await session.execute(select(User).limit(1))
            if result.scalar_one_or_none():
                return {"message": "Demo data already exists", "status": "skipped"}

            # Create demo users
            admin_user = User(
                email="admin@demo.com",
                hashed_password=hash_password("admin123"),
                full_name="Admin User",
                role=UserRole.ADMIN,
                is_active=True,
                is_verified=True,
            )
            seller_user = User(
                email="seller@demo.com",
                hashed_password=hash_password("seller123"),
                full_name="Demo Seller",
                role=UserRole.SELLER,
                is_active=True,
                is_verified=True,
            )
            customer_user = User(
                email="customer@demo.com",
                hashed_password=hash_password("customer123"),
                full_name="Demo Customer",
                role=UserRole.CUSTOMER,
                is_active=True,
                is_verified=True,
            )
            session.add_all([admin_user, seller_user, customer_user])
            await session.flush()

            # Create categories
            electronics = Category(name="Electronics", slug="electronics", description="Electronic devices and gadgets")
            clothing = Category(name="Clothing", slug="clothing", description="Fashion and apparel")
            books = Category(name="Books", slug="books", description="Books and literature")
            home = Category(name="Home & Garden", slug="home-garden", description="Home improvement and garden supplies")
            session.add_all([electronics, clothing, books, home])
            await session.flush()

            # Create products
            products = [
                Product(seller_id=seller_user.id, category_id=electronics.id, name="Wireless Bluetooth Headphones", slug="wireless-bluetooth-headphones", description="High-quality wireless headphones with noise cancellation and 30-hour battery life.", price=Decimal("79.99"), compare_at_price=Decimal("99.99"), stock=50, sku="ELEC-HEAD-001", is_active=True, is_featured=True),
                Product(seller_id=seller_user.id, category_id=electronics.id, name="Smart Watch Pro", slug="smart-watch-pro", description="Advanced fitness tracking, heart rate monitoring, and smartphone notifications.", price=Decimal("199.99"), compare_at_price=Decimal("249.99"), stock=30, sku="ELEC-WATCH-001", is_active=True, is_featured=True),
                Product(seller_id=seller_user.id, category_id=electronics.id, name="4K Webcam", slug="4k-webcam", description="Professional 4K webcam with autofocus and built-in microphone.", price=Decimal("89.99"), stock=25, sku="ELEC-CAM-001", is_active=True),
                Product(seller_id=seller_user.id, category_id=clothing.id, name="Classic Denim Jacket", slug="classic-denim-jacket", description="Timeless denim jacket, perfect for casual wear.", price=Decimal("59.99"), stock=40, sku="CLTH-JACK-001", is_active=True),
                Product(seller_id=seller_user.id, category_id=clothing.id, name="Cotton T-Shirt Pack (3-Pack)", slug="cotton-tshirt-pack", description="Comfortable 100% cotton t-shirts in assorted colors.", price=Decimal("29.99"), stock=100, sku="CLTH-TSHIRT-001", is_active=True, is_featured=True),
                Product(seller_id=seller_user.id, category_id=books.id, name="Python Programming Masterclass", slug="python-programming-masterclass", description="Comprehensive guide to mastering Python programming.", price=Decimal("39.99"), stock=75, sku="BOOK-PROG-001", is_active=True),
                Product(seller_id=seller_user.id, category_id=books.id, name="The Art of Clean Code", slug="art-of-clean-code", description="Learn to write maintainable and elegant code.", price=Decimal("34.99"), stock=60, sku="BOOK-CODE-001", is_active=True, is_featured=True),
                Product(seller_id=seller_user.id, category_id=home.id, name="Indoor Plant Set (5 Plants)", slug="indoor-plant-set", description="Beautiful indoor plants to brighten your home.", price=Decimal("49.99"), stock=20, sku="HOME-PLANT-001", is_active=True),
                Product(seller_id=seller_user.id, category_id=home.id, name="LED Desk Lamp", slug="led-desk-lamp", description="Modern LED desk lamp with adjustable brightness.", price=Decimal("24.99"), stock=45, sku="HOME-LAMP-001", is_active=True),
                Product(seller_id=seller_user.id, category_id=home.id, name="Bamboo Kitchen Utensil Set", slug="bamboo-kitchen-utensil-set", description="Eco-friendly bamboo utensils for your kitchen.", price=Decimal("19.99"), stock=55, sku="HOME-UTIL-001", is_active=True),
            ]
            session.add_all(products)
            await session.commit()

            return {
                "message": "Demo data seeded successfully",
                "status": "success",
                "users": 3,
                "categories": 4,
                "products": 10
            }
    except Exception as e:
        return {"message": f"Error seeding data: {str(e)}", "status": "error"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
