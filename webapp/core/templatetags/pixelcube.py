"""
Django template tags for pixel cube generation.
"""

from django import template
from django.utils.safestring import mark_safe
from ..pixelcube import pixelcube_to_base64

register = template.Library()

@register.simple_tag
def pixelcube(size='m', color=None, pattern='random', css_class='', alt='Pixel Cube', 
             cube_count=None, min_cubes=1, max_cubes=10, background='transparent', **kwargs):
    """
    Django template tag for generating pixel cube images.
    
    Usage:
        {% pixelcube size='l' color='#FF0000' pattern='gradient' css_class='my-cube' %}
        {% pixelcube 'm' cube_count=5 background='palette' %}
        {% pixelcube size='xl' pattern='mixed' min_cubes=3 max_cubes=7 %}
    """
    # Generate image data URL
    data_url = pixelcube_to_base64(size, color, pattern, 'PNG', 
                                  cube_count, min_cubes, max_cubes, background)
    
    # Build HTML attributes
    attributes = []
    if css_class:
        attributes.append(f'class="{css_class}"')
    if alt:
        attributes.append(f'alt="{alt}"')
    
    # Add any additional attributes
    for key, value in kwargs.items():
        # Convert underscores to hyphens for HTML attributes
        attr_name = key.replace('_', '-')
        attributes.append(f'{attr_name}="{value}"')
    
    attrs_str = ' '.join(attributes)
    
    # Return HTML img tag
    return mark_safe(f'<img src="{data_url}" {attrs_str}>')


@register.simple_tag
def pixelcube_url(size='m', color=None, pattern='random', cube_count=None, 
                 min_cubes=1, max_cubes=10, background='transparent'):
    """
    Django template tag that returns just the data URL.
    
    Usage:
        <img src="{% pixelcube_url size='l' color='#00FF00' cube_count=3 %}">
    """
    return pixelcube_to_base64(size, color, pattern, 'PNG', 
                              cube_count, min_cubes, max_cubes, background)