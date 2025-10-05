# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging
import os
import re
import urllib.parse
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.storage import default_storage
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from nanoid_field import NanoidField

logger = logging.getLogger("webapp")
User = get_user_model()


class BerylModelManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """Returns a queryset including soft-deleted objects."""
        return super().get_queryset()


class BerylCollectionStatsManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def count(self, **kwargs):
        return self.get_queryset().filter(**kwargs).count()

    def exists(self, **kwargs):
        return self.get_queryset().filter(**kwargs).exists()


class BerylModel(models.Model):
    hash = NanoidField(unique=True, editable=False, max_length=10)

    created = models.DateTimeField(auto_now_add=True, verbose_name="Date created")
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name="%(class)s_created"
    )

    updated = models.DateTimeField(auto_now=True, verbose_name="Date updated")

    name = models.CharField(max_length=200, unique=False, verbose_name="Name")
    is_deleted = models.BooleanField(default=False)

    objects = BerylModelManager()

    class Meta:
        abstract = True
        ordering = ["name", "created"]

    def __repr__(self):
        return f"<{self.__class__.__name__} pk={self.pk} hash='{self.hash}'>"

    def __str__(self):
        return f"{self.name}"

    def delete(self, using=None, keep_parents=False):
        """Overrides the delete method to soft-delete."""
        self.is_deleted = True
        self.save(using=using, update_fields=['is_deleted'])

    def undelete(self):
        """A method to restore a soft-deleted object."""
        self.is_deleted = False
        self.save()


class MediaFile(BerylModel):
    """
    Tracks all media files uploaded to the system and their storage backend status.
    Provides centralized media file management with storage backend tracking.
    """
    
    class MediaType(models.TextChoices):
        COLLECTION_HEADER = "COLLECTION_HEADER", _("Collection Header Image")
        COLLECTION_ITEM = "COLLECTION_ITEM", _("Collection Item Image")
        AVATAR = "AVATAR", _("User Avatar")
        OTHER = "OTHER", _("Other Media")
    
    class StorageBackend(models.TextChoices):
        LOCAL = "LOCAL", _("Local Filesystem")
        GCS = "GCS", _("Google Cloud Storage")
        S3 = "S3", _("Amazon S3")
    
    # Basic file information
    file_path = models.CharField(max_length=500, verbose_name=_("File Path"))
    original_filename = models.CharField(max_length=255, verbose_name=_("Original Filename"))
    file_size = models.BigIntegerField(null=True, blank=True, verbose_name=_("File Size (bytes)"))
    content_type = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Content Type"))
    
    # Media categorization
    media_type = models.CharField(
        max_length=20,
        choices=MediaType.choices,
        default=MediaType.OTHER,
        verbose_name=_("Media Type"),
        db_index=True
    )
    
    # Storage tracking
    storage_backend = models.CharField(
        max_length=10,
        choices=StorageBackend.choices,
        verbose_name=_("Storage Backend"),
        db_index=True
    )
    
    # File existence tracking
    file_exists = models.BooleanField(default=True, verbose_name=_("File Exists in Storage"))
    last_verified = models.DateTimeField(auto_now_add=True, verbose_name=_("Last Verified"))
    
    # Optional metadata
    width = models.IntegerField(null=True, blank=True, verbose_name=_("Image Width"))
    height = models.IntegerField(null=True, blank=True, verbose_name=_("Image Height"))
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_("Additional Metadata"))
    
    # Content moderation fields
    class ContentModerationStatus(models.TextChoices):
        PENDING = "PENDING", _("Pending Review")
        APPROVED = "APPROVED", _("Approved")
        FLAGGED = "FLAGGED", _("Flagged")
        REJECTED = "REJECTED", _("Rejected")
    
    content_moderation_status = models.CharField(
        max_length=20,
        choices=ContentModerationStatus.choices,
        default=ContentModerationStatus.PENDING,
        verbose_name=_("Content Moderation Status"),
        db_index=True
    )
    content_moderation_score = models.FloatField(
        null=True, 
        blank=True, 
        verbose_name=_("Content Moderation Score"),
        help_text=_("AI confidence score for inappropriate content (0.0-1.0)")
    )
    content_moderation_details = models.JSONField(
        default=dict, 
        blank=True, 
        verbose_name=_("Content Moderation Details"),
        help_text=_("Detailed results from content moderation analysis")
    )
    content_moderation_checked_at = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Last Content Check")
    )
    
    class Meta:
        verbose_name = _("Media File")
        verbose_name_plural = _("Media Files")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=['media_type', 'storage_backend']),
            models.Index(fields=['file_exists', 'last_verified']),
            models.Index(fields=['content_moderation_status']),
            models.Index(fields=['content_moderation_checked_at']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} ({self.get_media_type_display()})"
    
    @property
    def file_url(self):
        """
        Get the public URL for the file. Uses standard storage URL generation
        which works with public GCS buckets and local storage.
        """
        try:
            return default_storage.url(self.file_path)
        except Exception as e:
            logger.error(f"Error generating URL for {self.file_path}: {str(e)}")
            return None
    
    def get_user_safe_url(self, request=None):
        """
        Get URL for user-facing content. Returns error image URL for flagged content.
        For SYS admin views, always returns the actual file URL.
        
        Args:
            request: Django request object to determine if this is a SYS admin view
            
        Returns:
            str: File URL or error image URL
        """
        # For SYS admin views, always return actual file URL
        if request and hasattr(request, 'resolver_match') and request.resolver_match:
            url_name = getattr(request.resolver_match, 'url_name', '')
            if url_name and url_name.startswith('sys_'):
                return self.file_url
        
        # For user-facing content, check moderation status
        if self.content_moderation_status in [
            self.ContentModerationStatus.FLAGGED, 
            self.ContentModerationStatus.REJECTED
        ]:
            # Return a static error image URL
            from django.conf import settings
            return f"{settings.STATIC_URL}images/content-unavailable.svg"
        
        return self.file_url
    
    @property
    def formatted_file_size(self):
        """
        Get human-readable file size
        """
        if not self.file_size:
            return "Unknown"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def verify_file_exists(self):
        """
        Check if the file actually exists in storage and update the status
        """
        try:
            exists = default_storage.exists(self.file_path)
            self.file_exists = exists
            self.last_verified = datetime.now()
            self.save(update_fields=['file_exists', 'last_verified'])
            return exists
        except Exception as e:
            logger.error(f"Error verifying MediaFile {self.hash}: {str(e)}")
            self.file_exists = False
            self.last_verified = datetime.now()
            self.save(update_fields=['file_exists', 'last_verified'])
            return False
    
    def delete_file(self):
        """
        Delete the actual file from storage (not the database record)
        """
        try:
            if default_storage.exists(self.file_path):
                default_storage.delete(self.file_path)
                self.file_exists = False
                self.save(update_fields=['file_exists'])
                return True
        except Exception as e:
            logger.error(f"Error deleting file for MediaFile {self.hash}: {str(e)}")
        return False
    
    @classmethod
    def get_storage_statistics(cls):
        """
        Get comprehensive statistics about media file usage
        """
        from django.db.models import Count, Sum, Avg, Q
        
        # Basic counts
        total_files = cls.objects.count()
        active_files = cls.objects.filter(file_exists=True).count()
        missing_files = cls.objects.filter(file_exists=False).count()
        
        # Storage backend distribution
        storage_stats = cls.objects.values('storage_backend').annotate(
            count=Count('id'),
            total_size=Sum('file_size')
        ).order_by('storage_backend')
        
        # Media type distribution
        type_stats = cls.objects.values('media_type').annotate(
            count=Count('id'),
            total_size=Sum('file_size')
        ).order_by('media_type')
        
        # Size statistics
        size_stats = cls.objects.filter(file_size__isnull=False).aggregate(
            total_size=Sum('file_size'),
            average_size=Avg('file_size'),
            min_size=models.Min('file_size'),
            max_size=models.Max('file_size')
        )
        
        # Recent activity
        from django.utils import timezone
        from datetime import timedelta
        
        last_week = timezone.now() - timedelta(days=7)
        recent_uploads = cls.objects.filter(created__gte=last_week).count()
        
        return {
            'total_files': total_files,
            'active_files': active_files,
            'missing_files': missing_files,
            'storage_distribution': list(storage_stats),
            'type_distribution': list(type_stats),
            'size_statistics': size_stats,
            'recent_uploads': recent_uploads,
            'orphaned_files': cls.objects.filter(
                Q(media_type=cls.MediaType.COLLECTION_HEADER) |
                Q(media_type=cls.MediaType.COLLECTION_ITEM)
            ).filter(file_exists=False).count()
        }
    
    @classmethod
    def cleanup_missing_files(cls):
        """
        Remove database records for files that no longer exist in storage
        """
        missing_files = cls.objects.filter(file_exists=False)
        count = missing_files.count()
        missing_files.delete()
        return count
    
    def save(self, *args, **kwargs):
        """
        Override save to set storage backend and trigger content moderation if needed
        """
        is_new = self.pk is None
        
        if not self.storage_backend:
            # Determine storage backend based on feature flag only
            use_gcs = getattr(settings, 'FEATURE_FLAGS', {}).get('USE_GCS_STORAGE', False)
            
            if use_gcs:
                self.storage_backend = self.StorageBackend.GCS
            else:
                self.storage_backend = self.StorageBackend.LOCAL
        
        super().save(*args, **kwargs)
        
        # Trigger content moderation for new image files
        if is_new and self.content_type and self.content_type.startswith('image/'):
            self.schedule_content_moderation()
    
    def schedule_content_moderation(self):
        """
        Schedule content moderation analysis for this media file
        """
        from django.conf import settings
        
        # Only proceed if content moderation is enabled
        if not getattr(settings, 'CONTENT_MODERATION_ENABLED', False):
            return
        
        try:
            # Import here to avoid circular imports
            from web.services.content_moderation import content_moderation_service
            
            # Process in background or immediately based on configuration
            # For now, process immediately
            result = content_moderation_service.process_media_file(self)
            
            logger.info(f"Content moderation completed for {self.original_filename}: {result}")
            
        except Exception as e:
            logger.error(f"Failed to schedule content moderation for {self.original_filename}: {e}")
    
    def analyze_content(self, force=False):
        """
        Manually trigger content analysis for this media file
        
        Args:
            force: Whether to re-analyze even if already checked
            
        Returns:
            Dict with analysis results
        """
        from django.utils import timezone
        
        # Skip if already analyzed and not forcing
        if not force and self.content_moderation_checked_at:
            return {
                "status": "already_analyzed",
                "checked_at": self.content_moderation_checked_at,
                "current_status": self.content_moderation_status
            }
        
        # Never re-analyze approved images unless explicitly forced
        if not force and self.content_moderation_status == self.ContentModerationStatus.APPROVED:
            return {
                "status": "approved_skipped",
                "message": "Image is approved and will not be re-analyzed",
                "current_status": self.content_moderation_status
            }
        
        try:
            from web.services.content_moderation import content_moderation_service
            return content_moderation_service.process_media_file(self)
        except Exception as e:
            logger.error(f"Failed to analyze content for {self.original_filename}: {e}")
            return {"status": "error", "error": str(e)}
    
    def is_content_appropriate(self):
        """
        Check if content is appropriate based on moderation status
        """
        return self.content_moderation_status in [
            self.ContentModerationStatus.APPROVED,
            self.ContentModerationStatus.PENDING
        ]
    
    def needs_content_review(self):
        """
        Check if content needs manual review
        """
        return self.content_moderation_status == self.ContentModerationStatus.FLAGGED
    
    @property
    def content_moderation_summary(self):
        """
        Get a human-readable summary of content moderation status
        """
        status_messages = {
            self.ContentModerationStatus.PENDING: "Pending review",
            self.ContentModerationStatus.APPROVED: "Approved",
            self.ContentModerationStatus.FLAGGED: "Flagged for review",
            self.ContentModerationStatus.REJECTED: "Rejected"
        }
        
        message = status_messages.get(self.content_moderation_status, "Unknown")
        
        if self.content_moderation_score:
            message += f" (confidence: {self.content_moderation_score:.2f})"
        
        if self.content_moderation_checked_at:
            message += f" - checked {self.content_moderation_checked_at.strftime('%Y-%m-%d %H:%M')}"
        
        return message


class ItemType(BerylModel):
    """
    Defines different types of items that can be collected (books, lego sets, vinyl records, etc.)
    """
    display_name = models.CharField(max_length=100, verbose_name=_("Display Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Lucide Icon Name"))
    
    class Meta:
        verbose_name = _("Item Type")
        verbose_name_plural = _("Item Types")
        ordering = ["display_name"]
    
    def __str__(self):
        return str(self.display_name)
    
    @property
    def can_be_deleted(self):
        """
        Check if this item type can be deleted (no attributes and no items using it)
        """
        attributes_count = self.attributes.filter(is_deleted=False).count()
        items_count = self.items.filter(is_deleted=False).count()
        return attributes_count == 0 and items_count == 0
    
    @property
    def deletion_blocked_reason(self):
        """
        Get the reason why deletion is blocked
        """
        attributes_count = self.attributes.filter(is_deleted=False).count()
        items_count = self.items.filter(is_deleted=False).count()
        
        if attributes_count > 0 and items_count > 0:
            return f"Has {attributes_count} attribute{'s' if attributes_count != 1 else ''} and {items_count} item{'s' if items_count != 1 else ''}"
        elif attributes_count > 0:
            return f"Has {attributes_count} attribute{'s' if attributes_count != 1 else ''} defined"
        elif items_count > 0:
            return f"Used by {items_count} item{'s' if items_count != 1 else ''}"
        else:
            return None
    
    def delete(self, using=None, keep_parents=False):
        """
        Override delete method to prevent deletion if:
        1. There are attributes defined for this item type
        2. There are collection items using this item type
        """
        from django.core.exceptions import PermissionDenied
        
        # Check for attributes
        attributes_count = self.attributes.filter(is_deleted=False).count()
        if attributes_count > 0:
            raise PermissionDenied(
                f"Cannot delete item type '{self.display_name}'. "
                f"It has {attributes_count} attribute{'s' if attributes_count != 1 else ''} defined. "
                f"Delete all attributes first."
            )
        
        # Check for collection items using this type
        items_count = self.items.filter(is_deleted=False).count()
        if items_count > 0:
            raise PermissionDenied(
                f"Cannot delete item type '{self.display_name}'. "
                f"It is being used by {items_count} item{'s' if items_count != 1 else ''}. "
                f"Remove or change the type of all items first."
            )
        
        # If all checks pass, proceed with soft delete
        super().delete(using=using, keep_parents=keep_parents)


class ItemAttribute(BerylModel):
    """
    Defines attributes that can be associated with item types (e.g., author for books, piece count for lego)
    """
    class AttributeType(models.TextChoices):
        TEXT = "TEXT", _("Text")
        LONG_TEXT = "LONG_TEXT", _("Long Text")
        NUMBER = "NUMBER", _("Number")
        DATE = "DATE", _("Date")
        URL = "URL", _("URL")
        BOOLEAN = "BOOLEAN", _("Boolean")
        CHOICE = "CHOICE", _("Choice")
    
    item_type = models.ForeignKey(ItemType, on_delete=models.CASCADE, related_name="attributes", verbose_name=_("Item Type"))
    display_name = models.CharField(max_length=100, verbose_name=_("Display Name"))
    attribute_type = models.CharField(max_length=20, choices=AttributeType.choices, verbose_name=_("Attribute Type"))
    required = models.BooleanField(default=False, verbose_name=_("Required"))
    skip_validation = models.BooleanField(default=False, verbose_name=_("Skip Validation"))
    order = models.IntegerField(default=0, verbose_name=_("Display Order"))
    choices = models.JSONField(blank=True, null=True, verbose_name=_("Choices"), help_text=_("For choice fields, provide a list of options"))
    help_text = models.TextField(blank=True, null=True, verbose_name=_("Help Text"))
    
    class Meta:
        verbose_name = _("Item Attribute")
        verbose_name_plural = _("Item Attributes")
        ordering = ["item_type", "order", "display_name"]
        unique_together = ["item_type", "name"]
    
    def __str__(self):
        return f"{self.item_type.display_name} - {self.display_name}"
    
    def validate_value(self, value):
        """
        Validate a value against this attribute's type and constraints
        """
        if self.skip_validation:
            return value
            
        if not value and self.required:
            raise ValidationError(f"{self.display_name} is required")
            
        if not value:
            return value
            
        if self.attribute_type == self.AttributeType.TEXT:
            return str(value)
            
        elif self.attribute_type == self.AttributeType.LONG_TEXT:
            return str(value)
            
        elif self.attribute_type == self.AttributeType.NUMBER:
            try:
                return float(value)
            except (ValueError, TypeError):
                raise ValidationError(f"{self.display_name} must be a number")
                
        elif self.attribute_type == self.AttributeType.DATE:
            if isinstance(value, str):
                try:
                    datetime.strptime(value, '%Y-%m-%d')
                    return value
                except ValueError:
                    raise ValidationError(f"{self.display_name} must be a valid date (YYYY-MM-DD)")
            return value
            
        elif self.attribute_type == self.AttributeType.URL:
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            if not url_pattern.match(str(value)):
                raise ValidationError(f"{self.display_name} must be a valid URL")
            return str(value)
            
        elif self.attribute_type == self.AttributeType.BOOLEAN:
            return bool(value)
            
        elif self.attribute_type == self.AttributeType.CHOICE:
            if self.choices and str(value) not in self.choices:
                raise ValidationError(f"{self.display_name} must be one of: {', '.join(self.choices)}")
            return str(value)
            
        return value


class Collection(BerylModel):
    stats = BerylCollectionStatsManager()

    class Visibility(models.TextChoices):
        PRIVATE = "PRIVATE", _("Visible only to me")
        UNLISTED = "UNLISTED", _("Shared with link")
        PUBLIC = "PUBLIC", _("Public")

    # Add the new field to your model. 'Private' is a safe default.
    visibility = models.CharField(
        max_length=10,
        choices=Visibility.choices,
        default=Visibility.PRIVATE,
        verbose_name=_("Visibility"),
        db_index=True,
    )

    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image_url = models.URLField(blank=True, null=True, verbose_name=_("Image URL"))

    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    def get_absolute_url(self):
        return reverse("collection_detail", kwargs={"hash": self.hash})

    @property
    def can_be_deleted(self):
        """Returns True only if the collection has no items."""
        # Note: This requires the object to have `item_count` annotated
        # in list views for performance, which we already did.
        if hasattr(self, "item_count"):
            return self.item_count == 0
        return self.items.count() == 0

    # Get sharable linkt to the collection
    def get_sharable_link(self):
        """
        Returns a sharable link based on the collection's visibility.
        If the collection is private, returns None. Otherwise, it returns
        the public-facing URL.
        """
        if self.visibility == self.Visibility.PRIVATE:
            return None

        return self.hash

    def get_sharable_url(self):
        """
        Returns a sharable link based on the collection's visibility.
        If the collection is private, returns None. Otherwise, it returns
        the public-facing URL.
        """
        if self.visibility == self.Visibility.PRIVATE:
            return None

        current_site = Site.objects.get_current()
        relative_url = reverse("public_collection_view", kwargs={"hash": self.hash})
        protocol = 'https' if getattr(settings, 'SECURE_SSL_REDIRECT', False) else 'http'
        return f"{protocol}://{current_site.domain}{relative_url}"

    def delete(self, *args, **kwargs):
        """
        Overrides the delete method to prevent deleting a collection with items.
        """
        # First, check if there are any related items.
        if not self.can_be_deleted:
            # If there are items, raise an exception to stop the deletion.
            raise PermissionDenied("Cannot delete a collection that contains items.")

        # If there are no items, proceed with the original soft-delete logic.
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs):
        """
        Overrides the save method to add a placehold.co image URL
        if one isn't provided.
        """
        # We only generate a URL if the image_url field is empty and a name exists.
        if not self.image_url and self.name:

            # URL-encode the collection name to handle spaces and special characters
            # e.g., "Vintage Toys" becomes "Vintage+Toys"
            encoded_text = urllib.parse.quote_plus(self.name)

            # Construct the final URL for placehold.co
            # Format: https://placehold.co/{width}x{height}/{bg_color}/{text_color}.png?text={your_text}
            self.image_url = f"https://placehold.co/800x600/262626/FFFFFF.png?text={encoded_text}"

        # It's crucial to call the original save() method at the end.
        super().save(*args, **kwargs)
    
    @property
    def default_image(self):
        """Get the default image for this collection"""
        return self.images.filter(is_default=True).first()


class CollectionItem(BerylModel):

    class Status(models.TextChoices):
        # The format is: VARIABLE_NAME = 'DB_VALUE', _('Human Readable Label')
        IN_COLLECTION = "IN_COLLECTION", _("In Collection")
        PREVIOUSLY_OWNED = "PREVIOUSLY_OWNED", _("Previously Owned")
        LENT_OUT = "LENT_OUT", _("Lent to Someone")
        RESERVED = "RESERVED", _("Reserved by Someone")
        ORDERED = "ORDERED", _("Ordered (On its way)")
        WANTED = "WANTED", _("Wanted")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_COLLECTION,
        verbose_name=_("Status"),
        db_index=True,
    )

    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="items", verbose_name="Collection"
    )
    item_type = models.ForeignKey(
        ItemType, on_delete=models.PROTECT, related_name="items", verbose_name=_("Item Type"), null=True, blank=True
    )
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image_url = models.URLField(blank=True, null=True, verbose_name="Image URL")
    attributes = models.JSONField(default=dict, blank=True, verbose_name=_("Attributes"))

    # New fields for reservation details
    reserved_date = models.DateTimeField(null=True, blank=True, verbose_name="Reserved Date")
    reserved_by_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Reserved By Name"))
    reserved_by_email = models.EmailField(blank=True, null=True, verbose_name=_("Reserved By Email"))
    guest_reservation_token = models.CharField(max_length=64, blank=True, null=True, verbose_name=_("Guest Reservation Token"), db_index=True)
    
    # Favorite field
    is_favorite = models.BooleanField(default=False, verbose_name=_("Is Favorite"), db_index=True)

    class Meta:
        verbose_name = "Collection Item"
        verbose_name_plural = "Collection Items"

    @property
    def can_be_deleted(self):
        """
        Returns True if the item is not in a state that prevents deletion
        (e.g., lent out or reserved).
        """
        return self.status not in [self.Status.LENT_OUT, self.Status.RESERVED]

    def get_absolute_url(self):
        """Returns the canonical URL for a collection item."""
        return reverse("item_detail", kwargs={"hash": self.hash})

    def delete(self, *args, **kwargs):
        """
        Overrides the delete method to prevent deleting an item in a non-deletable state.
        """
        if not self.can_be_deleted:
            raise PermissionDenied(f"Cannot delete item in '{self.get_status_display()}' status.")
        return super().delete(*args, **kwargs)

    @property
    def is_bookable(self):
        """
        Returns True only if the item is in the 'Wanted' status and not already reserved.
        """
        return self.status == self.Status.WANTED
    
    def generate_guest_reservation_token(self):
        """
        Generate a secure token for guest reservations
        """
        import secrets
        return secrets.token_urlsafe(32)
    
    def unreserve_guest(self):
        """
        Unreserve an item that was reserved by a guest
        """
        if self.status == self.Status.RESERVED and self.guest_reservation_token:
            self.status = self.Status.WANTED
            self.reserved_date = None
            self.reserved_by_name = None
            self.reserved_by_email = None
            self.guest_reservation_token = None
            self.save()
            return True
        return False
    
    def get_attribute_value(self, attribute_name):
        """
        Get the value of a specific attribute
        """
        return self.attributes.get(attribute_name)
    
    def set_attribute_value(self, attribute_name, value):
        """
        Set the value of a specific attribute with validation
        """
        if self.item_type:
            try:
                attribute = self.item_type.attributes.get(name=attribute_name)
                validated_value = attribute.validate_value(value)
                self.attributes[attribute_name] = validated_value
            except ItemAttribute.DoesNotExist:
                # If attribute doesn't exist for this item type, just store the value
                self.attributes[attribute_name] = value
        else:
            # No item type, just store the value
            self.attributes[attribute_name] = value
    
    def get_display_attributes(self):
        """
        Get all attributes for display, ordered by the attribute definition order.
        Uses dual-mode support - retrieves from relational model first, then JSON fallback.
        Supports multiple values per attribute (e.g., multiple authors).
        """
        if not self.item_type:
            return []

        result = []

        # Get all attributes from dual-mode (relational + JSON)
        detailed_attrs = self.get_all_attributes_detailed()

        # Create a map for quick lookup
        attr_map = {attr['name']: attr for attr in detailed_attrs}

        # Track which attributes we've processed
        processed_names = set()

        # Order by ItemAttribute definition order
        for item_attr in self.item_type.attributes.all():
            attr_name = item_attr.name

            if attr_name in attr_map:
                attr_data = attr_map[attr_name]
                processed_names.add(attr_name)

                # Handle multiple values (list)
                if isinstance(attr_data['value'], list):
                    # Multiple values - create entry for each
                    for idx, value in enumerate(attr_data['value']):
                        display_value = attr_data['display_value'][idx] if isinstance(attr_data['display_value'], list) else str(value)
                        attr_value_hash = attr_data.get('attribute_value_hashes', [None])[idx] if 'attribute_value_hashes' in attr_data else None
                        result.append({
                            'attribute': item_attr,
                            'value': value,
                            'display_value': display_value,
                            'is_legacy': attr_data['is_legacy'],
                            'is_multiple': True,
                            'multiple_index': idx,
                            'multiple_count': len(attr_data['value']),
                            'attr_value_hash': attr_value_hash
                        })
                else:
                    # Single value
                    attr_value_hash = attr_data.get('attribute_value_hash', None)
                    result.append({
                        'attribute': item_attr,
                        'value': attr_data['value'],
                        'display_value': attr_data['display_value'],
                        'is_legacy': attr_data['is_legacy'],
                        'is_multiple': False,
                        'attr_value_hash': attr_value_hash
                    })

        # Add orphaned JSON attributes (no ItemAttribute definition) at the end
        for attr_name, attr_data in attr_map.items():
            if attr_name not in processed_names and attr_data['is_legacy']:
                # Create a simple attribute object for display
                class OrphanedAttribute:
                    def __init__(self, name):
                        self.name = name
                        self.display_name = name.replace('_', ' ').title()

                result.append({
                    'attribute': OrphanedAttribute(attr_name),
                    'value': attr_data['value'],
                    'display_value': attr_data['display_value'],
                    'is_legacy': True,
                    'is_multiple': False,
                    'attr_value_hash': None
                })

        return result
    
    def _format_attribute_value(self, attribute, value):
        """
        Format an attribute value for display
        """
        if value is None:
            return ""

        if attribute.attribute_type == ItemAttribute.AttributeType.BOOLEAN:
            return "Yes" if value else "No"
        elif attribute.attribute_type == ItemAttribute.AttributeType.URL:
            return f'<a href="{value}" target="_blank" class="link">{value}</a>'
        elif attribute.attribute_type == ItemAttribute.AttributeType.DATE:
            try:
                date_obj = datetime.strptime(str(value), '%Y-%m-%d')
                return date_obj.strftime('%B %d, %Y')
            except ValueError:
                return str(value)
        else:
            return str(value)

    # ========================================================================
    # DUAL-MODE ATTRIBUTE SUPPORT (JSON + Relational)
    # ========================================================================

    def get_all_attributes(self):
        """
        Get all attributes from both JSON and relational sources combined.
        Relational attributes take precedence over JSON for same attribute name.

        Returns:
            dict: {attribute_name: value} for all attributes
        """
        result = {}

        # Start with JSON attributes (legacy)
        if self.attributes:
            result.update(self.attributes)

        # Override with relational attributes (take precedence)
        # Group by item_attribute to handle multiple values
        from collections import defaultdict
        relational_attrs = defaultdict(list)

        for attr_value in self.attribute_values.select_related('item_attribute').all():
            attr_name = attr_value.item_attribute.name
            typed_value = attr_value.get_typed_value()
            relational_attrs[attr_name].append(typed_value)

        # Add relational attributes to result
        for attr_name, values in relational_attrs.items():
            if len(values) == 1:
                # Single value - just use it
                result[attr_name] = values[0]
            else:
                # Multiple values - return as list
                result[attr_name] = values

        return result

    def get_all_attributes_detailed(self):
        """
        Get detailed attribute information including source (JSON vs relational).
        Useful for migration UI and debugging.

        Returns:
            list of dicts with keys:
                - name: attribute name
                - value: attribute value (or list for multiple)
                - source: 'json' or 'relational'
                - is_legacy: True if from JSON
                - item_attribute: ItemAttribute object (if relational)
                - count: number of values (for relational with multiple)
        """
        result = []
        processed_names = set()

        # Get relational attributes first (they take precedence)
        from collections import defaultdict
        relational_attrs = defaultdict(list)

        for attr_value in self.attribute_values.select_related('item_attribute').all():
            attr_name = attr_value.item_attribute.name
            relational_attrs[attr_name].append(attr_value)

        # Add relational attributes
        for attr_name, attr_values in relational_attrs.items():
            if len(attr_values) == 1:
                # Single value
                attr_val = attr_values[0]
                result.append({
                    'name': attr_name,
                    'value': attr_val.get_typed_value(),
                    'display_value': attr_val.get_display_value(),
                    'source': 'relational',
                    'is_legacy': False,
                    'item_attribute': attr_val.item_attribute,
                    'count': 1,
                    'attribute_value_hash': attr_val.hash
                })
            else:
                # Multiple values
                values = [av.get_typed_value() for av in attr_values]
                display_values = [av.get_display_value() for av in attr_values]
                result.append({
                    'name': attr_name,
                    'value': values,
                    'display_value': display_values,
                    'source': 'relational',
                    'is_legacy': False,
                    'item_attribute': attr_values[0].item_attribute,
                    'count': len(values),
                    'attribute_value_hashes': [av.hash for av in attr_values]
                })
            processed_names.add(attr_name)

        # Add JSON attributes that haven't been migrated
        if self.attributes:
            for attr_name, attr_value in self.attributes.items():
                if attr_name not in processed_names:
                    # Find ItemAttribute if it exists
                    item_attribute = None
                    if self.item_type:
                        try:
                            item_attribute = self.item_type.attributes.get(name=attr_name)
                        except ItemAttribute.DoesNotExist:
                            pass

                    result.append({
                        'name': attr_name,
                        'value': attr_value,
                        'display_value': str(attr_value),
                        'source': 'json',
                        'is_legacy': True,
                        'item_attribute': item_attribute,
                        'count': 1
                    })

        return result

    def is_legacy_attribute(self, attribute_name):
        """
        Check if an attribute is stored in JSON (legacy) format.

        Args:
            attribute_name: Name of the attribute to check

        Returns:
            bool: True if attribute is in JSON and not migrated to relational
        """
        # Check if exists in relational
        has_relational = self.attribute_values.filter(
            item_attribute__name=attribute_name
        ).exists()

        if has_relational:
            return False

        # Check if exists in JSON
        if self.attributes and attribute_name in self.attributes:
            return True

        return False

    def get_legacy_attributes(self):
        """
        Get list of attribute names that are still in JSON (not migrated).

        Returns:
            list: Attribute names that are legacy (JSON-based)
        """
        if not self.attributes:
            return []

        # Get all relational attribute names
        relational_names = set(
            self.attribute_values.values_list('item_attribute__name', flat=True)
        )

        # Return JSON attribute names that aren't in relational
        return [
            name for name in self.attributes.keys()
            if name not in relational_names
        ]

    def migrate_attribute_to_relational(self, attribute_name):
        """
        Migrate a single attribute from JSON to relational format.

        Args:
            attribute_name: Name of the attribute to migrate

        Returns:
            tuple: (success: bool, message: str, attribute_value: CollectionItemAttributeValue or None)

        Raises:
            ValueError: If attribute doesn't exist in JSON or ItemAttribute not found
        """
        # Check if attribute exists in JSON
        if not self.attributes or attribute_name not in self.attributes:
            return (False, f"Attribute '{attribute_name}' not found in JSON", None)

        # Check if already migrated
        if self.attribute_values.filter(item_attribute__name=attribute_name).exists():
            return (False, f"Attribute '{attribute_name}' already migrated", None)

        # Find ItemAttribute definition
        if not self.item_type:
            return (False, "Item has no item_type set", None)

        try:
            item_attribute = self.item_type.attributes.get(name=attribute_name)
        except ItemAttribute.DoesNotExist:
            return (False, f"No ItemAttribute definition found for '{attribute_name}'", None)

        # Get value from JSON
        json_value = self.attributes[attribute_name]

        # Create relational attribute value
        try:
            from web.models import CollectionItemAttributeValue

            attr_value = CollectionItemAttributeValue(
                item=self,
                item_attribute=item_attribute,
                order=0
            )
            attr_value.set_typed_value(json_value)
            attr_value.save()

            return (True, f"Attribute '{attribute_name}' migrated successfully", attr_value)

        except Exception as e:
            return (False, f"Error migrating '{attribute_name}': {str(e)}", None)

    def get_attribute_count(self):
        """
        Get total count of all attributes (JSON + relational, deduplicated).

        Returns:
            int: Total number of unique attributes
        """
        return len(self.get_all_attributes())

    def has_legacy_attributes(self):
        """
        Check if this item has any legacy (JSON) attributes.

        Returns:
            bool: True if there are unmigrated JSON attributes
        """
        return len(self.get_legacy_attributes()) > 0

    # ========================================================================
    # END DUAL-MODE ATTRIBUTE SUPPORT
    # ========================================================================

    @property
    def default_image(self):
        """Get the default image for this collection item"""
        return self.images.filter(is_default=True).first()
    




class RecentActivity(BerylModel):
    """
    Stores user activity timeline events with simplified interface.
    Uses BerylModel's created_by and created fields.
    """
    icon = models.CharField(
        max_length=50, 
        default="activity", 
        verbose_name=_("Lucide Icon Name"),
        help_text="Must be a valid Lucide icon name"
    )
    message = models.TextField(
        verbose_name=_("Activity Message"), 
        help_text="Markdown supported for highlights"
    )
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Recent Activity"
        verbose_name_plural = "Recent Activities"
    
    def __str__(self):
        return f"{self.message} ({self.created_by.email if self.created_by else 'System'})"
    
    # Collection Activities
    @staticmethod
    def log_collection_created(user, collection_name):
        """Log when user creates a new collection"""
        RecentActivity.objects.create(
            created_by=user,
            message=f"Created collection **{collection_name}**",
            icon="plus"
        )
    
    @staticmethod
    def log_collection_deleted(user, collection_name):
        """Log when user deletes a collection"""
        RecentActivity.objects.create(
            created_by=user,
            message=f"Deleted collection **{collection_name}**",
            icon="trash-2"
        )
    
    @staticmethod
    def log_collection_visibility_changed(user, collection_name, visibility):
        """Log when user changes collection visibility"""
        visibility_display = {'PRIVATE': 'Private', 'PUBLIC': 'Public', 'UNLISTED': 'Unlisted'}.get(visibility, visibility)
        RecentActivity.objects.create(
            created_by=user,
            message=f"Changed **{collection_name}** visibility to **{visibility_display}**",
            icon="settings"
        )
    
    # Item Activities
    @staticmethod
    def log_item_added(user, item_name, collection_name):
        """Log when user adds an item to collection"""
        RecentActivity.objects.create(
            created_by=user,
            message=f"Added **{item_name}** to collection **{collection_name}**",
            icon="circle-plus"
        )
    
    @staticmethod
    def log_item_removed(user, item_name, collection_name):
        """Log when user removes an item from collection"""
        RecentActivity.objects.create(
            created_by=user,
            message=f"Removed **{item_name}** from collection **{collection_name}**",
            icon="circle-minus"
        )
    
    @staticmethod
    def log_item_status_changed(user, item_name, new_status):
        """Log when user changes item status"""
        status_messages = {
            'IN_COLLECTION': f"Marked **{item_name}** as **In Collection**",
            'WANTED': f"Added **{item_name}** to **wishlist**",
            'RESERVED': f"Marked **{item_name}** as **Reserved**",
            'ORDERED': f"Marked **{item_name}** as **Ordered**",
            'LENT': f"Marked **{item_name}** as **Lent**",
            'PREVIOUSLY_OWNED': f"Marked **{item_name}** as **Previously Owned**"
        }
        status_icons = {
            'IN_COLLECTION': 'package',
            'WANTED': 'star',
            'RESERVED': 'gift',
            'ORDERED': 'truck',
            'LENT': 'share-2',
            'PREVIOUSLY_OWNED': 'history'
        }
        RecentActivity.objects.create(
            created_by=user,
            message=status_messages.get(new_status, f"Changed **{item_name}** status to **{new_status}**"),
            icon=status_icons.get(new_status, 'pencil')
        )
    
    @staticmethod
    def log_item_favorited(user, item_name):
        """Log when user favorites an item"""
        RecentActivity.objects.create(
            created_by=user,
            message=f"Favorited **{item_name}**",
            icon="star"
        )
    
    @staticmethod
    def log_item_unfavorited(user, item_name):
        """Log when user unfavorites an item"""
        RecentActivity.objects.create(
            created_by=user,
            message=f"Unfavorited **{item_name}**",
            icon="heart"
        )
    
    @staticmethod
    def log_item_moved(user, item_name, from_collection, to_collection):
        """Log when user moves an item between collections"""
        RecentActivity.objects.create(
            created_by=user,
            message=f"Moved **{item_name}** from **{from_collection}** to **{to_collection}**",
            icon="arrow-right-left"
        )
    
    @staticmethod
    def log_item_copied(user, item_name, from_collection, to_collection):
        """Log when user copies an item between collections"""
        RecentActivity.objects.create(
            created_by=user,
            message=f"Copied **{item_name}** from **{from_collection}** to **{to_collection}**",
            icon="copy"
        )
    
    # Reservation Activities
    @staticmethod
    def log_item_reserved_by_user(collection_owner, item_name):
        """Log when someone reserves an item from user's collection"""
        RecentActivity.objects.create(
            created_by=collection_owner,
            message=f"Someone reserved **{item_name}** from your collection",
            icon="gift"
        )
    
    @staticmethod
    def log_item_reserved_by_guest(collection_owner, item_name):
        """Log when guest reserves an item from user's collection"""
        RecentActivity.objects.create(
            created_by=collection_owner,
            message=f"Someone reserved **{item_name}** from your collection",
            icon="gift"
        )
    
    @staticmethod
    def log_item_unreserved(collection_owner, item_name):
        """Log when someone cancels their reservation"""
        RecentActivity.objects.create(
            created_by=collection_owner,
            message=f"Someone cancelled their reservation for **{item_name}**",
            icon="circle-x"
        )


class LinkPattern(BerylModel):
    """
    Defines URL patterns for automatic link recognition and display
    """
    display_name = models.CharField(max_length=100, verbose_name=_("Display Name"))
    url_pattern = models.CharField(max_length=255, verbose_name=_("URL Pattern"), 
                                  help_text=_("Use * as wildcard, e.g., https://www.amazon.de/*"))
    icon = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Lucide Icon Name"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    
    class Meta:
        verbose_name = _("Link Pattern")
        verbose_name_plural = _("Link Patterns")
        ordering = ["display_name"]
    
    def __str__(self):
        return f"{self.display_name} ({self.url_pattern})"
    
    def matches_url(self, url):
        """
        Check if a URL matches this pattern
        """
        import fnmatch
        return fnmatch.fnmatch(url.lower(), self.url_pattern.lower())
    
    @classmethod
    def find_matching_pattern(cls, url):
        """
        Find the first matching pattern for a given URL
        """
        for pattern in cls.objects.filter(is_active=True):
            if pattern.matches_url(url):
                return pattern
        return None


class CollectionItemLink(BerylModel):
    """
    Links associated with collection items (similar to attributes)
    """
    item = models.ForeignKey(CollectionItem, on_delete=models.CASCADE, related_name="links", verbose_name=_("Item"))
    url = models.URLField(max_length=2000, verbose_name=_("URL"))
    display_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Display Name"))
    link_pattern = models.ForeignKey(LinkPattern, on_delete=models.SET_NULL, blank=True, null=True, 
                                   related_name="links", verbose_name=_("Link Pattern"))
    order = models.IntegerField(default=0, verbose_name=_("Display Order"))
    
    class Meta:
        verbose_name = _("Collection Item Link")
        verbose_name_plural = _("Collection Item Links")
        ordering = ["item", "order", "display_name"]
    
    def __str__(self):
        return f"{self.item.name} - {self.get_display_name()}"
    
    def get_display_name(self):
        """
        Get the display name for this link
        """
        if self.display_name:
            return self.display_name
        elif self.link_pattern:
            return self.link_pattern.display_name
        else:
            # Fallback: extract domain from URL
            try:
                from urllib.parse import urlparse
                parsed = urlparse(self.url)
                domain = parsed.netloc.lower()
                # Remove www. prefix
                if domain.startswith('www.'):
                    domain = domain[4:]
                return domain
            except Exception:
                return "Link"
    
    def get_icon(self):
        """
        Get the icon for this link
        """
        if self.link_pattern and self.link_pattern.icon:
            return self.link_pattern.icon
        return "external-link"  # Default icon
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically match URL patterns
        """
        # Find matching pattern if not already set
        if not self.link_pattern and self.url:
            self.link_pattern = LinkPattern.find_matching_pattern(self.url)
        
        super().save(*args, **kwargs)


class CollectionItemAttributeValue(BerylModel):
    """
    Stores individual attribute values for collection items in a relational format.
    This replaces the JSON-based attributes field with proper database relations,
    allowing for better querying, multiple values per attribute, and data integrity.

    Migration from JSON: Legacy JSON attributes are marked with is_legacy flag
    and can be individually migrated via the UI.
    """
    item = models.ForeignKey(
        CollectionItem,
        on_delete=models.CASCADE,
        related_name="attribute_values",
        verbose_name=_("Collection Item")
    )
    item_attribute = models.ForeignKey(
        ItemAttribute,
        on_delete=models.PROTECT,
        related_name="values",
        verbose_name=_("Attribute Definition"),
        help_text=_("The attribute schema this value conforms to")
    )
    value = models.TextField(
        verbose_name=_("Value"),
        help_text=_("Stored as text, converted to appropriate type on retrieval")
    )

    class Meta:
        verbose_name = _("Collection Item Attribute Value")
        verbose_name_plural = _("Collection Item Attribute Values")
        ordering = ["item", "item_attribute", "value", "created"]
        indexes = [
            models.Index(fields=["item", "item_attribute"]),
            models.Index(fields=["item", "item_attribute", "value"]),
        ]

    def __str__(self):
        return f"{self.item.name} - {self.item_attribute.display_name}: {self.value[:50]}"

    def get_typed_value(self):
        """
        Convert the stored string value to the appropriate Python type
        based on the attribute's type definition.

        Returns:
            The value converted to int, float, bool, date string, or str
        """
        if not self.value:
            return None

        attr_type = self.item_attribute.attribute_type

        if attr_type == ItemAttribute.AttributeType.NUMBER:
            try:
                # Convert to float first
                float_value = float(self.value)
                # If it's a whole number, return as int
                if float_value.is_integer():
                    return int(float_value)
                return float_value
            except (ValueError, TypeError):
                return self.value  # Return as-is if conversion fails

        elif attr_type == ItemAttribute.AttributeType.BOOLEAN:
            # Handle various boolean representations
            if isinstance(self.value, bool):
                return self.value
            return self.value.lower() in ('true', '1', 'yes', 'on')

        elif attr_type == ItemAttribute.AttributeType.DATE:
            # Return as date string in YYYY-MM-DD format
            # Template will handle formatting
            return self.value

        elif attr_type in (ItemAttribute.AttributeType.TEXT,
                          ItemAttribute.AttributeType.LONG_TEXT,
                          ItemAttribute.AttributeType.URL,
                          ItemAttribute.AttributeType.CHOICE):
            return self.value

        return self.value

    def set_typed_value(self, value):
        """
        Convert any Python type to string for storage.

        Args:
            value: The value to store (can be str, int, float, bool, etc.)
        """
        if value is None:
            self.value = ""
            return

        attr_type = self.item_attribute.attribute_type

        if attr_type == ItemAttribute.AttributeType.BOOLEAN:
            # Store boolean as 'true' or 'false'
            self.value = 'true' if value else 'false'
        elif attr_type == ItemAttribute.AttributeType.NUMBER:
            # Store numbers as string
            self.value = str(value)
        elif attr_type == ItemAttribute.AttributeType.DATE:
            # Expect YYYY-MM-DD format
            if isinstance(value, str):
                self.value = value
            else:
                # If it's a date object, convert to string
                try:
                    self.value = value.strftime('%Y-%m-%d')
                except AttributeError:
                    self.value = str(value)
        else:
            # Everything else stored as string
            self.value = str(value)

    def get_display_value(self):
        """
        Get a formatted display value suitable for templates.

        Returns:
            Formatted string for display
        """
        typed_value = self.get_typed_value()

        if typed_value is None or typed_value == "":
            return ""

        attr_type = self.item_attribute.attribute_type

        if attr_type == ItemAttribute.AttributeType.BOOLEAN:
            return "Yes" if typed_value else "No"

        elif attr_type == ItemAttribute.AttributeType.DATE:
            try:
                date_obj = datetime.strptime(str(typed_value), '%Y-%m-%d')
                return date_obj.strftime('%B %d, %Y')
            except (ValueError, TypeError):
                return str(typed_value)

        elif attr_type == ItemAttribute.AttributeType.URL:
            # Return as-is, template will handle link rendering
            return str(typed_value)

        else:
            return str(typed_value)

    def validate(self):
        """
        Validate the stored value against the attribute's type and constraints.

        Raises:
            ValidationError: If validation fails
        """
        typed_value = self.get_typed_value()
        validated = self.item_attribute.validate_value(typed_value)
        # Re-store the validated value
        self.set_typed_value(validated)

    def save(self, *args, **kwargs):
        """
        Override save to validate before saving.
        """
        # Validate the value before saving
        if not self.item_attribute.skip_validation:
            self.validate()

        super().save(*args, **kwargs)


class CollectionImage(BerylModel):
    """
    Links MediaFile records to Collections for image management.
    Supports up to 3 images per collection with ordering and default selection.
    """
    collection = models.ForeignKey(
        Collection, 
        on_delete=models.CASCADE, 
        related_name="images",
        verbose_name=_("Collection")
    )
    media_file = models.ForeignKey(
        MediaFile, 
        on_delete=models.CASCADE, 
        related_name="collection_images",
        verbose_name=_("Media File")
    )
    is_default = models.BooleanField(
        default=False, 
        verbose_name=_("Default Image"),
        help_text=_("The primary image shown in collection displays")
    )
    order = models.IntegerField(
        default=0, 
        verbose_name=_("Display Order"),
        help_text=_("Order for thumbnail display (0-2)")
    )
    
    class Meta:
        verbose_name = _("Collection Image")
        verbose_name_plural = _("Collection Images")
        ordering = ["collection", "order"]
        unique_together = ["collection", "media_file"]
        indexes = [
            models.Index(fields=["collection", "is_default"]),
            models.Index(fields=["collection", "order"]),
        ]
    
    def __str__(self):
        return f"{self.collection.name} - {self.media_file.original_filename}"
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure media_file has correct media_type and handle default logic
        """
        # Ensure MediaFile has correct type
        if self.media_file.media_type != MediaFile.MediaType.COLLECTION_HEADER:
            self.media_file.media_type = MediaFile.MediaType.COLLECTION_HEADER
            self.media_file.save(update_fields=['media_type'])
        
        # Handle default image logic
        if self.is_default:
            # Unset other default images for this collection
            CollectionImage.objects.filter(
                collection=self.collection, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        # If this is the first image for the collection, make it default
        if not self.pk and not CollectionImage.objects.filter(collection=self.collection).exists():
            self.is_default = True
        
        super().save(*args, **kwargs)
    
    @classmethod
    def can_add_image(cls, collection):
        """Check if collection can accept another image (max 3)"""
        return cls.objects.filter(collection=collection).count() < 3


class CollectionItemImage(BerylModel):
    """
    Links MediaFile records to CollectionItems for image management.
    Supports up to 3 images per item with ordering and default selection.
    """
    item = models.ForeignKey(
        CollectionItem, 
        on_delete=models.CASCADE, 
        related_name="images",
        verbose_name=_("Collection Item")
    )
    media_file = models.ForeignKey(
        MediaFile, 
        on_delete=models.CASCADE, 
        related_name="item_images",
        verbose_name=_("Media File")
    )
    is_default = models.BooleanField(
        default=False, 
        verbose_name=_("Default Image"),
        help_text=_("The primary image shown in item displays")
    )
    order = models.IntegerField(
        default=0, 
        verbose_name=_("Display Order"),
        help_text=_("Order for thumbnail display (0-2)")
    )
    
    class Meta:
        verbose_name = _("Collection Item Image")
        verbose_name_plural = _("Collection Item Images")
        ordering = ["item", "order"]
        unique_together = ["item", "media_file"]
        indexes = [
            models.Index(fields=["item", "is_default"]),
            models.Index(fields=["item", "order"]),
        ]
    
    def __str__(self):
        return f"{self.item.name} - {self.media_file.original_filename}"
    
    def save(self, *args, **kwargs):
        """
        Override save to ensure media_file has correct media_type and handle default logic
        """
        # Ensure MediaFile has correct type
        if self.media_file.media_type != MediaFile.MediaType.COLLECTION_ITEM:
            self.media_file.media_type = MediaFile.MediaType.COLLECTION_ITEM
            self.media_file.save(update_fields=['media_type'])
        
        # Handle default image logic
        if self.is_default:
            # Unset other default images for this item
            CollectionItemImage.objects.filter(
                item=self.item, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        # If this is the first image for the item, make it default
        if not self.pk and not CollectionItemImage.objects.filter(item=self.item).exists():
            self.is_default = True
        
        super().save(*args, **kwargs)
    
    @classmethod
    def can_add_image(cls, item):
        """Check if item can accept another image (max 3)"""
        return cls.objects.filter(item=item).count() < 3


# Import user profile models
from .models_user_profile import UserProfile

# Import metrics models
from .models_metrics import DailyMetrics
