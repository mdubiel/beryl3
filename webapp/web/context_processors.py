"""
Context processors for the web application.
"""
import hashlib
from pathlib import Path
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
        'EXTERNAL_LOKI_URL': getattr(settings, 'EXTERNAL_LOKI_URL', None),
        'EXTERNAL_GRAFANA_URL': getattr(settings, 'EXTERNAL_GRAFANA_URL', None),
        'EXTERNAL_RESEND_URL': getattr(settings, 'EXTERNAL_RESEND_URL', None),
        'EXTERNAL_REGISTRY_URL': getattr(settings, 'EXTERNAL_REGISTRY_URL', None),
        'SITE_DOMAIN': getattr(settings, 'SITE_DOMAIN', 'beryl3.localdomain'),
        'ALLOW_USER_REGISTRATION': getattr(settings, 'ALLOW_USER_REGISTRATION', False),
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


def app_version(request):
    """
    Add application version to template context.
    Reads version from VERSION file in the project root.
    """
    try:
        version_file = Path(settings.BASE_DIR) / 'VERSION'
        if version_file.exists():
            content = version_file.read_text().strip()
            # Parse VERSION file format: MAJOR=x MINOR=y BUILD=z
            version_parts = {}
            for line in content.split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    version_parts[key.strip()] = value.strip()
            
            major = version_parts.get('MAJOR', '0')
            minor = version_parts.get('MINOR', '0')  
            build = version_parts.get('BUILD', '0')
            
            return {
                'APP_VERSION': f"{major}.{minor}.{build}",
                'APP_VERSION_MAJOR': major,
                'APP_VERSION_MINOR': minor,
                'APP_VERSION_BUILD': build,
            }
    except Exception:
        pass
    
    return {
        'APP_VERSION': 'dev',
        'APP_VERSION_MAJOR': '0',
        'APP_VERSION_MINOR': '0',
        'APP_VERSION_BUILD': '0',
    }