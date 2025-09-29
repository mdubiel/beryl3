"""
Preprod logging configuration for beryl3.
All logs go to separate files in the logs/ directory with rotating file handlers.
"""
import os
from pathlib import Path

def get_logging_config(base_dir):
    """
    Returns logging configuration for preprod environment.
    All logs are sent to separate rotating files in logs/ directory.
    """
    # Ensure logs directory exists
    logs_dir = Path(base_dir) / 'logs'
    os.makedirs(logs_dir, exist_ok=True)
    
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
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            },
            "webapp_json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(user)s %(path)s %(message)s",
            },
        },
        "handlers": {
            # Django framework logs
            "django_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "django.log",
                "maxBytes": 1024 * 1024 * 15,  # 15MB
                "backupCount": 10,
                "formatter": "verbose",
                "level": "INFO",
            },
            # Web application logs
            "web_file": {
                "class": "logging.handlers.RotatingFileHandler", 
                "filename": logs_dir / "web.log",
                "maxBytes": 1024 * 1024 * 15,  # 15MB
                "backupCount": 10,
                "formatter": "verbose",
                "level": "INFO",
            },
            # Security-related logs
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "security.log",
                "maxBytes": 1024 * 1024 * 15,  # 15MB
                "backupCount": 10,
                "formatter": "verbose",
                "level": "INFO",
            },
            # Database query logs (debug level)
            "db_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "db.log",
                "maxBytes": 1024 * 1024 * 15,  # 15MB
                "backupCount": 5,
                "formatter": "verbose",
                "level": "DEBUG",
            },
            # Performance monitoring logs
            "performance_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "performance.jsonl",
                "maxBytes": 1024 * 1024 * 15,  # 15MB
                "backupCount": 5,
                "formatter": "json",
                "level": "INFO",
            },
            # Webapp structured logs with user info
            "webapp_json_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": logs_dir / "webapp.jsonl",
                "maxBytes": 1024 * 1024 * 15,  # 15MB
                "backupCount": 5,
                "formatter": "webapp_json",
                "filters": ["user_info"],
                "level": "INFO",
            },
            # Console fallback for critical errors
            "console": {
                "class": "logging.StreamHandler", 
                "formatter": "simple",
                "level": "ERROR",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
        "loggers": {
            "django": {
                "handlers": ["django_file"],
                "level": "INFO",
                "propagate": False,
            },
            "django.security": {
                "handlers": ["security_file"],
                "level": "INFO",
                "propagate": False,
            },
            "django.db.backends": {
                "handlers": ["db_file"],
                "level": "INFO",  # Set to DEBUG to capture queries
                "propagate": False,
            },
            "web": {
                "handlers": ["web_file"],
                "level": "INFO",
                "propagate": False,
            },
            "webapp": {
                "handlers": ["webapp_json_file"],
                "level": "INFO", 
                "propagate": False,
            },
            "performance": {
                "handlers": ["performance_file"],
                "level": "INFO",
                "propagate": False,
            },
            # Suppress verbose extension loading messages
            "markdown.extensions": {
                "level": "WARNING",
                "propagate": False,
            },
            # Reduce template noise in files
            "django.template": {
                "level": "WARNING",
                "propagate": True,
            },
        },
    }