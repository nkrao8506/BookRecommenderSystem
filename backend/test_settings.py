"""
Test settings - disables DEBUG and logging to avoid Python 3.14 compatibility issues
with Django 4.2 template context copying during error logging.
"""

from backend.settings import *  # noqa: F401, F403

# Disable DEBUG for tests to avoid template context copying issues
DEBUG = False
TEMPLATE_DEBUG = False

# Use in-memory database for faster tests
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Completely disable logging during tests to prevent Python 3.14 compatibility issues
# with Django 4.2's debug template context copying
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
    "loggers": {
        "django": {
            "handlers": ["null"],
            "level": "CRITICAL",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["null"],
            "level": "CRITICAL",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["null"],
            "level": "CRITICAL",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["null"],
            "level": "CRITICAL",
            "propagate": False,
        },
    },
}
