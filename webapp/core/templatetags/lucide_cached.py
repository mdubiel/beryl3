"""
Cached lucide icon template tag for better performance.

The standard lucide template tag performs XML parsing, deep copying, and
string conversion for every icon call. With 13 icons per item card × 25 items,
this adds up to 325 icon renders per page, taking ~50ms per item.

This cached version pre-renders common icon combinations and caches them.
"""
from django import template
from django.core.cache import cache
from functools import lru_cache
import hashlib

register = template.Library()

# Import the original lucide function
try:
    from lucide.templatetags.lucide import lucide as original_lucide
except ImportError:
    original_lucide = None


def _make_cache_key(name: str, size: int, **kwargs) -> str:
    """Create a cache key for an icon with specific parameters"""
    # Sort kwargs for consistent key generation
    kwargs_str = ''.join(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_str = f"lucide_icon:{name}:{size}:{kwargs_str}"
    # Hash to keep key length reasonable
    return f"lucide:{hashlib.md5(key_str.encode()).hexdigest()}"


@lru_cache(maxsize=1000)
def _render_cached_icon(name: str, size: int, kwargs_tuple: tuple) -> str:
    """
    Cached icon rendering with LRU cache.
    Uses tuple for kwargs because dicts aren't hashable.
    """
    if not original_lucide:
        return f"[{name}]"

    # Convert tuple back to dict
    kwargs = dict(kwargs_tuple)

    # Call original lucide function
    return original_lucide(name, size=size, **kwargs)


@register.simple_tag
def lucide_cached(name: str, *, size: int = 24, **kwargs) -> str:
    """
    Cached version of lucide icon rendering.

    Usage: {% lucide_cached 'icon-name' size=20 class='text-primary' %}

    This version caches rendered SVG output for faster template rendering.
    Common icons like 'star', 'tag', 'bookmark' are cached in memory.
    """
    # Convert kwargs to tuple for hashing
    kwargs_tuple = tuple(sorted(kwargs.items()))

    # Try in-memory LRU cache first (fastest)
    return _render_cached_icon(name, size, kwargs_tuple)


@register.simple_tag
def lucide_static(name: str, *, size: int = 24, **kwargs) -> str:
    """
    Alternative: Return a placeholder that can be replaced client-side.
    Fastest option but requires JavaScript.

    Usage: {% lucide_static 'icon-name' size=20 class='text-primary' %}

    Returns: <i data-lucide="icon-name" data-size="20" class="text-primary"></i>

    Requires: lucide.js or similar client-side icon library to replace placeholders
    """
    attrs = ' '.join(f'{k.replace("_", "-")}="{v}"' for k, v in kwargs.items())
    return f'<i data-lucide="{name}" data-size="{size}" {attrs}></i>'


# Alias for backward compatibility
lucide = lucide_cached
