"""
cache.py - Fresh Picks: Redis Cache Module

Provides Flask-Caching instance backed by Redis.
Falls back to SimpleCache (in-memory) when Redis is not available.
"""
from flask_caching import Cache

cache = Cache()


def init_cache(app):
    """Initialize the Flask-Caching extension."""
    redis_url = app.config.get("REDIS_URL")

    if redis_url:
        # Production / development with Redis
        cache.init_app(
            app,
            config={
                "CACHE_TYPE": "RedisCache",
                "CACHE_REDIS_URL": redis_url,
                "CACHE_DEFAULT_TIMEOUT": app.config.get("CACHE_DEFAULT_TIMEOUT", 60),
                "CACHE_KEY_PREFIX": app.config.get("CACHE_KEY_PREFIX", "fp"),
            },
        )
        app.logger.info("CACHE: Redis initialized (RedisCache backend)")

    else:
        # Fallback: SimpleCache (in-memory) for testing or when Redis is unavailable
        # Note: SimpleCache is per-process and lost on restart.
        # Not suitable for multi-worker production without Redis.
        is_test = app.config.get("TESTING")
        cache.init_app(
            app,
            config={
                "CACHE_TYPE": "SimpleCache",
                "CACHE_DEFAULT_TIMEOUT": 300,
            },
        )
        if is_test:
            app.logger.info("CACHE: SimpleCache initialized (testing mode)")
        else:
            app.logger.warning(
                "CACHE: REDIS_URL not set — using SimpleCache (in-memory). "
                "Not suitable for multi-worker production. Set REDIS_URL for Redis."
            )
