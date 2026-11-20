"""
test_mail.py - Test all email types via SMTP fallback to verify email output.
Run: python test_mail.py
"""
import os
import sys

from flask import Flask
from flask_mail import Message
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To

from app.config import Config
from app.extensions import db, mail
from app.models import User, Admin, Order
from app.logging_setup import setup_logging

# Force SMTP fallback for testing
SMTP_EMAIL = os.environ.get("SMTP_EMAIL")
SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 465))
SENDER_NAME = os.environ.get("SENDER_NAME", "FreshPicks")

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

TEST_RECIPIENT = "yashwantharumugam2007@gmail.com"

def create_test_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Mail config
    app.config["MAIL_SERVER"] = SMTP_HOST
    app.config["MAIL_PORT"] = SMTP_PORT
    app.config["MAIL_USE_SSL"] = SMTP_PORT == 465
    app.config["MAIL_USE_TLS"] = SMTP_PORT == 587
    app.config["MAIL_USERNAME"] = SMTP_EMAIL
    app.config["MAIL_PASSWORD"] = SMTP_APP_PASSWORD
    app.config["MAIL_DEFAULT_SENDER"] = (SENDER_NAME, SMTP_EMAIL)
    
    db.init_app(app)
    mail.init_app(app)
    setup_logging(app)
    return app

def test_smtp_registration_otp(app):
    """Test 1: Registration OTP via SMTP"""
    print("\n" + "="*60)
    print("TEST 1: Registration OTP (SMTP)")
    print("="*60)
    
    with app.app_context():
        msg = Message(
            subject="FreshPicks Registration OTP",
            sender=(SENDER_NAME, SMTP_EMAIL),
            recipients=[TEST_RECIPIENT],
            body="Your verification OTP is: 1234\n\nValid for 10 minutes."
        )
        msg.html = f"""
        <h1 style="margin:0 0 16px 0;color:#007acc;font-family:Arial,sans-serif;">FreshPicks</h1>
        <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;color:#333;">Dear Customer,</p>
        <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;color:#333;">Your verification OTP is:</p>
        <div style="display:inline-block;padding:12px 18px;border-radius:8px;background:#f4f8fb;border:1px solid #d4e4f2;font-size:28px;letter-spacing:0.25em;font-weight:700;color:#007acc;font-family:monospace;">1234</div>
        <p style="margin:16px 0 0;font-family:Arial,sans-serif;color:#333;">This OTP is valid for <strong>10 minutes</strong>.</p>
        <p style="margin:16px 0 0;font-family:Arial,sans-serif;color:#333;">Regards,<br><strong>FreshPicks</strong></p>
        """
        try:
            mail.send(msg)
            print(f"SUCCESS: Registration OTP sent to {TEST_RECIPIENT}")
            return True
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {e}")
            return False

def test_smtp_cancel_order_otp(app):
    """Test 2: Cancel Order OTP via SMTP"""
    print("\n" + "="*60)
    print("TEST 2: Cancel Order OTP (SMTP)")
    print("="*60)
    
    with app.app_context():
        msg = Message(
            subject="FreshPicks Cancellation OTP - FP1001",
            sender=(SENDER_NAME, SMTP_EMAIL),
            recipients=[TEST_RECIPIENT],
            body="Cancellation OTP for FP1001: 5678"
        )
        msg.html = f"""
        <h1 style="margin:0 0 16px 0;color:#dc3545;font-family:Arial,sans-serif;">FreshPicks</h1>
        <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;color:#333;">Dear Customer,</p>
        <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;color:#333;">We received a request to cancel <strong>FP1001</strong>.</p>
        <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;color:#333;">Your cancellation OTP is:</p>
        <div style="display:inline-block;padding:12px 18px;border-radius:8px;background:#fff5f5;border:1px solid #f0c2c2;font-size:28px;letter-spacing:0.25em;font-weight:700;color:#dc3545;font-family:monospace;">5678</div>
        <p style="margin:16px 0 0;font-family:Arial,sans-serif;color:#333;">This OTP is valid for <strong>10 minutes</strong>.</p>
        <p style="margin:16px 0 0;font-family:Arial,sans-serif;color:#333;">Regards,<br><strong>FreshPicks</strong></p>
        """
        try:
            mail.send(msg)
            print(f"SUCCESS: Cancel Order OTP sent to {TEST_RECIPIENT}")
            return True
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {e}")
            return False

def test_smtp_password_change_otp(app):
    """Test 3: Password Change OTP via SMTP"""
    print("\n" + "="*60)
    print("TEST 3: Password Change OTP (SMTP)")
    print("="*60)
    
    with app.app_context():
        msg = Message(
            subject="FreshPicks Password Change OTP",
            sender=(SENDER_NAME, SMTP_EMAIL),
            recipients=[TEST_RECIPIENT],
            body="Password change OTP: 9012"
        )
        msg.html = f"""
        <h1 style="margin:0 0 16px 0;color:#7b4dff;font-family:Arial,sans-serif;">FreshPicks</h1>
        <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;color:#333;">Dear Customer,</p>
        <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;color:#333;">We received a request to change your <strong>FreshPicks</strong> account password.</p>
        <p style="margin:0 0 16px 0;font-family:Arial,sans-serif;color:#333;">Your password-change OTP is:</p>
        <div style="display:inline-block;padding:12px 18px;border-radius:8px;background:#f7f2ff;border:1px solid #d7c4ff;font-size:28px;letter-spacing:0.25em;font-weight:700;color:#7b4dff;font-family:monospace;">9012</div>
        <p style="margin:16px 0 0;font-family:Arial,sans-serif;color:#333;">This OTP is valid for <strong>10 minutes</strong>.</p>
        <p style="margin:16px 0 0;font-family:Arial,sans-serif;color:#333;">Regards,<br><strong>FreshPicks</strong></p>
        """
        try:
            mail.send(msg)
            print(f"SUCCESS: Password Change OTP sent to {TEST_RECIPIENT}")
            return True
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {e}")
            return False

def test_smtp_receipt_email(app):
    """Test 4: Receipt Email via SMTP"""
    print("\n" + "="*60)
    print("TEST 4: Receipt Email (SMTP)")
    print("="*60)
    
    with app.app_context():
        msg = Message(
            subject="FreshPicks Receipt - FP1001",
            sender=(SENDER_NAME, SMTP_EMAIL),
            recipients=[TEST_RECIPIENT],
            body="Dear Customer,\n\nYour order FP1001 has been placed successfully.\n\nRegards,\nFreshPicks"
        )
        msg.html = "<p>Dear Customer,</p><p>Your order <strong>FP1001</strong> has been placed successfully. Receipt attached.</p><p><strong>FreshPicks</strong></p>"
        try:
            mail.send(msg)
            print(f"SUCCESS: Receipt email sent to {TEST_RECIPIENT}")
            return True
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {e}")
            return False

def test_sendgrid_registration_otp():
    """Test 5: Registration OTP via SendGrid"""
    print("\n" + "="*60)
    print("TEST 5: Registration OTP (SendGrid)")
    print("="*60)
    
    if not SENDGRID_API_KEY:
        print("SKIPPED: No SENDGRID_API_KEY set")
        return False
    
    try:
        message = Mail(
            from_email=From(SENDGRID_API_KEY.split('.')[1] + "@example.com", "FreshPicks"),
            to_emails=To(TEST_RECIPIENT),
            subject="FreshPicks Registration OTP",
            html_content="<p>Your verification OTP is: <strong>1234</strong></p>",
            plain_text_content="Your verification OTP is: 1234"
        )
        sg = SendGridAPIClient(api_key=SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"SUCCESS: SendGrid status={response.status_code}")
        return response.status_code == 202
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {e}")
        if hasattr(e, 'body'):
            print(f"SendGrid body: {e.body}")
        return False

def main():
    print("\n" + "#"*60)
    print("# FreshPicks Email Test Suite")
    print("#"*60)
    print(f"\nSMTP: {SMTP_EMAIL} -> {SMTP_HOST}:{SMTP_PORT}")
    print(f"SendGrid API Key: {'SET' if SENDGRID_API_KEY else 'NOT SET'}")
    print(f"Testing to: {TEST_RECIPIENT}")
    
    app = create_test_app()
    
    results = []
    
    results.append(("SMTP Registration OTP", test_smtp_registration_otp(app)))
    results.append(("SMTP Cancel Order OTP", test_smtp_cancel_order_otp(app)))
    results.append(("SMTP Password Change OTP", test_smtp_password_change_otp(app)))
    results.append(("SMTP Receipt Email", test_smtp_receipt_email(app)))
    results.append(("SendGrid Registration OTP", test_sendgrid_registration_otp()))
    
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  [{status}] {name}")
    
    passed = sum(1 for _, r in results if r)
    print(f"\nTotal: {passed}/{len(results)} passed")
    
    if passed == len(results):
        print("\nAll emails sent successfully! Check your inbox.")
    else:
        print(f"\n{len(results) - passed} test(s) failed. Check error messages above.")
    
    return 0 if passed == len(results) else 1

if __name__ == "__main__":
    sys.exit(main())
