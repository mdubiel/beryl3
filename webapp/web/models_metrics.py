"""
Daily Metrics Model

This module contains the DailyMetrics model for collecting and storing
daily system metrics snapshots.
"""

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from decimal import Decimal


class DailyMetrics(models.Model):
    """
    Daily snapshot of system metrics.

    One record is created per day containing all key metrics for trending
    and monitoring purposes. Metrics are collected via management command
    and displayed in the /sys/metrics dashboard.
    """

    # Timestamp
    collected_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When metrics were collected")
    )
    collection_date = models.DateField(
        unique=True,
        help_text=_("Date of metrics snapshot (one per day)")
    )
    collection_duration_seconds = models.IntegerField(
        default=0,
        help_text=_("How long collection took in seconds")
    )

    # === USERS ===
    total_users = models.IntegerField(
        default=0,
        help_text=_("Total registered users")
    )
    active_users_24h = models.IntegerField(
        default=0,
        help_text=_("Users active in last 24 hours")
    )
    active_users_7d = models.IntegerField(
        default=0,
        help_text=_("Users active in last 7 days")
    )
    active_users_30d = models.IntegerField(
        default=0,
        help_text=_("Users active in last 30 days")
    )
    new_users_24h = models.IntegerField(
        default=0,
        help_text=_("New users in last 24 hours")
    )
    new_users_7d = models.IntegerField(
        default=0,
        help_text=_("New users in last 7 days")
    )
    new_users_30d = models.IntegerField(
        default=0,
        help_text=_("New users in last 30 days")
    )

    # === COLLECTIONS & ITEMS ===
    total_collections = models.IntegerField(
        default=0,
        help_text=_("Total collections")
    )
    total_items = models.IntegerField(
        default=0,
        help_text=_("Total items across all collections")
    )
    collections_private = models.IntegerField(
        default=0,
        help_text=_("Private collections count")
    )
    collections_public = models.IntegerField(
        default=0,
        help_text=_("Public collections count")
    )
    collections_unlisted = models.IntegerField(
        default=0,
        help_text=_("Unlisted collections count")
    )

    # === ITEM STATUS DISTRIBUTION ===
    items_in_collection = models.IntegerField(
        default=0,
        help_text=_("Items with status: In Collection")
    )
    items_wanted = models.IntegerField(
        default=0,
        help_text=_("Items with status: Wanted")
    )
    items_reserved = models.IntegerField(
        default=0,
        help_text=_("Items with status: Reserved")
    )
    items_ordered = models.IntegerField(
        default=0,
        help_text=_("Items with status: Ordered")
    )
    items_lent = models.IntegerField(
        default=0,
        help_text=_("Items with status: Lent")
    )
    items_previously_owned = models.IntegerField(
        default=0,
        help_text=_("Items with status: Previously Owned")
    )
    items_sold = models.IntegerField(
        default=0,
        help_text=_("Items with status: Sold")
    )
    items_given_away = models.IntegerField(
        default=0,
        help_text=_("Items with status: Given Away")
    )

    # === ITEM TYPES & ATTRIBUTES ===
    item_types_count = models.IntegerField(
        default=0,
        help_text=_("Total item types defined")
    )
    item_type_distribution = models.JSONField(
        default=dict,
        help_text=_("Distribution of items by type {type_name: count}")
    )
    total_attributes = models.IntegerField(
        default=0,
        help_text=_("Total attribute definitions")
    )
    attribute_usage = models.JSONField(
        default=dict,
        help_text=_("Attribute usage statistics {attr_name: count}")
    )

    # === LINKS ===
    total_links = models.IntegerField(
        default=0,
        help_text=_("Total links in items and collections")
    )
    matched_link_patterns = models.IntegerField(
        default=0,
        help_text=_("Links matching defined patterns")
    )
    unmatched_link_patterns = models.IntegerField(
        default=0,
        help_text=_("Links not matching any pattern")
    )
    link_pattern_distribution = models.JSONField(
        default=dict,
        help_text=_("Link usage by pattern {pattern_name: count}")
    )

    # === STORAGE ===
    total_media_files = models.IntegerField(
        default=0,
        help_text=_("Total media files")
    )
    total_storage_bytes = models.BigIntegerField(
        default=0,
        help_text=_("Total storage used in bytes")
    )
    recent_uploads_24h = models.IntegerField(
        default=0,
        help_text=_("Media files uploaded in last 24h")
    )
    recent_uploads_7d = models.IntegerField(
        default=0,
        help_text=_("Media files uploaded in last 7 days")
    )
    recent_uploads_30d = models.IntegerField(
        default=0,
        help_text=_("Media files uploaded in last 30 days")
    )
    orphaned_files = models.IntegerField(
        default=0,
        help_text=_("Media files not linked to items/collections")
    )
    corrupted_files = models.IntegerField(
        default=0,
        help_text=_("Media files that failed integrity check")
    )
    storage_by_type = models.JSONField(
        default=dict,
        help_text=_("Storage distribution by file type {ext: bytes}")
    )

    # === EMAIL ===
    total_emails = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Total emails tracked")
    )
    emails_pending = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Emails pending delivery")
    )
    emails_sent = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Emails successfully sent")
    )
    emails_failed = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Emails that failed to send")
    )
    marketing_opt_in = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Users opted in to marketing")
    )
    marketing_opt_out = models.IntegerField(
        null=True,
        blank=True,
        help_text=_("Users opted out of marketing")
    )
    emails_synced_resend = models.BooleanField(
        default=False,
        help_text=_("Whether email stats are synced with Resend")
    )

    # === CONTENT MODERATION ===
    flagged_content = models.IntegerField(
        default=0,
        help_text=_("Content items flagged for review")
    )
    pending_review = models.IntegerField(
        default=0,
        help_text=_("Content items pending moderation")
    )
    user_violations = models.IntegerField(
        default=0,
        help_text=_("Total user violations")
    )
    banned_users = models.IntegerField(
        default=0,
        help_text=_("Currently banned users")
    )

    # === ENGAGEMENT METRICS ===
    favorite_items_total = models.IntegerField(
        default=0,
        help_text=_("Total favorited items")
    )
    items_with_images_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Percentage of items with images")
    )
    items_with_attributes_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Percentage of items with custom attributes")
    )
    items_with_links_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Percentage of items with links")
    )
    avg_attributes_per_item = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Average attributes per item")
    )
    avg_items_per_collection = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_("Average items per collection")
    )

    # === ACTIVITY METRICS ===
    items_created_24h = models.IntegerField(
        default=0,
        help_text=_("Items created in last 24h")
    )
    items_created_7d = models.IntegerField(
        default=0,
        help_text=_("Items created in last 7 days")
    )
    items_created_30d = models.IntegerField(
        default=0,
        help_text=_("Items created in last 30 days")
    )
    collections_created_24h = models.IntegerField(
        default=0,
        help_text=_("Collections created in last 24h")
    )
    collections_created_7d = models.IntegerField(
        default=0,
        help_text=_("Collections created in last 7 days")
    )
    collections_created_30d = models.IntegerField(
        default=0,
        help_text=_("Collections created in last 30 days")
    )

    class Meta:
        verbose_name = _("Daily Metrics")
        verbose_name_plural = _("Daily Metrics")
        ordering = ['-collection_date']
        indexes = [
            models.Index(fields=['-collection_date']),
            models.Index(fields=['collected_at']),
        ]

    def __str__(self):
        return f"Metrics for {self.collection_date}"

    def get_change(self, field_name, days_ago=1):
        """
        Calculate change from N days ago for a given metric field.

        Args:
            field_name: Name of the metric field
            days_ago: How many days back to compare (1, 7, or 30)

        Returns:
            dict with 'value', 'change', 'change_pct', 'direction' (+1, 0, -1)
        """
        from datetime import timedelta

        current_value = getattr(self, field_name, 0)
        if current_value is None:
            current_value = 0

        compare_date = self.collection_date - timedelta(days=days_ago)

        try:
            previous = DailyMetrics.objects.get(collection_date=compare_date)
            previous_value = getattr(previous, field_name, 0)
            if previous_value is None:
                previous_value = 0
        except DailyMetrics.DoesNotExist:
            return {
                'value': current_value,
                'change': None,
                'change_pct': None,
                'direction': 0
            }

        change = current_value - previous_value
        change_pct = (change / previous_value * 100) if previous_value != 0 else 0
        direction = 1 if change > 0 else (-1 if change < 0 else 0)

        return {
            'value': current_value,
            'previous': previous_value,
            'change': change,
            'change_pct': round(change_pct, 2),
            'direction': direction
        }

    @classmethod
    def cleanup_old_records(cls, days_to_keep=365):
        """Delete metrics older than specified days."""
        from datetime import timedelta
        cutoff_date = timezone.now().date() - timedelta(days=days_to_keep)
        deleted_count = cls.objects.filter(collection_date__lt=cutoff_date).count()
        cls.objects.filter(collection_date__lt=cutoff_date).delete()
        return deleted_count
