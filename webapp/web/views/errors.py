"""
Task 56: Custom error page views
"""
from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)


def bad_request(request, exception=None):
    """Handle 400 Bad Request errors."""
    logger.warning(
        'bad_request: 400 error',
        extra={
            'function': 'bad_request',
            'path': request.path,
            'method': request.method,
            'user': request.user.username if request.user.is_authenticated else 'anonymous'
        }
    )
    return render(request, 'errors/400.html', status=400)


def permission_denied(request, exception=None):
    """Handle 403 Permission Denied errors."""
    logger.warning(
        'permission_denied: 403 error',
        extra={
            'function': 'permission_denied',
            'path': request.path,
            'method': request.method,
            'user': request.user.username if request.user.is_authenticated else 'anonymous',
            'exception': str(exception) if exception else None
        }
    )
    context = {
        'exception': exception
    }
    return render(request, 'errors/403.html', context, status=403)


def page_not_found(request, exception=None):
    """Handle 404 Page Not Found errors."""
    logger.info(
        'page_not_found: 404 error',
        extra={
            'function': 'page_not_found',
            'path': request.path,
            'method': request.method,
            'user': request.user.username if request.user.is_authenticated else 'anonymous'
        }
    )
    context = {
        'request_path': request.path
    }
    return render(request, 'errors/404.html', context, status=404)


def server_error(request):
    """Handle 500 Internal Server Error."""
    logger.error(
        'server_error: 500 error',
        extra={
            'function': 'server_error',
            'path': request.path,
            'method': request.method,
            'user': request.user.username if request.user.is_authenticated else 'anonymous'
        },
        exc_info=True
    )
    return render(request, 'errors/500.html', status=500)
