"""
mail_service.py - Fresh Picks: Dual Mailer Service

Supports two mail providers via MAILER_PROVIDER env var:
  - "smtp"    : Flask-Mail (Gmail SMTP)   – used in development
  - "resend"  : Resend API (resend.com)  – used in production

Usage:
    from .mail_service import send_otp_email
    result = send_otp_email(to, subject, text_body, html_body)
"""
import os
import requests
from flask import render_template_string
from flask_mail import Message

from .extensions import mail


# ── Provider Selection ──────────────────────────────────────────────
MAILER_PROVIDER = os.environ.get("MAILER_PROVIDER", "smtp").lower()

# ── SMTP Config (fallback) ─────────────────────────────────────────
SMTP_EMAIL     = os.environ.get("SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", "")
SMTP_HOST      = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT      = int(os.environ.get("SMTP_PORT", 465))
SENDER_NAME    = os.environ.get("SENDER_NAME", "FreshPicks")

# ── Resend Config (production) ─────────────────────────────────────
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")
RESEND_FROM = os.environ.get("RESEND_FROM", SENDER_NAME + " <" + SMTP_EMAIL + ">") if SMTP_EMAIL else ""


def send_otp_email(recipient_email, otp_code, purpose, reference="", full_name="", ttl_minutes=10):
    """
    Send an OTP email. Uses the configured mailer provider.
    Returns {"status": "SUCCESS"|"ERROR", "data": message}
    """
    subject, text_body, html_body = _build_otp_email(purpose, otp_code, reference, full_name, ttl_minutes)
    return send_email(recipient_email, subject, text_body, html_body)


def send_email(recipient_email, subject, text_body, html_body, sender_name=None, sender_email=None):
    """
    Send an email via the configured provider.
    """
    if MAILER_PROVIDER == "resend" and RESEND_API_KEY:
        return _send_via_resend(recipient_email, subject, text_body, html_body, sender_name, sender_email)
    else:
        return _send_via_smtp(recipient_email, subject, text_body, html_body, sender_name, sender_email)


def _build_otp_email(purpose, otp_code, reference="", full_name="", ttl_minutes=10):
    """Build OTP email content."""
    purpose_labels = {
        "registration": "Email Verification",
        "password_change": "Password Change Verification",
        "cancel_order": "Order Cancellation Verification",
    }
    label = purpose_labels.get(purpose, "Verification")

    text_body = f"""Hello {full_name},

Your {label} code is: {otp_code}

This code will expire in {ttl_minutes} minutes.
If you didn't request this, please ignore this email.

Thanks,
FreshPicks Team
"""
    html_body = f"""<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #2ecc71;">FreshPicks</h2>
        <p>Hello {full_name},</p>
        <p>Your <strong>{label}</strong> code is:</p>
        <div style="background: #f0f0f0; padding: 15px; text-align: center; font-size: 28px; font-weight: bold; letter-spacing: 5px; border-radius: 8px;">
            {otp_code}
        </div>
        <p>This code will expire in <strong>{ttl_minutes} minutes</strong>.</p>
        <p>If you didn't request this, please ignore this email.</p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
        <p style="color: #888; font-size: 12px;">Thanks,<br>FreshPicks Team</p>
    </div>
</body>
</html>"""

    subject = f"[FreshPicks] {label}"
    return subject, text_body, html_body


def _send_via_smtp(recipient_email, subject, text_body, html_body, sender_name=None, sender_email=None):
    """Send email via Flask-Mail / SMTP."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        from flask import current_app
        app = current_app._get_current_object()
        from flask_mail import Message

        sender_name = sender_name or app.config.get("SENDER_NAME", "FreshPicks")
        sender_email = sender_email or app.config.get("SMTP_EMAIL", SMTP_EMAIL)

        msg = Message(
            subject=subject,
            sender=(sender_name, sender_email),
            recipients=[recipient_email],
            body=text_body,
            html=html_body
        )
        mail.send(msg)
        logger.info("MAIL SMTP SUCCESS | to=%s | subject=%s", recipient_email, subject)
        return {"status": "SUCCESS", "data": "Email sent via SMTP"}
    except Exception as e:
        logger.error("MAIL SMTP ERROR: %s: %s | to=%s", type(e).__name__, e, recipient_email)
        return {"status": "ERROR", "data": str(e)}


def _send_via_resend(recipient_email, subject, text_body, html_body, sender_name=None, sender_email=None):
    """Send email via Resend API (resend.com)."""
    import logging
    logger = logging.getLogger(__name__)

    try:
        sender_name = sender_name or "FreshPicks"
        sender_email = sender_email or SMTP_EMAIL or "noreply@yourdomain.com"

        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "from": f"{sender_name} <{sender_email}>",
            "to": [recipient_email],
            "subject": subject,
            "text": text_body,
            "html": html_body,
        }

        response = requests.post(
            "https://api.resend.com/emails",
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            logger.info("MAIL RESEND SUCCESS | to=%s | id=%s", recipient_email, data.get("id"))
            return {"status": "SUCCESS", "data": f"Email sent via Resend (id: {data.get('id')})"}
        else:
            logger.error("MAIL RESEND ERROR: %d | %s | to=%s", response.status_code, response.text, recipient_email)
            return {"status": "ERROR", "data": f"Resend API error: {response.status_code} - {response.text}"}
    except Exception as e:
        logger.error("MAIL RESEND EXCEPTION: %s: %s | to=%s", type(e).__name__, e, recipient_email)
        return {"status": "ERROR", "data": str(e)}
