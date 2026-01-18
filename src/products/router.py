"""Product API routes."""

from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AdminUser, CurrentUser, SellerUser
from src.auth.models import UserRole
from src.database import get_db
from src.products.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    CategoryWithChildrenResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
    TagCreate,
    TagResponse,
)
from src.products.service import CategoryService, ProductService, TagService

router = APIRouter(tags=["Products"])

# Category routes
category_router = APIRouter(prefix="/categories", tags=["Categories"])


@category_router.get("", response_model=list[CategoryWithChildrenResponse])
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    parent_id: int | None = None,
) -> list[CategoryWithChildrenResponse]:
    """List all categories."""
    service = CategoryService(db)
    categories = await service.get_all_categories(parent_id=parent_id)
    return [CategoryWithChildrenResponse.model_validate(c) for c in categories]


@category_router.get("/{category_id}", response_model=CategoryWithChildrenResponse)
async def get_category(
    category_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryWithChildrenResponse:
    """Get category by ID."""
    service = CategoryService(db)
    category = await service.get_category_by_id(category_id)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return CategoryWithChildrenResponse.model_validate(category)


@category_router.get("/slug/{slug}", response_model=CategoryWithChildrenResponse)
async def get_category_by_slug(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryWithChildrenResponse:
    """Get category by slug."""
    service = CategoryService(db)
    category = await service.get_category_by_slug(slug)

    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )

    return CategoryWithChildrenResponse.model_validate(category)


@category_router.post(
    "", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    category_data: CategoryCreate,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    """Create a new category (admin only)."""
    service = CategoryService(db)
    category = await service.create_category(category_data)
    return CategoryResponse.model_validate(category)


@category_router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryResponse:
    """Update a category (admin only)."""
    service = CategoryService(db)
    category = await service.update_category(category_id, category_data)
    return CategoryResponse.model_validate(category)


@category_router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a category (admin only)."""
    service = CategoryService(db)
    await service.delete_category(category_id)


# Tag routes
tag_router = APIRouter(prefix="/tags", tags=["Tags"])


@tag_router.get("", response_model=list[TagResponse])
async def list_tags(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[TagResponse]:
    """List all tags."""
    service = TagService(db)
    tags = await service.get_all_tags()
    return [TagResponse.model_validate(t) for t in tags]


@tag_router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TagResponse:
    """Create a new tag (admin only)."""
    service = TagService(db)
    tag = await service.create_tag(tag_data)
    return TagResponse.model_validate(tag)


# Product routes
product_router = APIRouter(prefix="/products", tags=["Products"])


@product_router.get("", response_model=ProductListResponse)
async def list_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    category_id: int | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    in_stock: bool | None = None,
    is_featured: bool | None = None,
    search: str | None = Query(None, alias="q"),
    sort_by: str = Query("created_at", pattern="^(name|price|created_at|average_rating)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
) -> ProductListResponse:
    """List products with filters and pagination."""
    service = ProductService(db)
    skip = (page - 1) * size

    products, total = await service.get_products(
        skip=skip,
        limit=size,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        in_stock=in_stock,
        is_featured=is_featured,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    pages = (total + size - 1) // size

    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


@product_router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductResponse:
    """Get product by ID."""
    service = ProductService(db)
    product = await service.get_product_by_id(product_id)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductResponse.model_validate(product)


@product_router.get("/slug/{slug}", response_model=ProductResponse)
async def get_product_by_slug(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductResponse:
    """Get product by slug."""
    service = ProductService(db)
    product = await service.get_product_by_slug(slug)

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    return ProductResponse.model_validate(product)


@product_router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: SellerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductResponse:
    """Create a new product (seller/admin only)."""
    service = ProductService(db)
    product = await service.create_product(product_data, current_user.id)
    return ProductResponse.model_validate(product)


@product_router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductResponse:
    """Update a product (owner/admin only)."""
    service = ProductService(db)
    is_admin = current_user.role == UserRole.ADMIN
    product = await service.update_product(
        product_id, product_data, current_user.id, is_admin
    )
    return ProductResponse.model_validate(product)


@product_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a product (owner/admin only)."""
    service = ProductService(db)
    is_admin = current_user.role == UserRole.ADMIN
    await service.delete_product(product_id, current_user.id, is_admin)


@product_router.get("/seller/my-products", response_model=ProductListResponse)
async def list_my_products(
    current_user: SellerUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
) -> ProductListResponse:
    """List current seller's products."""
    service = ProductService(db)
    skip = (page - 1) * size

    products, total = await service.get_products(
        skip=skip,
        limit=size,
        seller_id=current_user.id,
        is_active=is_active if is_active is not None else None,
    )

    pages = (total + size - 1) // size

    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


# Include all routers
router.include_router(category_router)
router.include_router(tag_router)
router.include_router(product_router)
