# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging
import re
import urllib.parse
from datetime import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ValidationError
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
