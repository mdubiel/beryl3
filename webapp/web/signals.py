# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from web.models import Collection, CollectionItem, RecentActivity, ACTION_ATTRIBUTES

logger = logging.getLogger('webapp')

@receiver(user_logged_in)
def log_user_first_login(sender, request, user, **kwargs):
    """Logs when a user logs in for the very first time."""
    if user.last_login and (user.last_login - user.date_joined).total_seconds() < 5:
        RecentActivity.objects.create(
            created_by=user,
            subject=user,
            name=RecentActivity.ActionVerb.USER_JOINED,
            target_repr=str(user),
            description="Welcome! You created your account.",
            details={'user_id': user.id, 'username': user.username}
        )

@receiver(post_save, sender=Collection)
def log_collection_activity(sender, instance: Collection, created, **kwargs):
    """Logs when a Collection is created or soft-deleted."""
    if created:
        RecentActivity.objects.create(
            created_by=instance.created_by,
            subject=instance.created_by,
            name=RecentActivity.ActionVerb.COLLECTION_CREATED,
            target_repr=str(instance),
            description=f'You created the collection <strong>"{instance.name}"</strong>.',
            details={'collection_hash': instance.hash, 'collection_name': instance.name}
        )
    elif instance.is_deleted and kwargs.get('update_fields') and 'is_deleted' in kwargs['update_fields']:
        RecentActivity.objects.create(
            created_by=instance.created_by,
            subject=instance.created_by,
            name=RecentActivity.ActionVerb.COLLECTION_DELETED,
            target_repr=str(instance),
            description=f'You deleted the collection <strong>"{instance.name}"</strong>.',
            details={'collection_hash': instance.hash, 'collection_name': instance.name}
        )

@receiver(post_save, sender=CollectionItem)
def log_item_activity(sender, instance: CollectionItem, created, **kwargs):
    """
    Logs when a CollectionItem is created, soft-deleted, or its status changes.
    """
    verb = None

    if created:
        if instance.status == CollectionItem.Status.IN_COLLECTION:
            verb = RecentActivity.ActionVerb.ITEM_ADDED
        elif instance.status == CollectionItem.Status.WANTED:
            verb = RecentActivity.ActionVerb.ITEM_WANTED

    elif instance.is_deleted and kwargs.get('update_fields') and 'is_deleted' in kwargs['update_fields']:
        verb = RecentActivity.ActionVerb.ITEM_REMOVED

    elif not created and kwargs.get('update_fields') and 'status' in kwargs['update_fields']:
        status_to_verb_map = {
            CollectionItem.Status.RESERVED: RecentActivity.ActionVerb.ITEM_RESERVED,
            CollectionItem.Status.ORDERED: RecentActivity.ActionVerb.ITEM_ORDERED,
            CollectionItem.Status.LENT_OUT: RecentActivity.ActionVerb.ITEM_LENT,
            CollectionItem.Status.PREVIOUSLY_OWNED: RecentActivity.ActionVerb.ITEM_PREVIOUSLY_OWNED,
            CollectionItem.Status.IN_COLLECTION: RecentActivity.ActionVerb.ITEM_ADDED,
            CollectionItem.Status.WANTED: RecentActivity.ActionVerb.ITEM_WANTED,
        }
        verb = status_to_verb_map.get(instance.status)

    if verb:
        subject_user = instance.collection.created_by
        actor_user = instance.created_by or subject_user

        description_template = ACTION_ATTRIBUTES[verb]['description']
        description_text = description_template.format(target=instance.name)

        RecentActivity.objects.create(
            created_by=actor_user,
            subject=subject_user,
            name=verb,
            target_repr=str(instance),
            description=description_text,
            details={
                'item_hash': instance.hash,
                'item_name': instance.name,
                'collection_name': instance.collection.name
            }
        )
