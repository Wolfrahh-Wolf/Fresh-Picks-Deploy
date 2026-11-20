"""
extensions.py - Fresh Picks: Extension Instances
"""
import razorpay
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect


db = SQLAlchemy()
mail = Mail()
limiter = Limiter(key_func=get_remote_address)
csrf = CSRFProtect()


class _RzpClientWrapper:
    """Thin wrapper to lazily initialize Razorpay client per app."""
    def __init__(self):
        self._client = None

    def init(self, key_id, key_secret):
        self._client = razorpay.Client(auth=(key_id, key_secret))

    @property
    def client(self):
        if not self._client:
            raise RuntimeError("Razorpay client not initialized. Did you call rzp_client.init()?")
        return self._client


rzp_client = _RzpClientWrapper()
