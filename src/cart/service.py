"""Cart service with business logic."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.cart.models import Cart, CartItem
from src.cart.schemas import CartItemCreate, CartItemUpdate
from src.exceptions import BadRequestError, NotFoundError
from src.products.service import ProductService


class CartService:
    """Service for cart operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cart_by_user_id(self, user_id: UUID) -> Cart | None:
        """Get cart by user ID."""
        result = await self.db.execute(
            select(Cart)
            .options(selectinload(Cart.items).selectinload(CartItem.product))
            .where(Cart.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_cart(self, user_id: UUID) -> Cart:
        """Get existing cart or create a new one for user."""
        cart = await self.get_cart_by_user_id(user_id)

        if not cart:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            await self.db.flush()
            await self.db.refresh(cart)

        return cart

    async def get_cart_item(self, cart_id: UUID, item_id: UUID) -> CartItem | None:
        """Get cart item by ID."""
        result = await self.db.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.id == item_id, CartItem.cart_id == cart_id)
        )
        return result.scalar_one_or_none()

    async def get_cart_item_by_product(
        self, cart_id: UUID, product_id: UUID
    ) -> CartItem | None:
        """Get cart item by product ID."""
        result = await self.db.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.cart_id == cart_id, CartItem.product_id == product_id)
        )
        return result.scalar_one_or_none()

    async def add_item(self, user_id: UUID, item_data: CartItemCreate) -> Cart:
        """Add item to cart."""
        # Get or create cart
        cart = await self.get_or_create_cart(user_id)

        # Verify product exists and is available
        product_service = ProductService(self.db)
        product = await product_service.get_product_by_id(item_data.product_id)

        if not product:
            raise NotFoundError("Product", str(item_data.product_id))

        if not product.is_active:
            raise BadRequestError("Product is not available")

        if product.stock < item_data.quantity:
            raise BadRequestError(
                f"Insufficient stock. Only {product.stock} available."
            )

        # Check if item already exists in cart
        existing_item = await self.get_cart_item_by_product(
            cart.id, item_data.product_id
        )

        if existing_item:
            # Update quantity
            new_quantity = existing_item.quantity + item_data.quantity
            if new_quantity > product.stock:
                raise BadRequestError(
                    f"Cannot add more. Only {product.stock} available in stock."
                )
            existing_item.quantity = new_quantity
        else:
            # Add new item
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
            )
            self.db.add(cart_item)

        await self.db.flush()

        # Refresh cart with items
        return await self.get_or_create_cart(user_id)

    async def update_item(
        self, user_id: UUID, item_id: UUID, item_data: CartItemUpdate
    ) -> Cart:
        """Update cart item quantity."""
        cart = await self.get_cart_by_user_id(user_id)

        if not cart:
            raise NotFoundError("Cart")

        cart_item = await self.get_cart_item(cart.id, item_id)

        if not cart_item:
            raise NotFoundError("Cart item", str(item_id))

        # Verify stock availability
        product_service = ProductService(self.db)
        product = await product_service.get_product_by_id(cart_item.product_id)

        if not product:
            raise NotFoundError("Product", str(cart_item.product_id))

        if item_data.quantity > product.stock:
            raise BadRequestError(
                f"Insufficient stock. Only {product.stock} available."
            )

        cart_item.quantity = item_data.quantity
        await self.db.flush()

        # Refresh cart
        return await self.get_or_create_cart(user_id)

    async def remove_item(self, user_id: UUID, item_id: UUID) -> Cart:
        """Remove item from cart."""
        cart = await self.get_cart_by_user_id(user_id)

        if not cart:
            raise NotFoundError("Cart")

        cart_item = await self.get_cart_item(cart.id, item_id)

        if not cart_item:
            raise NotFoundError("Cart item", str(item_id))

        await self.db.delete(cart_item)
        await self.db.flush()

        # Refresh cart
        return await self.get_or_create_cart(user_id)

    async def clear_cart(self, user_id: UUID) -> Cart:
        """Remove all items from cart."""
        cart = await self.get_cart_by_user_id(user_id)

        if not cart:
            raise NotFoundError("Cart")

        # Delete all cart items
        for item in cart.items:
            await self.db.delete(item)

        await self.db.flush()

        # Refresh cart
        return await self.get_or_create_cart(user_id)

    async def validate_cart_for_checkout(self, user_id: UUID) -> Cart:
        """Validate cart is ready for checkout."""
        cart = await self.get_cart_by_user_id(user_id)

        if not cart:
            raise NotFoundError("Cart")

        if not cart.items:
            raise BadRequestError("Cart is empty")

        # Validate each item
        product_service = ProductService(self.db)
        invalid_items = []

        for item in cart.items:
            product = await product_service.get_product_by_id(item.product_id)

            if not product:
                invalid_items.append(f"Product {item.product_id} no longer exists")
                continue

            if not product.is_active:
                invalid_items.append(f"Product '{product.name}' is no longer available")
                continue

            if item.quantity > product.stock:
                invalid_items.append(
                    f"Product '{product.name}' has only {product.stock} in stock"
                )

        if invalid_items:
            raise BadRequestError(
                "Cart validation failed: " + "; ".join(invalid_items)
            )

        return cart
