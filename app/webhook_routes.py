"""Webhook handlers for Razorpay payment events."""
import json
import logging

import razorpay.errors
from flask import Blueprint, request, jsonify

from .extensions import db, rzp_client, csrf
from .models import Order

bp = Blueprint("webhook", __name__)
logger = logging.getLogger(__name__)

# Webhook secret loaded once at module init (after app creation)
_WEBHOOK_SECRET = None

# Razorpay event names (without "razorpay." prefix — confirmed via SDK docs)
_EVENT_SUCCEEDED = "payment.succeeded"
_EVENT_FAILED = "payment.failed"


def init_webhook(app):
    """Register the webhook blueprint and load the webhook secret."""
    global _WEBHOOK_SECRET
    _WEBHOOK_SECRET = app.config.get("RAZORPAY_WEBHOOK_SECRET")
    if not _WEBHOOK_SECRET:
        logger.warning(
            "RAZORPAY_WEBHOOK_SECRET not configured — webhooks will be rejected"
        )
    app.register_blueprint(bp)


# CSRF exempted: Razorpay webhook delivers server-to-server requests
# without CSRF tokens. Mitigated by: HMAC-SHA256 signature verification
# via X-Razorpay-Signature header.
@bp.route("/api/webhook/razorpay", methods=["POST"])
@csrf.exempt
def razorpay_webhook():
    """Handle Razorpay webhook events.

    Verifies webhook signature, processes payment.succeeded and
    payment.failed events. Returns 200 to acknowledge receipt
    (required by Razorpay).
    """
    # 1. Get raw body as string (SDK requires string, not bytes)
    raw_body = request.get_data(as_text=True)

    # 2. Get signature header
    signature = request.headers.get("X-Razorpay-Signature")

    if not signature:
        logger.warning("Webhook received without X-Razorpay-Signature header")
        return jsonify({"status": "error", "message": "Missing signature"}), 400

    # 3. Check webhook secret is configured
    if not _WEBHOOK_SECRET:
        logger.error("RAZORPAY_WEBHOOK_SECRET not configured — dropping webhook")
        return jsonify({"status": "error", "message": "Server misconfigured"}), 500

    # 4. Verify webhook signature
    try:
        rzp_client.client.utility.verify_webhook_signature(
            raw_body, signature, _WEBHOOK_SECRET
        )
    except razorpay.errors.SignatureVerificationError:
        logger.warning("Webhook signature verification failed")
        return jsonify({"status": "error", "message": "Invalid signature"}), 400
    except Exception as e:
        logger.exception("Unexpected error during signature verification")
        return jsonify({"status": "error", "message": "Server error"}), 500

    # 5. Parse event payload
    try:
        event_data = json.loads(raw_body)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Webhook payload not valid JSON: %s", e)
        return jsonify({"status": "error", "message": "Invalid payload"}), 400

    event_type = event_data.get("event", "")
    payload = event_data.get("payload", {})

    # 6. Handle known events
    if event_type == _EVENT_SUCCEEDED:
        return _handle_payment_succeeded(payload)
    elif event_type == _EVENT_FAILED:
        return _handle_payment_failed(payload)
    else:
        # Silently acknowledge other events (Razorpay may send subscription events, etc.)
        logger.info("Webhook event not handled: %s", event_type)
        return jsonify({"status": "ok", "message": "Event acknowledged"}), 200


def _handle_payment_succeeded(payload):
    """Handle successful payment — confirm order status if not already done."""
    payment = payload.get("payment", {})
    payment_id = payment.get("id", "")
    amount = payment.get("amount", 0)

    if not payment_id:
        logger.warning("Payment succeeded event missing payment.id")
        return jsonify({"status": "error", "message": "Missing payment ID"}), 400

    # Idempotency: if already linked to an order, confirm and check consistency
    order = Order.query.filter_by(razorpay_payment_id=payment_id).first()
    if order:
        expected_paise = int(order.total_amount * 100)
        if abs(amount - expected_paise) > 1:
            logger.warning(
                "Webhook amount mismatch: order %s has Rs.%.2f "
                "(expected %d paise), Razorpay reports %d paise",
                order.order_id, order.total_amount, expected_paise, amount,
            )
        return jsonify({"status": "ok", "message": "Payment confirmed"}), 200

    # No order found — log for admin reconciliation
    logger.warning(
        "Webhook: payment %s succeeded but no matching order found "
        "(client may not have completed /verify — amount=%d paise)",
        payment_id, amount,
    )
    return jsonify(
        {"status": "ok", "message": "Payment recorded for reconciliation"}
    ), 200


def _handle_payment_failed(payload):
    """Handle failed payment — cancel order if it exists and is still pending."""
    payment = payload.get("payment", {})
    payment_id = payment.get("id", "")
    error_desc = payment.get("error_description", "Unknown")

    if not payment_id:
        logger.warning("Payment failed event missing payment.id")
        return jsonify({"status": "error", "message": "Missing payment ID"}), 400

    order = Order.query.filter_by(razorpay_payment_id=payment_id).first()
    if order and order.status == "Order Placed":
        order.status = "Cancelled"
        try:
            db.session.commit()
            logger.info(
                "Order %s cancelled due to failed payment %s: %s",
                order.order_id, payment_id, error_desc,
            )
            return jsonify({"status": "ok", "message": "Order cancelled"}), 200
        except Exception:
            db.session.rollback()
            logger.exception("Failed to cancel order %s for payment %s", order.order_id, payment_id)
            return jsonify({"status": "error", "message": "Internal error"}), 500

    logger.info("Webhook: payment %s failed — no actionable order found", payment_id)
    return jsonify({"status": "ok", "message": "Payment failure recorded"}), 200
