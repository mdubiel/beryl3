# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging
import urllib.parse

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.db import models
from django.urls import reverse
from django.contrib.sites.models import Site
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
        self.save()

    def undelete(self):
        """A method to restore a soft-deleted object."""
        self.is_deleted = False
        self.save()


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
        protocol = 'https' # if settings.SECURE_PROXY_SSL_HEADER else 'http' # Adjust based on your setup
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
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    image_url = models.URLField(blank=True, null=True, verbose_name="Image URL")

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
        """Returns True only if the item is in the 'Wanted' status."""
        return self.status == self.Status.WANTED


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
        actor_name = self.created_by.username if self.created_by else "System"
        return f"'{self.get_name_display()}' by {actor_name} for {self.subject}"
