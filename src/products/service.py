"""Product service with business logic."""

import json
import re
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.exceptions import ConflictError, ForbiddenError, NotFoundError
from src.products.models import Category, Product, Tag
from src.products.schemas import (
    CategoryCreate,
    CategoryUpdate,
    ProductCreate,
    ProductUpdate,
    TagCreate,
)


def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a name."""
    slug = name.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[-\s]+", "-", slug)
    return slug.strip("-")


class CategoryService:
    """Service for category operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_category_by_id(self, category_id: int) -> Category | None:
        """Get category by ID."""
        result = await self.db.execute(
            select(Category).where(Category.id == category_id)
        )
        return result.scalar_one_or_none()

    async def get_category_by_slug(self, slug: str) -> Category | None:
        """Get category by slug."""
        result = await self.db.execute(
            select(Category).where(Category.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_all_categories(
        self,
        parent_id: int | None = None,
        include_inactive: bool = False,
    ) -> list[Category]:
        """Get all categories with optional parent filter."""
        query = select(Category).options(selectinload(Category.children))

        if parent_id is not None:
            query = query.where(Category.parent_id == parent_id)
        else:
            query = query.where(Category.parent_id.is_(None))

        if not include_inactive:
            query = query.where(Category.is_active == True)

        query = query.order_by(Category.name)
        result = await self.db.execute(query)

        return list(result.scalars().all())

    async def create_category(self, category_data: CategoryCreate) -> Category:
        """Create a new category."""
        # Generate slug if not provided
        slug = category_data.slug or generate_slug(category_data.name)

        # Check for duplicate slug
        existing = await self.get_category_by_slug(slug)
        if existing:
            raise ConflictError(f"Category with slug '{slug}' already exists")

        # Verify parent exists if provided
        if category_data.parent_id:
            parent = await self.get_category_by_id(category_data.parent_id)
            if not parent:
                raise NotFoundError("Parent category", str(category_data.parent_id))

        category = Category(
            name=category_data.name,
            slug=slug,
            description=category_data.description,
            parent_id=category_data.parent_id,
            image_url=category_data.image_url,
        )

        self.db.add(category)
        await self.db.flush()
        await self.db.refresh(category)

        return category

    async def update_category(
        self, category_id: int, category_data: CategoryUpdate
    ) -> Category:
        """Update a category."""
        category = await self.get_category_by_id(category_id)
        if not category:
            raise NotFoundError("Category", str(category_id))

        update_data = category_data.model_dump(exclude_unset=True)

        # Check slug uniqueness if being updated
        if "slug" in update_data and update_data["slug"] != category.slug:
            existing = await self.get_category_by_slug(update_data["slug"])
            if existing:
                raise ConflictError(
                    f"Category with slug '{update_data['slug']}' already exists"
                )

        # Verify parent exists if being updated
        if "parent_id" in update_data and update_data["parent_id"]:
            if update_data["parent_id"] == category_id:
                raise ConflictError("Category cannot be its own parent")
            parent = await self.get_category_by_id(update_data["parent_id"])
            if not parent:
                raise NotFoundError("Parent category", str(update_data["parent_id"]))

        for field, value in update_data.items():
            setattr(category, field, value)

        await self.db.flush()
        await self.db.refresh(category)

        return category

    async def delete_category(self, category_id: int) -> None:
        """Delete a category."""
        category = await self.get_category_by_id(category_id)
        if not category:
            raise NotFoundError("Category", str(category_id))

        await self.db.delete(category)
        await self.db.flush()


class TagService:
    """Service for tag operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_tag_by_id(self, tag_id: int) -> Tag | None:
        """Get tag by ID."""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    async def get_tag_by_slug(self, slug: str) -> Tag | None:
        """Get tag by slug."""
        result = await self.db.execute(select(Tag).where(Tag.slug == slug))
        return result.scalar_one_or_none()

    async def get_all_tags(self) -> list[Tag]:
        """Get all tags."""
        result = await self.db.execute(select(Tag).order_by(Tag.name))
        return list(result.scalars().all())

    async def create_tag(self, tag_data: TagCreate) -> Tag:
        """Create a new tag."""
        slug = tag_data.slug or generate_slug(tag_data.name)

        existing = await self.get_tag_by_slug(slug)
        if existing:
            raise ConflictError(f"Tag with slug '{slug}' already exists")

        tag = Tag(name=tag_data.name, slug=slug)

        self.db.add(tag)
        await self.db.flush()
        await self.db.refresh(tag)

        return tag

    async def get_or_create_tag(self, name: str) -> Tag:
        """Get existing tag or create a new one."""
        slug = generate_slug(name)
        existing = await self.get_tag_by_slug(slug)
        if existing:
            return existing

        tag = Tag(name=name, slug=slug)
        self.db.add(tag)
        await self.db.flush()
        await self.db.refresh(tag)

        return tag


class ProductService:
    """Service for product operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_product_by_id(self, product_id: UUID) -> Product | None:
        """Get product by ID."""
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category), selectinload(Product.tags))
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_product_by_slug(self, slug: str) -> Product | None:
        """Get product by slug."""
        result = await self.db.execute(
            select(Product)
            .options(selectinload(Product.category), selectinload(Product.tags))
            .where(Product.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_product_by_sku(self, sku: str) -> Product | None:
        """Get product by SKU."""
        result = await self.db.execute(select(Product).where(Product.sku == sku))
        return result.scalar_one_or_none()

    async def get_products(
        self,
        skip: int = 0,
        limit: int = 20,
        category_id: int | None = None,
        seller_id: UUID | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        in_stock: bool | None = None,
        is_featured: bool | None = None,
        is_active: bool = True,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Product], int]:
        """Get products with filters and pagination."""
        query = select(Product).options(
            selectinload(Product.category), selectinload(Product.tags)
        )

        # Apply filters
        if is_active is not None:
            query = query.where(Product.is_active == is_active)

        if category_id:
            query = query.where(Product.category_id == category_id)

        if seller_id:
            query = query.where(Product.seller_id == seller_id)

        if min_price is not None:
            query = query.where(Product.price >= min_price)

        if max_price is not None:
            query = query.where(Product.price <= max_price)

        if in_stock is True:
            query = query.where(Product.stock > 0)
        elif in_stock is False:
            query = query.where(Product.stock == 0)

        if is_featured is not None:
            query = query.where(Product.is_featured == is_featured)

        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_pattern),
                    Product.description.ilike(search_pattern),
                    Product.sku.ilike(search_pattern),
                )
            )

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        products = list(result.scalars().all())

        return products, total

    async def create_product(
        self, product_data: ProductCreate, seller_id: UUID
    ) -> Product:
        """Create a new product."""
        # Generate slug if not provided
        slug = product_data.slug or generate_slug(product_data.name)

        # Check for duplicate slug
        existing_slug = await self.get_product_by_slug(slug)
        if existing_slug:
            # Append seller ID portion to make it unique
            slug = f"{slug}-{str(seller_id)[:8]}"

        # Check for duplicate SKU
        existing_sku = await self.get_product_by_sku(product_data.sku)
        if existing_sku:
            raise ConflictError(f"Product with SKU '{product_data.sku}' already exists")

        # Verify category exists if provided
        if product_data.category_id:
            category_service = CategoryService(self.db)
            category = await category_service.get_category_by_id(product_data.category_id)
            if not category:
                raise NotFoundError("Category", str(product_data.category_id))

        # Convert image_urls list to JSON string
        image_urls_json = None
        if product_data.image_urls:
            image_urls_json = json.dumps(product_data.image_urls)

        product = Product(
            seller_id=seller_id,
            category_id=product_data.category_id,
            name=product_data.name,
            slug=slug,
            description=product_data.description,
            price=product_data.price,
            compare_at_price=product_data.compare_at_price,
            cost_price=product_data.cost_price,
            stock=product_data.stock,
            sku=product_data.sku,
            barcode=product_data.barcode,
            is_active=product_data.is_active,
            is_featured=product_data.is_featured,
            image_url=product_data.image_url,
            image_urls=image_urls_json,
            weight=product_data.weight,
            dimensions=product_data.dimensions,
        )

        # Handle tags
        if product_data.tag_ids:
            tag_service = TagService(self.db)
            for tag_id in product_data.tag_ids:
                tag = await tag_service.get_tag_by_id(tag_id)
                if tag:
                    product.tags.append(tag)

        self.db.add(product)
        await self.db.flush()
        await self.db.refresh(product)

        return product

    async def update_product(
        self,
        product_id: UUID,
        product_data: ProductUpdate,
        user_id: UUID,
        is_admin: bool = False,
    ) -> Product:
        """Update a product."""
        product = await self.get_product_by_id(product_id)
        if not product:
            raise NotFoundError("Product", str(product_id))

        # Check ownership
        if not is_admin and product.seller_id != user_id:
            raise ForbiddenError("Not authorized to update this product")

        update_data = product_data.model_dump(exclude_unset=True)

        # Check slug uniqueness if being updated
        if "slug" in update_data and update_data["slug"] != product.slug:
            existing = await self.get_product_by_slug(update_data["slug"])
            if existing:
                raise ConflictError(
                    f"Product with slug '{update_data['slug']}' already exists"
                )

        # Check SKU uniqueness if being updated
        if "sku" in update_data and update_data["sku"] != product.sku:
            existing = await self.get_product_by_sku(update_data["sku"])
            if existing:
                raise ConflictError(
                    f"Product with SKU '{update_data['sku']}' already exists"
                )

        # Verify category exists if being updated
        if "category_id" in update_data and update_data["category_id"]:
            category_service = CategoryService(self.db)
            category = await category_service.get_category_by_id(
                update_data["category_id"]
            )
            if not category:
                raise NotFoundError("Category", str(update_data["category_id"]))

        # Handle image_urls conversion
        if "image_urls" in update_data:
            update_data["image_urls"] = json.dumps(update_data["image_urls"]) if update_data["image_urls"] else None

        # Handle tags update
        if "tag_ids" in update_data:
            tag_ids = update_data.pop("tag_ids")
            product.tags.clear()
            if tag_ids:
                tag_service = TagService(self.db)
                for tag_id in tag_ids:
                    tag = await tag_service.get_tag_by_id(tag_id)
                    if tag:
                        product.tags.append(tag)

        for field, value in update_data.items():
            setattr(product, field, value)

        await self.db.flush()
        await self.db.refresh(product)

        return product

    async def delete_product(
        self, product_id: UUID, user_id: UUID, is_admin: bool = False
    ) -> None:
        """Delete a product."""
        product = await self.get_product_by_id(product_id)
        if not product:
            raise NotFoundError("Product", str(product_id))

        # Check ownership
        if not is_admin and product.seller_id != user_id:
            raise ForbiddenError("Not authorized to delete this product")

        await self.db.delete(product)
        await self.db.flush()

    async def update_product_stock(self, product_id: UUID, quantity: int) -> Product:
        """Update product stock (increase or decrease)."""
        product = await self.get_product_by_id(product_id)
        if not product:
            raise NotFoundError("Product", str(product_id))

        new_stock = product.stock + quantity
        if new_stock < 0:
            raise ConflictError("Insufficient stock")

        product.stock = new_stock
        await self.db.flush()
        await self.db.refresh(product)

        return product

    async def update_product_rating(self, product_id: UUID) -> Product:
        """Recalculate and update product rating based on reviews."""
        from src.reviews.models import Review

        product = await self.get_product_by_id(product_id)
        if not product:
            raise NotFoundError("Product", str(product_id))

        # Calculate average rating
        result = await self.db.execute(
            select(
                func.avg(Review.rating).label("avg_rating"),
                func.count(Review.id).label("count"),
            ).where(Review.product_id == product_id, Review.is_approved == True)
        )
        row = result.one()

        product.average_rating = float(row.avg_rating) if row.avg_rating else 0.0
        product.review_count = row.count or 0

        await self.db.flush()
        await self.db.refresh(product)

        return product
