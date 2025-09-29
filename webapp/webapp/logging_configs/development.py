"""
Development logging configuration for beryl3.
All logs go to console with appropriate formatting for development debugging.
"""
import os

def get_logging_config(base_dir):
    """
    Returns logging configuration for development environment.
    All logs are sent to console with different levels and formatting.
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "user_info": {
                "()": "webapp.logging_middleware.RequestUserInfoFilter",
            }
        },
        "formatters": {
            "verbose": {
                "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
                "style": "{",
            },
            "simple": {
                "format": "{levelname} {message}",
                "style": "{",
            },
            "minimal": {
                "format": "{message}",
                "style": "{",
            },
            "development": {
                "format": "🔧 {levelname} | {name} | {message}",
                "style": "{",
            },
            "webapp_dev": {
                "format": "📱 {levelname} | {module}.{funcName} | {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler", 
                "formatter": "development",
                "level": "INFO",
            },
            "console_webapp": {
                "class": "logging.StreamHandler", 
                "formatter": "webapp_dev",
                "level": "INFO",
            },
            "console_simple": {
                "class": "logging.StreamHandler", 
                "formatter": "simple",
                "level": "WARNING",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console_simple"],
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "webapp": {
                "handlers": ["console_webapp"],
                "level": "INFO",
                "propagate": False,
            },
            "web": {
                "handlers": ["console_webapp"],
                "level": "INFO", 
                "propagate": False,
            },
            "performance": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            # Suppress verbose extension loading messages
            "markdown.extensions": {
                "level": "WARNING",
                "propagate": False,
            },
            # Reduce template noise
            "django.template": {
                "level": "WARNING",
                "propagate": True,
            },
            # Reduce migration noise
            "django.db.migrations": {
                "level": "WARNING",
                "propagate": True,
            },
        },
    }