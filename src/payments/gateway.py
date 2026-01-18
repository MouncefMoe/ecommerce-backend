"""Mock payment gateway for simulating payment processing."""

import secrets
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum

from src.payments.models import PaymentMethod


class GatewayResponseCode(str, Enum):
    """Gateway response codes."""

    SUCCESS = "success"
    DECLINED = "declined"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    INVALID_CARD = "invalid_card"
    EXPIRED_CARD = "expired_card"
    PROCESSING_ERROR = "processing_error"


@dataclass
class GatewayResponse:
    """Response from payment gateway."""

    success: bool
    transaction_id: str | None
    code: GatewayResponseCode
    message: str
    raw_response: dict


class MockPaymentGateway:
    """
    Mock payment gateway that simulates payment processing.

    Test card numbers:
    - 4242424242424242: Always succeeds
    - 4000000000000002: Always declines
    - 4000000000009995: Insufficient funds
    - 4000000000000069: Expired card
    - Any other: Random success (80% chance)
    """

    # Test card mappings
    TEST_CARDS = {
        "4242424242424242": GatewayResponseCode.SUCCESS,
        "4000000000000002": GatewayResponseCode.DECLINED,
        "4000000000009995": GatewayResponseCode.INSUFFICIENT_FUNDS,
        "4000000000000069": GatewayResponseCode.EXPIRED_CARD,
    }

    RESPONSE_MESSAGES = {
        GatewayResponseCode.SUCCESS: "Payment processed successfully",
        GatewayResponseCode.DECLINED: "Card declined by issuer",
        GatewayResponseCode.INSUFFICIENT_FUNDS: "Insufficient funds",
        GatewayResponseCode.INVALID_CARD: "Invalid card number",
        GatewayResponseCode.EXPIRED_CARD: "Card has expired",
        GatewayResponseCode.PROCESSING_ERROR: "Payment processing error",
    }

    def __init__(self):
        pass

    def generate_transaction_id(self) -> str:
        """Generate a mock transaction ID."""
        return f"TXN_{secrets.token_hex(12).upper()}"

    def process_payment(
        self,
        amount: Decimal,
        method: PaymentMethod,
        card_number: str | None = None,
        **kwargs,
    ) -> GatewayResponse:
        """
        Process a payment (mock implementation).

        Args:
            amount: Payment amount
            method: Payment method
            card_number: Card number for card payments
            **kwargs: Additional payment details

        Returns:
            GatewayResponse with transaction result
        """
        # For non-card methods, simulate success
        if method in [PaymentMethod.PAYPAL, PaymentMethod.BANK_TRANSFER]:
            return self._create_success_response()

        # For cash on delivery, always succeed (payment collected later)
        if method == PaymentMethod.CASH_ON_DELIVERY:
            return GatewayResponse(
                success=True,
                transaction_id=self.generate_transaction_id(),
                code=GatewayResponseCode.SUCCESS,
                message="Cash on delivery order confirmed",
                raw_response={"method": "cod", "status": "pending_collection"},
            )

        # For card payments, check test cards
        if card_number:
            # Remove spaces and dashes
            clean_card = card_number.replace(" ", "").replace("-", "")

            # Check if it's a test card
            if clean_card in self.TEST_CARDS:
                code = self.TEST_CARDS[clean_card]
                if code == GatewayResponseCode.SUCCESS:
                    return self._create_success_response()
                else:
                    return self._create_failure_response(code)

            # Validate card number (basic Luhn check simulation)
            if not self._validate_card_number(clean_card):
                return self._create_failure_response(GatewayResponseCode.INVALID_CARD)

        # Random success for other cards (80% success rate)
        if secrets.randbelow(100) < 80:
            return self._create_success_response()
        else:
            return self._create_failure_response(GatewayResponseCode.DECLINED)

    def process_refund(
        self,
        transaction_id: str,
        amount: Decimal,
        reason: str | None = None,
    ) -> GatewayResponse:
        """
        Process a refund (mock implementation).

        Args:
            transaction_id: Original transaction ID
            amount: Refund amount
            reason: Refund reason

        Returns:
            GatewayResponse with refund result
        """
        # Simulate 95% refund success rate
        if secrets.randbelow(100) < 95:
            return GatewayResponse(
                success=True,
                transaction_id=f"REF_{secrets.token_hex(12).upper()}",
                code=GatewayResponseCode.SUCCESS,
                message="Refund processed successfully",
                raw_response={
                    "original_transaction": transaction_id,
                    "refund_amount": str(amount),
                    "reason": reason,
                    "status": "completed",
                },
            )
        else:
            return GatewayResponse(
                success=False,
                transaction_id=None,
                code=GatewayResponseCode.PROCESSING_ERROR,
                message="Refund processing failed. Please try again.",
                raw_response={
                    "original_transaction": transaction_id,
                    "error": "gateway_timeout",
                },
            )

    def _create_success_response(self) -> GatewayResponse:
        """Create a successful gateway response."""
        return GatewayResponse(
            success=True,
            transaction_id=self.generate_transaction_id(),
            code=GatewayResponseCode.SUCCESS,
            message=self.RESPONSE_MESSAGES[GatewayResponseCode.SUCCESS],
            raw_response={
                "status": "approved",
                "auth_code": secrets.token_hex(3).upper(),
            },
        )

    def _create_failure_response(self, code: GatewayResponseCode) -> GatewayResponse:
        """Create a failed gateway response."""
        return GatewayResponse(
            success=False,
            transaction_id=None,
            code=code,
            message=self.RESPONSE_MESSAGES[code],
            raw_response={
                "status": "declined",
                "error_code": code.value,
            },
        )

    def _validate_card_number(self, card_number: str) -> bool:
        """
        Basic card number validation (length and numeric check).
        In production, use proper Luhn algorithm validation.
        """
        if not card_number.isdigit():
            return False
        if len(card_number) < 13 or len(card_number) > 19:
            return False
        return True


# Singleton instance
payment_gateway = MockPaymentGateway()
