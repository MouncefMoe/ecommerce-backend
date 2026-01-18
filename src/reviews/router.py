"""Review API routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.dependencies import AdminUser, CurrentUser
from src.auth.models import UserRole
from src.database import get_db
from src.reviews.schemas import (
    ReviewCreate,
    ReviewListResponse,
    ReviewResponse,
    ReviewStats,
    ReviewUpdate,
)
from src.reviews.service import ReviewService

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewResponse:
    """Create a new product review."""
    service = ReviewService(db)
    review = await service.create_review(current_user.id, review_data)
    return ReviewResponse.model_validate(review)


@router.get("/product/{product_id}", response_model=ReviewListResponse)
async def list_product_reviews(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> ReviewListResponse:
    """List reviews for a product."""
    service = ReviewService(db)
    skip = (page - 1) * size

    reviews, total, avg_rating = await service.get_product_reviews(
        product_id=product_id,
        skip=skip,
        limit=size,
    )

    pages = (total + size - 1) // size

    return ReviewListResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        page=page,
        size=size,
        pages=pages,
        average_rating=avg_rating,
    )


@router.get("/product/{product_id}/stats", response_model=ReviewStats)
async def get_product_review_stats(
    product_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewStats:
    """Get review statistics for a product."""
    service = ReviewService(db)
    stats = await service.get_review_stats(product_id)
    return ReviewStats(**stats)


@router.get("/my-reviews", response_model=ReviewListResponse)
async def list_my_reviews(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> ReviewListResponse:
    """List current user's reviews."""
    service = ReviewService(db)
    skip = (page - 1) * size

    reviews, total = await service.get_user_reviews(
        user_id=current_user.id,
        skip=skip,
        limit=size,
    )

    pages = (total + size - 1) // size

    return ReviewListResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        page=page,
        size=size,
        pages=pages,
        average_rating=0.0,  # Not applicable for user reviews
    )


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewResponse:
    """Get review by ID."""
    service = ReviewService(db)
    review = await service.get_review_by_id(review_id)

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )

    return ReviewResponse.model_validate(review)


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    review_data: ReviewUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewResponse:
    """Update a review (owner only)."""
    service = ReviewService(db)
    review = await service.update_review(review_id, current_user.id, review_data)
    return ReviewResponse.model_validate(review)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a review (owner or admin)."""
    service = ReviewService(db)
    is_admin = current_user.role == UserRole.ADMIN
    await service.delete_review(review_id, current_user.id, is_admin)


# Admin endpoints
@router.get("/admin/pending", response_model=ReviewListResponse)
async def list_pending_reviews(
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
) -> ReviewListResponse:
    """List pending reviews (admin only)."""
    service = ReviewService(db)
    skip = (page - 1) * size

    reviews, total = await service.get_pending_reviews(skip=skip, limit=size)
    pages = (total + size - 1) // size

    return ReviewListResponse(
        items=[ReviewResponse.model_validate(r) for r in reviews],
        total=total,
        page=page,
        size=size,
        pages=pages,
        average_rating=0.0,
    )


@router.post("/{review_id}/approve", response_model=ReviewResponse)
async def approve_review(
    review_id: UUID,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewResponse:
    """Approve a review (admin only)."""
    service = ReviewService(db)
    review = await service.approve_review(review_id)
    return ReviewResponse.model_validate(review)


@router.post("/{review_id}/reject", response_model=ReviewResponse)
async def reject_review(
    review_id: UUID,
    admin_user: AdminUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReviewResponse:
    """Reject/unapprove a review (admin only)."""
    service = ReviewService(db)
    review = await service.reject_review(review_id)
    return ReviewResponse.model_validate(review)
