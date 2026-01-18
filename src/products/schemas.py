"""Pydantic schemas for products."""

import json
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryBase(BaseModel):
    """Base schema for category data."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    image_url: str | None = Field(None, max_length=500)


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""

    slug: str | None = Field(None, max_length=100)
    parent_id: int | None = None


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: str | None = Field(None, min_length=1, max_length=100)
    slug: str | None = Field(None, max_length=100)
    description: str | None = None
    parent_id: int | None = None
    is_active: bool | None = None
    image_url: str | None = Field(None, max_length=500)


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    parent_id: int | None
    is_active: bool
    created_at: datetime


class CategoryWithChildrenResponse(CategoryResponse):
    """Schema for category with children."""

    children: list["CategoryResponse"] = []


class TagBase(BaseModel):
    """Base schema for tag data."""

    name: str = Field(..., min_length=1, max_length=50)


class TagCreate(TagBase):
    """Schema for creating a new tag."""

    slug: str | None = Field(None, max_length=50)


class TagResponse(TagBase):
    """Schema for tag response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str


class ProductBase(BaseModel):
    """Base schema for product data."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str
    price: Decimal = Field(..., ge=0, decimal_places=2)
    compare_at_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    cost_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    stock: int = Field(0, ge=0)
    sku: str = Field(..., min_length=1, max_length=100)
    barcode: str | None = Field(None, max_length=100)
    image_url: str | None = Field(None, max_length=500)
    weight: float | None = Field(None, ge=0)
    dimensions: str | None = Field(None, max_length=100)


class ProductCreate(ProductBase):
    """Schema for creating a new product."""

    slug: str | None = Field(None, max_length=255)
    category_id: int | None = None
    is_active: bool = True
    is_featured: bool = False
    image_urls: list[str] | None = None
    tag_ids: list[int] | None = None


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, max_length=255)
    description: str | None = None
    price: Decimal | None = Field(None, ge=0, decimal_places=2)
    compare_at_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    cost_price: Decimal | None = Field(None, ge=0, decimal_places=2)
    stock: int | None = Field(None, ge=0)
    sku: str | None = Field(None, min_length=1, max_length=100)
    barcode: str | None = Field(None, max_length=100)
    category_id: int | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    image_url: str | None = Field(None, max_length=500)
    image_urls: list[str] | None = None
    tag_ids: list[int] | None = None
    weight: float | None = Field(None, ge=0)
    dimensions: str | None = Field(None, max_length=100)


class SellerInfo(BaseModel):
    """Schema for seller info in product response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str


class ProductResponse(BaseModel):
    """Schema for product response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    seller_id: UUID
    category_id: int | None
    name: str
    slug: str
    description: str
    price: Decimal
    compare_at_price: Decimal | None
    stock: int
    sku: str
    barcode: str | None
    is_active: bool
    is_featured: bool
    image_url: str | None
    average_rating: float
    review_count: int
    weight: float | None
    dimensions: str | None
    created_at: datetime
    updated_at: datetime
    is_in_stock: bool
    discount_percentage: float | None

    # Nested responses
    category: CategoryResponse | None = None
    tags: list[TagResponse] = []

    @field_validator("is_in_stock", mode="before")
    @classmethod
    def compute_is_in_stock(cls, v, info):
        if v is not None:
            return v
        stock = info.data.get("stock", 0)
        return stock > 0


class ProductListResponse(BaseModel):
    """Schema for paginated product list response."""

    items: list[ProductResponse]
    total: int
    page: int
    size: int
    pages: int


class ProductSearchParams(BaseModel):
    """Schema for product search parameters."""

    q: str | None = Field(None, description="Search query")
    category_id: int | None = None
    min_price: Decimal | None = Field(None, ge=0)
    max_price: Decimal | None = Field(None, ge=0)
    in_stock: bool | None = None
    is_featured: bool | None = None
    seller_id: UUID | None = None
    tag_ids: list[int] | None = None
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
