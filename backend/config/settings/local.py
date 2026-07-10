"""
Local development settings.
"""

from os import getenv

from .base import *  # noqa: F403

DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ------------------------------------------------------------------------------
# Cookies
# ------------------------------------------------------------------------------

AUTH_COOKIE = "access"
AUTH_COOKIE_MAX_AGE = 60 * 60 * 24
AUTH_COOKIE_SECURE = getenv("AUTH_COOKIE_SECURE", "True") == "True"
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = "/"
AUTH_COOKIE_SAMESITE = "Lax"


# ------------------------------------------------------------------------------
# Email
# ------------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ------------------------------------------------------------------------------
# Cache (Redis if available, otherwise local memory)
# ------------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
    }
}

# ------------------------------------------------------------------------------
# Django REST Framework
# ------------------------------------------------------------------------------

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [  # noqa: F405
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
]

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "1000/hour",
    "user": "5000/hour",
}

# logging data error and response

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "production_grade_verbose": {
            "format": "[{asctime}] {levelname} | Component: {name} | Execution: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "interactive_terminal_console": {
            "class": "logging.StreamHandler",
            "formatter": "production_grade_verbose",
        },
    },
    "loggers": {
        # Prints a log to your terminal for EVERY HTTP request (200, 201, 404, etc.)
        "django.server": {
            "handlers": ["interactive_terminal_console"],
            "level": "INFO",
            "propagate": False,
        },
        # Intercepts case 4 system crashes with full traceback printouts
        "django.request": {
            "handlers": ["interactive_terminal_console"],
            "level": "ERROR",
            "propagate": False,
        },
        # Intercepts case 1 security metric tracking and rate-limit warnings
        "security": {
            "handlers": ["interactive_terminal_console"],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
