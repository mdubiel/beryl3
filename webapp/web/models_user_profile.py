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
    
    # Display name preferences
    nickname = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Nickname",
        help_text="Optional nickname to display instead of your first name"
    )
    use_nickname = models.BooleanField(
        default=False,
        verbose_name="Use Nickname for Display",
        help_text="If checked, your nickname will be used instead of your first name"
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
    
    # Resend sync status tracking
    resend_sync_status = models.CharField(
        max_length=20,
        choices=[
            ('unknown', 'Unknown'),
            ('synced', 'Synced'),
            ('out_of_sync', 'Out of Sync'),
            ('error', 'Error'),
        ],
        default='unknown',
        verbose_name="Resend Sync Status",
        help_text="Current synchronization status with Resend audience"
    )
    resend_last_checked_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Last Resend Check",
        help_text="When we last checked the status with Resend"
    )
    resend_is_subscribed = models.BooleanField(
        default=False,
        verbose_name="Actually Subscribed in Resend",
        help_text="Whether the email is actually in the Resend audience (last known status)"
    )
    
    # Content moderation and misuse tracking
    content_moderation_violations = models.IntegerField(
        default=0,
        verbose_name="Content Violations Count",
        help_text="Number of inappropriate content violations"
    )
    is_content_banned = models.BooleanField(
        default=False,
        verbose_name="Content Banned",
        help_text="User is banned due to content policy violations"
    )
    content_ban_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name="Content Ban Reason",
        help_text="Reason for content-related ban"
    )
    content_banned_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Content Banned At"
    )
    last_violation_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Last Violation"
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
    
    def get_display_name(self):
        """
        Get the user's preferred display name

        Returns the nickname if use_nickname is True and nickname exists,
        otherwise returns the user's full name or email
        """
        if self.use_nickname and self.nickname:
            return self.nickname

        if self.user.first_name or self.user.last_name:
            return self.user.get_full_name().strip()

        return self.user.email.split('@')[0]  # Use email prefix as fallback

    def get_public_profile_url(self):
        """
        Task 64: Get the URL to this user's public profile

        Returns URL using nickname if set, otherwise uses user ID
        """
        from django.urls import reverse

        if self.use_nickname and self.nickname:
            return reverse('public_user_profile', kwargs={'username': self.nickname})
        else:
            return reverse('public_user_profile', kwargs={'username': str(self.user.id)})
    
    def get_sync_status_display(self):
        """
        Get a user-friendly display of sync status with color coding
        
        Returns:
            tuple: (status_text, color_class)
        """
        from django.conf import settings
        from django.utils import timezone
        from datetime import timedelta
        
        # Check if we have sync status information
        if self.resend_sync_status == 'unknown' or not self.resend_last_checked_at:
            return ("Never checked", "warning")
        
        # Check if sync is stale (older than configured timeout)
        timeout_minutes = getattr(settings, 'RESEND_SYNC_TIMEOUT_MINUTES', 15)
        timeout = timedelta(minutes=timeout_minutes)
        is_stale = timezone.now() - self.resend_last_checked_at > timeout
        
        if is_stale:
            return ("Sync timeout", "warning")
        
        # Determine status based on sync state
        if self.resend_sync_status == 'error':
            return ("Error", "error")
        elif self.resend_sync_status == 'out_of_sync':
            return ("Out of sync", "error")
        elif self.resend_sync_status == 'synced':
            # Both opted in and subscribed, or both opted out and not subscribed
            if self.receive_marketing_emails == self.resend_is_subscribed:
                return ("Synced", "success")
            else:
                return ("Out of sync", "error")
        
        return ("Unknown", "warning")
    
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
    
    def add_content_violation(self, reason=None):
        """
        Add a content violation and check if user should be banned
        
        Returns:
            bool: Whether user was banned as a result
        """
        from django.utils import timezone
        from django.conf import settings
        
        self.content_moderation_violations += 1
        self.last_violation_at = timezone.now()
        
        # Check ban thresholds based on moderation action setting
        action = getattr(settings, 'CONTENT_MODERATION_ACTION', 'flag_only')
        threshold = getattr(settings, 'CONTENT_MODERATION_SOFT_BAN_THRESHOLD', 3)
        
        banned = False
        if action == 'hard_ban':
            # Ban immediately on first violation
            banned = self._ban_user(reason or "Inappropriate content detected - hard ban policy")
        elif action == 'soft_ban' and self.content_moderation_violations >= threshold:
            # Ban after threshold violations
            banned = self._ban_user(reason or f"Inappropriate content detected - {self.content_moderation_violations} violations")
        
        self.save()
        
        logger.warning(
            f"Content violation added for user {self.user.id} ({self.user.email}). "
            f"Total violations: {self.content_moderation_violations}. "
            f"Banned: {banned}"
        )
        
        return banned
    
    def _ban_user(self, reason):
        """
        Ban user from the platform
        
        Returns:
            bool: True if user was successfully banned
        """
        from django.utils import timezone
        
        if not self.is_content_banned:
            self.is_content_banned = True
            self.content_ban_reason = reason
            self.content_banned_at = timezone.now()
            
            # Set user as inactive to prevent login
            self.user.is_active = False
            self.user.save(update_fields=['is_active'])
            
            logger.error(f"User {self.user.id} ({self.user.email}) has been banned: {reason}")
            return True
        
        return False
    
    def is_user_content_banned(self):
        """
        Check if user is banned due to content violations
        """
        return self.is_content_banned and not self.user.is_active


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