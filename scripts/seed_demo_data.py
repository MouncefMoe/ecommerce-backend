"""Seed database with demo data for testing."""

import asyncio
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.models import User, UserRole
from src.auth.security import hash_password
from src.cart.models import Cart, CartItem
from src.database import async_session_maker, create_tables
from src.products.models import Category, Product


async def seed_demo_data():
    """Seed database with demo data."""
    print("🌱 Starting database seeding...")

    # Create tables
    await create_tables()
    print("✅ Tables created")

    async with async_session_maker() as session:
        # Create demo users
        print("\n👥 Creating demo users...")

        admin_user = User(
            email="admin@demo.com",
            hashed_password=hash_password("admin123"),
            full_name="Admin User",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )

        seller_user = User(
            email="seller@demo.com",
            hashed_password=hash_password("seller123"),
            full_name="Demo Seller",
            role=UserRole.SELLER,
            is_active=True,
            is_verified=True,
        )

        customer_user = User(
            email="customer@demo.com",
            hashed_password=hash_password("customer123"),
            full_name="Demo Customer",
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,
        )

        session.add_all([admin_user, seller_user, customer_user])
        await session.flush()

        print(f"   ✓ Admin: admin@demo.com / admin123")
        print(f"   ✓ Seller: seller@demo.com / seller123")
        print(f"   ✓ Customer: customer@demo.com / customer123")

        # Create categories
        print("\n📁 Creating categories...")

        electronics = Category(
            name="Electronics",
            slug="electronics",
            description="Electronic devices and gadgets",
        )

        clothing = Category(
            name="Clothing",
            slug="clothing",
            description="Fashion and apparel",
        )

        books = Category(
            name="Books",
            slug="books",
            description="Books and literature",
        )

        home = Category(
            name="Home & Garden",
            slug="home-garden",
            description="Home improvement and garden supplies",
        )

        session.add_all([electronics, clothing, books, home])
        await session.flush()

        print(f"   ✓ Created {4} categories")

        # Create products
        print("\n📦 Creating products...")

        products = [
            # Electronics
            Product(
                seller_id=seller_user.id,
                category_id=electronics.id,
                name="Wireless Bluetooth Headphones",
                slug="wireless-bluetooth-headphones",
                description="High-quality wireless headphones with noise cancellation and 30-hour battery life.",
                price=Decimal("79.99"),
                compare_at_price=Decimal("99.99"),
                stock=50,
                sku="ELEC-HEAD-001",
                is_active=True,
                is_featured=True,
            ),
            Product(
                seller_id=seller_user.id,
                category_id=electronics.id,
                name="Smart Watch Pro",
                slug="smart-watch-pro",
                description="Advanced fitness tracking, heart rate monitoring, and smartphone notifications.",
                price=Decimal("199.99"),
                compare_at_price=Decimal("249.99"),
                stock=30,
                sku="ELEC-WATCH-001",
                is_active=True,
                is_featured=True,
            ),
            Product(
                seller_id=seller_user.id,
                category_id=electronics.id,
                name="4K Webcam",
                slug="4k-webcam",
                description="Professional 4K webcam with autofocus and built-in microphone.",
                price=Decimal("89.99"),
                stock=25,
                sku="ELEC-CAM-001",
                is_active=True,
            ),

            # Clothing
            Product(
                seller_id=seller_user.id,
                category_id=clothing.id,
                name="Classic Denim Jacket",
                slug="classic-denim-jacket",
                description="Timeless denim jacket, perfect for casual wear.",
                price=Decimal("59.99"),
                stock=40,
                sku="CLTH-JACK-001",
                is_active=True,
            ),
            Product(
                seller_id=seller_user.id,
                category_id=clothing.id,
                name="Cotton T-Shirt Pack (3-Pack)",
                slug="cotton-tshirt-pack",
                description="Comfortable 100% cotton t-shirts in assorted colors.",
                price=Decimal("29.99"),
                stock=100,
                sku="CLTH-TSHIRT-001",
                is_active=True,
                is_featured=True,
            ),

            # Books
            Product(
                seller_id=seller_user.id,
                category_id=books.id,
                name="Python Programming Masterclass",
                slug="python-programming-masterclass",
                description="Comprehensive guide to mastering Python programming.",
                price=Decimal("39.99"),
                stock=75,
                sku="BOOK-PROG-001",
                is_active=True,
            ),
            Product(
                seller_id=seller_user.id,
                category_id=books.id,
                name="The Art of Clean Code",
                slug="art-of-clean-code",
                description="Learn to write maintainable and elegant code.",
                price=Decimal("34.99"),
                stock=60,
                sku="BOOK-CODE-001",
                is_active=True,
                is_featured=True,
            ),

            # Home & Garden
            Product(
                seller_id=seller_user.id,
                category_id=home.id,
                name="Indoor Plant Set (5 Plants)",
                slug="indoor-plant-set",
                description="Beautiful indoor plants to brighten your home.",
                price=Decimal("49.99"),
                stock=20,
                sku="HOME-PLANT-001",
                is_active=True,
            ),
            Product(
                seller_id=seller_user.id,
                category_id=home.id,
                name="LED Desk Lamp",
                slug="led-desk-lamp",
                description="Modern LED desk lamp with adjustable brightness.",
                price=Decimal("24.99"),
                stock=45,
                sku="HOME-LAMP-001",
                is_active=True,
            ),
            Product(
                seller_id=seller_user.id,
                category_id=home.id,
                name="Bamboo Kitchen Utensil Set",
                slug="bamboo-kitchen-utensil-set",
                description="Eco-friendly bamboo utensils for your kitchen.",
                price=Decimal("19.99"),
                stock=55,
                sku="HOME-UTIL-001",
                is_active=True,
            ),
        ]

        session.add_all(products)
        await session.flush()

        print(f"   ✓ Created {len(products)} products")

        # Commit all changes
        await session.commit()

        print("\n✅ Database seeding completed successfully!")
        print("\n📝 Demo Credentials:")
        print("   Admin:    admin@demo.com / admin123")
        print("   Seller:   seller@demo.com / seller123")
        print("   Customer: customer@demo.com / customer123")


if __name__ == "__main__":
    asyncio.run(seed_demo_data())
