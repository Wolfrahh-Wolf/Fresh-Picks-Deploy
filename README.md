# Fresh Picks — Fresh Vegetable Delivery Platform

Flask-based web application for ordering fresh vegetables with Razorpay
payments, OTP email verification, and automated PDF receipts.

## Architecture

```
Fresh-Picks-Deploy/
├── app/                    # Flask application package
│   ├── __init__.py         # Application factory (create_app)
│   ├── config.py           # Config classes (Dev/Test/Prod)
│   ├── extensions.py       # Shared extension instances
│   ├── models.py           # SQLAlchemy ORM models + OTPVerification
│   ├── main_routes.py      # All routes & business logic
│   ├── constants.py        # Business rules & thresholds
│   ├── logging_setup.py    # JSON (prod) / colored (dev) logging
│   ├── generate_receipt.py # PDF receipt engine (fpdf2)
│   └── templates/emails/   # Jinja2 OTP email templates
├── migrations/             # Alembic migrations
├── static/                 # CSS, JS, fonts, icons
├── templates/              # HTML page templates
├── seed.py                 # Database seeder
├── flush_db.py             # Destructive DB reset (env-guarded)
├── gunicorn.conf.py        # Production WSGI config
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Container image
├── render.yaml             # Render.com deploy definition
├── requirements.txt        # Python dependencies
└── .env                    # Local environment variables
```

## Tech Stack

| Layer       | Technology                        |
|-------------|-----------------------------------|
| Framework   | Flask (application factory)       |
| Database    | PostgreSQL 16 (Neon)              |
| ORM         | SQLAlchemy                        |
| Migrations  | Alembic                           |
| Payments    | Razorpay                          |
| Email       | SendGrid + SMTP (Gmail OAuth)     |
| Auth        | werkzeug.pbkdf2:sha256 hashing    |
| Security    | Flask-Limiter, Flask-WTF (CSRF)   |
| Deployment  | Gunicorn → Render.com             |
| Container   | Docker + docker-compose           |

## Environment Variables

| Variable              | Required | Description                        |
|-----------------------|----------|------------------------------------|
| `APP_SECRET_KEY`      | Yes      | Flask secret key                   |
| `DATABASE_URL`        | Yes      | Neon transaction-mode (6543)       |
| `DIRECT_URL`          | Yes      | Neon session-mode (5432)           |
| `RAZORPAY_KEY_ID`     | Yes      | Razorpay API key ID                |
| `RAZORPAY_KEY_SECRET` | Yes      | Razorpay API key secret            |
| `SMTP_EMAIL`          | Yes      | Gmail address for sending OTPs     |
| `SMTP_APP_PASSWORD`   | Yes      | Gmail app password                 |
| `SENDGRID_API_KEY`    | Yes      | SendGrid API key for receipts      |
| `FLASK_DEBUG`         | No       | `true` for dev, `false` for prod   |
| `FLUSH_DB_ENABLED`    | No       | `1` to allow destructive reset     |
| `OTP_TTL_MINUTES`     | No       | OTP validity (default: 10)         |

## Quick Start

### Local Development

```bash
# 1. Clone and setup
git clone <repo-url>
cd Fresh-Picks-Deploy

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env from example
cp .env.example .env  # edit with your credentials

# 4. Initialize database
python seed.py

# 5. Run development server
flask run --debug
# or: python app.py
```

### Docker

```bash
docker-compose up --build
```

### Production (Render.com)

Deploy `render.yaml` to Render.com. Environment variables are configured
via the Render dashboard.

## API Endpoints

### Authentication
| Method | Endpoint                    | Description              |
|--------|-----------------------------|--------------------------|
| POST   | `/api/auth/login`           | User/Admin login         |
| POST   | `/api/auth/logout`          | Logout                   |
| POST   | `/api/auth/register`        | Start registration OTP   |
| POST   | `/api/auth/register/verify` | Verify registration OTP  |
| POST   | `/api/auth/register/resend-otp` | Resend registration OTP |

### User Profile
| Method | Endpoint                          | Description            |
|--------|-----------------------------------|------------------------|
| GET    | `/api/users/me`                   | Get profile            |
| PATCH  | `/api/users/me`                   | Update profile field   |
| POST   | `/api/users/me/password/send-otp` | Send password change OTP |
| PATCH  | `/api/users/me/password`          | Change password        |

### Orders
| Method | Endpoint                               | Description             |
|--------|----------------------------------------|-------------------------|
| GET    | `/api/orders`                          | User's orders           |
| POST   | `/api/orders/<id>/cancel/send-otp`     | Send cancel OTP         |
| POST   | `/api/orders/<id>/cancel/verify`       | Verify cancel OTP       |

### Checkout
| Method | Endpoint                           | Description              |
|--------|------------------------------------|--------------------------|
| POST   | `/api/checkout/razorpay-order`     | Create Razorpay order    |
| POST   | `/api/checkout/verify`             | Verify payment + checkout|

### Admin
| Method | Endpoint                              | Description              |
|--------|---------------------------------------|--------------------------|
| GET    | `/api/admin/inventory`               | All products + free items|
| GET    | `/api/admin/orders`                  | All orders               |
| GET    | `/api/admin/orders/stream`           | SSE live order stream    |
| PATCH  | `/api/admin/orders/<id>/status`      | Update order status      |
| POST   | `/api/admin/orders/promote-slot`     | Promote slot to delivery |
| DELETE | `/api/admin/orders/<id>`             | Admin cancel order       |

## Database Models

- **User** — Customer accounts with custom `U1001` IDs
- **Admin** — Admin accounts with custom `A1001` IDs
- **Product** — Vegetable inventory (48 items, 8 categories)
- **FreeItem** — Promo items triggered at ₹500+ orders
- **DeliveryBoy** — Delivery agents with round-robin assignment
- **Order** — Customer orders with 7 statuses
- **OrderItem** — Line items with price snapshots
- **CartItem** — Persistent user cart
- **OTPVerification** — Persistent OTP storage in SQLite/PostgreSQL

## Security Features

- **Password hashing**: werkzeug.pbkdf2:sha256 (1M iterations)
- **CSRF protection**: Flask-WTF CSRFProtect on all state-changing endpoints
- **Rate limiting**: 200/day, 50/hour per IP (Flask-Limiter, memory backend)
- **OTP flow**: Client-token scoped, 10min TTL, 3-minute resend cooldown
- **Payment verification**: Razorpay signature validation
- **Order cancellation**: OTP verification + ownership check
- **Password change**: Old password verification + OTP confirmation

## Business Rules

- **Minimum order**: ₹500
- **Freebie threshold**: ₹500 → 50g curry leaves + 50g coriander
- **Delivery slots**: Morning (6AM-10AM), Afternoon (11AM-3PM), Evening (5PM-8PM)
- **Stock deduction**: At checkout for purchased items + injected freebies
- **Delivery agent**: Round-robin assignment by last_assigned time

## Deployment

### Render.com

1. Push to GitHub/GitLab
2. Connect repository in Render dashboard
3. Deploy `render.yaml` (auto-provisioned from YAML)
4. Set environment variables in Render dashboard
5. Run `alembic upgrade head` in Render console for first migration

### Docker

```bash
docker build -t fresh-picks .
docker run -p 8000:8000 --env-file .env fresh-picks
```

## Maintenance

### Database Migration

```bash
# Create a new migration after model changes
export ALEMBIC_ENV=development
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Reset Database (DESTRUCTIVE)

```bash
# Only in development! Requires FLUSH_DB_ENABLED=1
export FLUSH_DB_ENABLED=1
python flush_db.py
python seed.py
```

### Health Check

```bash
curl http://localhost:8000/health
# → {"status": "OK"}
```

## Project Structure Notes

- All business constants centralized in `app/constants.py`
- All models in `app/models.py` with indexed columns
- No hardcoded secrets — loaded from environment
- Custom prefixed IDs preserved for backward compatibility
- Memory backend for rate limiting (no Redis required)
- Alembic for schema migrations (production)

## License

Private — Fresh Picks Project
