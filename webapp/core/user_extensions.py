"""
User model extensions
"""
from django.contrib.auth import get_user_model


def display_name(self):
    """
    Returns the user's first name if available, otherwise returns their email.
    """
    if self.first_name and self.first_name.strip():
        return self.first_name.strip()
    
    return self.email if self.email else ""


# Add the method to the User model
User = get_user_model()
User.add_to_class('display_name', display_name)