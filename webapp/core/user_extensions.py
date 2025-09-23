"""
User model extensions
"""
from django.contrib.auth import get_user_model


def display_name(self):
    """
    Returns the user's display name based on their preferences:
    1. Nickname (if use_nickname is True and nickname exists)
    2. First name (if available)
    3. Email (fallback)
    """
    # Check if user has a profile and nickname preference
    if hasattr(self, 'profile'):
        profile = self.profile
        if profile.use_nickname and profile.nickname and profile.nickname.strip():
            return profile.nickname.strip()
    
    # Fallback to first name
    if self.first_name and self.first_name.strip():
        return self.first_name.strip()
    
    # Final fallback to email
    return self.email if self.email else ""


# Add the method to the User model
User = get_user_model()
User.add_to_class('display_name', display_name)