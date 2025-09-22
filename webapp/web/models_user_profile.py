"""
User profile extension for marketing email consent
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger("webapp")
User = get_user_model()


class UserProfile(models.Model):
    """
    Extended user profile for marketing preferences and other user-specific settings
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    receive_marketing_emails = models.BooleanField(
        default=False, 
        verbose_name="Receive Marketing Emails",
        help_text="If checked, you will receive marketing emails from us"
    )
    
    # Marketing email tracking
    resend_audience_id = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        verbose_name="Resend Audience ID",
        help_text="Internal ID for tracking in Resend audience"
    )
    marketing_email_subscribed_at = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Marketing Email Subscribed At"
    )
    marketing_email_unsubscribed_at = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Marketing Email Unsubscribed At"
    )
    
    # Secure unsubscribe token
    unsubscribe_token = models.CharField(
        max_length=64, 
        blank=True, 
        null=True,
        verbose_name="Unsubscribe Token",
        help_text="Secure token for unsubscribe links"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
    
    def __str__(self):
        return f"Profile for {self.user.email}"
    
    def generate_unsubscribe_token(self):
        """
        Generate a secure unsubscribe token
        """
        import secrets
        self.unsubscribe_token = secrets.token_urlsafe(32)
        self.save(update_fields=['unsubscribe_token'])
        return self.unsubscribe_token
    
    def get_unsubscribe_url(self):
        """
        Get the secure unsubscribe URL
        """
        if not self.unsubscribe_token:
            self.generate_unsubscribe_token()
        
        from django.urls import reverse
        from django.contrib.sites.models import Site
        from django.conf import settings
        
        current_site = Site.objects.get_current()
        relative_url = reverse("marketing_unsubscribe", kwargs={"token": self.unsubscribe_token})
        protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
        return f"{protocol}://{current_site.domain}{relative_url}"
    
    def save(self, *args, **kwargs):
        """
        Override save to sync marketing email subscription with Resend
        """
        # Check if marketing email preference changed
        marketing_changed = False
        if self.pk:
            try:
                old_profile = UserProfile.objects.get(pk=self.pk)
                marketing_changed = old_profile.receive_marketing_emails != self.receive_marketing_emails
            except UserProfile.DoesNotExist:
                pass
        else:
            # New profile, check if we should sync on creation
            marketing_changed = self.receive_marketing_emails
        
        super().save(*args, **kwargs)
        
        # Sync with Resend if marketing preference changed
        if marketing_changed:
            self._sync_resend_subscription()
    
    def _sync_resend_subscription(self):
        """
        Sync the marketing email subscription with Resend
        """
        try:
            from web.services.resend_service import sync_user_marketing_subscription
            sync_user_marketing_subscription(self.user)
        except ImportError:
            logger.warning("Resend service not available, skipping subscription sync")


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile when a User is created
    """
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the UserProfile when the User is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        UserProfile.objects.create(user=instance)