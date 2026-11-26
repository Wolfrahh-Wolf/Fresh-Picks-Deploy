"""
cache.py - Fresh Picks: Redis Cache Module

Provides Flask-Caching instance backed by Redis.
Falls back to SimpleCache for testing (no Redis required).
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

    elif app.config.get("TESTING"):
        # Test environment: use in-memory cache (no Redis needed)
        cache.init_app(
            app,
            config={
                "CACHE_TYPE": "SimpleCache",
                "CACHE_DEFAULT_TIMEOUT": 300,
            },
        )
        app.logger.info("CACHE: SimpleCache initialized (testing mode)")

    else:
        raise RuntimeError(
            "REDIS_URL is not set. Redis caching is required for production."
        )
