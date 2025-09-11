"""
Context processors for the web application.
"""
import hashlib
from urllib.parse import urlencode
from django.conf import settings


def external_services(request):
    """
    Add external services URLs and system settings to the template context.
    
    This makes external service URLs and system configuration available globally 
    across all templates that need them, rather than manually adding them to 
    individual view contexts.
    """
    return {
        'EXTERNAL_DB_URL': getattr(settings, 'EXTERNAL_DB_URL', None),
        'EXTERNAL_INBUCKET_URL': getattr(settings, 'EXTERNAL_INBUCKET_URL', None),
        'EXTERNAL_MONITORING_URL': getattr(settings, 'EXTERNAL_MONITORING_URL', None),
        'EXTERNAL_SENTRY_URL': getattr(settings, 'EXTERNAL_SENTRY_URL', None),
        'EXTERNAL_LOKI_URL': getattr(settings, 'EXTERNAL_LOKI_URL', None),
        'EXTERNAL_GRAFANA_URL': getattr(settings, 'EXTERNAL_GRAFANA_URL', None),
    }


def gravatar_url(email, size=32, default='identicon'):
    """
    Generate a gravatar URL for the given email address.
    
    Args:
        email: The email address to generate gravatar for
        size: The size of the avatar (default: 32px)
        default: The default avatar type if no gravatar exists (default: 'identicon')
    
    Returns:
        The gravatar URL string
    """
    if not email:
        email = ''
    
    # Create the MD5 hash of the email address
    email_hash = hashlib.md5(email.lower().encode('utf-8')).hexdigest()
    
    # Build the gravatar URL
    params = {
        's': str(size),
        'd': default,
    }
    
    return f"https://www.gravatar.com/avatar/{email_hash}?{urlencode(params)}"


def user_avatar(request):
    """
    Add user avatar URL to template context.
    """
    context = {}
    if request.user.is_authenticated:
        context['user_avatar_url'] = gravatar_url(request.user.email, size=32)
    return context