"""
app.py - Fresh Picks: Application Entry Point

Run locally:  python app.py
Run in prod:  gunicorn app:app (Flask finds the 'app' object)
"""
import os
import socket
import logging

logger = logging.getLogger(__name__)


def _make_app():
    """Create and configure the Flask application."""
    from app import create_app
    from app.config import Config
    return create_app(Config)


app = _make_app()


if __name__ == "__main__":
    with app.app_context():
        from app.extensions import db
        db.create_all()

    HOST  = "0.0.0.0"
    PORT  = int(os.environ.get("PORT", 5000))
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    def get_local_ip():
        """Detect the machine's active LAN/Wi-Fi IPv4 address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    LOCAL_IP = get_local_ip()

    logger.info("=" * 62)
    logger.info("  FreshPicks  |  CodeCrafters  |  SDP-1  |  HTTP Server")
    logger.info("=" * 62)
    logger.info("  Mode         :  Intranet")
    logger.info("  Home         :  http://%s:%s/", LOCAL_IP, PORT)
    logger.info("  Presentation :  http://%s:%s/presentation", LOCAL_IP, PORT)
    logger.info("  Admin Portal :  http://%s:%s/login/admin", LOCAL_IP, PORT)
    logger.info("  User Portal  :  http://%s:%s/login/user", LOCAL_IP, PORT)
    logger.info("=" * 62)

    app.run(
        host=HOST,
        port=PORT,
        debug=DEBUG,
        threaded=True
    )
