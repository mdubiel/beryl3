from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def media_url(context, media_file):
    """
    Get the appropriate URL for a media file based on content moderation status.
    For user-facing content, returns error image for flagged content.
    For SYS admin views, always returns the actual file URL.
    
    Usage: {% media_url image %}
    """
    if not media_file:
        return ""
    
    request = context.get('request')
    return media_file.get_user_safe_url(request)


@register.simple_tag
def admin_media_url(media_file):
    """
    Always get the actual file URL regardless of moderation status.
    Use this in admin/SYS templates where you want to see the actual content.
    
    Usage: {% admin_media_url image %}
    """
    if not media_file:
        return ""
    
    return media_file.file_url