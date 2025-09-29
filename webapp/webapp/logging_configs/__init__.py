"""
Logging configuration modules for beryl3.

This package contains environment-specific logging configurations:
- development.py: Console-based logging for local development
- preprod.py: File-based logging for preproduction environment

Each module provides a get_logging_config(base_dir) function that returns
a complete Django logging configuration dictionary.
"""