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
    
    class Meta:
        verbose_name = _("Media File")
        verbose_name_plural = _("Media Files")
        ordering = ["-created"]
        indexes = [
            models.Index(fields=['media_type', 'storage_backend']),
            models.Index(fields=['file_exists', 'last_verified']),
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
        Override save to set storage backend based on current configuration
        """
        if not self.storage_backend:
            # Determine storage backend based on current settings
            use_gcs = getattr(settings, 'USE_GCS_STORAGE', False)
            is_production = not getattr(settings, 'DEBUG', True)
            
            if is_production or use_gcs:
                self.storage_backend = self.StorageBackend.GCS
            else:
                self.storage_backend = self.StorageBackend.LOCAL
        
        super().save(*args, **kwargs)


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
        Get all attributes for display, ordered by the attribute definition order
        """
        if not self.item_type:
            return []
        
        result = []
        for attr in self.item_type.attributes.all():
            value = self.attributes.get(attr.name)
            if value is not None:
                result.append({
                    'attribute': attr,
                    'value': value,
                    'display_value': self._format_attribute_value(attr, value)
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


ACTION_ATTRIBUTES = {
    "USER_JOINED": {
        "label": _("User Joined"),
        "icon": "party-popper",
        "style": "bg-accent",
        "description": "Your journey of collecting began!",
    },
    "COLLECTION_CREATED": {
        "label": _("Collection Created"),
        "icon": "plus",
        "style": "bg-success",
        "description": 'You created the collection "{target}".',
    },
    "COLLECTION_DELETED": {
        "label": _("Collection Deleted"),
        "icon": "trash-2",
        "style": "bg-error",
        "description": 'You deleted the collection "{target}".',
    },
    "ITEM_ADDED": {
        "label": _("Item Added"),
        "icon": "archive",
        "style": "bg-success",
        "description": 'You added the item <strong>"{target}"</strong> to your collection.',
    },
    "ITEM_WANTED": {
        "label": _("Item Wanted"),
        "icon": "star",
        "style": "bg-info",
        "description": 'You added <strong>"{target}"</strong> to your wishlist.',
    },
    "ITEM_ORDERED": {
        "label": _("Item Ordered"),
        "icon": "truck",
        "style": "bg-blue-500",
        "description": 'You marked <strong>"{target}"</strong> as ordered. It\'s on its way!',
    },
    "ITEM_RESERVED": {
        "label": _("Item Reserved"),
        "icon": "gift",
        "style": "bg-warning",
        "description": 'An item, <strong>"{target}"</strong>, was reserved from your wishlist.',
    },
    "ITEM_LENT": {
        "label": _("Item Lent"),
        "icon": "share-2",
        "style": "bg-neutral",
        "description": 'You lent out your item: <strong>"{target}"</strong>.',
    },
    "ITEM_PREVIOUSLY_OWNED": {
        "label": _("Item Previously Owned"),
        "icon": "history",
        "style": "bg-base-300",
        "description": 'You marked <strong>"{target}"</strong> as previously owned.',
    },
    "ITEM_REMOVED": {
        "label": _("Item Removed"),
        "icon": "archive-x",
        "style": "bg-error",
        "description": 'You removed the item <strong>"{target}"</strong> from your collection.',
    },
    "ITEM_FAVORITED": {
        "label": _("Item Favorited"),
        "icon": "star",
        "style": "bg-warning",
        "description": 'You marked <strong>"{target}"</strong> as a favorite.',
    },
    "ITEM_UNFAVORITED": {
        "label": _("Item Unfavorited"),
        "icon": "star-off",
        "style": "bg-neutral",
        "description": 'You removed <strong>"{target}"</strong> from your favorites.',
    },
}


class RecentActivity(BerylModel):
    """
    Inherits from BerylModel to store a log of significant events.
    All attributes for an action (verb, icon, style, description) are
    defined in the central ACTION_ATTRIBUTES dictionary.
    """

    class ActionVerb(models.TextChoices):
        USER_JOINED = "USER_JOINED", ACTION_ATTRIBUTES["USER_JOINED"]["label"]
        COLLECTION_CREATED = "COLLECTION_CREATED", ACTION_ATTRIBUTES["COLLECTION_CREATED"]["label"]
        COLLECTION_DELETED = "COLLECTION_DELETED", ACTION_ATTRIBUTES["COLLECTION_DELETED"]["label"]
        ITEM_ADDED = "ITEM_ADDED", ACTION_ATTRIBUTES["ITEM_ADDED"]["label"]
        ITEM_WANTED = "ITEM_WANTED", ACTION_ATTRIBUTES["ITEM_WANTED"]["label"]
        ITEM_ORDERED = "ITEM_ORDERED", ACTION_ATTRIBUTES["ITEM_ORDERED"]["label"]
        ITEM_RESERVED = "ITEM_RESERVED", ACTION_ATTRIBUTES["ITEM_RESERVED"]["label"]
        ITEM_LENT = "ITEM_LENT", ACTION_ATTRIBUTES["ITEM_LENT"]["label"]
        ITEM_PREVIOUSLY_OWNED = "ITEM_PREVIOUSLY_OWNED", ACTION_ATTRIBUTES["ITEM_PREVIOUSLY_OWNED"]["label"]
        ITEM_REMOVED = "ITEM_REMOVED", ACTION_ATTRIBUTES["ITEM_REMOVED"]["label"]
        ITEM_FAVORITED = "ITEM_FAVORITED", ACTION_ATTRIBUTES["ITEM_FAVORITED"]["label"]
        ITEM_UNFAVORITED = "ITEM_UNFAVORITED", ACTION_ATTRIBUTES["ITEM_UNFAVORITED"]["label"]

    subject = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="timeline_events",
        help_text="The user whose timeline this event belongs to.",
    )
    name = models.CharField(max_length=50, choices=ActionVerb.choices, verbose_name=_("Action Verb"))
    target_repr = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    details = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Recent Activity"
        verbose_name_plural = "Recent Activities"

    @property
    def _attributes(self):
        """A helper to safely get the attribute dictionary for the current verb."""
        return ACTION_ATTRIBUTES.get(self.name, {})

    @property
    def icon(self):
        return self._attributes.get("icon", "activity")

    @property
    def icon_style(self):
        return self._attributes.get("style", "bg-neutral")

    def __str__(self):
        actor_name = getattr(self.created_by, 'username', 'System') if self.created_by else "System"
        subject_name = getattr(self.subject, 'username', 'Unknown') if self.subject else "Unknown"
        return f"'{self.name}' by {actor_name} for {subject_name}"


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
