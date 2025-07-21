# -*- coding: utf-8 -*-

"""
Tests for the Lucide Icons utility module.
"""

from django.test import TestCase
from core.lucide import LucideIcons, is_valid_lucide_icon, validate_lucide_icon


class LucideIconsTest(TestCase):
    """Test cases for the LucideIcons utility class."""
    
    def test_is_valid_with_valid_icons(self):
        """Test validation with valid icon names."""
        valid_icons = ['book', 'user', 'settings', 'home', 'star']
        for icon in valid_icons:
            self.assertTrue(LucideIcons.is_valid(icon))
    
    def test_is_valid_with_invalid_icons(self):
        """Test validation with invalid icon names."""
        invalid_icons = ['invalid-icon', 'nonexistent', 'fake-icon']
        for icon in invalid_icons:
            self.assertFalse(LucideIcons.is_valid(icon))
    
    def test_is_valid_with_empty_or_none(self):
        """Test validation with empty or None values."""
        self.assertTrue(LucideIcons.is_valid(''))
        self.assertTrue(LucideIcons.is_valid(None))
        self.assertTrue(LucideIcons.is_valid('   '))  # whitespace only
    
    def test_is_valid_case_insensitive(self):
        """Test that validation is case insensitive."""
        self.assertTrue(LucideIcons.is_valid('BOOK'))
        self.assertTrue(LucideIcons.is_valid('Book'))
        self.assertTrue(LucideIcons.is_valid('bOoK'))
    
    def test_validate_method(self):
        """Test the validate method returns proper tuple."""
        # Valid icon
        is_valid, error = LucideIcons.validate('book')
        self.assertTrue(is_valid)
        self.assertIsNone(error)
        
        # Invalid icon
        is_valid, error = LucideIcons.validate('invalid-icon')
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
        self.assertIn('Invalid icon name', error)
        self.assertIn('lucide.dev', error)
    
    def test_get_validation_error(self):
        """Test getting validation error messages."""
        # Valid icon should return None
        self.assertIsNone(LucideIcons.get_validation_error('book'))
        
        # Invalid icon should return error message
        error = LucideIcons.get_validation_error('invalid-icon')
        self.assertIsNotNone(error)
        self.assertIn('Invalid icon name', error)
    
    def test_get_all_icons(self):
        """Test getting all icons."""
        icons = LucideIcons.get_all_icons()
        self.assertIsInstance(icons, set)
        self.assertGreater(len(icons), 100)  # Should have many icons
        self.assertIn('book', icons)
        self.assertIn('user', icons)
    
    def test_get_icons_list(self):
        """Test getting icons as a list."""
        # Unsorted list
        icons = LucideIcons.get_icons_list(sorted=False)
        self.assertIsInstance(icons, list)
        self.assertGreater(len(icons), 100)
        
        # Sorted list
        sorted_icons = LucideIcons.get_icons_list(sorted=True)
        self.assertEqual(sorted(icons), sorted_icons)
    
    def test_search_icons(self):
        """Test searching for icons."""
        # Search for 'user' related icons
        user_icons = LucideIcons.search_icons('user')
        self.assertIn('user', user_icons)
        self.assertIn('user-plus', user_icons)
        self.assertIn('users', user_icons)
        
        # Empty search should return empty list
        empty_result = LucideIcons.search_icons('')
        self.assertEqual(empty_result, [])
    
    def test_get_suggestions(self):
        """Test getting icon suggestions."""
        suggestions = LucideIcons.get_suggestions('usr')  # typo for 'user'
        self.assertIsInstance(suggestions, list)
        self.assertTrue(any('user' in icon for icon in suggestions))
        
        # Limit should work
        limited_suggestions = LucideIcons.get_suggestions('arrow', limit=3)
        self.assertLessEqual(len(limited_suggestions), 3)
    
    def test_get_stats(self):
        """Test getting statistics."""
        stats = LucideIcons.get_stats()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_icons', stats)
        self.assertGreater(stats['total_icons'], 100)
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly."""
        # is_valid_lucide_icon
        self.assertTrue(is_valid_lucide_icon('book'))
        self.assertFalse(is_valid_lucide_icon('invalid'))
        
        # validate_lucide_icon
        is_valid, error = validate_lucide_icon('book')
        self.assertTrue(is_valid)
        self.assertIsNone(error)