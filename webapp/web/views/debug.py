# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring

import logging
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_safe
import sentry_sdk

logger = logging.getLogger("webapp")


@require_safe
def sentry_test(request):
    """
    Debug endpoint to test Sentry integration.
    Only available in DEBUG mode.
    """
    if not settings.DEBUG:
        return JsonResponse({'error': 'Debug endpoint only available in DEBUG mode'}, status=404)
    
    try:
        # Log some breadcrumbs
        logger.info("Sentry test endpoint accessed by user: %s", request.user.email if request.user.is_authenticated else 'Anonymous')
        
        # Debug Sentry configuration
        sentry_dsn = getattr(settings, 'SENTRY_DSN', None)
        logger.info("Sentry DSN configured: %s", sentry_dsn)
        logger.info("Sentry SDK client: %s", sentry_sdk.Hub.current.client)
        
        # Test Sentry connectivity - try direct event capture
        try:
            event_id = sentry_sdk.capture_message("Manual Sentry test from debug endpoint", level="info")
            logger.info("Sentry message captured successfully with event ID: %s", event_id)
        except Exception as e:
            logger.error("Failed to capture Sentry message: %s", str(e))
        
        # Test Sentry connectivity
        sentry_sdk.add_breadcrumb(message="Sentry test endpoint accessed", level="info")
        
        # Intentional error to test Sentry
        test_type = request.GET.get('type', 'division_by_zero')
        
        if test_type == 'division_by_zero':
            # Test basic error reporting
            result = 1 / 0  # This will trigger a ZeroDivisionError
        elif test_type == 'key_error':
            # Test KeyError
            test_dict = {}
            result = test_dict['nonexistent_key']
        elif test_type == 'custom_error':
            # Test custom exception
            raise ValueError("This is a test error for Sentry integration")
        else:
            return JsonResponse({
                'error': 'Invalid test type', 
                'available_types': ['division_by_zero', 'key_error', 'custom_error']
            }, status=400)
            
        return JsonResponse({'result': result})
        
    except Exception as e:
        logger.error("Sentry test error occurred: %s", str(e))
        # Re-raise to let Sentry catch it
        raise