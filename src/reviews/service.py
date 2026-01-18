"""Review service with business logic."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.exceptions import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from src.orders.models import Order, OrderStatus
from src.products.service import ProductService
from src.reviews.models import Review
from src.reviews.schemas import ReviewCreate, ReviewUpdate


class ReviewService:
    """Service for review operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_review_by_id(self, review_id: UUID) -> Review | None:
        """Get review by ID."""
        result = await self.db.execute(
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.id == review_id)
        )
        return result.scalar_one_or_none()

    async def get_user_product_review(
        self, user_id: UUID, product_id: UUID
    ) -> Review | None:
        """Get user's review for a specific product."""
        result = await self.db.execute(
            select(Review).where(
                Review.user_id == user_id, Review.product_id == product_id
            )
        )
        return result.scalar_one_or_none()

    async def get_product_reviews(
        self,
        product_id: UUID,
        skip: int = 0,
        limit: int = 20,
        only_approved: bool = True,
    ) -> tuple[list[Review], int, float]:
        """Get reviews for a product with pagination."""
        query = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.product_id == product_id)
        )

        if only_approved:
            query = query.where(Review.is_approved == True)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Calculate average rating
        avg_query = select(func.avg(Review.rating)).where(
            Review.product_id == product_id
        )
        if only_approved:
            avg_query = avg_query.where(Review.is_approved == True)
        avg_result = await self.db.execute(avg_query)
        average_rating = avg_result.scalar() or 0.0

        # Apply pagination and ordering
        query = query.order_by(Review.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        return reviews, total, float(average_rating)

    async def get_user_reviews(
        self, user_id: UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Review], int]:
        """Get reviews by a user with pagination."""
        query = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.user_id == user_id)
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Review.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        return reviews, total

    async def check_verified_purchase(
        self, user_id: UUID, product_id: UUID
    ) -> bool:
        """Check if user has purchased the product."""
        from src.orders.models import OrderItem

        result = await self.db.execute(
            select(Order)
            .join(OrderItem)
            .where(
                Order.user_id == user_id,
                OrderItem.product_id == product_id,
                Order.status.in_([OrderStatus.DELIVERED, OrderStatus.SHIPPED]),
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_review(self, user_id: UUID, review_data: ReviewCreate) -> Review:
        """Create a new review."""
        # Check if product exists
        product_service = ProductService(self.db)
        product = await product_service.get_product_by_id(review_data.product_id)

        if not product:
            raise NotFoundError("Product", str(review_data.product_id))

        # Check if user already reviewed this product
        existing_review = await self.get_user_product_review(
            user_id, review_data.product_id
        )
        if existing_review:
            raise ConflictError("You have already reviewed this product")

        # Check if verified purchase
        is_verified = await self.check_verified_purchase(
            user_id, review_data.product_id
        )

        review = Review(
            user_id=user_id,
            product_id=review_data.product_id,
            rating=review_data.rating,
            title=review_data.title,
            comment=review_data.comment,
            is_verified_purchase=is_verified,
        )

        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)

        # Update product rating
        await product_service.update_product_rating(review_data.product_id)

        return review

    async def update_review(
        self, review_id: UUID, user_id: UUID, review_data: ReviewUpdate
    ) -> Review:
        """Update a review."""
        review = await self.get_review_by_id(review_id)

        if not review:
            raise NotFoundError("Review", str(review_id))

        # Check ownership
        if review.user_id != user_id:
            raise ForbiddenError("Not authorized to update this review")

        update_data = review_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)

        await self.db.flush()
        await self.db.refresh(review)

        # Update product rating
        product_service = ProductService(self.db)
        await product_service.update_product_rating(review.product_id)

        return review

    async def delete_review(
        self, review_id: UUID, user_id: UUID, is_admin: bool = False
    ) -> None:
        """Delete a review."""
        review = await self.get_review_by_id(review_id)

        if not review:
            raise NotFoundError("Review", str(review_id))

        # Check ownership (or admin)
        if not is_admin and review.user_id != user_id:
            raise ForbiddenError("Not authorized to delete this review")

        product_id = review.product_id
        await self.db.delete(review)
        await self.db.flush()

        # Update product rating
        product_service = ProductService(self.db)
        await product_service.update_product_rating(product_id)

    async def approve_review(self, review_id: UUID) -> Review:
        """Approve a review (admin)."""
        review = await self.get_review_by_id(review_id)

        if not review:
            raise NotFoundError("Review", str(review_id))

        review.is_approved = True
        await self.db.flush()
        await self.db.refresh(review)

        # Update product rating
        product_service = ProductService(self.db)
        await product_service.update_product_rating(review.product_id)

        return review

    async def reject_review(self, review_id: UUID) -> Review:
        """Reject/unapprove a review (admin)."""
        review = await self.get_review_by_id(review_id)

        if not review:
            raise NotFoundError("Review", str(review_id))

        review.is_approved = False
        await self.db.flush()
        await self.db.refresh(review)

        # Update product rating
        product_service = ProductService(self.db)
        await product_service.update_product_rating(review.product_id)

        return review

    async def get_pending_reviews(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[Review], int]:
        """Get pending reviews (admin)."""
        query = (
            select(Review)
            .options(selectinload(Review.user))
            .where(Review.is_approved == False)
        )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(Review.created_at.desc()).offset(skip).limit(limit)

        result = await self.db.execute(query)
        reviews = list(result.scalars().all())

        return reviews, total

    async def get_review_stats(self, product_id: UUID) -> dict:
        """Get review statistics for a product."""
        # Get rating distribution
        result = await self.db.execute(
            select(Review.rating, func.count(Review.id))
            .where(Review.product_id == product_id, Review.is_approved == True)
            .group_by(Review.rating)
        )

        distribution = {i: 0 for i in range(1, 6)}
        total = 0
        rating_sum = 0

        for row in result:
            distribution[row[0]] = row[1]
            total += row[1]
            rating_sum += row[0] * row[1]

        average = rating_sum / total if total > 0 else 0.0

        return {
            "total_reviews": total,
            "average_rating": round(average, 2),
            "rating_distribution": distribution,
        }
