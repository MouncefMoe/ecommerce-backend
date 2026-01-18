"""Payment models."""

import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base, TimestampMixin


class PaymentStatus(str, enum.Enum):
    """Payment status enumeration."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, enum.Enum):
    """Payment method enumeration."""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CASH_ON_DELIVERY = "cash_on_delivery"


class Payment(Base, TimestampMixin):
    """Payment model."""

    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    status: Mapped[PaymentStatus] = mapped_column(default=PaymentStatus.PENDING)
    method: Mapped[PaymentMethod] = mapped_column()
    transaction_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    gateway_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    refunded_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00")
    )
    paid_at: Mapped[datetime | None] = mapped_column(nullable=True)
    refunded_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Relationships
    order: Mapped["Order"] = relationship(  # noqa: F821
        "Order",
        back_populates="payment",
    )

    __table_args__ = (Index("idx_payment_status", "status"),)

    def __repr__(self) -> str:
        return f"<Payment {self.id}>"

    @property
    def is_successful(self) -> bool:
        """Check if payment was successful."""
        return self.status == PaymentStatus.COMPLETED

    @property
    def can_refund(self) -> bool:
        """Check if payment can be refunded."""
        return self.status == PaymentStatus.COMPLETED and self.refunded_amount < self.amount
