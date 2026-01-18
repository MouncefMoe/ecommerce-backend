"""Cart models."""

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base, TimestampMixin


class Cart(Base, TimestampMixin):
    """Shopping cart model."""

    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(  # noqa: F821
        "User",
        back_populates="cart",
    )
    items: Mapped[list["CartItem"]] = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Cart {self.id}>"

    @property
    def total(self) -> Decimal:
        """Calculate total cart value."""
        return sum((item.subtotal for item in self.items), Decimal("0.00"))

    @property
    def item_count(self) -> int:
        """Get total number of items in cart."""
        return sum(item.quantity for item in self.items)


class CartItem(Base, TimestampMixin):
    """Cart item model."""

    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"),
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    cart: Mapped["Cart"] = relationship(
        "Cart",
        back_populates="items",
    )
    product: Mapped["Product"] = relationship(  # noqa: F821
        "Product",
        back_populates="cart_items",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_product"),
    )

    def __repr__(self) -> str:
        return f"<CartItem {self.id}>"

    @property
    def subtotal(self) -> Decimal:
        """Calculate item subtotal."""
        return self.product.price * self.quantity

    @property
    def unit_price(self) -> Decimal:
        """Get unit price from product."""
        return self.product.price
