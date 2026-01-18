"""Pydantic schemas for reviews."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewerInfo(BaseModel):
    """Schema for reviewer information."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str


class ReviewBase(BaseModel):
    """Base schema for review data."""

    rating: int = Field(..., ge=1, le=5)
    title: str | None = Field(None, max_length=255)
    comment: str = Field(..., min_length=10)


class ReviewCreate(ReviewBase):
    """Schema for creating a review."""

    product_id: UUID


class ReviewUpdate(BaseModel):
    """Schema for updating a review."""

    rating: int | None = Field(None, ge=1, le=5)
    title: str | None = Field(None, max_length=255)
    comment: str | None = Field(None, min_length=10)


class ReviewResponse(ReviewBase):
    """Schema for review response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    product_id: UUID
    is_verified_purchase: bool
    is_approved: bool
    helpful_count: int
    created_at: datetime
    updated_at: datetime

    # Optional nested reviewer info
    user: ReviewerInfo | None = None


class ReviewListResponse(BaseModel):
    """Schema for paginated review list response."""

    items: list[ReviewResponse]
    total: int
    page: int
    size: int
    pages: int
    average_rating: float


class ReviewStats(BaseModel):
    """Schema for review statistics."""

    total_reviews: int
    average_rating: float
    rating_distribution: dict[int, int]  # {1: count, 2: count, ...}
