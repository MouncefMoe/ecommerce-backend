"""Product and Category models."""

import uuid
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base, TimestampMixin


class Category(Base, TimestampMixin):
    """Product category model with self-referential relationship for subcategories."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Self-referential relationship for subcategories
    parent: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="children",
        remote_side=[id],
    )
    children: Mapped[list["Category"]] = relationship(
        "Category",
        back_populates="parent",
    )
    products: Mapped[list["Product"]] = relationship(
        "Product",
        back_populates="category",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class Tag(Base, TimestampMixin):
    """Tag model for product tagging."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)

    products: Mapped[list["Product"]] = relationship(
        "Product",
        secondary="product_tags",
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"


class ProductTag(Base):
    """Association table for Product-Tag many-to-many relationship."""

    __tablename__ = "product_tags"

    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id: Mapped[int] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Product(Base, TimestampMixin):
    """Product model."""

    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    seller_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    compare_at_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    cost_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    sku: Mapped[str] = mapped_column(String(100), unique=True)
    barcode: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_urls: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    weight: Mapped[float | None] = mapped_column(Float, nullable=True)
    dimensions: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Relationships
    seller: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="products",
    )
    category: Mapped["Category | None"] = relationship(
        "Category",
        back_populates="products",
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag",
        secondary="product_tags",
        back_populates="products",
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review",
        back_populates="product",
        lazy="selectin",
    )
    cart_items: Mapped[list["CartItem"]] = relationship(  # noqa: F821
        "CartItem",
        back_populates="product",
    )
    order_items: Mapped[list["OrderItem"]] = relationship(  # noqa: F821
        "OrderItem",
        back_populates="product",
    )

    __table_args__ = (
        Index("idx_product_price", "price"),
        Index("idx_product_active", "is_active"),
        Index("idx_product_featured", "is_featured"),
        CheckConstraint("price >= 0", name="ck_product_price_positive"),
        CheckConstraint("stock >= 0", name="ck_product_stock_positive"),
    )

    def __repr__(self) -> str:
        return f"<Product {self.name}>"

    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        return self.stock > 0

    @property
    def discount_percentage(self) -> float | None:
        """Calculate discount percentage if compare_at_price is set."""
        if self.compare_at_price and self.compare_at_price > self.price:
            discount = (
                (self.compare_at_price - self.price) / self.compare_at_price
            ) * 100
            return round(float(discount), 1)
        return None
