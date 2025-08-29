# -*- coding: utf-8 -*-

"""
Lucide Icons Utility

This module provides a centralized way to validate Lucide icon names
used throughout the application. It contains a comprehensive list of
available Lucide icons and provides validation methods.

Usage:
    from core.lucide import LucideIcons
    
    # Validate an icon name
    if LucideIcons.is_valid('book'):
        print("Valid icon!")
    
    # Get all available icons
    icons = LucideIcons.get_all_icons()
    
    # Get validation error message
    error = LucideIcons.get_validation_error('invalid-icon')
"""

import logging

logger = logging.getLogger('webapp')


class LucideIcons:
    """
    Utility class for Lucide icon validation and management.
    
    This class provides methods to validate Lucide icon names against
    a comprehensive list of available icons. It's designed to be used
    throughout the application wherever icon validation is needed.
    """
    
    # Comprehensive list of Lucide icon names
    # Based on Lucide v0.400+ icon set
    _VALID_ICONS = {
        # Navigation & Interface
        'arrow-down', 'arrow-left', 'arrow-right', 'arrow-up', 'chevron-down', 'chevron-left', 
        'chevron-right', 'chevron-up', 'menu', 'ellipsis', 'x', 'x-circle',
        'x-octagon', 'x-square', 'plus', 'plus-circle', 'plus-square', 'minus', 'check', 
        'check-circle', 'external-link', 'link', 'link-2',
        
        # Content & Media
        'book', 'book-key', 'bookmark', 'file', 'file-text', 'folder', 'folder-open', 'image', 'video', 
        'video-off', 'music', 'headphones', 'disc', 'film', 'camera', 'mic', 'mic-off',
        'volume', 'volume-1', 'volume-2', 'volume-x', 'play', 'play-circle', 'pause', 
        'pause-circle', 'stop-circle', 'skip-back', 'skip-forward', 'fast-forward', 'rewind',
        
        # Communication
        'mail', 'message-circle', 'message-square', 'phone', 'phone-call', 'phone-forwarded',
        'phone-incoming', 'phone-missed', 'phone-off', 'phone-outgoing', 'send', 'share',
        'share-2', 'at-sign', 'bell', 'rss',
        
        # User & Account
        'user', 'user-check', 'user-minus', 'user-plus', 'user-x', 'users', 'crown', 'shield',
        'shield-off', 'key', 'lock', 'lock-open', 'unlock', 'log-in', 'log-out',
        
        # System & Settings
        'settings', 'tool', 'cog', 'sliders', 'command', 'terminal', 'cpu', 'server', 'database',
        'hard-drive', 'wifi', 'wifi-off', 'bluetooth', 'cast', 'radio', 'power', 'zap', 'zap-off',
        
        # Shopping & Commerce
        'shopping-bag', 'shopping-cart', 'credit-card', 'dollar-sign', 'tag', 'gift', 'package',
        'box', 'truck', 'award',
        
        # Location & Navigation
        'map', 'map-pin', 'compass', 'navigation', 'navigation-2', 'globe', 'home', 'building',
        
        # Time & Calendar
        'clock', 'calendar', 'sunrise', 'sunset', 'sun', 'moon', 'watch',
        
        # Weather & Nature
        'cloud', 'umbrella', 'wind', 'thermometer', 'droplets',
        
        # Gaming & Entertainment
        'gamepad-2', 'dice-1', 'dice-2', 'dice-3', 'dice-4', 'dice-5', 'dice-6', 'puzzle',
        
        # Actions & Tools
        'edit', 'edit-2', 'edit-3', 'pencil', 'pen-tool', 'scissors', 'copy', 'clipboard',
        'save', 'download', 'upload', 'upload-cloud', 'refresh-ccw', 'refresh-cw', 'rotate-ccw',
        'rotate-cw', 'repeat', 'shuffle', 'trash', 'trash-2', 'delete', 'archive', 'search',
        'filter', 'sort-asc', 'sort-desc',
        
        # Layout & Design
        'layout', 'grid', 'list', 'columns', 'rows', 'sidebar', 'align-left', 'align-center',
        'align-right', 'align-justify', 'bold', 'italic', 'underline', 'type',
        
        # Status & Feedback
        'info', 'help-circle', 'alert-circle', 'alert-triangle', 'alert-octagon', 'activity',
        'loader', 'target', 'crosshair', 'eye', 'eye-off', 'heart', 'star', 'flag',
        
        # Geometry & Shapes
        'circle', 'square', 'triangle', 'octagon', 'diamond', 'hexagon',
        
        # Social Media
        'facebook', 'twitter', 'instagram', 'linkedin', 'youtube', 'github', 'slack',
        
        # Transportation
        'car', 'plane', 'train', 'bike', 'bus',
        
        # Business & Work
        'briefcase', 'building-2', 'factory', 'store', 'office-building',
        
        # Health & Medical
        'heart-pulse', 'pill', 'syringe', 'stethoscope', 'cross',
        
        # Miscellaneous
        'anchor', 'coffee', 'utensils', 'wine', 'beer', 'ice-cream', 'pizza',
        'smartphone', 'tablet', 'laptop', 'monitor', 'tv', 'keyboard', 'mouse-pointer',
        'printer', 'scanner', 'projector', 'speaker', 'battery', 'plug',
    }
    
    @classmethod
    def is_valid(cls, icon_name):
        """
        Check if the provided icon name is valid.
        
        Args:
            icon_name (str): The icon name to validate
            
        Returns:
            bool: True if the icon name is valid or empty, False otherwise
        """
        if not icon_name:
            return True  # Empty icon names are allowed
        
        # Convert to lowercase for case-insensitive comparison
        return icon_name.lower().strip() in cls._VALID_ICONS
    
    @classmethod
    def validate(cls, icon_name):
        """
        Validate an icon name and return validation result.
        
        Args:
            icon_name (str): The icon name to validate
            
        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if cls.is_valid(icon_name):
            return True, None
        
        error_message = (
            f"Invalid icon name '{icon_name}'. Please use a valid Lucide icon name. "
            f"See https://lucide.dev/icons/ for available options."
        )
        return False, error_message
    
    @classmethod
    def get_validation_error(cls, icon_name):
        """
        Get validation error message for an invalid icon name.
        
        Args:
            icon_name (str): The icon name that failed validation
            
        Returns:
            str: Error message, or None if icon is valid
        """
        is_valid, error_message = cls.validate(icon_name)
        return error_message if not is_valid else None
    
    @classmethod
    def get_all_icons(cls):
        """
        Get all available icon names.
        
        Returns:
            set: Set of all valid icon names
        """
        return cls._VALID_ICONS.copy()
    
    @classmethod
    def get_icons_list(cls, sorted=True):
        """
        Get all available icon names as a list.
        
        Args:
            sorted (bool): Whether to return sorted list
            
        Returns:
            list: List of all valid icon names
        """
        icons = list(cls._VALID_ICONS)
        return sorted(icons) if sorted else icons
    
    @classmethod
    def search_icons(cls, query):
        """
        Search for icons matching the query.
        
        Args:
            query (str): Search term
            
        Returns:
            list: List of matching icon names
        """
        if not query:
            return []
        
        query = query.lower().strip()
        matching_icons = [
            icon for icon in cls._VALID_ICONS 
            if query in icon
        ]
        return sorted(matching_icons)
    
    @classmethod
    def get_suggestions(cls, icon_name, limit=5):
        """
        Get suggestions for similar icon names.
        
        Args:
            icon_name (str): The invalid icon name
            limit (int): Maximum number of suggestions
            
        Returns:
            list: List of suggested icon names
        """
        if not icon_name:
            return []
        
        query = icon_name.lower().strip()
        
        # Find icons that contain parts of the query
        suggestions = []
        
        # Exact partial matches first
        for icon in cls._VALID_ICONS:
            if query in icon:
                suggestions.append(icon)
        
        # If not enough suggestions, look for similar patterns
        if len(suggestions) < limit:
            query_parts = query.replace('-', ' ').split()
            for icon in cls._VALID_ICONS:
                if icon not in suggestions:
                    icon_parts = icon.replace('-', ' ').split()
                    if any(part in icon_parts for part in query_parts):
                        suggestions.append(icon)
        
        return sorted(suggestions)[:limit]
    
    @classmethod
    def get_stats(cls):
        """
        Get statistics about the icon set.
        
        Returns:
            dict: Dictionary with statistics
        """
        return {
            'total_icons': len(cls._VALID_ICONS),
            'categories_estimated': len([
                icon for icon in cls._VALID_ICONS 
                if any(cat in icon for cat in ['user', 'file', 'arrow', 'play', 'settings'])
            ]),
        }


# Convenience functions for backward compatibility and ease of use
def is_valid_lucide_icon(icon_name):
    """Convenience function to check if an icon name is valid."""
    return LucideIcons.is_valid(icon_name)


def validate_lucide_icon(icon_name):
    """Convenience function to validate an icon name."""
    return LucideIcons.validate(icon_name)


def get_lucide_validation_error(icon_name):
    """Convenience function to get validation error message."""
    return LucideIcons.get_validation_error(icon_name)