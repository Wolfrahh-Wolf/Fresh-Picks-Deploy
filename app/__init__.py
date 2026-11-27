"""
__init__.py - Fresh Picks: Application Factory
"""
import os
import mimetypes
mimetypes.add_type("image/svg+xml", ".svg")

from flask import Flask, send_from_directory

from .config import Config
from .extensions import db, mail, rzp_client, limiter, csrf
from .logging_setup import setup_logging


def create_app(config_class=None):
    """Application factory for Fresh Picks."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Register MIME types for static files
    app.config.update(
        SEND_FILE_MAX_AGE_DEFAULT=3600,
    )

    # Configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config.from_object(Config)

    # Development bypass: allow SESSION_COOKIE_SECURE=False when explicitly in dev mode
    if os.environ.get("FLASK_DEBUG") in ("1", "true"):
        app.config["SESSION_COOKIE_SECURE"] = False

    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    rzp_client.init(app.config.get("RAZORPAY_KEY_ID"), app.config.get("RAZORPAY_KEY_SECRET"))

    # Redis cache (mandatory)
    from .cache import cache, init_cache as init_cache_func
    init_cache_func(app)

    # Rate limiting (memory backend, no Redis required)
    limiter.init_app(app)

    # CSRF protection for all POST/PATCH/PUT/DELETE requests
    csrf.init_app(app)

    # Mail config
    mail_configured = os.environ.get("MAILER_PROVIDER", "smtp") == "resend" and os.environ.get("RESEND_API_KEY")
    if mail_configured:
        app.logger.info("MAILER: Using Resend API for email delivery")
    else:
        app.config["MAIL_DEFAULT_SENDER"] = (
            app.config.get("SENDER_NAME", "FreshPicks"),
            app.config.get("SMTP_EMAIL")
        )
        app.logger.info("MAILER: Using SMTP (%s:%s) for email delivery",
                        app.config.get("SMTP_HOST", "smtp.gmail.com"),
                        app.config.get("SMTP_PORT", 465))

    # Validate config
    from .config import validate_config
    validate_config(app)

    # Setup logging
    setup_logging(app)

    # Register blueprints/routes
    from . import main_routes
    app.register_blueprint(main_routes.bp)

    # Razorpay webhook handler (must be after app creation for secret)
    from .webhook_routes import init_webhook as init_webhook_bp
    init_webhook_bp(app)

    # ── Favicon Routes ────────────────────────────────────────────────
    @app.route("/favicon.ico")
    def favicon_ico():
        return app.send_static_file("favicon.ico")

    @app.route("/favicon.svg")
    def favicon_svg():
        return send_from_directory(
            app.static_folder,
            "favicon.svg",
            mimetype="image/svg+xml"
        )

    # ── Database Table Initialization ───────────────────────────────
    with app.app_context():
        from .models import OTPVerification
        db.create_all()

    # ── Cache Warming ───────────────────────────────────────────────
    def _build_analytics_data():
        """Build analytics data dict for cache warming."""
        from .models import Order, User, DeliveryBoy, Product
        from .constants import PRICE_DIVISOR_G, LOW_STOCK_THRESHOLD_G
        orders        = db.session.query(Order).all()
        products      = db.session.query(Product).all()
        users         = db.session.query(User).all()
        delivery_boys = db.session.query(DeliveryBoy).all()

        total_revenue = sum(o.total_amount for o in orders)
        total_orders  = len(orders)

        return {
            "status": "SUCCESS",
            "stats": {
                "total_revenue":          round(total_revenue, 2),
                "total_orders":           total_orders,
                "avg_order_value":        round(total_revenue / total_orders, 2) if total_orders else 0.0,
                "orders_placed":          sum(1 for o in orders if o.status == "Order Placed"),
                "orders_out":             sum(1 for o in orders if o.status == "Out for Delivery"),
                "orders_delivered":       sum(1 for o in orders if o.status == "Delivered"),
                "orders_cancelled":       sum(1 for o in orders if o.status == "Cancelled"),
                "slot_morning":           sum(1 for o in orders if o.delivery_slot == "Morning"),
                "slot_afternoon":         sum(1 for o in orders if o.delivery_slot == "Afternoon"),
                "slot_evening":           sum(1 for o in orders if o.delivery_slot == "Evening"),
                "total_stock_kg":         round(sum(p.stock_g for p in products) / PRICE_DIVISOR_G, 2),
                "low_stock_items":        sum(1 for p in products if p.stock_g < LOW_STOCK_THRESHOLD_G),
                "total_users":            len(users),
                "active_delivery_boys":   sum(1 for b in delivery_boys if b.is_active),
                "inactive_delivery_boys": sum(1 for b in delivery_boys if not b.is_active),
            }
        }

    def _warm_cache():
        """Pre-populate the cache with frequently-read data on startup."""
        try:
            from sqlalchemy.orm import joinedload
            from .models import Order, Product, FreeItem
            with app.app_context():
                products = [p.to_dict() for p in db.session.query(Product).all()]
                cache.set("/api/products", products, timeout=60)

                inventory = {
                    "vegetables": [p.to_dict() for p in db.session.query(Product).all()],
                    "free_items": [f.to_dict() for f in db.session.query(FreeItem).all()],
                }
                cache.set("/api/admin/inventory", inventory, timeout=60)

                active_orders = db.session.query(Order).options(
                    joinedload(Order.items)
                ).filter(
                    Order.status.in_(["Order Placed", "Out for Delivery"])
                ).all()
                cache.set("/api/admin/orders/active", active_orders, timeout=30)

                analytics_data = _build_analytics_data()
                cache.set("/api/admin/analytics", analytics_data, timeout=120)
        except Exception as e:
            app.logger.error("CACHE: Cache warming failed: %s", e)

    _warm_cache()
    app.logger.info("CACHE: Cache warming complete")

    # ── Error Handlers ──────────────────────────────────────────────────
    @app.errorhandler(400)
    def bad_request(e):
        return {"status": "ERROR", "message": "Bad request"}, 400

    @app.errorhandler(404)
    def not_found(e):
        return {"status": "ERROR", "message": "Resource not found"}, 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return {"status": "ERROR", "message": "Method not allowed"}, 405

    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return {"status": "ERROR", "message": "Rate limit exceeded. Please try again later."}, 429

    @app.errorhandler(500)
    def internal_error(e):
        app.logger.error("Unhandled server error: %s", e)
        return {"status": "ERROR", "message": "Internal server error"}, 500

    return app


app = create_app()
