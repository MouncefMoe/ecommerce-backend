# E-commerce Backend API

A production-ready E-commerce Backend API built with **FastAPI** and **Python 3.11+**. This project demonstrates professional backend development practices including async patterns, JWT authentication, role-based access control, comprehensive testing, and Docker deployment.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

### Authentication & Authorization
- JWT-based authentication with access and refresh tokens
- Role-based access control (Customer, Seller, Admin)
- Secure password hashing with bcrypt
- User profile management

### Product Catalog
- Full CRUD operations for products
- Category management with nested subcategories
- Product tagging system
- Advanced filtering (price range, category, search)
- Pagination and sorting

### Shopping Cart
- Persistent cart storage
- Add/update/remove items
- Stock validation
- Automatic cart creation

### Order Management
- Create orders from cart
- Order status tracking (pending → confirmed → processing → shipped → delivered)
- Order cancellation with stock restoration
- Order history

### Payment Processing
- Mock payment gateway for development
- Multiple payment methods (Credit Card, PayPal, Bank Transfer, COD)
- Test card numbers for different scenarios
- Refund handling
- Invoice generation

### Reviews & Ratings
- Product reviews with 1-5 star ratings
- Verified purchase badges
- Review moderation (admin)
- Automatic average rating calculation

### Admin Dashboard
- Dashboard statistics (users, orders, revenue)
- Order management
- User management
- Sales analytics
- Low stock alerts

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL (production) / SQLite (development)
- **ORM:** SQLAlchemy 2.0 (async)
- **Authentication:** JWT (python-jose)
- **Password Hashing:** bcrypt (passlib)
- **Validation:** Pydantic v2
- **Migrations:** Alembic
- **Rate Limiting:** SlowAPI
- **Testing:** pytest + pytest-asyncio
- **Containerization:** Docker + Docker Compose

## Project Structure

```
ecommerce-backend/
├── src/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database setup
│   ├── exceptions.py           # Custom exceptions
│   ├── auth/                   # Authentication domain
│   ├── products/               # Products domain
│   ├── cart/                   # Cart domain
│   ├── orders/                 # Orders domain
│   ├── payments/               # Payments domain
│   ├── reviews/                # Reviews domain
│   ├── admin/                  # Admin dashboard
│   └── common/                 # Shared utilities
├── tests/                      # Test suite
├── alembic/                    # Database migrations
├── docker/                     # Docker configuration
├── requirements.txt            # Production dependencies
├── requirements-dev.txt        # Development dependencies
└── pyproject.toml              # Project metadata
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (optional, SQLite works for development)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MouncefMoe/ecommerce-backend.git
   cd ecommerce-backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Run the application:**
   ```bash
   uvicorn src.main:app --reload
   ```

6. **Access the API:**
   - API: http://localhost:8000
   - Swagger Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Using Docker

```bash
cd docker
docker-compose up --build
```

The API will be available at http://localhost:8000

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login with email/password |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/auth/me` | Get current user |
| PATCH | `/api/v1/auth/me` | Update profile |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products` | List products (filterable) |
| GET | `/api/v1/products/{id}` | Get product details |
| POST | `/api/v1/products` | Create product (Seller) |
| PATCH | `/api/v1/products/{id}` | Update product (Owner) |
| DELETE | `/api/v1/products/{id}` | Delete product (Owner) |

### Categories
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/categories` | List categories |
| POST | `/api/v1/categories` | Create category (Admin) |
| PATCH | `/api/v1/categories/{id}` | Update category (Admin) |

### Cart
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/cart` | Get cart |
| POST | `/api/v1/cart/items` | Add item to cart |
| PATCH | `/api/v1/cart/items/{id}` | Update item quantity |
| DELETE | `/api/v1/cart/items/{id}` | Remove item |
| DELETE | `/api/v1/cart` | Clear cart |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/orders` | List user's orders |
| GET | `/api/v1/orders/{id}` | Get order details |
| POST | `/api/v1/orders` | Create order from cart |
| POST | `/api/v1/orders/{id}/cancel` | Cancel order |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/payments/methods` | List payment methods |
| POST | `/api/v1/payments/process` | Process payment |
| GET | `/api/v1/payments/order/{id}/invoice` | Get invoice |

### Reviews
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/reviews/product/{id}` | List product reviews |
| POST | `/api/v1/reviews` | Create review |
| PATCH | `/api/v1/reviews/{id}` | Update review (Owner) |
| DELETE | `/api/v1/reviews/{id}` | Delete review |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/dashboard` | Dashboard stats |
| GET | `/api/v1/admin/analytics/sales` | Sales analytics |
| GET | `/api/v1/admin/products/low-stock` | Low stock alerts |

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_auth/test_router.py

# Run tests in parallel
pytest -n auto
```

### Test Payment Cards

| Card Number | Result |
|-------------|--------|
| 4242424242424242 | Success |
| 4000000000000002 | Declined |
| 4000000000009995 | Insufficient funds |
| 4000000000000069 | Expired card |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./ecommerce.db` |
| `SECRET_KEY` | JWT secret key | (required) |
| `ENVIRONMENT` | development/staging/production | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `ALLOWED_ORIGINS` | CORS allowed origins | `http://localhost:3000` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT access token expiry | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | JWT refresh token expiry | `7` |

## Database Migrations

```bash
# Generate new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

## Security Features

- JWT authentication with short-lived access tokens
- Password hashing with bcrypt
- Role-based access control (RBAC)
- Rate limiting on sensitive endpoints
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention (SQLAlchemy ORM)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Deployment

### Option 1: Render (Recommended - Free)

1. Fork this repository
2. Go to [Render](https://render.com/) and sign up
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Render will auto-detect `render.yaml` and deploy!

### Option 2: Railway

1. Go to [Railway](https://railway.app/)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select this repository
4. Add PostgreSQL database
5. Set environment variables
6. Deploy!

### Option 3: Fly.io

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Login and launch
fly auth login
fly launch
fly deploy
```

### Demo Data

Seed the database with demo data:

```bash
python scripts/seed_demo_data.py
```

**Demo Credentials:**
- Admin: `admin@demo.com` / `admin123`
- Seller: `seller@demo.com` / `seller123`
- Customer: `customer@demo.com` / `customer123`

## Live Demo

Once deployed, access:
- **API Docs:** `https://your-app.com/docs`
- **Demo Page:** `https://your-app.com/demo/`
- **Health Check:** `https://your-app.com/health`

## Author

**MouncefMoe** - [GitHub](https://github.com/MouncefMoe)

---

Built with FastAPI and Python 🚀
