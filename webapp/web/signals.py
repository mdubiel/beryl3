# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging
from django.utils import timezone

from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from web.models import Collection, CollectionItem, CollectionImage, CollectionItemImage, CollectionItemLink

logger = logging.getLogger('webapp')

# ============================================================================
# Helper Functions for Timestamp Updates
# ============================================================================

def update_collection_timestamp(collection):
    """
    Helper function to update a collection's timestamp
    """
    try:
        if collection and not collection.is_deleted:
            Collection.objects.filter(pk=collection.pk).update(updated=timezone.now())
            logger.debug("Updated timestamp for Collection %s", collection.hash)
    except (AttributeError, TypeError, ValueError) as e:
        logger.error("Error updating collection timestamp: %s", str(e))

def update_item_timestamp(item):
    """
    Helper function to update an item's timestamp
    """
    try:
        if item and not item.is_deleted:
            CollectionItem.objects.filter(pk=item.pk).update(updated=timezone.now())
            logger.debug("Updated timestamp for CollectionItem %s", item.hash)
    except (AttributeError, TypeError, ValueError) as e:
        logger.error("Error updating item timestamp: %s", str(e))

# ============================================================================
# Collection Timestamp Update Signals
# ============================================================================

@receiver(post_save, sender=CollectionItem)
def update_collection_on_item_save(sender, instance, created, **kwargs):
    # pylint: disable=unused-argument
    """
    Update collection timestamp when an item is saved
    """
    if instance.collection:
        update_collection_timestamp(instance.collection)

@receiver(post_delete, sender=CollectionItem)
def update_collection_on_item_delete(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    """
    Update collection timestamp when an item is deleted
    """
    if instance.collection:
        update_collection_timestamp(instance.collection)

@receiver(post_save, sender=CollectionImage)
def update_collection_on_collection_image_save(sender, instance, created, **kwargs):
    # pylint: disable=unused-argument
    """
    Update collection timestamp when a collection image is saved
    """
    if instance.collection:
        update_collection_timestamp(instance.collection)

@receiver(post_delete, sender=CollectionImage)
def update_collection_on_collection_image_delete(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    """
    Update collection timestamp when a collection image is deleted
    """
    if instance.collection:
        update_collection_timestamp(instance.collection)

@receiver(post_save, sender=CollectionItemImage)
def update_collection_on_item_image_save(sender, instance, created, **kwargs):
    # pylint: disable=unused-argument
    """
    Update collection and item timestamps when an item image is saved
    """
    if instance.item:
        update_item_timestamp(instance.item)
        if instance.item.collection:
            update_collection_timestamp(instance.item.collection)

@receiver(post_delete, sender=CollectionItemImage)
def update_collection_on_item_image_delete(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    """
    Update collection and item timestamps when an item image is deleted
    """
    if instance.item:
        update_item_timestamp(instance.item)
        if instance.item.collection:
            update_collection_timestamp(instance.item.collection)

@receiver(post_save, sender=CollectionItemLink)
def update_collection_on_item_link_save(sender, instance, created, **kwargs):
    # pylint: disable=unused-argument
    """
    Update collection and item timestamps when an item link is saved
    """
    if instance.item:
        update_item_timestamp(instance.item)
        if instance.item.collection:
            update_collection_timestamp(instance.item.collection)

@receiver(post_delete, sender=CollectionItemLink)
def update_collection_on_item_link_delete(sender, instance, **kwargs):
    # pylint: disable=unused-argument
    """
    Update collection and item timestamps when an item link is deleted
    """
    if instance.item:
        update_item_timestamp(instance.item)
        if instance.item.collection:
            update_collection_timestamp(instance.item.collection)

# ============================================================================
# Disabled automatic logging - using manual RecentActivity calls in views
# ============================================================================

# @receiver(user_logged_in)
# def log_user_first_login(sender, request, user, **kwargs):
#     """Logs when a user logs in for the very first time."""
#     pass

# @receiver(post_save, sender=Collection)
# def log_collection_activity(sender, instance: Collection, created, **kwargs):
#     """Logs when a Collection is created or soft-deleted."""
#     pass

# @receiver(post_save, sender=CollectionItem)
# def log_item_activity(sender, instance: CollectionItem, created, **kwargs):
#     """Logs when a CollectionItem is created, soft-deleted, or its status changes."""
#     pass
