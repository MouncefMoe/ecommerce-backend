"""User model and role enumeration."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base, TimestampMixin


class UserRole(str, enum.Enum):
    """User role enumeration."""

    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"


class User(Base, TimestampMixin):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(default=UserRole.CUSTOMER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships - will be defined when related models are created
    products: Mapped[list["Product"]] = relationship(  # noqa: F821
        "Product", back_populates="seller", lazy="selectin"
    )
    orders: Mapped[list["Order"]] = relationship(  # noqa: F821
        "Order", back_populates="user", lazy="selectin"
    )
    reviews: Mapped[list["Review"]] = relationship(  # noqa: F821
        "Review", back_populates="user", lazy="selectin"
    )
    cart: Mapped["Cart | None"] = relationship(  # noqa: F821
        "Cart", back_populates="user", uselist=False, lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
