"""
Production settings.
"""

import os
from os import getenv

from config.settings.base import *  # noqa: F403

DEBUG = False

ALLOWED_HOSTS = getenv(
    "DJANGO_ALLOWED_HOSTS",
    "",
).split(",")

CORS_ALLOWED_ORIGINS = getenv(
    "CORS_ALLOWED_ORIGINS",
    "",
).split(",")

CSRF_TRUSTED_ORIGINS = getenv(
    "CSRF_TRUSTED_ORIGINS",
    "",
).split(",")

# ------------------------------------------------------------------------------
# Security
# ------------------------------------------------------------------------------

SECURE_SSL_REDIRECT = True

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SESSION_COOKIE_HTTPONLY = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

X_FRAME_OPTIONS = "DENY"

# ------------------------------------------------------------------------------
# Authentication Cookie
# ------------------------------------------------------------------------------

AUTH_COOKIE_SECURE = True
AUTH_COOKIE_SAMESITE = "None"

# ------------------------------------------------------------------------------
# Redis Cache
# ------------------------------------------------------------------------------

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
    }
}

# ------------------------------------------------------------------------------
# Django REST Framework Throttling
# ------------------------------------------------------------------------------

REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = [  # noqa: F405
    "rest_framework.throttling.AnonRateThrottle",
    "rest_framework.throttling.UserRateThrottle",
    "rest_framework.throttling.ScopedRateThrottle",
]

REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {  # noqa: F405
    "anon": "100/hour",
    "user": "1000/hour",
    "login": "10/minute",
    "register": "5/hour",
    "password_reset": "5/hour",
    "email_verify": "10/hour",
}


# Establish safe, isolated directory layouts for live storage tracking
PRODUCTION_LOG_DIR = os.path.join(BASE_DIR, "var", "log", "django")  # noqa: F405
if not os.path.exists(PRODUCTION_LOG_DIR):
    os.makedirs(PRODUCTION_LOG_DIR)

# MULTI-ROUTING COMPREHENSIVE PRODUCTION LOGGING STRUCTURE
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "production_grade_verbose": {
            "format": "[{asctime}] {levelname} | Component: {name} | Trace: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "production_standard_stdout": {
            "class": "logging.StreamHandler",
            "formatter": "production_grade_verbose",
        },
        "rotating_file_application_errors": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(PRODUCTION_LOG_DIR, "application_errors.log"),
            "maxBytes": 1024 * 1024 * 10,  # 10 Megabytes max per file segment block
            "backupCount": 5,  # Archives up to 5 history files automatically
            "formatter": "production_grade_verbose",
        },
        "rotating_file_security_telemetry": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(PRODUCTION_LOG_DIR, "security_metrics.log"),
            "maxBytes": 1024 * 1024 * 5,  # 5 Megabytes max per file segment block
            "backupCount": 3,  # Archives up to 3 history files automatically
            "formatter": "production_grade_verbose",
        },
    },
    "loggers": {
        # General HTTP requests route directly to stdout for live metrics
        "django.server": {
            "handlers": ["production_standard_stdout"],
            "level": "INFO",
            "propagate": False,
        },
        # Core system error crashes hit BOTH live stdout and your file archives
        "django.request": {
            "handlers": [
                "production_standard_stdout",
                "rotating_file_application_errors",
            ],
            "level": "ERROR",
            "propagate": False,
        },
        # Rate-limiting actions and security warnings hit BOTH stdout and security files
        "security": {
            "handlers": [
                "production_standard_stdout",
                "rotating_file_security_telemetry",
            ],
            "level": "WARNING",
            "propagate": False,
        },
    },
}
