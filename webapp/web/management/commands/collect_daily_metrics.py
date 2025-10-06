"""
Management command to collect daily metrics.

This command collects comprehensive system metrics and stores them in the
DailyMetrics model. It should be run daily via cron job, preferably at midnight
Europe/Zurich timezone.

Usage:
    python manage.py collect_daily_metrics [--date YYYY-MM-DD] [--send-email] [--verbose]
"""

import time
from datetime import date, datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

import pytz

from web.models import (
    DailyMetrics,
    Collection,
    CollectionItem,
    ItemType,
    ItemAttribute,
    CollectionItemLink,
    LinkPattern,
    MediaFile,
    RecentActivity,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Collect daily system metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to collect metrics for (YYYY-MM-DD), defaults to today'
        )
        parser.add_argument(
            '--send-email',
            action='store_true',
            help='Send email report to superusers'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress'
        )

    def handle(self, *args, **options):
        start_time = time.time()

        # Determine collection date
        if options['date']:
            try:
                collection_date = datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError('Invalid date format. Use YYYY-MM-DD')
        else:
            # Use Europe/Zurich timezone
            zurich_tz = pytz.timezone('Europe/Zurich')
            collection_date = datetime.now(zurich_tz).date()

        self.stdout.write(f"Collecting metrics for {collection_date}...")

        # Check if metrics already exist for this date
        if DailyMetrics.objects.filter(collection_date=collection_date).exists():
            if not options.get('force'):
                raise CommandError(
                    f'Metrics for {collection_date} already exist. '
                    'Use --force to overwrite (not yet implemented)'
                )

        # Initialize metrics dictionary
        metrics = {}

        # Collect all metrics
        self._collect_user_metrics(metrics, collection_date, options['verbose'])
        self._collect_collection_metrics(metrics, collection_date, options['verbose'])
        self._collect_item_metrics(metrics, collection_date, options['verbose'])
        self._collect_link_metrics(metrics, collection_date, options['verbose'])
        self._collect_storage_metrics(metrics, collection_date, options['verbose'])
        self._collect_email_metrics(metrics, collection_date, options['verbose'])
        self._collect_moderation_metrics(metrics, collection_date, options['verbose'])
        self._collect_engagement_metrics(metrics, collection_date, options['verbose'])
        self._collect_activity_metrics(metrics, collection_date, options['verbose'])

        # Calculate duration
        duration = int(time.time() - start_time)
        metrics['collection_duration_seconds'] = duration

        # Create metrics record
        daily_metrics = DailyMetrics.objects.create(
            collection_date=collection_date,
            **metrics
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Metrics collected successfully in {duration}s'
            )
        )

        # Send email report if requested
        if options['send_email']:
            self._send_email_report(daily_metrics)

        # Cleanup old records
        retention_days = getattr(settings, 'METRICS_RETENTION_DAYS', 365)
        deleted = DailyMetrics.cleanup_old_records(retention_days)
        if deleted > 0:
            self.stdout.write(f"Cleaned up {deleted} old metrics records")

    def _collect_user_metrics(self, metrics, collection_date, verbose=False):
        """Collect user-related metrics."""
        if verbose:
            self.stdout.write("  Collecting user metrics...")

        now = timezone.now()
        metrics['total_users'] = User.objects.count()

        # Active users (based on last_login)
        metrics['active_users_24h'] = User.objects.filter(
            last_login__gte=now - timedelta(hours=24)
        ).count()
        metrics['active_users_7d'] = User.objects.filter(
            last_login__gte=now - timedelta(days=7)
        ).count()
        metrics['active_users_30d'] = User.objects.filter(
            last_login__gte=now - timedelta(days=30)
        ).count()

        # New users
        metrics['new_users_24h'] = User.objects.filter(
            date_joined__gte=now - timedelta(hours=24)
        ).count()
        metrics['new_users_7d'] = User.objects.filter(
            date_joined__gte=now - timedelta(days=7)
        ).count()
        metrics['new_users_30d'] = User.objects.filter(
            date_joined__gte=now - timedelta(days=30)
        ).count()

        if verbose:
            self.stdout.write(f"    Total users: {metrics['total_users']}")

    def _collect_collection_metrics(self, metrics, collection_date, verbose=False):
        """Collect collection-related metrics."""
        if verbose:
            self.stdout.write("  Collecting collection metrics...")

        metrics['total_collections'] = Collection.objects.count()

        # Visibility distribution
        visibility_counts = Collection.objects.values('visibility').annotate(
            count=Count('id')
        )

        metrics['collections_private'] = 0
        metrics['collections_public'] = 0
        metrics['collections_unlisted'] = 0

        for vc in visibility_counts:
            if vc['visibility'] == 'PRIVATE':
                metrics['collections_private'] = vc['count']
            elif vc['visibility'] == 'PUBLIC':
                metrics['collections_public'] = vc['count']
            elif vc['visibility'] == 'UNLISTED':
                metrics['collections_unlisted'] = vc['count']

        # Collections created
        now = timezone.now()
        metrics['collections_created_24h'] = Collection.objects.filter(
            created__gte=now - timedelta(hours=24)
        ).count()
        metrics['collections_created_7d'] = Collection.objects.filter(
            created__gte=now - timedelta(days=7)
        ).count()
        metrics['collections_created_30d'] = Collection.objects.filter(
            created__gte=now - timedelta(days=30)
        ).count()

    def _collect_item_metrics(self, metrics, collection_date, verbose=False):
        """Collect item-related metrics."""
        if verbose:
            self.stdout.write("  Collecting item metrics...")

        metrics['total_items'] = CollectionItem.objects.count()

        # Status distribution
        status_counts = CollectionItem.objects.values('status').annotate(
            count=Count('id')
        )

        # Initialize all status counts
        metrics['items_in_collection'] = 0
        metrics['items_wanted'] = 0
        metrics['items_reserved'] = 0
        metrics['items_ordered'] = 0
        metrics['items_lent'] = 0
        metrics['items_previously_owned'] = 0
        metrics['items_sold'] = 0
        metrics['items_given_away'] = 0

        for sc in status_counts:
            status = sc['status']
            if status == 'IN_COLLECTION':
                metrics['items_in_collection'] = sc['count']
            elif status == 'WANTED':
                metrics['items_wanted'] = sc['count']
            elif status == 'RESERVED':
                metrics['items_reserved'] = sc['count']
            elif status == 'ORDERED':
                metrics['items_ordered'] = sc['count']
            elif status == 'LENT':
                metrics['items_lent'] = sc['count']
            elif status == 'PREVIOUSLY_OWNED':
                metrics['items_previously_owned'] = sc['count']
            elif status == 'SOLD':
                metrics['items_sold'] = sc['count']
            elif status == 'GIVEN_AWAY':
                metrics['items_given_away'] = sc['count']

        # Item types
        metrics['item_types_count'] = ItemType.objects.count()

        # Item type distribution
        type_distribution = CollectionItem.objects.filter(
            item_type__isnull=False
        ).values('item_type__display_name').annotate(
            count=Count('id')
        ).order_by('-count')[:20]  # Top 20
        metrics['item_type_distribution'] = {
            item['item_type__display_name']: item['count']
            for item in type_distribution
        }

        # Attributes
        metrics['total_attributes'] = ItemAttribute.objects.count()

        # Attribute usage (top 20)
        attr_usage = ItemAttribute.objects.values('display_name').annotate(
            count=Count('id')
        ).order_by('-count')[:20]
        metrics['attribute_usage'] = {
            attr['display_name']: attr['count']
            for attr in attr_usage
        }

        # Items created
        now = timezone.now()
        metrics['items_created_24h'] = CollectionItem.objects.filter(
            created__gte=now - timedelta(hours=24)
        ).count()
        metrics['items_created_7d'] = CollectionItem.objects.filter(
            created__gte=now - timedelta(days=7)
        ).count()
        metrics['items_created_30d'] = CollectionItem.objects.filter(
            created__gte=now - timedelta(days=30)
        ).count()

    def _collect_link_metrics(self, metrics, collection_date, verbose=False):
        """Collect link-related metrics."""
        if verbose:
            self.stdout.write("  Collecting link metrics...")

        metrics['total_links'] = CollectionItemLink.objects.count()

        # Links with/without patterns
        metrics['matched_link_patterns'] = CollectionItemLink.objects.filter(
            link_pattern__isnull=False
        ).count()
        metrics['unmatched_link_patterns'] = CollectionItemLink.objects.filter(
            link_pattern__isnull=True
        ).count()

        # Link pattern distribution
        pattern_dist = CollectionItemLink.objects.filter(
            link_pattern__isnull=False
        ).values('link_pattern__display_name').annotate(
            count=Count('id')
        ).order_by('-count')[:20]
        metrics['link_pattern_distribution'] = {
            p['link_pattern__display_name']: p['count']
            for p in pattern_dist
        }

    def _collect_storage_metrics(self, metrics, collection_date, verbose=False):
        """Collect storage and media metrics."""
        if verbose:
            self.stdout.write("  Collecting storage metrics...")

        metrics['total_media_files'] = MediaFile.objects.count()

        # Total storage
        total_bytes = MediaFile.objects.aggregate(
            total=Sum('file_size')
        )['total'] or 0
        metrics['total_storage_bytes'] = total_bytes

        # Recent uploads
        now = timezone.now()
        metrics['recent_uploads_24h'] = MediaFile.objects.filter(
            created__gte=now - timedelta(hours=24)
        ).count()
        metrics['recent_uploads_7d'] = MediaFile.objects.filter(
            created__gte=now - timedelta(days=7)
        ).count()
        metrics['recent_uploads_30d'] = MediaFile.objects.filter(
            created__gte=now - timedelta(days=30)
        ).count()

        # Orphaned files (files not linked to collections or items)
        # Count files that are not linked to any collection or item image
        orphaned = MediaFile.objects.filter(
            collection_images__isnull=True,
            item_images__isnull=True
        ).count()
        metrics['orphaned_files'] = orphaned

        # Corrupted files (files with integrity issues)
        corrupted = MediaFile.objects.filter(
            file_exists=False
        ).count()
        metrics['corrupted_files'] = corrupted

        # Storage by type
        storage_by_type = MediaFile.objects.values('media_type').annotate(
            total_size=Sum('file_size')
        ).order_by('-total_size')[:10]
        metrics['storage_by_type'] = {
            s['media_type'] or 'unknown': s['total_size']
            for s in storage_by_type
        }

        if verbose:
            self.stdout.write(f"    Total storage: {total_bytes / (1024**3):.2f} GB")

    def _collect_email_metrics(self, metrics, collection_date, verbose=False):
        """Collect email-related metrics (from Resend if available)."""
        if verbose:
            self.stdout.write("  Collecting email metrics...")

        # Placeholder for Resend integration
        # TODO: Integrate with Resend API to get email statistics
        metrics['total_emails'] = None
        metrics['emails_pending'] = None
        metrics['emails_sent'] = None
        metrics['emails_failed'] = None

        # Marketing consent (if UserProfile has these fields)
        try:
            from web.models import UserProfile
            metrics['marketing_opt_in'] = UserProfile.objects.filter(
                marketing_consent=True
            ).count()
            metrics['marketing_opt_out'] = UserProfile.objects.filter(
                marketing_consent=False
            ).count()
        except:
            metrics['marketing_opt_in'] = None
            metrics['marketing_opt_out'] = None

        metrics['emails_synced_resend'] = False

    def _collect_moderation_metrics(self, metrics, collection_date, verbose=False):
        """Collect content moderation metrics."""
        if verbose:
            self.stdout.write("  Collecting moderation metrics...")

        # Flagged content
        metrics['flagged_content'] = MediaFile.objects.filter(
            content_moderation_status='FLAGGED'
        ).count() if hasattr(MediaFile, 'content_moderation_status') else 0

        # Pending review
        metrics['pending_review'] = MediaFile.objects.filter(
            content_moderation_status='PENDING'
        ).count() if hasattr(MediaFile, 'content_moderation_status') else 0

        # User violations
        try:
            from web.models import UserProfile
            metrics['user_violations'] = UserProfile.objects.filter(
                violations_count__gt=0
            ).count()
            metrics['banned_users'] = UserProfile.objects.filter(
                is_banned=True
            ).count()
        except:
            metrics['user_violations'] = 0
            metrics['banned_users'] = 0

    def _collect_engagement_metrics(self, metrics, collection_date, verbose=False):
        """Collect user engagement metrics."""
        if verbose:
            self.stdout.write("  Collecting engagement metrics...")

        # Favorite items
        metrics['favorite_items_total'] = CollectionItem.objects.filter(
            is_favorite=True
        ).count()

        # Items with images
        items_with_images = CollectionItem.objects.filter(
            images__isnull=False
        ).distinct().count()
        total_items = CollectionItem.objects.count()
        metrics['items_with_images_pct'] = Decimal(
            (items_with_images / total_items * 100) if total_items > 0 else 0
        ).quantize(Decimal('0.01'))

        # Items with custom attributes (using relational model)
        items_with_attrs = CollectionItem.objects.filter(
            attribute_values__isnull=False
        ).distinct().count()
        metrics['items_with_attributes_pct'] = Decimal(
            (items_with_attrs / total_items * 100) if total_items > 0 else 0
        ).quantize(Decimal('0.01'))

        # Items with links
        items_with_links = CollectionItem.objects.filter(
            links__isnull=False
        ).distinct().count()
        metrics['items_with_links_pct'] = Decimal(
            (items_with_links / total_items * 100) if total_items > 0 else 0
        ).quantize(Decimal('0.01'))

        # Average attributes per item (using relational model)
        avg_attrs = CollectionItem.objects.annotate(
            attr_count=Count('attribute_values')
        ).aggregate(avg=Avg('attr_count'))['avg'] or 0
        metrics['avg_attributes_per_item'] = Decimal(avg_attrs).quantize(Decimal('0.01'))

        # Average items per collection
        avg_items = Collection.objects.annotate(
            item_count=Count('items')
        ).aggregate(avg=Avg('item_count'))['avg'] or 0
        metrics['avg_items_per_collection'] = Decimal(avg_items).quantize(Decimal('0.01'))

    def _collect_activity_metrics(self, metrics, collection_date, verbose=False):
        """Collect activity metrics."""
        if verbose:
            self.stdout.write("  Collecting activity metrics...")

        # Recent activity is already counted in items_created and collections_created
        # This is a placeholder for additional activity tracking if needed
        pass

    def _send_email_report(self, daily_metrics):
        """Send HTML email report to superusers."""
        self.stdout.write("  Sending email report...")

        # Get previous metrics for comparison
        yesterday = daily_metrics.collection_date - timedelta(days=1)
        week_ago = daily_metrics.collection_date - timedelta(days=7)

        try:
            previous_day = DailyMetrics.objects.get(collection_date=yesterday)
        except DailyMetrics.DoesNotExist:
            previous_day = None

        try:
            previous_week = DailyMetrics.objects.get(collection_date=week_ago)
        except DailyMetrics.DoesNotExist:
            previous_week = None

        # Prepare context for email template
        context = {
            'metrics': daily_metrics,
            'previous_day': previous_day,
            'previous_week': previous_week,
            'collection_date': daily_metrics.collection_date,
            'alert_threshold_warning': getattr(settings, 'METRICS_ALERT_THRESHOLD_WARNING', 10),
            'alert_threshold_critical': getattr(settings, 'METRICS_ALERT_THRESHOLD_CRITICAL', 25),
        }

        # Render email
        html_content = render_to_string('emails/daily_metrics_report.html', context)
        text_content = f"Daily Metrics Report for {daily_metrics.collection_date}\n\nView full report at /sys/metrics"

        # Get superuser emails
        superuser_emails = list(
            User.objects.filter(is_superuser=True, is_active=True)
            .values_list('email', flat=True)
        )

        if not superuser_emails:
            self.stdout.write(self.style.WARNING("No superuser emails found"))
            return

        # Send email
        subject = f'Daily Metrics Report - {daily_metrics.collection_date}'
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=superuser_emails
        )
        email.attach_alternative(html_content, "text/html")
        email.send()

        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Email sent to {len(superuser_emails)} superuser(s)'
            )
        )
