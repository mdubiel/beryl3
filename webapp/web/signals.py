# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from web.models import Collection, CollectionItem, RecentActivity

logger = logging.getLogger('webapp')

# Disabled automatic logging - using manual RecentActivity calls in views
# @receiver(user_logged_in)
# def log_user_first_login(sender, request, user, **kwargs):
#     """Logs when a user logs in for the very first time."""
#     pass

# Disabled automatic logging - using manual RecentActivity calls in views
# @receiver(post_save, sender=Collection)
# def log_collection_activity(sender, instance: Collection, created, **kwargs):
#     """Logs when a Collection is created or soft-deleted."""
#     pass

# Disabled automatic logging - using manual RecentActivity calls in views
# @receiver(post_save, sender=CollectionItem)
# def log_item_activity(sender, instance: CollectionItem, created, **kwargs):
#     """Logs when a CollectionItem is created, soft-deleted, or its status changes."""
#     pass
