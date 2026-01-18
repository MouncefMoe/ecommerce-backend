"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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

    return app


# Create application instance
app = create_application()


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.is_development else "disabled",
    }


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
