"""
Resend API service for managing marketing email audiences
"""
import logging
import requests
from django.conf import settings
from django.utils import timezone
from typing import Optional, Dict, Any

logger = logging.getLogger("webapp")


class ResendService:
    """
    Service for managing Resend audience subscriptions for marketing emails
    """
    
    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.audience_id = settings.RESEND_MARKETING_AUDIENCE_ID
        self.base_url = "https://api.resend.com"
        
        if not self.api_key:
            logger.warning("RESEND_API_KEY not configured. Marketing email features will be disabled.")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict[str, Any]]:
        """
        Make an authenticated request to Resend API
        """
        if not self.api_key:
            logger.error("Resend API key not configured")
            return None
            
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(method, url, headers=headers, json=data, timeout=30)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"Resend API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Resend API request failed: {str(e)}")
            return None
    
    def subscribe_to_audience(self, email: str, first_name: str = "", last_name: str = "") -> bool:
        """
        Subscribe an email to the marketing audience
        
        Args:
            email: Email address to subscribe
            first_name: User's first name (optional)
            last_name: User's last name (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.api_key or not self.audience_id:
            logger.warning("Resend not configured, skipping audience subscription")
            return False
        
        data = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "unsubscribed": False
        }
        
        endpoint = f"/audiences/{self.audience_id}/contacts"
        result = self._make_request("POST", endpoint, data)
        
        if result:
            logger.info(f"Successfully subscribed {email} to Resend audience {self.audience_id}")
            return True
        else:
            logger.error(f"Failed to subscribe {email} to Resend audience")
            return False
    
    def unsubscribe_from_audience(self, email: str) -> bool:
        """
        Unsubscribe an email from the marketing audience
        
        Args:
            email: Email address to unsubscribe
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.api_key or not self.audience_id:
            logger.warning("Resend not configured, skipping audience unsubscription")
            return False
        
        # First, get the contact to find their ID
        contact = self.get_contact_by_email(email)
        if not contact:
            logger.warning(f"Contact {email} not found in audience, considering unsubscribe successful")
            return True
        
        contact_id = contact.get('id')
        if not contact_id:
            logger.error(f"No contact ID found for {email}")
            return False
        
        # Remove the contact from the audience
        endpoint = f"/audiences/{self.audience_id}/contacts/{contact_id}"
        result = self._make_request("DELETE", endpoint)
        
        if result is not None:  # DELETE returns no content on success
            logger.info(f"Successfully unsubscribed {email} from Resend audience {self.audience_id}")
            return True
        else:
            logger.error(f"Failed to unsubscribe {email} from Resend audience")
            return False
    
    def get_contact_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get contact information by email address
        
        Args:
            email: Email address to search for
            
        Returns:
            Dict containing contact info if found, None otherwise
        """
        if not self.api_key or not self.audience_id:
            return None
        
        endpoint = f"/audiences/{self.audience_id}/contacts"
        result = self._make_request("GET", endpoint)
        
        if result and 'data' in result:
            for contact in result['data']:
                if contact.get('email') == email:
                    return contact
        
        return None
    
    def is_email_in_audience(self, email: str) -> bool:
        """
        Check if an email is currently in the marketing audience
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if email is in audience, False otherwise
        """
        contact = self.get_contact_by_email(email)
        return contact is not None and not contact.get('unsubscribed', False)
    
    def get_audience_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get statistics about the marketing audience
        
        Returns:
            Dict containing audience stats if successful, None otherwise
        """
        if not self.api_key or not self.audience_id:
            return None
        
        endpoint = f"/audiences/{self.audience_id}"
        return self._make_request("GET", endpoint)


# Singleton instance
resend_service = ResendService()


def sync_user_marketing_subscription(user):
    """
    Sync a user's marketing email subscription with Resend based on their profile preferences
    
    Args:
        user: User instance to sync
    """
    if not hasattr(user, 'profile'):
        logger.warning(f"User {user.email} has no profile, cannot sync marketing subscription")
        return
    
    profile = user.profile
    should_be_subscribed = profile.receive_marketing_emails
    
    # Check current status in Resend
    is_currently_subscribed = resend_service.is_email_in_audience(user.email)
    now = timezone.now()
    
    # Update profile with current status from Resend
    profile.resend_is_subscribed = is_currently_subscribed
    profile.resend_last_checked_at = now
    
    # Determine sync status
    if should_be_subscribed == is_currently_subscribed:
        profile.resend_sync_status = 'synced'
    else:
        profile.resend_sync_status = 'out_of_sync'
    
    if should_be_subscribed and not is_currently_subscribed:
        # Subscribe user
        success = resend_service.subscribe_to_audience(
            email=user.email,
            first_name=user.first_name or "",
            last_name=user.last_name or ""
        )
        
        if success:
            profile.marketing_email_subscribed_at = now
            profile.marketing_email_unsubscribed_at = None
            profile.resend_is_subscribed = True
            profile.resend_sync_status = 'synced'
            logger.info(f"Subscribed user {user.email} to marketing emails")
        else:
            profile.resend_sync_status = 'error'
            logger.error(f"Failed to subscribe user {user.email} to marketing emails")
        
    elif not should_be_subscribed and is_currently_subscribed:
        # Unsubscribe user
        success = resend_service.unsubscribe_from_audience(user.email)
        
        if success:
            profile.marketing_email_unsubscribed_at = now
            profile.resend_is_subscribed = False
            profile.resend_sync_status = 'synced'
            logger.info(f"Unsubscribed user {user.email} from marketing emails")
        else:
            profile.resend_sync_status = 'error'
            logger.error(f"Failed to unsubscribe user {user.email} from marketing emails")
    
    # Save the updated profile
    profile.save(update_fields=[
        'marketing_email_subscribed_at', 
        'marketing_email_unsubscribed_at',
        'resend_is_subscribed',
        'resend_last_checked_at',
        'resend_sync_status'
    ])


def handle_marketing_unsubscribe(token: str) -> bool:
    """
    Handle secure unsubscribe via token
    
    Args:
        token: Unsubscribe token
        
    Returns:
        bool: True if successful, False otherwise
    """
    from web.models import UserProfile
    
    try:
        profile = UserProfile.objects.get(unsubscribe_token=token)
        
        # Unsubscribe from Resend
        success = resend_service.unsubscribe_from_audience(profile.user.email)
        
        if success:
            # Update profile
            profile.receive_marketing_emails = False
            profile.marketing_email_unsubscribed_at = timezone.now()
            profile.save(update_fields=['receive_marketing_emails', 'marketing_email_unsubscribed_at'])
            
            logger.info(f"Successfully unsubscribed user {profile.user.email} via token")
            return True
        else:
            logger.error(f"Failed to unsubscribe user {profile.user.email} from Resend")
            return False
            
    except UserProfile.DoesNotExist:
        logger.warning(f"Invalid unsubscribe token: {token}")
        return False