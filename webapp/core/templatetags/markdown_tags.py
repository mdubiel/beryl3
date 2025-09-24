"""
Template filters for secure markdown rendering
"""
import markdown
import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Allowed HTML tags for secure markdown rendering
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'code', 'pre', 
    'ul', 'ol', 'li', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'a', 'hr'
]

# Allowed attributes for HTML tags
ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
    'code': ['class'],
    'pre': ['class'],
}

# Allowed protocols for links
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

@register.filter
def markdown_safe(value):
    """
    Convert markdown to HTML with security restrictions.
    Only allows safe HTML tags and attributes.
    """
    if not value:
        return ""
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra', 'codehilite'])
    html = md.convert(str(value))
    
    # Sanitize HTML to only allow safe tags and attributes
    clean_html = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )
    
    return mark_safe(clean_html)

@register.filter  
def markdown_inline(value):
    """
    Convert markdown to inline HTML (no block elements like p, h1-h6).
    Useful for short descriptions and activity messages.
    """
    if not value:
        return ""
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['extra'])
    html = md.convert(str(value))
    
    # Only allow inline tags
    inline_tags = ['strong', 'b', 'em', 'i', 'u', 'code', 'a']
    
    clean_html = bleach.clean(
        html,
        tags=inline_tags,
        attributes={'a': ['href', 'title']},
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )
    
    # Remove paragraph tags if they wrap the entire content
    if clean_html.startswith('<p>') and clean_html.endswith('</p>') and clean_html.count('<p>') == 1:
        clean_html = clean_html[3:-4]
    
    return mark_safe(clean_html)