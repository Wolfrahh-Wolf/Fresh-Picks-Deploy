"""
app.py - Fresh Picks: Flask Application (PostgreSQL Edition)

Replaces all C binary subprocess IPC with direct SQLAlchemy queries.
Frontend templates are unchanged except for fetch() URLs, which now
follow REST conventions (see REST_ROUTE_MAPPING.md).
"""

import os
import re
import json
import secrets
import hashlib
import heapq
import tempfile
import socket
import threading
import sendgrid
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail as SGMail,
    Attachment,
    FileContent,
    FileName, 
    FileType, 
    Disposition
)
from datetime import datetime, timedelta
from queue import SimpleQueue
from generate_receipt import generate_receipt
from sqlalchemy.orm import joinedload
import razorpay
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    send_from_directory,
    send_file,
    Response
)

from flask_mail import Mail, Message

from config import Config, validate_config
from models import db, User, Admin, Product, FreeItem, DeliveryBoy, Order, OrderItem, CartItem


# ═════════════════════════════════════════════════════════════
# APP INITIALIZATION
# ═════════════════════════════════════════════════════════════
app = Flask(__name__)
app.config.from_object(Config)
validate_config(app)

db.init_app(app)

app.config["MAIL_SERVER"]   = Config.SMTP_HOST
app.config["MAIL_PORT"]     = Config.SMTP_PORT
app.config["MAIL_USE_TLS"]  = True
app.config["MAIL_USE_SSL"]  = False
app.config["MAIL_USERNAME"] = Config.SMTP_EMAIL
app.config["MAIL_PASSWORD"] = Config.SMTP_APP_PASSWORD
app.config["MAIL_DEFAULT_SENDER"] = (Config.SENDER_NAME, Config.SMTP_EMAIL)
# mail = Mail(app)

_rzp_client = razorpay.Client(auth=(Config.RAZORPAY_KEY_ID, Config.RAZORPAY_KEY_SECRET))

OTP_STORE = {}
OTP_TTL_MINUTES = Config.OTP_TTL_MINUTES

# One SimpleQueue per connected admin SSE stream — broadcast on new order.
_order_listeners: list = []


# ═════════════════════════════════════════════════════════════
# HELPERS — Password / Validation
# ═════════════════════════════════════════════════════════════
def _hash_password(plaintext: str) -> str:
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def _is_valid_email(value):
    return bool(value and "@" in value and " " not in value)


def _is_strong_password(value):
    return bool(
        value and
        len(value) >= 8 and
        re.search(r"[A-Z]", value) and
        re.search(r"[a-z]", value) and
        re.search(r"[0-9]", value) and
        re.search(r"[^A-Za-z0-9]", value)
    )


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ═════════════════════════════════════════════════════════════
# HELPERS — OTP Flow (unchanged from original — pure Python, no C dependency)
# ═════════════════════════════════════════════════════════════
def _purge_expired_otps():
    now_ts = datetime.now(datetime.UTC).timestamp() if hasattr(datetime, "UTC") \
        else datetime.utcnow().timestamp()
    expired_keys = [k for k, v in OTP_STORE.items() if v.get("expires_at", 0) < now_ts]
    for key in expired_keys:
        OTP_STORE.pop(key, None)


def _get_otp_client_token():
    client_token = session.get("otp_client_token")
    if not client_token:
        client_token = secrets.token_urlsafe(16)
        session["otp_client_token"] = client_token
    return client_token


def _otp_store_key(flow_key):
    return f"{_get_otp_client_token()}:{flow_key}"


def _generate_otp_code():
    return f"{secrets.randbelow(10000):04d}"


# ── Email Templates (translated 1:1 from mailer.c build_otp_email) ──────────
def _otp_email_html(purpose, otp_code, reference=""):
    display_ref = reference or "your order"

    if purpose == "register":
        return (
            "FreshPicks Registration OTP",
            f"Your verification OTP is: {otp_code}\n\nValid for {OTP_TTL_MINUTES} minutes.",
            f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
            <p>Dear Customer,</p>
            <p>Thank you for registering with <strong>FreshPicks</strong>.</p>
            <p>Your verification OTP is:</p>
            <div style="display:inline-block;padding:12px 18px;border-radius:8px;
            background:#f4f8fb;border:1px solid #d4e4f2;font-size:28px;
            letter-spacing:0.25em;font-weight:700;color:#007acc;">{otp_code}</div>
            <p>This OTP is valid for <strong>{OTP_TTL_MINUTES} minutes</strong>.</p>
            <p>Regards,<br><strong>FreshPicks</strong></p></body></html>"""
        )

    if purpose == "cancel_order":
        return (
            f"FreshPicks Cancellation OTP - {display_ref}",
            f"Cancellation OTP for {display_ref}: {otp_code}",
            f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
            <p>Dear Customer,</p>
            <p>We received a request to cancel <strong>{display_ref}</strong>.</p>
            <p>Your cancellation OTP is:</p>
            <div style="display:inline-block;padding:12px 18px;border-radius:8px;
            background:#fff5f5;border:1px solid #f0c2c2;font-size:28px;
            letter-spacing:0.25em;font-weight:700;color:#dc3545;">{otp_code}</div>
            <p>This OTP is valid for <strong>{OTP_TTL_MINUTES} minutes</strong>.</p>
            <p>Regards,<br><strong>FreshPicks</strong></p></body></html>"""
        )

    if purpose == "password_change":
        return (
            "FreshPicks Password Change OTP",
            f"Password change OTP: {otp_code}",
            f"""<html><body style="font-family:Arial,sans-serif;color:#333;">
            <p>Dear Customer,</p>
            <p>We received a request to change your <strong>FreshPicks</strong> account password.</p>
            <p>Your password-change OTP is:</p>
            <div style="display:inline-block;padding:12px 18px;border-radius:8px;
            background:#f7f2ff;border:1px solid #d7c4ff;font-size:28px;
            letter-spacing:0.25em;font-weight:700;color:#7b4dff;">{otp_code}</div>
            <p>This OTP is valid for <strong>{OTP_TTL_MINUTES} minutes</strong>.</p>
            <p>Regards,<br><strong>FreshPicks</strong></p></body></html>"""
        )

    return ("FreshPicks OTP", f"Your OTP: {otp_code}", f"<p>Your OTP: {otp_code}</p>")


def _send_otp_email(recipient_email, otp_code, purpose, reference=""):
    try:
        subject, text_body, html_body = _otp_email_html(purpose, otp_code, reference)
        message = SGMail(
            from_email = ("FreshPicks", Config.SMTP_EMAIL),
            to_emails    = recipient_email,
            subject      = subject,
            html_content = html_body
        )
        sg = SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        sg.client.mail.send.post(request_body=message.get())
        return {"status": "SUCCESS", "data": "Email sent"}
    except Exception as e:
        print(f"MAIL ERROR: {type(e).__name__}: {e}")
        return {"status": "ERROR", "data": str(e)}


def _start_otp_flow(flow_key, recipient_email, purpose, reference="", payload=None):
    _purge_expired_otps()
    otp_code = _generate_otp_code()
    OTP_STORE[_otp_store_key(flow_key)] = {
        "otp": otp_code,
        "recipient_email": recipient_email,
        "purpose": purpose,
        "reference": reference,
        "expires_at": (datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES)).timestamp()
    }
    if payload is not None:
        OTP_STORE[_otp_store_key(flow_key)]["payload"] = payload

    print(f"\n{'='*52}\nOTP\nPurpose  : {purpose}\nReference: {reference or '—'}\n"
          f"To       : {recipient_email}\nOTP Code : {otp_code}\n"
          f"Expires  : {OTP_TTL_MINUTES} minutes\n{'='*52}\n")

    return _send_otp_email(recipient_email, otp_code, purpose, reference)


def _restart_otp_flow(flow_key, otp_state):
    return _start_otp_flow(
        flow_key, otp_state["recipient_email"], otp_state["purpose"],
        otp_state.get("reference", ""), otp_state.get("payload")
    )


def _get_otp_flow(flow_key):
    _purge_expired_otps()
    return OTP_STORE.get(_otp_store_key(flow_key))


def _clear_otp_flow(flow_key):
    OTP_STORE.pop(_otp_store_key(flow_key), None)


def _validate_otp_flow(flow_key, entered_code, reference=""):
    otp_state = _get_otp_flow(flow_key)
    if not otp_state:
        return False, "OTP expired or not found. Please request a new OTP."
    if reference and otp_state.get("reference") != reference:
        return False, "OTP context mismatch. Please request a new OTP."
    if otp_state.get("otp") != entered_code:
        return False, "Incorrect OTP. Please try again."
    return True, ""


def _password_change_flow_key():
    return f"password_change:{session.get('role', 'user')}:{session.get('user_id', '')}"


def _cancel_order_flow_key(order_id):
    return f"cancel_order:{session.get('role', 'guest')}:{order_id}"


def _load_current_account_email():
    """Fetch the logged-in account's registered email."""
    cached_email = session.get("email", "").strip()
    if _is_valid_email(cached_email):
        return cached_email, None

    if "user_id" not in session:
        return None, (jsonify({"status": "ERROR", "message": "Not logged in"}), 401)

    if session.get("role") == "admin":
        admin = db.session.get(Admin, session["user_id"])
        if not admin:
            return None, (jsonify({"status": "ERROR", "message": "Admin not found"}), 500)
        email = admin.email
    else:
        user = db.session.get(User, session["user_id"])
        if not user:
            return None, (jsonify({"status": "ERROR", "message": "User not found"}), 500)
        email = user.email

    if not _is_valid_email(email):
        return None, (jsonify({"status": "ERROR",
                               "message": "No valid email is registered for this account"}), 400)

    session["email"] = email
    return email, None


# ═════════════════════════════════════════════════════════════
# HELPERS — ID Generation
# ═════════════════════════════════════════════════════════════
def _generate_next_id(prefix, model, id_column):
    """
    Mirrors the original C ID scheme: PREFIX + (ID_BASE + count).
    e.g. _generate_next_id("U", User, User.user_id) → "U1001", "U1002", ...
    """
    count = db.session.query(model).count()
    return f"{prefix}{1001 + count}"


# ═════════════════════════════════════════════════════════════
# RAZORPAY SECURITY HEADERS
# ═════════════════════════════════════════════════════════════
@app.after_request
def set_security_headers(response):
    response.headers["Permissions-Policy"] = "accelerometer=*, gyroscope=*, magnetometer=*"
    response.headers["Access-Control-Expose-Headers"] = "x-rtb-fingerprint-id, request-id"
    return response


# ═════════════════════════════════════════════════════════════
# PAGE ROUTES — Server-rendered HTML (REST-corrected paths)
# ═════════════════════════════════════════════════════════════
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/presentation")
def presentation():
    return render_template("presentation.html")


@app.route("/login/<role>")
def login_page(role):
    if role not in ("user", "admin"):
        role = "user"
    return render_template("login.html", role=role)


@app.route("/register")
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
def user_dashboard():
    return render_template("user_home.html", username=session.get("username"))


@app.route("/admin/dashboard")
def admin_dashboard():
    return render_template(
        "admin_dash.html",
        admin_name=session.get("admin_name", "Admin")
    )


@app.route("/profile")
def profile_page():
    return render_template("profile.html")


@app.route("/settings/security")
def security_page():
    return render_template("security.html")


@app.route("/shop")
def shop_page():
    return render_template("shop.html")


@app.route("/cart")
def cart_page():
    return render_template("cart.html")


@app.route("/orders")
def user_orders_page():
    return render_template("user_orders.html", username=session.get("username"))


@app.route("/admin/inventory")
def admin_inventory_page():
    return render_template("admin_inventory.html")


@app.route("/admin/users")
def admin_users_page():
    return render_template("admin_users.html")


@app.route("/admin/orders")
def admin_orders_page():
    return render_template("admin_orders.html")


@app.route("/admin/analytics")
def admin_analytics_page():
    return render_template("admin_analytics.html")


@app.route("/product_images/<filename>")
def product_images_alias(filename):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(
        os.path.join(root_dir, "static", "product_images"), filename
    )


@app.route("/static/product_images/<filename>")
def product_images(filename):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(os.path.join(root_dir, "static", "product_images"), filename)


# ═════════════════════════════════════════════════════════════
# API ROUTES — AUTH
# ═════════════════════════════════════════════════════════════
@app.route("/api/auth/login", methods=["POST"])
def api_login():
    """
    POST /api/auth/login
    Body: { "username", "password", "role": "user|admin" }
    """
    data     = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    role     = data.get("role",     "user").strip()

    if not username or not password:
        return jsonify({"status": "ERROR", "message": "Required fields missing"})

    if role not in ("user", "admin"):
        return jsonify({"status": "ERROR", "message": "Invalid role"})

    hashed = _hash_password(password)

    if role == "admin":
        account = db.session.query(Admin).filter_by(
            username=username, password=hashed
        ).first()
    else:
        account = db.session.query(User).filter_by(
            username=username, password=hashed
        ).first()

    if not account:
        return jsonify({"status": "ERROR", "message": "Invalid username or password"})

    session["role"]     = role
    session["username"] = username
    session.pop("email", None)
    session.pop("admin_name", None)

    if role == "admin":
        session["user_id"]    = account.admin_id
        session["admin_name"] = account.admin_name
        session["email"]      = account.email
    else:
        session["user_id"] = account.user_id

    redirect_url = "/admin/dashboard" if role == "admin" else "/dashboard"
    return jsonify({"status": "SUCCESS", "role": role, "redirect": redirect_url})


@app.route("/api/auth/logout", methods=["POST"])
def api_logout():
    """POST /api/auth/logout — state-mutating, so POST not GET."""
    session.clear()
    return jsonify({"status": "SUCCESS", "redirect": "/"})


@app.route("/api/auth/register", methods=["POST"])
def api_register():
    """
    POST /api/auth/register
    Body: { username, password, full_name, email, phone, door, street, area, pincode }
    Stages registration and emails an OTP. Commit happens on verify.
    """
    data = request.get_json() or {}

    username  = data.get("username",  "").strip()
    password  = data.get("password",  "")
    full_name = data.get("full_name", "").strip()
    email     = data.get("email",     "").strip()
    phone     = data.get("phone",     "").strip()
    door      = data.get("door",      "").strip()
    street    = data.get("street",    "").strip()
    area      = data.get("area",      "").strip()
    pincode   = data.get("pincode",   "").strip()

    required = [username, password, full_name, email, phone, door, street, area, pincode]
    if not all(required):
        return jsonify({"status": "ERROR", "message": "All fields required"})
    if not _is_valid_email(email):
        return jsonify({"status": "ERROR", "message": "A valid email is required"})
    if not _is_strong_password(password):
        return jsonify({
            "status": "ERROR",
            "message": "Password must be 8+ chars with uppercase, lowercase, digit, and special character."
        })

    # Duplicate username check
    existing = db.session.query(User).filter_by(username=username).first()
    if existing:
        return jsonify({"status": "ERROR", "message": "Username already exists"})

    address = f"{door},{street},{area},{pincode}"
    pending_registration = {
        "username": username,
        "password": _hash_password(password),
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "address": address,
    }
    otp_result = _start_otp_flow("register", email, "register", username,
                                 payload=pending_registration)

    return jsonify({
        "status":   "SUCCESS",
        "message":  "Registration OTP created. Complete verification to finish signup.",
        "user_email": email,
        "otp_sent": otp_result["status"] == "SUCCESS",
        "otp_message": (
            "Verification OTP sent to your registered email."
            if otp_result["status"] == "SUCCESS"
            else otp_result.get("data", "Could not send OTP email. Use resend OTP.")
        )
    })


@app.route("/api/auth/register/verify", methods=["POST"])
def api_verify_registration_otp():
    """POST /api/auth/register/verify — Body: { "otp" }"""
    data = request.get_json(silent=True) or {}
    otp  = data.get("otp", "").strip()

    if not otp:
        return jsonify({"status": "ERROR", "message": "OTP is required"})

    otp_state = _get_otp_flow("register")
    if not otp_state:
        return jsonify({
            "status": "ERROR", "message": "OTP expired or not found. Please register again.",
            "restart_required": True
        }), 400

    is_valid, message = _validate_otp_flow("register", otp)
    if not is_valid:
        return jsonify({"status": "ERROR", "message": message})

    payload = otp_state.get("payload") or {}
    required_fields = ["username", "password", "full_name", "email", "phone", "address"]
    if not all(payload.get(field, "") for field in required_fields):
        _clear_otp_flow("register")
        return jsonify({
            "status": "ERROR", "message": "Registration session expired. Please register again.",
            "restart_required": True
        }), 400

    new_id = _generate_next_id("U", User, User.user_id)
    new_user = User(
        user_id=new_id,
        username=payload["username"],
        password=payload["password"],
        full_name=payload["full_name"],
        email=payload["email"],
        phone=payload["phone"],
        address=payload["address"],
    )
    db.session.add(new_user)
    db.session.commit()

    _clear_otp_flow("register")
    return jsonify({"status": "SUCCESS", "message": "Registration completed successfully"})


@app.route("/api/auth/register/resend-otp", methods=["POST"])
def api_resend_registration_otp():
    """POST /api/auth/register/resend-otp"""
    otp_state = _get_otp_flow("register")
    if not otp_state:
        return jsonify({
            "status": "ERROR", "message": "Registration OTP session expired. Please register again."
        }), 400

    otp_result = _restart_otp_flow("register", otp_state)
    if otp_result["status"] != "SUCCESS":
        return jsonify({"status": "ERROR", "message": otp_result.get("data", "Could not resend OTP")})

    return jsonify({
        "status": "SUCCESS", "message": "OTP resent successfully",
        "user_email": otp_state["recipient_email"]
    })


# ═════════════════════════════════════════════════════════════
# API ROUTES — PROFILE / SETTINGS
# ═════════════════════════════════════════════════════════════
@app.route("/api/admin/me", methods=["GET"])
def api_get_admin_info():
    """GET /api/admin/me"""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"})

    admin = db.session.get(Admin, session.get("user_id"))
    if not admin:
        return jsonify({"status": "ERROR", "message": "Admin not found"})

    return jsonify({
        "status":   "SUCCESS",
        "user_id":  admin.admin_id,
        "username": admin.username,
        "name":     admin.admin_name,
        "email":    admin.email
    })


@app.route("/api/users/me", methods=["GET"])
def api_get_profile():
    """GET /api/users/me"""
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"})

    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"status": "ERROR", "message": "User not found"})

    if _is_valid_email(user.email):
        session["email"] = user.email

    return jsonify({"status": "SUCCESS", **user.to_dict()})


@app.route("/api/users/me", methods=["PATCH"])
def api_update_profile():
    """
    PATCH /api/users/me
    Body: { "field": "full_name|email|phone|address", "new_value": "..." }
    """
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"})

    data      = request.get_json(silent=True) or {}
    field     = data.get("field", "").strip()
    new_value = data.get("new_value", "").strip()

    valid_fields = {"full_name", "email", "phone", "address"}
    if field not in valid_fields:
        return jsonify({"status": "ERROR", "message": "Unknown field"})
    if not new_value:
        return jsonify({"status": "ERROR", "message": "New value required"})

    user = db.session.get(User, session["user_id"])
    if not user:
        return jsonify({"status": "ERROR", "message": "User not found"})

    setattr(user, field, new_value)
    db.session.commit()

    if field == "email":
        session["email"] = new_value

    return jsonify({"status": "SUCCESS", "message": "Profile updated"})


@app.route("/api/users/me/password/send-otp", methods=["POST"])
def api_send_password_change_otp():
    """POST /api/users/me/password/send-otp"""
    email, error = _load_current_account_email()
    if error:
        return error

    otp_result = _start_otp_flow(_password_change_flow_key(), email, "password_change")
    return jsonify({
        "status": "SUCCESS",
        "otp_sent": otp_result["status"] == "SUCCESS",
        "otp_message": (
            "OTP sent to your registered email."
            if otp_result["status"] == "SUCCESS"
            else otp_result.get("data", "Could not send OTP email.")
        )
    })


@app.route("/api/users/me/password/resend-otp", methods=["POST"])
def api_resend_password_change_otp():
    """POST /api/users/me/password/resend-otp"""
    flow_key = _password_change_flow_key()
    otp_state = _get_otp_flow(flow_key)
    if not otp_state:
        return jsonify({"status": "ERROR", "message": "OTP session expired. Please try again."}), 400

    otp_result = _restart_otp_flow(flow_key, otp_state)
    if otp_result["status"] != "SUCCESS":
        return jsonify({"status": "ERROR", "message": otp_result.get("data", "Could not resend OTP")})

    return jsonify({"status": "SUCCESS", "message": "OTP resent successfully"})


@app.route("/api/users/me/password", methods=["PATCH"])
def api_change_password():
    """
    PATCH /api/users/me/password
    Body: { "old_password", "new_password", "otp" }
    """
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"})

    data         = request.get_json(silent=True) or {}
    old_password = data.get("old_password", "")
    new_password = data.get("new_password", "")
    otp          = data.get("otp", "").strip()

    if not old_password or not new_password or not otp:
        return jsonify({"status": "ERROR", "message": "All fields required"})
    if not _is_strong_password(new_password):
        return jsonify({
            "status": "ERROR",
            "message": "Password must be 8+ chars with uppercase, lowercase, digit, and special character."
        })

    is_valid, message = _validate_otp_flow(_password_change_flow_key(), otp)
    if not is_valid:
        return jsonify({"status": "ERROR", "message": message})

    role = session.get("role", "user")
    old_hashed = _hash_password(old_password)
    new_hashed = _hash_password(new_password)

    if role == "admin":
        account = db.session.get(Admin, session["user_id"])
    else:
        account = db.session.get(User, session["user_id"])

    if not account:
        return jsonify({"status": "ERROR", "message": "Account not found"})

    if account.password != old_hashed:
        return jsonify({"status": "ERROR", "message": "Old password is incorrect"})

    account.password = new_hashed
    db.session.commit()
    _clear_otp_flow(_password_change_flow_key())

    return jsonify({"status": "SUCCESS", "message": "Password changed successfully"})

# ==============> Part 2

# ═════════════════════════════════════════════════════════════
# API ROUTES — INVENTORY (Public + Admin)
# ═════════════════════════════════════════════════════════════
@app.route("/api/admin/inventory", methods=["GET"])
def api_admin_inventory_data():
    """GET /api/admin/inventory (admin only)"""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"}), 403

    vegetables = [p.to_dict() for p in db.session.query(Product).all()]
    free_items = [f.to_dict() for f in db.session.query(FreeItem).all()]

    return jsonify({
        "status":     "SUCCESS",
        "vegetables": vegetables,
        "free_items": free_items,
    })


@app.route("/api/products", methods=["GET"])
def api_list_products():
    """GET /api/products"""
    products = [p.to_dict() for p in db.session.query(Product).all()]
    return jsonify({"status": "SUCCESS", "products": products})


@app.route("/api/products/<veg_id>", methods=["PATCH"])
def api_update_stock(veg_id):
    """
    PATCH /api/products/<veg_id>  (admin only)
    Body: { "stock_g": 75000, "price": 45.50, "validity": 10 }
    """
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"})

    data     = request.get_json() or {}
    stock_g  = int(data.get("stock_g",  0))
    price    = float(data.get("price",  0))
    validity = int(data.get("validity", 1))

    if stock_g < 0:
        return jsonify({"status": "ERROR", "message": "Stock cannot be negative"})
    if price <= 0:
        return jsonify({"status": "ERROR", "message": "Price must be greater than zero"})
    if validity < 1:
        return jsonify({"status": "ERROR", "message": "Validity must be at least 1 day"})

    product = db.session.get(Product, veg_id)
    if not product:
        return jsonify({"status": "ERROR", "message": "Vegetable ID not found"})

    product.stock_g         = stock_g
    product.price_per_1000g = price
    product.validity_days   = validity
    db.session.commit()

    return jsonify({"status": "SUCCESS", "message": "Stock updated successfully"})


@app.route("/api/promo-items/<vf_id>", methods=["PATCH"])
def api_update_promo_stock(vf_id):
    """PATCH /api/promo-items/<vf_id>  (admin only) — Body: { "stock_g": 5000 }"""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"})

    data    = request.get_json() or {}
    stock_g = int(data.get("stock_g", 0))

    if stock_g < 0:
        return jsonify({"status": "ERROR", "message": "Promo stock cannot be negative"})

    free_item = db.session.get(FreeItem, vf_id)
    if not free_item:
        return jsonify({"status": "ERROR", "message": "Promo item ID not found"})

    free_item.stock_g = stock_g
    db.session.commit()

    return jsonify({"status": "SUCCESS", "message": "Promo stock updated successfully"})


# ═════════════════════════════════════════════════════════════
# API ROUTES — CART
# ═════════════════════════════════════════════════════════════
def _serialize_cart(user_id):
    """Builds the { total, items } payload shared by cart read endpoints."""
    rows = db.session.query(CartItem).filter_by(user_id=user_id).all()
    items = [row.to_dict() for row in rows]
    total = round(sum(item["item_total"] for item in items), 2)
    return total, items


@app.route("/api/cart/items", methods=["POST"])
def api_add_to_cart():
    """POST /api/cart/items — Body: { "veg_id": "V1001", "qty_g": 500 }"""
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"})

    data   = request.get_json() or {}
    veg_id = data.get("veg_id", "").strip()
    qty_g  = int(data.get("qty_g", 0))

    if not veg_id or qty_g <= 0:
        return jsonify({"status": "ERROR", "message": "Invalid veg_id or qty_g"})

    product = db.session.get(Product, veg_id)
    if not product:
        return jsonify({"status": "ERROR", "message": "Product not found"})

    existing = db.session.query(CartItem).filter_by(
        user_id=session["user_id"], item_id=veg_id
    ).first()

    if existing:
        existing.qty_g = qty_g
    else:
        db.session.add(CartItem(
            user_id=session["user_id"],
            item_id=veg_id,
            name=product.name,
            qty_g=qty_g,
            price_per_1000g=product.price_per_1000g,
            is_free=False
        ))

    db.session.commit()
    return jsonify({"status": "SUCCESS", "message": "Item added to cart"})


@app.route("/api/cart", methods=["GET"])
def api_view_cart():
    """GET /api/cart"""
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"})

    total, items = _serialize_cart(session["user_id"])
    return jsonify({"status": "SUCCESS", "total": total, "items": items})


@app.route("/api/cart/items/<item_id>", methods=["PATCH"])
def api_update_cart_qty(item_id):
    """PATCH /api/cart/items/<item_id> — Body: { "qty_g": 750 }"""
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"})

    data  = request.get_json() or {}
    qty_g = int(data.get("qty_g", 0))

    if qty_g <= 0:
        return jsonify({"status": "ERROR", "message": "Invalid qty_g"})

    cart_item = db.session.query(CartItem).filter_by(
        user_id=session["user_id"], item_id=item_id
    ).first()

    if not cart_item:
        return jsonify({"status": "ERROR", "message": "Item not in cart"})

    cart_item.qty_g = qty_g
    db.session.commit()

    return jsonify({"status": "SUCCESS", "message": "Cart updated"})


@app.route("/api/cart/items/<item_id>", methods=["DELETE"])
def api_remove_item(item_id):
    """DELETE /api/cart/items/<item_id>"""
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"})

    cart_item = db.session.query(CartItem).filter_by(
        user_id=session["user_id"], item_id=item_id
    ).first()

    if not cart_item:
        return jsonify({"status": "ERROR", "message": "Item not in cart"})

    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({"status": "SUCCESS", "message": "Item removed"})


def _apply_freebies(user_id, cart_total):
    """
    Checks every FreeItem's min_trigger_amt against the current cart
    total. Any free item whose threshold is met and isn't already in
    the cart gets added at qty=free_qty_g, price=0, is_free=True.
    """
    free_items = db.session.query(FreeItem).filter(FreeItem.stock_g > 0).all()

    for fi in free_items:
        if cart_total < fi.min_trigger_amt:
            continue

        already_in_cart = db.session.query(CartItem).filter_by(
            user_id=user_id, item_id=fi.vf_id
        ).first()
        if already_in_cart:
            continue

        db.session.add(CartItem(
            user_id=user_id,
            item_id=fi.vf_id,
            name=fi.name,
            qty_g=fi.free_qty_g,
            price_per_1000g=0.0,
            is_free=True
        ))

    db.session.commit()


# ═════════════════════════════════════════════════════════════
# API ROUTES — CHECKOUT / RAZORPAY
# ═════════════════════════════════════════════════════════════
@app.route("/api/checkout/razorpay-order", methods=["POST"])
def api_create_razorpay_order():
    """
    POST /api/checkout/razorpay-order
    Body: { "delivery_slot": "Morning|Afternoon|Evening" }

    Creates a Razorpay order for the current cart total. Does not
    touch the orders table — no order exists until payment is verified.
    """
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    slot = data.get("delivery_slot", "").strip()

    if slot not in {"Morning", "Afternoon", "Evening"}:
        return jsonify({"status": "ERROR", "message": "Invalid delivery slot"})

    cart_total, _ = _serialize_cart(session["user_id"])

    if cart_total < 100.0:
        return jsonify({"status": "ERROR", "message": "Minimum order amount is ₹100"})

    amount_paise = int(round(cart_total * 100))

    try:
        rzp_order = _rzp_client.order.create({
            "amount":   amount_paise,
            "currency": "INR",
            "receipt":  f"fp_{session['user_id']}_{slot}",
            "notes": {
                "user_id": session["user_id"],
                "slot":    slot,
                "project": "FreshPicks"
            }
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": f"Razorpay order creation failed: {str(e)}"})

    session["pending_slot"]      = slot
    session["pending_rzp_order"] = rzp_order["id"]

    return jsonify({
        "status":            "SUCCESS",
        "razorpay_order_id": rzp_order["id"],
        "amount":            amount_paise,
        "currency":          "INR",
        "key_id":            Config.RAZORPAY_KEY_ID,
        "slot":              slot
    })


def _assign_delivery_boy():
    """
    Round Robin assignment. Picks the active delivery boy who was
    assigned least recently. last_assigned is a real DateTime column,
    so this works correctly across requests with no in-memory state.
    """
    boys = db.session.query(DeliveryBoy).filter_by(is_active=True).all()
    if not boys:
        return None

    # NULL last_assigned (never assigned) sorts first, then oldest timestamp
    boys.sort(key=lambda b: b.last_assigned or datetime.min)
    chosen = boys[0]
    chosen.last_assigned = datetime.utcnow()
    db.session.commit()
    return chosen


@app.route("/api/checkout/verify", methods=["POST"])
def api_verify_and_checkout():
    """
    POST /api/checkout/verify
    Body: { razorpay_order_id, razorpay_payment_id, razorpay_signature }

    Verifies the HMAC-SHA256 signature, then commits the order. The
    database write only happens after signature verification passes.
    """
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"}), 401

    data           = request.get_json(silent=True) or {}
    rzp_order_id   = data.get("razorpay_order_id",   "").strip()
    rzp_payment_id = data.get("razorpay_payment_id", "").strip()
    rzp_signature  = data.get("razorpay_signature",  "").strip()

    if not rzp_order_id or not rzp_payment_id or not rzp_signature:
        return jsonify({"status": "ERROR", "message": "Incomplete payment response"})

    if rzp_order_id != session.get("pending_rzp_order"):
        return jsonify({"status": "ERROR", "message": "Order ID mismatch — possible replay attempt"})

    try:
        _rzp_client.utility.verify_payment_signature({
            "razorpay_order_id":   rzp_order_id,
            "razorpay_payment_id": rzp_payment_id,
            "razorpay_signature":  rzp_signature
        })
    except Exception:
        return jsonify({"status": "ERROR", "message": "Payment verification failed — invalid signature"})

    slot = session.get("pending_slot", "")
    if slot not in {"Morning", "Afternoon", "Evening"}:
        return jsonify({"status": "ERROR", "message": "Session slot missing"})

    user_id = session["user_id"]
    cart_rows = db.session.query(CartItem).filter_by(user_id=user_id).all()

    if not cart_rows:
        return jsonify({"status": "ERROR", "message": "Cart is empty"})

    cart_total = round(sum(
        (row.qty_g / 1000.0) * row.price_per_1000g for row in cart_rows
    ), 2)

    # ── Inject freebies if cart total ≥ ₹500 ──────────────────────────
    FREEBIE_THRESHOLD = 500.0
    if cart_total >= FREEBIE_THRESHOLD:
        multiplier = int(cart_total // FREEBIE_THRESHOLD)
        freebie_qty = multiplier * 50  # 50g per ₹500 tier
        freebies = [
            {"item_id": "VF1001", "name": "Curry Leaves",     "qty_g": freebie_qty},
            {"item_id": "VF1002", "name": "Coriander Leaves", "qty_g": freebie_qty},
        ]
    else:
        freebies = []

    boy = _assign_delivery_boy()

    new_order_id = _generate_next_id("ORD", Order, Order.order_id)
    new_order = Order(
        order_id=new_order_id,
        user_id=user_id,
        total_amount=cart_total,
        delivery_slot=slot,
        delivery_boy_id=boy.boy_id if boy else None,
        status="Order Placed",
        timestamp=datetime.utcnow()
    )
    db.session.add(new_order)

    for row in cart_rows:
        db.session.add(OrderItem(
            order_id=new_order_id,
            item_id=row.item_id,
            name=row.name,
            qty_g=row.qty_g,
            price_at_order=row.price_per_1000g,
            is_free=row.is_free
        ))
        db.session.delete(row)

    for fb in freebies:
        db.session.add(OrderItem(
            order_id=new_order_id,
            item_id=fb["item_id"],
            name=fb["name"],
            qty_g=fb["qty_g"],
            price_at_order=0.0,
            is_free=True
        ))

    # ── Deduct stock for purchased vegetables ─────────────────────────────
    for row in cart_rows:
        if not row.is_free and row.item_id.startswith("V"):
            product = db.session.get(Product, row.item_id)
            if product:
                product.stock_g = max(0, product.stock_g - row.qty_g)

    # ── Deduct stock for injected freebies ────────────────────────────────
    for fb in freebies:
        if fb["item_id"].startswith("VF"):
            free_item = db.session.get(FreeItem, fb["item_id"])
            if free_item:
                free_item.stock_g = max(0, free_item.stock_g - fb["qty_g"])

    db.session.commit()

    session.pop("pending_slot",      None)
    session.pop("pending_rzp_order", None)

    items_summary = [
        {
            "item_id":       it.item_id,
            "name":          it.name,
            "qty_g":         it.qty_g,
            "price_at_order": float(it.price_at_order),
            "is_free":       it.is_free
        }
        for it in new_order.items
    ]

    for q in _order_listeners:
        q.put({
            "order_id": new_order_id,
            "total":    cart_total,
            "slot":     slot
        })

    return jsonify({
        "status":    "SUCCESS",
        "order_id":  new_order_id,
        "total":     cart_total,
        "slot":      slot,
        "boy_name":  boy.name  if boy else "Unknown",
        "boy_phone": boy.phone if boy else "N/A",
        "items":     items_summary
    })


# ═════════════════════════════════════════════════════════════
# API ROUTES — ORDERS (User)
# ═════════════════════════════════════════════════════════════
@app.route("/api/orders", methods=["GET"])
def api_get_user_orders():
    """GET /api/orders"""
    if "user_id" not in session:
        return jsonify({"status": "ERROR", "message": "Not logged in"})

    orders = db.session.query(Order).options(
        joinedload(Order.items)
    ).filter_by(
        user_id=session["user_id"]
    ).order_by(Order.timestamp.desc()).all()

    return jsonify({"status": "SUCCESS", "orders": [o.to_dict() for o in orders]})

# ============> Part 3

# ═════════════════════════════════════════════════════════════
# HELPERS — Receipt
# ═════════════════════════════════════════════════════════════
def _load_receipt_data(order_id):
    """
    Fetches one order's full receipt payload from the database.
    Returns (receipt_data_dict, error_response_or_None).
    """
    order = db.session.get(Order, order_id)
    if not order:
        return None, (jsonify({"status": "ERROR", "message": "Order not found"}), 404)

    user = db.session.get(User, order.user_id)
    if not user:
        return None, (jsonify({"status": "ERROR", "message": "User not found"}), 500)

    boy_name  = "Unknown"
    boy_phone = "N/A"
    if order.delivery_boy_id:
        boy = db.session.get(DeliveryBoy, order.delivery_boy_id)
        if boy:
            boy_name  = boy.name
            boy_phone = boy.phone

    items_string = ",".join(
        f"{item.item_id}:{item.name}:{item.qty_g}:{item.price_at_order:.2f}"
        for item in order.items
    )

    return {
        "order_id":    order.order_id,
        "user_id":     order.user_id,
        "full_name":   user.full_name,
        "user_phone":  user.phone,
        "user_email":  user.email,
        "address":     user.address,
        "slot":        order.delivery_slot,
        "status":      order.status,
        "timestamp":   order.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        "boy_name":    boy_name,
        "boy_phone":   boy_phone,
        "total":       order.total_amount,
        "items_string": items_string,
    }, None


def _generate_receipt_pdf_file(receipt_data):
    """Renders a receipt PDF to a temp file and returns its absolute path."""
    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
        prefix=f"{receipt_data['order_id']}_{receipt_data['user_id']}_"
    ) as tmp:
        tmp_path = tmp.name

    generate_receipt(receipt_data, tmp_path)
    return tmp_path


def _build_receipt_pdf(order_id):
    """Shared helper for both download and email receipt flows."""
    receipt_data, error_response = _load_receipt_data(order_id)
    if error_response:
        return None, None, error_response

    try:
        pdf_path = _generate_receipt_pdf_file(receipt_data)
    except Exception as e:
        return None, None, (
            jsonify({"status": "ERROR", "message": f"PDF generation failed: {str(e)}"}), 500
        )

    return receipt_data, pdf_path, None


def _cleanup_temp_file(path):
    """Best-effort removal for generated receipt files."""
    if path and os.path.exists(path):
        os.remove(path)


# ═════════════════════════════════════════════════════════════
# HELPERS — Analytics (Min-Heap order sorting)
# ═════════════════════════════════════════════════════════════
_SLOT_PRIORITY = {"Morning": 1, "Afternoon": 2, "Evening": 3}


def _orders_sorted_by_slot(orders):
    """
    Returns orders sorted by slot priority using Python's heapq (min-heap).
    Morning=1, Afternoon=2, Evening=3.
    """
    heap = []
    for o in orders:
        priority = _SLOT_PRIORITY.get(o.delivery_slot, 4)
        heapq.heappush(heap, (priority, o.timestamp, o))

    result = []
    while heap:
        _, _, order = heapq.heappop(heap)
        result.append(order)
    return result


def _enrich_order(order):
    """Adds boy_name and boy_phone to an order's to_dict() output."""
    data      = order.to_dict()
    boy_name  = "Unknown"
    boy_phone = "N/A"
    if order.delivery_boy_id:
        boy = db.session.get(DeliveryBoy, order.delivery_boy_id)
        if boy:
            boy_name  = boy.name
            boy_phone = boy.phone
    data["boy_name"]  = boy_name
    data["boy_phone"] = boy_phone
    return data


# ═════════════════════════════════════════════════════════════
# API ROUTES — ORDERS (Admin)
# ═════════════════════════════════════════════════════════════
@app.route("/api/admin/orders/page-data", methods=["GET"])
def api_admin_orders_page():
    """GET /api/admin/orders/page-data (admin only) — slot-priority sorted via Min-Heap."""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"})

    orders = db.session.query(Order).options(
        joinedload(Order.items)
    ).all()

    sorted_ = _orders_sorted_by_slot(orders)
    return jsonify({"status": "SUCCESS", "orders": [_enrich_order(o) for o in sorted_]})


@app.route("/api/admin/orders", methods=["GET"])
def api_get_admin_orders():
    """GET /api/admin/orders (admin only) — newest-first, enriched with delivery boy info."""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin access required"}), 403

    orders = db.session.query(Order).options(
        joinedload(Order.items)
    ).order_by(Order.timestamp.desc()).all()
    return jsonify({"status": "SUCCESS", "orders": [_enrich_order(o) for o in orders]})


@app.route("/api/admin/orders/stream", methods=["GET"])
def api_admin_order_stream():
    """
    GET /api/admin/orders/stream (admin only)
    Server-Sent Events — pushes new order notifications to Admin Dashboard.
    One queue per connected admin; broadcast fires on checkout verify.
    """
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"}), 403

    q = SimpleQueue()
    _order_listeners.append(q)

    def event_generator():
        try:
            while True:
                try:
                    order = q.get(timeout=25)   # unblock before Gunicorn timeout
                    yield f"data: {json.dumps(order)}\n\n"
                except Exception:
                    yield f": keepalive\n\n"    # SSE comment — keeps connection alive
        finally:
            if q in _order_listeners:
                _order_listeners.remove(q)


@app.route("/api/admin/orders/<order_id>/status", methods=["PATCH"])
def api_update_order_status(order_id):
    """
    PATCH /api/admin/orders/<order_id>/status (admin only)
    Body: { "status": "Out for Delivery" }
    """
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin access required"}), 403

    data       = request.get_json(silent=True) or {}
    new_status = data.get("status", "").strip()

    VALID_STATUSES = {"Order Placed", "Out for Delivery", "Delivered", "Cancelled"}
    if new_status not in VALID_STATUSES:
        return jsonify({"status": "ERROR", "message": f"Invalid status: {new_status}"})

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"status": "ERROR", "message": "Order not found"})

    order.status = new_status
    db.session.commit()

    return jsonify({"status": "SUCCESS", "message": "Status updated"})


@app.route("/api/admin/orders/promote-slot", methods=["POST"])
def api_promote_slot_orders():
    """
    POST /api/admin/orders/promote-slot (admin only)
    Body: { "slot": "Morning|Afternoon|Evening" }
    Flips all "Order Placed" orders for the given slot to "Out for Delivery".
    """
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"})

    slot = (request.get_json(silent=True) or {}).get("slot", "").strip()
    if slot not in {"Morning", "Afternoon", "Evening"}:
        return jsonify({"status": "ERROR", "message": "Invalid slot"})

    orders = db.session.query(Order).filter_by(
        delivery_slot=slot, status="Order Placed"
    ).all()

    for order in orders:
        order.status = "Out for Delivery"

    db.session.commit()
    return jsonify({"status": "SUCCESS", "promoted": len(orders)})


@app.route("/api/orders/<order_id>/cancel/send-otp", methods=["POST"])
def api_send_cancel_order_otp(order_id):
    """POST /api/orders/<order_id>/cancel/send-otp"""
    if session.get("role") not in {"user", "admin"}:
        return jsonify({"status": "ERROR", "message": "Login required"}), 403

    receipt_data, error_response = _load_receipt_data(order_id)
    if error_response:
        return error_response

    if receipt_data["status"] != "Order Placed":
        return jsonify({
            "status": "ERROR",
            "message": "Only Order Placed orders can be cancelled"
        }), 400

    if session.get("role") == "user" and receipt_data["user_id"] != session.get("user_id"):
        return jsonify({"status": "ERROR", "message": "Order does not belong to this user"}), 403

    if session.get("role") == "admin":
        recipient_email, err = _load_current_account_email()
        if err:
            return err
    else:
        recipient_email = receipt_data.get("user_email", "").strip()
        if not _is_valid_email(recipient_email):
            return jsonify({"status": "ERROR",
                            "message": "No valid email found for this order"}), 400

    flow_key   = _cancel_order_flow_key(order_id)
    otp_result = _start_otp_flow(flow_key, recipient_email, "cancel_order", order_id)

    if otp_result["status"] != "SUCCESS":
        return jsonify({
            "status": "ERROR",
            "message": otp_result.get("data", "Could not send cancellation OTP")
        })

    return jsonify({
        "status":     "SUCCESS",
        "message":    "Cancellation OTP sent successfully",
        "user_email": recipient_email
    })


@app.route("/api/orders/<order_id>/cancel/verify", methods=["POST"])
def api_cancel_order_with_otp(order_id):
    """
    POST /api/orders/<order_id>/cancel/verify
    Body: { "otp": "1234" }
    """
    if session.get("role") not in {"user", "admin"}:
        return jsonify({"status": "ERROR", "message": "Login required"}), 403

    otp = (request.get_json(silent=True) or {}).get("otp", "").strip()
    if not otp:
        return jsonify({"status": "ERROR", "message": "OTP is required"})

    receipt_data, error_response = _load_receipt_data(order_id)
    if error_response:
        return error_response

    if session.get("role") == "user" and receipt_data["user_id"] != session.get("user_id"):
        return jsonify({"status": "ERROR", "message": "Order does not belong to this user"}), 403

    if receipt_data["status"] != "Order Placed":
        return jsonify({
            "status": "ERROR",
            "message": "Only Order Placed orders can be cancelled"
        }), 400

    flow_key = _cancel_order_flow_key(order_id)
    is_valid, message = _validate_otp_flow(flow_key, otp, reference=order_id)
    if not is_valid:
        return jsonify({"status": "ERROR", "message": message}), 400

    order = db.session.get(Order, order_id)
    order.status = "Cancelled"
    db.session.commit()
    _clear_otp_flow(flow_key)

    return jsonify({"status": "SUCCESS", "message": "Order cancelled"})


@app.route("/api/admin/orders/<order_id>", methods=["DELETE"])
def api_admin_cancel_order(order_id):
    """DELETE /api/admin/orders/<order_id> (admin only) — direct cancel, no OTP."""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"}), 403

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"status": "ERROR", "message": "Order not found"})

    if order.status != "Order Placed":
        return jsonify({"status": "ERROR",
                        "message": "Only Order Placed orders can be cancelled"})

    order.status = "Cancelled"
    db.session.commit()

    return jsonify({"status": "SUCCESS", "message": "Order cancelled"})


@app.route("/api/admin/orders/active", methods=["GET"])
def api_get_active_orders():
    """GET /api/admin/orders/active (admin only) — Order Placed and Out for Delivery only."""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"}), 403

    orders = db.session.query(Order).options(
        joinedload(Order.items)
    ).filter(
        Order.status.in_(["Order Placed", "Out for Delivery"])
    ).all()

    return jsonify({"status": "SUCCESS", "orders": [_enrich_order(o) for o in orders]})


@app.route("/api/admin/orders/<order_id>/agent", methods=["PATCH"])
def api_assign_agent(order_id):
    """PATCH /api/admin/orders/<order_id>/agent (admin only) — Body: { "boy_id": "D1003" }"""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"}), 403

    boy_id = (request.get_json(silent=True) or {}).get("boy_id", "").strip()
    if not boy_id:
        return jsonify({"status": "ERROR", "message": "boy_id is required"})

    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"status": "ERROR", "message": "Order not found"})

    boy = db.session.get(DeliveryBoy, boy_id)
    if not boy:
        return jsonify({"status": "ERROR", "message": "Delivery boy not found"})

    order.delivery_boy_id = boy_id
    db.session.commit()

    return jsonify({"status": "SUCCESS", "message": "Agent assigned"})


# ═════════════════════════════════════════════════════════════
# API ROUTES — RECEIPTS
# ═════════════════════════════════════════════════════════════
@app.route("/api/orders/<order_id>/receipt", methods=["GET"])
def api_download_receipt(order_id):
    """GET /api/orders/<order_id>/receipt — accessible by logged-in users and admins."""
    if "user_id" not in session and session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Not logged in"}), 401

    receipt_data, tmp_path, error_response = _build_receipt_pdf(order_id)
    if error_response:
        return error_response

    filename = f"{receipt_data['order_id']}_{receipt_data['user_id']}.pdf"
    response = send_file(
        tmp_path,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )
    response.call_on_close(lambda: _cleanup_temp_file(tmp_path))
    return response


@app.route("/api/orders/<order_id>/receipt/email", methods=["POST"])
def api_email_receipt(order_id):
    """POST /api/orders/<order_id>/receipt/email"""
    if session.get("role") != "user":
        return jsonify({"status": "ERROR", "message": "Login required"}), 403

    receipt_data, tmp_path, error_response = _build_receipt_pdf(order_id)
    if error_response:
        return error_response

    try:
        if receipt_data["user_id"] != session.get("user_id"):
            return jsonify({"status": "ERROR",
                            "message": "Order does not belong to this user"}), 403

        user_email = receipt_data.get("user_email", "").strip()
        if not user_email or "@" not in user_email:
            return jsonify({"status": "ERROR",
                            "message": "No valid email found for this order"}), 400

        with open(tmp_path, "rb") as f:
            pdf_data = base64.b64encode(f.read()).decode()

        message = SGMail(
            from_email = ("FreshPicks", Config.SMTP_EMAIL),
            to_emails    = user_email,
            subject      = f"FreshPicks Receipt — {order_id}",
            html_content = f"<p>Dear {receipt_data['full_name']},</p><p>Please find your FreshPicks receipt for order <strong>{order_id}</strong> attached.</p><p>Thank you for shopping with us!</p><p><strong>FreshPicks</strong></p>"
        )

        attachment = Attachment(
            file_content = FileContent(pdf_data),
            file_name    = FileName(f"{order_id}_receipt.pdf"),
            file_type    = FileType("application/pdf"),
            disposition  = Disposition("attachment")
        )
        message.attachment = attachment

        sg = SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        sg.client.mail.send.post(request_body=message.get())

    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)})
    finally:
        _cleanup_temp_file(tmp_path)

    return jsonify({"status": "SUCCESS", "message": "Email sent", "user_email": user_email})


# ═════════════════════════════════════════════════════════════
# API ROUTES — USERS (Admin)
# ═════════════════════════════════════════════════════════════
def _user_status(user):
    return "Active" if user.password else "Inactive"


@app.route("/api/admin/users", methods=["GET"])
def api_admin_list_users():
    """
    GET /api/admin/users?filter=active|inactive (admin only)
    Query param filter is optional — omit for all users.
    """
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"}), 403

    status_filter = request.args.get("filter", "").strip().lower()
    query = db.session.query(User)

    if status_filter == "active":
        query = query.filter(User.password != "")
    elif status_filter == "inactive":
        query = query.filter(User.password == "")

    users = query.all()
    result = [
        {**u.to_dict(), "status": _user_status(u)}
        for u in users
    ]

    return jsonify({"status": "SUCCESS", "users": result, "total": len(result)})


@app.route("/api/admin/users/search", methods=["GET"])
def api_admin_search_users():
    """
    GET /api/admin/users/search?q=Ravi (admin only)
    Matches exact user_id or full_name substring (case-insensitive).
    """
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"}), 403

    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"status": "ERROR", "message": "q is required"})

    exact = db.session.get(User, query)
    if exact:
        return jsonify({
            "status": "SUCCESS",
            "users":  [{**exact.to_dict(), "status": _user_status(exact)}],
            "total":  1
        })

    users = db.session.query(User).filter(
        User.full_name.ilike(f"%{query}%")
    ).all()

    result = [{**u.to_dict(), "status": _user_status(u)} for u in users]
    return jsonify({"status": "SUCCESS", "users": result, "total": len(result)})


@app.route("/api/admin/users/<user_id>", methods=["GET"])
def api_admin_get_user(user_id):
    """GET /api/admin/users/<user_id> (admin only)"""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"}), 403

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"status": "ERROR", "message": "User not found"})

    return jsonify({
        "status": "SUCCESS",
        "user":   {**user.to_dict(), "status": _user_status(user)}
    })


# ═════════════════════════════════════════════════════════════
# API ROUTES — ANALYTICS (Admin)
# ═════════════════════════════════════════════════════════════
@app.route("/api/admin/analytics", methods=["GET"])
def api_analytics():
    """GET /api/admin/analytics (admin only)"""
    if session.get("role") != "admin":
        return jsonify({"status": "ERROR", "message": "Admin only"}), 403

    orders       = db.session.query(Order).all()
    products     = db.session.query(Product).all()
    users        = db.session.query(User).all()
    delivery_boys = db.session.query(DeliveryBoy).all()

    total_revenue    = sum(o.total_amount for o in orders)
    total_orders     = len(orders)
    avg_order_value  = round(total_revenue / total_orders, 2) if total_orders else 0.0

    orders_placed    = sum(1 for o in orders if o.status == "Order Placed")
    orders_out       = sum(1 for o in orders if o.status == "Out for Delivery")
    orders_delivered = sum(1 for o in orders if o.status == "Delivered")
    orders_cancelled = sum(1 for o in orders if o.status == "Cancelled")

    slot_morning   = sum(1 for o in orders if o.delivery_slot == "Morning")
    slot_afternoon = sum(1 for o in orders if o.delivery_slot == "Afternoon")
    slot_evening   = sum(1 for o in orders if o.delivery_slot == "Evening")

    total_stock_kg = round(sum(p.stock_g for p in products) / 1000.0, 2)
    low_stock      = sum(1 for p in products if p.stock_g < 5000)

    total_users            = len(users)
    active_delivery_boys   = sum(1 for b in delivery_boys if b.is_active)
    inactive_delivery_boys = sum(1 for b in delivery_boys if not b.is_active)

    return jsonify({
        "status": "SUCCESS",
        "stats": {
            "total_revenue":          round(total_revenue, 2),
            "total_orders":           total_orders,
            "avg_order_value":        avg_order_value,
            "orders_placed":          orders_placed,
            "orders_out":             orders_out,
            "orders_delivered":       orders_delivered,
            "orders_cancelled":       orders_cancelled,
            "slot_morning":           slot_morning,
            "slot_afternoon":         slot_afternoon,
            "slot_evening":           slot_evening,
            "total_stock_kg":         total_stock_kg,
            "low_stock_items":        low_stock,
            "total_users":            total_users,
            "active_delivery_boys":   active_delivery_boys,
            "inactive_delivery_boys": inactive_delivery_boys,
        }
    })


# ═════════════════════════════════════════════════════════════
# APP STARTUP
# ═════════════════════════════════════════════════════════════
# if __name__ == "__main__":
#     with app.app_context():
#         db.create_all()

#     app.run(
#         host     = "0.0.0.0",
#         port     = int(os.environ.get("PORT", 5000)),
#         debug    = os.environ.get("FLASK_DEBUG", "false").lower() == "true",
#         threaded = True
#     )

# if __name__ == "__main__":
#     with app.app_context():
#         db.create_all()

#     app.run(
#         host="0.0.0.0",
#         port=int(os.environ.get("PORT", 5000)),
#         debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true",
#         threaded=True
#     )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    HOST  = "0.0.0.0"
    PORT  = 5000
    DEBUG = True

    def get_local_ip():
        """
        Detect the machine's active LAN/Wi-Fi IPv4 address without
        sending any real traffic. Falls back to 127.0.0.1 on failure.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    LOCAL_IP = get_local_ip()

    print()
    print("=" * 62)
    print("  FreshPicks  |  CodeCrafters  |  SDP-1  |  HTTP Server")
    print("=" * 62)
    print()
    print("  Mode         :  Intranet")
    print(f"  Home         :  http://{LOCAL_IP}:{PORT}/")
    print(f"  Presentation :  http://{LOCAL_IP}:{PORT}/presentation")
    print(f"  Admin Portal :  http://{LOCAL_IP}:{PORT}/login/admin")
    print(f"  User Portal  :  http://{LOCAL_IP}:{PORT}/login/user")
    print("=" * 62)
    print()

    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
        threaded=True
    )