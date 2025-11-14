# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from post_office import mail
from post_office.models import Email, EmailTemplate
from django.core.paginator import Paginator
from django.db.models import Count, Q, Avg, Max
from django.db import models
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from allauth.account.models import EmailAddress
from django.contrib import messages
from django.conf import settings

from web.decorators import log_execution_time
from web.models import Collection, CollectionItem, RecentActivity, ItemType, ItemAttribute, LinkPattern, MediaFile
from web.models_user_profile import UserProfile

logger = logging.getLogger('webapp')
User = get_user_model()


def is_application_admin(user):
    """Check if user belongs to Application admin group"""
    return user.groups.filter(name='Application admin').exists()


def application_admin_required(view_func):
    """Decorator to ensure user is in Application admin group"""
    actual_decorator = user_passes_test(
        is_application_admin,
        login_url='/',
        redirect_field_name=None
    )
    return login_required(actual_decorator(view_func))


@application_admin_required
@log_execution_time
def sys_dashboard(request):
    """System dashboard with overview metrics"""
    logger.info("System dashboard accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
    # Calculate metrics
    total_users = User.objects.count()
    active_users = User.objects.filter(last_login__gte=timezone.now() - timedelta(days=30)).count()
    total_collections = Collection.objects.count()
    total_items = CollectionItem.objects.count()
    
    # Recent activity
    recent_activities = RecentActivity.objects.select_related('created_by').order_by('-created')[:10]
    
    # User activity in last 24 hours
    recent_user_activity = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    # Collection visibility breakdown
    visibility_stats = Collection.objects.values('visibility').annotate(count=Count('id'))
    
    # Item status breakdown
    status_stats = CollectionItem.objects.values('status').annotate(count=Count('id'))
    
    # System information
    from django.db import connection
    import django
    
    database_engine = connection.settings_dict.get('ENGINE', 'Unknown')
    if 'postgresql' in database_engine:
        database_engine = 'PostgreSQL'
    elif 'mysql' in database_engine:
        database_engine = 'MySQL'
    elif 'sqlite' in database_engine:
        database_engine = 'SQLite'
    else:
        database_engine = database_engine.split('.')[-1] if '.' in database_engine else database_engine
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_collections': total_collections,
        'total_items': total_items,
        'recent_activities': recent_activities,
        'recent_user_activity': recent_user_activity,
        'visibility_stats': visibility_stats,
        'status_stats': status_stats,
        'debug': settings.DEBUG,
        'django_version': django.get_version(),
        'database_engine': database_engine,
        'now': timezone.now(),
    }
    
    return render(request, 'sys/dashboard.html', context)


@application_admin_required
@log_execution_time
def sys_users(request):
    """User management interface"""
    logger.info("System users view accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    group_filter = request.GET.get('group', '')
    active_filter = request.GET.get('active', '')
    
    # Build queryset
    users = User.objects.select_related().prefetch_related('groups')
    
    if search:
        users = users.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if group_filter:
        users = users.filter(groups__name=group_filter)
    
    if active_filter == 'active':
        users = users.filter(is_active=True, last_login__isnull=False)
    elif active_filter == 'inactive':
        users = users.filter(Q(is_active=False) | Q(last_login__isnull=True))
    
    users = users.order_by('-date_joined')
    
    # Pagination
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all groups for filter dropdown
    groups = Group.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'group_filter': group_filter,
        'active_filter': active_filter,
        'groups': groups,
        'total_count': users.count(),
        'debug': settings.DEBUG,
    }
    
    return render(request, 'sys/users.html', context)


@application_admin_required
@log_execution_time
def sys_user_profile(request, user_id):
    """Detailed user profile page with comprehensive information"""
    user = get_object_or_404(User, id=user_id)
    logger.info("System user profile accessed by admin user '%s' [%s] for user '%s' [%s]", 
                request.user.username, request.user.id, user.email, user.id)
    
    # User basic information
    user_groups = user.groups.all()
    
    # Django-allauth email addresses
    email_addresses = EmailAddress.objects.filter(user=user).order_by('-primary', 'email')
    
    # User activity statistics
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    
    user_activity_stats = {
        'total_activities': RecentActivity.objects.filter(
            created_by=user
        ).count(),
        'activities_30d': RecentActivity.objects.filter(
            created_by=user,
            created__gte=last_30_days
        ).count(),
        'activities_7d': RecentActivity.objects.filter(
            created_by=user,
            created__gte=last_7_days
        ).count(),
        'last_activity': RecentActivity.objects.filter(
            created_by=user
        ).order_by('-created').first(),
    }
    
    # User collections with aggregated item stats
    collections = Collection.objects.filter(created_by=user).prefetch_related('items')
    collection_stats = []
    
    for collection in collections:
        items = collection.items.all()
        item_stats = {
            'total_items': items.count(),
            'favorites': items.filter(is_favorite=True).count(),
            'in_collection': items.filter(status='IN_COLLECTION').count(),
            'wanted': items.filter(status='WANTED').count(),
            'reserved': items.filter(status='RESERVED').count(),
            'sold': items.filter(status='SOLD').count(),
            'given_away': items.filter(status='GIVEN_AWAY').count(),
        }
        
        collection_stats.append({
            'collection': collection,
            'stats': item_stats
        })
    
    # Overall user statistics
    user_stats = {
        'total_collections': collections.count(),
        'public_collections': collections.filter(visibility='PUBLIC').count(),
        'private_collections': collections.filter(visibility='PRIVATE').count(),
        'unlisted_collections': collections.filter(visibility='UNLISTED').count(),
        'total_items': CollectionItem.objects.filter(collection__created_by=user).count(),
        'favorite_items': CollectionItem.objects.filter(collection__created_by=user, is_favorite=True).count(),
    }
    
    # Recent activity for this user
    recent_activities = RecentActivity.objects.filter(
        created_by=user
    ).select_related('created_by').order_by('-created')[:10]
    
    # User permissions and flags
    user_permissions = {
        'is_superuser': user.is_superuser,
        'is_staff': user.is_staff,
        'is_active': user.is_active,
        'groups': [group.name for group in user_groups],
        'date_joined': user.date_joined,
        'last_login': user.last_login,
    }
    
    context = {
        'profile_user': user,  # Using profile_user to distinguish from request.user
        'user_groups': user_groups,
        'email_addresses': email_addresses,
        'user_activity_stats': user_activity_stats,
        'collection_stats': collection_stats,
        'user_stats': user_stats,
        'recent_activities': recent_activities,
        'user_permissions': user_permissions,
        'debug': settings.DEBUG,
    }
    
    return render(request, 'sys/user_profile.html', context)




@application_admin_required
@log_execution_time
def sys_metrics(request):
    """System metrics dashboard using DailyMetrics model"""
    from web.models import DailyMetrics

    logger.info("System metrics accessed by admin user '%s' [%s]", request.user.username, request.user.id)

    # Get latest metrics
    latest_metrics = DailyMetrics.objects.order_by('-collection_date').first()

    if not latest_metrics:
        return render(request, 'sys/metrics.html', {'no_metrics': True})

    # Get historical for charts (last 30 days)
    historical = list(DailyMetrics.objects.order_by('-collection_date')[:30])
    historical.reverse()  # Oldest first for charts

    # Get threshold settings from environment
    alert_warning = int(os.environ.get('METRICS_ALERT_THRESHOLD_WARNING', 10))
    alert_critical = int(os.environ.get('METRICS_ALERT_THRESHOLD_CRITICAL', 25))

    # Pre-compute all metrics with their trend data
    # Define all metric fields we want to display
    metric_fields = [
        # User metrics
        'total_users', 'active_users_24h', 'active_users_7d', 'active_users_30d',
        'new_users_24h', 'new_users_7d', 'new_users_30d',
        # Collection metrics
        'total_collections', 'collections_private', 'collections_public', 'collections_unlisted',
        'collections_created_24h', 'collections_created_7d', 'collections_created_30d',
        # Item metrics
        'total_items', 'items_in_collection', 'items_wanted', 'items_reserved', 'favorite_items_total',
        'items_created_24h', 'items_created_7d', 'items_created_30d',
        # Storage metrics
        'total_media_files', 'total_storage_bytes', 'recent_uploads_24h', 'orphaned_files', 'corrupted_files',
        # Engagement metrics
        'items_with_images_pct', 'items_with_attributes_pct', 'items_with_links_pct',
        'avg_attributes_per_item', 'avg_items_per_collection',
        # Moderation metrics
        'flagged_content', 'pending_review', 'user_violations', 'banned_users',
    ]

    # Build metrics_data dict with current value and trends
    metrics_data = {}
    for field in metric_fields:
        metrics_data[field] = {
            'current': getattr(latest_metrics, field),
            'change_1d': latest_metrics.get_change(field, 1),
            'change_7d': latest_metrics.get_change(field, 7),
            'change_30d': latest_metrics.get_change(field, 30),
        }

    context = {
        'latest_metrics': latest_metrics,
        'metrics_data': metrics_data,
        'historical': historical,
        'alert_warning': alert_warning,
        'alert_critical': alert_critical,
    }

    return render(request, 'sys/metrics.html', context)


def sys_prometheus_metrics(request):
    """Prometheus-compatible metrics endpoint for Grafana using DailyMetrics"""
    from web.models import DailyMetrics
    from django.http import HttpResponse

    logger.info("Prometheus metrics accessed")

    # Get latest metrics from DailyMetrics
    latest = DailyMetrics.objects.order_by('-collection_date').first()

    if not latest:
        return HttpResponse('# No metrics available\n', content_type='text/plain; version=0.0.4; charset=utf-8')

    # Collect all metrics
    metrics = []

    # User metrics
    metrics.extend([
        f'# HELP beryl_users_total Total number of users',
        f'# TYPE beryl_users_total gauge',
        f'beryl_users_total {latest.total_users}',
        f'',
        f'# HELP beryl_users_active Active users by time period',
        f'# TYPE beryl_users_active gauge',
        f'beryl_users_active{{period="24h"}} {latest.active_users_24h}',
        f'beryl_users_active{{period="7d"}} {latest.active_users_7d}',
        f'beryl_users_active{{period="30d"}} {latest.active_users_30d}',
        f'',
        f'# HELP beryl_users_new New users by time period',
        f'# TYPE beryl_users_new gauge',
        f'beryl_users_new{{period="24h"}} {latest.new_users_24h}',
        f'beryl_users_new{{period="7d"}} {latest.new_users_7d}',
        f'beryl_users_new{{period="30d"}} {latest.new_users_30d}',
        f'',
    ])

    # Collection metrics
    metrics.extend([
        f'# HELP beryl_collections_total Total number of collections',
        f'# TYPE beryl_collections_total gauge',
        f'beryl_collections_total {latest.total_collections}',
        f'',
        f'# HELP beryl_collections_by_visibility Collections by visibility type',
        f'# TYPE beryl_collections_by_visibility gauge',
        f'beryl_collections_by_visibility{{visibility="public"}} {latest.collections_public}',
        f'beryl_collections_by_visibility{{visibility="private"}} {latest.collections_private}',
        f'beryl_collections_by_visibility{{visibility="unlisted"}} {latest.collections_unlisted}',
        f'',
        f'# HELP beryl_collections_created Collections created by time period',
        f'# TYPE beryl_collections_created gauge',
        f'beryl_collections_created{{period="24h"}} {latest.collections_created_24h}',
        f'beryl_collections_created{{period="7d"}} {latest.collections_created_7d}',
        f'beryl_collections_created{{period="30d"}} {latest.collections_created_30d}',
        f'',
    ])

    # Item metrics
    metrics.extend([
        f'# HELP beryl_items_total Total number of items',
        f'# TYPE beryl_items_total gauge',
        f'beryl_items_total {latest.total_items}',
        f'',
        f'# HELP beryl_items_by_status Items grouped by status',
        f'# TYPE beryl_items_by_status gauge',
        f'beryl_items_by_status{{status="in_collection"}} {latest.items_in_collection}',
        f'beryl_items_by_status{{status="wanted"}} {latest.items_wanted}',
        f'beryl_items_by_status{{status="reserved"}} {latest.items_reserved}',
        f'beryl_items_by_status{{status="ordered"}} {latest.items_ordered}',
        f'beryl_items_by_status{{status="lent"}} {latest.items_lent}',
        f'beryl_items_by_status{{status="previously_owned"}} {latest.items_previously_owned}',
        f'beryl_items_by_status{{status="sold"}} {latest.items_sold}',
        f'beryl_items_by_status{{status="given_away"}} {latest.items_given_away}',
        f'',
        f'# HELP beryl_items_favorites Total favorite items',
        f'# TYPE beryl_items_favorites gauge',
        f'beryl_items_favorites {latest.favorite_items_total}',
        f'',
        f'# HELP beryl_items_created Items created by time period',
        f'# TYPE beryl_items_created gauge',
        f'beryl_items_created{{period="24h"}} {latest.items_created_24h}',
        f'beryl_items_created{{period="7d"}} {latest.items_created_7d}',
        f'beryl_items_created{{period="30d"}} {latest.items_created_30d}',
        f'',
    ])

    # Item type distribution (from JSON field)
    if latest.item_type_distribution:
        metrics.extend([
            f'# HELP beryl_items_by_type Items grouped by type',
            f'# TYPE beryl_items_by_type gauge',
        ])
        for type_name, count in latest.item_type_distribution.items():
            safe_name = type_name.replace(' ', '_').replace('-', '_').lower()
            metrics.append(f'beryl_items_by_type{{type="{safe_name}"}} {count}')
        metrics.append('')

    # Link metrics
    metrics.extend([
        f'# HELP beryl_links_total Total links in items and collections',
        f'# TYPE beryl_links_total gauge',
        f'beryl_links_total {latest.total_links}',
        f'',
        f'# HELP beryl_links_matched Links matching defined patterns',
        f'# TYPE beryl_links_matched gauge',
        f'beryl_links_matched {latest.matched_link_patterns}',
        f'',
        f'# HELP beryl_links_unmatched Links not matching any pattern',
        f'# TYPE beryl_links_unmatched gauge',
        f'beryl_links_unmatched {latest.unmatched_link_patterns}',
        f'',
    ])

    # Link pattern distribution (from JSON field)
    if latest.link_pattern_distribution:
        metrics.extend([
            f'# HELP beryl_links_by_pattern Link usage by pattern',
            f'# TYPE beryl_links_by_pattern gauge',
        ])
        for pattern_name, count in latest.link_pattern_distribution.items():
            safe_name = pattern_name.replace(' ', '_').replace('-', '_').lower()
            metrics.append(f'beryl_links_by_pattern{{pattern="{safe_name}"}} {count}')
        metrics.append('')

    # Storage metrics
    metrics.extend([
        f'# HELP beryl_storage_files_total Total media files',
        f'# TYPE beryl_storage_files_total gauge',
        f'beryl_storage_files_total {latest.total_media_files}',
        f'',
        f'# HELP beryl_storage_bytes_total Total storage used in bytes',
        f'# TYPE beryl_storage_bytes_total gauge',
        f'beryl_storage_bytes_total {latest.total_storage_bytes}',
        f'',
        f'# HELP beryl_storage_uploads_recent Recent uploads by time period',
        f'# TYPE beryl_storage_uploads_recent gauge',
        f'beryl_storage_uploads_recent{{period="24h"}} {latest.recent_uploads_24h}',
        f'beryl_storage_uploads_recent{{period="7d"}} {latest.recent_uploads_7d}',
        f'beryl_storage_uploads_recent{{period="30d"}} {latest.recent_uploads_30d}',
        f'',
        f'# HELP beryl_storage_orphaned_files Media files not linked to items/collections',
        f'# TYPE beryl_storage_orphaned_files gauge',
        f'beryl_storage_orphaned_files {latest.orphaned_files}',
        f'',
        f'# HELP beryl_storage_corrupted_files Media files that failed integrity check',
        f'# TYPE beryl_storage_corrupted_files gauge',
        f'beryl_storage_corrupted_files {latest.corrupted_files}',
        f'',
    ])

    # Storage by type distribution (from JSON field)
    if latest.storage_by_type:
        metrics.extend([
            f'# HELP beryl_storage_by_type Storage distribution by file type',
            f'# TYPE beryl_storage_by_type gauge',
        ])
        for file_ext, size_bytes in latest.storage_by_type.items():
            safe_ext = file_ext.replace('.', '').lower()
            metrics.append(f'beryl_storage_by_type{{extension="{safe_ext}"}} {size_bytes}')
        metrics.append('')

    # Attribute metrics
    metrics.extend([
        f'# HELP beryl_attributes_total Total attribute definitions',
        f'# TYPE beryl_attributes_total gauge',
        f'beryl_attributes_total {latest.total_attributes}',
        f'',
    ])

    # Attribute usage distribution (from JSON field)
    if latest.attribute_usage:
        metrics.extend([
            f'# HELP beryl_attributes_usage Attribute usage statistics',
            f'# TYPE beryl_attributes_usage gauge',
        ])
        for attr_name, count in latest.attribute_usage.items():
            safe_name = attr_name.replace(' ', '_').replace('-', '_').lower()
            metrics.append(f'beryl_attributes_usage{{attribute="{safe_name}"}} {count}')
        metrics.append('')

    # Email metrics (if available)
    if latest.total_emails is not None:
        metrics.extend([
            f'# HELP beryl_emails_total Total emails tracked',
            f'# TYPE beryl_emails_total gauge',
            f'beryl_emails_total {latest.total_emails}',
            f'',
            f'# HELP beryl_emails_by_status Emails by delivery status',
            f'# TYPE beryl_emails_by_status gauge',
            f'beryl_emails_by_status{{status="pending"}} {latest.emails_pending or 0}',
            f'beryl_emails_by_status{{status="sent"}} {latest.emails_sent or 0}',
            f'beryl_emails_by_status{{status="failed"}} {latest.emails_failed or 0}',
            f'',
            f'# HELP beryl_emails_marketing_opt Marketing email preferences',
            f'# TYPE beryl_emails_marketing_opt gauge',
            f'beryl_emails_marketing_opt{{status="opted_in"}} {latest.marketing_opt_in or 0}',
            f'beryl_emails_marketing_opt{{status="opted_out"}} {latest.marketing_opt_out or 0}',
            f'',
        ])

    # Content moderation metrics
    metrics.extend([
        f'# HELP beryl_moderation_flagged Content items flagged for review',
        f'# TYPE beryl_moderation_flagged gauge',
        f'beryl_moderation_flagged {latest.flagged_content}',
        f'',
        f'# HELP beryl_moderation_pending Content items pending moderation',
        f'# TYPE beryl_moderation_pending gauge',
        f'beryl_moderation_pending {latest.pending_review}',
        f'',
        f'# HELP beryl_moderation_violations Total user violations',
        f'# TYPE beryl_moderation_violations gauge',
        f'beryl_moderation_violations {latest.user_violations}',
        f'',
        f'# HELP beryl_moderation_banned_users Currently banned users',
        f'# TYPE beryl_moderation_banned_users gauge',
        f'beryl_moderation_banned_users {latest.banned_users}',
        f'',
    ])

    # Engagement metrics
    metrics.extend([
        f'# HELP beryl_engagement_items_with_images_pct Percentage of items with images',
        f'# TYPE beryl_engagement_items_with_images_pct gauge',
        f'beryl_engagement_items_with_images_pct {float(latest.items_with_images_pct)}',
        f'',
        f'# HELP beryl_engagement_items_with_attributes_pct Percentage of items with custom attributes',
        f'# TYPE beryl_engagement_items_with_attributes_pct gauge',
        f'beryl_engagement_items_with_attributes_pct {float(latest.items_with_attributes_pct)}',
        f'',
        f'# HELP beryl_engagement_items_with_links_pct Percentage of items with links',
        f'# TYPE beryl_engagement_items_with_links_pct gauge',
        f'beryl_engagement_items_with_links_pct {float(latest.items_with_links_pct)}',
        f'',
        f'# HELP beryl_engagement_avg_attributes_per_item Average attributes per item',
        f'# TYPE beryl_engagement_avg_attributes_per_item gauge',
        f'beryl_engagement_avg_attributes_per_item {float(latest.avg_attributes_per_item)}',
        f'',
        f'# HELP beryl_engagement_avg_items_per_collection Average items per collection',
        f'# TYPE beryl_engagement_avg_items_per_collection gauge',
        f'beryl_engagement_avg_items_per_collection {float(latest.avg_items_per_collection)}',
        f'',
    ])

    # Item type counts
    metrics.extend([
        f'# HELP beryl_item_types_count Total item types defined',
        f'# TYPE beryl_item_types_count gauge',
        f'beryl_item_types_count {latest.item_types_count}',
        f'',
    ])

    # Metadata
    metrics.extend([
        f'# HELP beryl_metrics_collection_duration_seconds How long metrics collection took',
        f'# TYPE beryl_metrics_collection_duration_seconds gauge',
        f'beryl_metrics_collection_duration_seconds {latest.collection_duration_seconds}',
        f'',
        f'# HELP beryl_metrics_collection_timestamp_seconds When metrics were collected',
        f'# TYPE beryl_metrics_collection_timestamp_seconds gauge',
        f'beryl_metrics_collection_timestamp_seconds {int(latest.collected_at.timestamp())}',
        f'',
    ])

    # Join all metrics with newlines
    response_content = '\n'.join(metrics)

    return HttpResponse(response_content, content_type='text/plain; version=0.0.4; charset=utf-8')


def sys_user_toggle_active(request, user_id):
    """Toggle user active status via HTMX"""
    user = get_object_or_404(User, id=user_id)
    
    # Don't allow deactivating self
    if user == request.user:
        return JsonResponse({'error': 'Cannot deactivate your own account'}, status=400)
    
    user.is_active = not user.is_active
    user.save()
    
    logger.info("Admin user '%s' [%s] toggled active status for user '%s' [%s] to %s", 
                request.user.username, request.user.id, user.email, user.id, user.is_active)
    
    return JsonResponse({
        'success': True,
        'is_active': user.is_active,
        'message': f"User {'activated' if user.is_active else 'deactivated'}"
    })




@application_admin_required
@require_http_methods(["POST"])
def sys_user_reset_password(request, user_id):
    """Reset user password and send email notification"""
    user = get_object_or_404(User, id=user_id)
    
    try:
        # Generate password reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Create reset URL (using Django's built-in password reset)
        reset_url = request.build_absolute_uri(
            f"/accounts/password/reset/key/{uid}-{token}/"
        )
        
        # Get user's primary email
        primary_email = None
        if hasattr(user, 'emailaddress_set'):
            primary_email_obj = user.emailaddress_set.filter(primary=True).first()
            if primary_email_obj:
                primary_email = primary_email_obj.email
        
        # Fallback to User.email if no primary email found
        email_address = primary_email or user.email
        
        if not email_address:
            return JsonResponse({
                'success': False,
                'error': 'User has no email address configured'
            }, status=400)
        
        # Send password reset email
        subject = 'Password Reset - Beryl Collection Management'
        html_message = render_to_string('emails/admin_password_reset.html', {
            'user': user,
            'reset_url': reset_url,
            'admin_user': request.user,
            'site_name': 'Beryl',
        })
        
        # Plain text fallback
        plain_message = f"""
Hi {user.first_name or user.email},

An administrator has initiated a password reset for your Beryl account.

You can reset your password by clicking the following link:
{reset_url}

If you didn't request this reset, you can safely ignore this email.

Best regards,
The Beryl Team
"""
        
        mail.send(
            recipients=[email_address],
            sender=settings.DEFAULT_FROM_EMAIL,
            subject=subject,
            message=plain_message,
            html_message=html_message,
            priority='high',  # High priority for admin password resets
        )
        
        # Log the action
        logger.info("Admin user '%s' [%s] initiated password reset for user '%s' [%s]", 
                   request.user.email, request.user.id, user.email, user.id)
        
        return JsonResponse({
            'success': True,
            'message': f'Password reset email sent to {email_address}'
        })
        
    except Exception as e:
        logger.error("Password reset failed for user '%s' [%s]: %s", user.email, user.id, str(e))
        return JsonResponse({
            'success': False,
            'error': 'Failed to send password reset email'
        }, status=500)


@application_admin_required
@require_http_methods(["POST"])
def sys_user_unlock_account(request, user_id):
    """Unlock user account and reset failed login attempts"""
    user = get_object_or_404(User, id=user_id)
    
    try:
        # Activate user account if it's inactive
        if not user.is_active:
            user.is_active = True
            user.save()
            
        # Clear any django-allauth related locks/attempts
        # This would typically reset failed login attempts if you're tracking them
        
        # Log the action
        logger.info("Admin user '%s' [%s] unlocked account for user '%s' [%s]", 
                   request.user.email, request.user.id, user.email, user.id)
        
        return JsonResponse({
            'success': True,
            'message': f'Account unlocked for {user.email}'
        })
        
    except Exception as e:
        logger.error("Account unlock failed for user '%s' [%s]: %s", user.email, user.id, str(e))
        return JsonResponse({
            'success': False,
            'error': 'Failed to unlock account'
        }, status=500)


@application_admin_required  
@require_http_methods(["POST"])
def sys_user_force_email_verification(request, user_id):
    """Force verify user's email addresses"""
    user = get_object_or_404(User, id=user_id)
    
    try:
        # Mark all user's email addresses as verified
        verified_count = 0
        for email_address in user.emailaddress_set.all():
            if not email_address.verified:
                email_address.verified = True
                email_address.save()
                verified_count += 1
        
        # Log the action
        logger.info("Admin user '%s' [%s] force-verified %d emails for user '%s' [%s]", 
                   request.user.email, request.user.id, verified_count, user.email, user.id)
        
        return JsonResponse({
            'success': True,
            'message': f'Verified {verified_count} email address(es) for {user.email}'
        })
        
    except Exception as e:
        logger.error("Email verification failed for user '%s' [%s]: %s", user.email, user.id, str(e))
        return JsonResponse({
            'success': False,
            'error': 'Failed to verify email addresses'
        }, status=500)


@application_admin_required
@log_execution_time
def sys_item_types(request):
    """Item type management interface"""
    logger.info("System item types accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
    # Get all item types with their attribute count and usage count
    item_types = ItemType.objects.annotate(
        attribute_count=Count('attributes', filter=Q(attributes__is_deleted=False)),
        items_using_count=Count('items', filter=Q(items__is_deleted=False))
    ).order_by('display_name')
    
    context = {
        'item_types': item_types,
        'total_count': item_types.count(),
    }
    
    return render(request, 'sys/item_types.html', context)


@application_admin_required
@log_execution_time  
def sys_item_type_detail(request, item_type_id):
    """Item type detail and attribute management"""
    logger.info("System item type detail accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
    item_type = get_object_or_404(ItemType, id=item_type_id)
    attributes = item_type.attributes.filter(is_deleted=False).order_by('order', 'display_name')
    
    # Get usage statistics
    item_count = CollectionItem.objects.filter(item_type=item_type, is_deleted=False).count()
    
    context = {
        'item_type': item_type,
        'attributes': attributes,
        'item_count': item_count,
        'attribute_types': ItemAttribute.AttributeType.choices,
    }
    
    return render(request, 'sys/item_type_detail.html', context)


@application_admin_required
@require_http_methods(["POST"])
def sys_item_type_create(request):
    """Create new item type"""
    try:
        display_name = request.POST.get('display_name', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '').strip()
        
        if not display_name:
            messages.error(request, 'Display name is required')
            return redirect('sys_item_types')
            
            
        item_type = ItemType.objects.create(
            display_name=display_name,
            description=description or None,
            icon=icon or None,
            created_by=request.user
        )
        
        logger.info("Admin user '%s' [%s] created item type '%s' [%s]", 
                   request.user.username, request.user.id, item_type.display_name, item_type.id)
        
        messages.success(request, f"Item type '{display_name}' created successfully")
        return redirect('sys_item_types')
        
    except Exception as e:
        logger.error("Item type creation failed: %s", str(e))
        messages.error(request, 'Failed to create item type')
        return redirect('sys_item_types')


@application_admin_required
@require_http_methods(["POST"])
def sys_item_type_update(request, item_type_id):
    """Update existing item type"""
    item_type = get_object_or_404(ItemType, id=item_type_id)
    
    try:
        display_name = request.POST.get('display_name', '').strip()
        description = request.POST.get('description', '').strip()
        icon = request.POST.get('icon', '').strip()
        
        if not display_name:
            messages.error(request, 'Display name is required')
            return redirect('sys_item_types')
            
            
        item_type.display_name = display_name
        item_type.description = description or None
        item_type.icon = icon or None
        item_type.save()
        
        logger.info("Admin user '%s' [%s] updated item type '%s' [%s]", 
                   request.user.username, request.user.id, item_type.display_name, item_type.id)
        
        messages.success(request, f"Item type '{display_name}' updated successfully")
        return redirect('sys_item_types')
        
    except Exception as e:
        logger.error("Item type update failed: %s", str(e))
        messages.error(request, 'Failed to update item type')
        return redirect('sys_item_types')


@application_admin_required
@require_http_methods(["POST"])
def sys_item_type_delete(request, item_type_id):
    """Soft delete item type"""
    item_type = get_object_or_404(ItemType, id=item_type_id)
    item_type_name = item_type.display_name
    
    try:
        item_type.delete()  # Will raise PermissionDenied if constraints violated
        
        logger.info("Admin user '%s' [%s] deleted item type '%s' [%s]", 
                   request.user.username, request.user.id, item_type_name, item_type_id)
        
        messages.success(request, f"Item type '{item_type_name}' deleted successfully")
        return redirect('sys_item_types')
        
    except PermissionDenied as e:
        logger.warning("Item type deletion blocked: %s", str(e))
        messages.error(request, str(e))
        return redirect('sys_item_types')
        
    except Exception as e:
        logger.error("Item type deletion failed: %s", str(e))
        messages.error(request, 'Failed to delete item type')
        return redirect('sys_item_types')


@application_admin_required
@require_http_methods(["POST"])
def sys_item_attribute_create(request, item_type_id):
    """Create new item attribute"""
    item_type = get_object_or_404(ItemType, id=item_type_id)
    
    try:
        display_name = request.POST.get('display_name', '').strip()
        attribute_type = request.POST.get('attribute_type', '').strip()
        required = request.POST.get('required') == 'on'
        help_text = request.POST.get('help_text', '').strip()
        choices_text = request.POST.get('choices', '').strip()
        
        if not display_name:
            messages.error(request, 'Display name is required')
            return redirect('sys_item_type_detail', item_type_id=item_type_id)
            
        if not attribute_type or attribute_type not in dict(ItemAttribute.AttributeType.choices):
            messages.error(request, 'Valid attribute type is required')
            return redirect('sys_item_type_detail', item_type_id=item_type_id)
        
        # Parse choices for CHOICE type
        choices = None
        if attribute_type == 'CHOICE' and choices_text:
            choices = [choice.strip() for choice in choices_text.split('\n') if choice.strip()]
            
        # Get next order number
        max_order = item_type.attributes.aggregate(Max('order'))['order__max'] or 0
        
        # Generate a name from display_name (lowercase, replace spaces with underscores)
        name = display_name.lower().replace(' ', '_').replace('-', '_')
        # Remove any non-alphanumeric characters except underscores
        name = ''.join(char for char in name if char.isalnum() or char == '_')
        
        attribute = ItemAttribute.objects.create(
            item_type=item_type,
            name=name,
            display_name=display_name,
            attribute_type=attribute_type,
            required=required,
            help_text=help_text or None,
            choices=choices,
            order=max_order + 1,
            created_by=request.user
        )
        
        logger.info("Admin user '%s' [%s] created attribute '%s' [%s] for item type '%s'", 
                   request.user.username, request.user.id, attribute.display_name, 
                   attribute.id, item_type.display_name)
        
        messages.success(request, f"Attribute '{display_name}' created successfully")
        return redirect('sys_item_type_detail', item_type_id=item_type_id)
        
    except Exception as e:
        logger.error("Attribute creation failed: %s", str(e))
        messages.error(request, 'Failed to create attribute')
        return redirect('sys_item_type_detail', item_type_id=item_type_id)


@application_admin_required
@require_http_methods(["POST"])
def sys_item_attribute_update(request, attribute_id):
    """Update existing item attribute"""
    attribute = get_object_or_404(ItemAttribute, id=attribute_id)
    
    try:
        display_name = request.POST.get('display_name', '').strip()
        attribute_type = request.POST.get('attribute_type', '').strip()
        required = request.POST.get('required') == 'on'
        help_text = request.POST.get('help_text', '').strip()
        choices_text = request.POST.get('choices', '').strip()
        
        if not display_name:
            messages.error(request, 'Display name is required')
            return redirect('sys_item_type_detail', item_type_id=attribute.item_type.id)
            
        if not attribute_type or attribute_type not in dict(ItemAttribute.AttributeType.choices):
            messages.error(request, 'Valid attribute type is required')
            return redirect('sys_item_type_detail', item_type_id=attribute.item_type.id)
        
        # Parse choices for CHOICE type
        choices = None
        if attribute_type == 'CHOICE' and choices_text:
            choices = [choice.strip() for choice in choices_text.split('\n') if choice.strip()]
            
        # Generate a name from display_name (lowercase, replace spaces with underscores)
        name = display_name.lower().replace(' ', '_').replace('-', '_')
        # Remove any non-alphanumeric characters except underscores
        name = ''.join(char for char in name if char.isalnum() or char == '_')
            
        attribute.name = name
        attribute.display_name = display_name
        attribute.attribute_type = attribute_type
        attribute.required = required
        attribute.help_text = help_text or None
        attribute.choices = choices
        attribute.save()
        
        logger.info("Admin user '%s' [%s] updated attribute '%s' [%s]", 
                   request.user.username, request.user.id, attribute.display_name, attribute.id)
        
        messages.success(request, f"Attribute '{display_name}' updated successfully")
        return redirect('sys_item_type_detail', item_type_id=attribute.item_type.id)
        
    except Exception as e:
        logger.error("Attribute update failed: %s", str(e))
        messages.error(request, 'Failed to update attribute')
        return redirect('sys_item_type_detail', item_type_id=attribute.item_type.id)


@application_admin_required
@require_http_methods(["POST"])
def sys_item_attribute_delete(request, attribute_id):
    """Delete item attribute with usage check and force delete option"""
    attribute = get_object_or_404(ItemAttribute, id=attribute_id)
    item_type_id = attribute.item_type.id
    attribute_name = attribute.display_name
    force_delete = request.POST.get('force_delete') == 'true'
    
    try:
        # Check for usage in collection items
        items_with_attribute = CollectionItem.objects.filter(
            item_type=attribute.item_type,
            attributes__has_key=attribute.name,
            is_deleted=False
        )
        usage_count = items_with_attribute.count()
        
        if usage_count == 0:
            # No usage found - safe to delete
            attribute.delete()  # Soft delete via BerylModel
            
            logger.info("Admin user '%s' [%s] deleted unused attribute '%s' [%s]", 
                       request.user.username, request.user.id, attribute_name, attribute_id)
            
            messages.success(request, f"Attribute '{attribute_name}' deleted successfully (no items were using it)")
            return redirect('sys_item_type_detail', item_type_id=item_type_id)
        
        elif not force_delete:
            # Usage found - show confirmation page
            context = {
                'attribute': attribute,
                'item_type': attribute.item_type,
                'usage_count': usage_count,
                'items_with_attribute': items_with_attribute[:10],  # Show first 10 items
                'show_more': usage_count > 10,
            }
            return render(request, 'sys/attribute_delete_confirm.html', context)
        
        else:
            # Force delete - remove attribute from all items and delete
            items_updated = 0
            for item in items_with_attribute:
                if attribute.name in item.attributes:
                    del item.attributes[attribute.name]
                    item.save(update_fields=['attributes'])
                    items_updated += 1
            
            attribute.delete()  # Soft delete via BerylModel
            
            logger.warning("Admin user '%s' [%s] force deleted attribute '%s' [%s] and cleaned %d items", 
                          request.user.username, request.user.id, attribute_name, attribute_id, items_updated)
            
            messages.success(request, f"Attribute '{attribute_name}' force deleted and removed from {items_updated} items")
            return redirect('sys_item_type_detail', item_type_id=item_type_id)
        
    except Exception as e:
        logger.error("Attribute deletion failed: %s", str(e))
        messages.error(request, 'Failed to delete attribute')
        return redirect('sys_item_type_detail', item_type_id=item_type_id)




@application_admin_required
@log_execution_time
def sys_link_patterns(request):
    """List all link patterns"""
    logger.info("Sys link patterns list requested by user '%s' [%s]", request.user.username, request.user.id)
    
    link_patterns = LinkPattern.objects.all().order_by('display_name')
    
    # Count usage for each pattern
    for pattern in link_patterns:
        pattern.usage_count = pattern.links.count()
    
    # Find most used pattern and calculate total links
    most_used_pattern = None
    total_links_count = 0
    if link_patterns:
        most_used_pattern = max(link_patterns, key=lambda p: p.usage_count, default=None)
        if most_used_pattern and most_used_pattern.usage_count == 0:
            most_used_pattern = None
        total_links_count = sum(p.usage_count for p in link_patterns)
    
    context = {
        'link_patterns': link_patterns,
        'most_used_pattern': most_used_pattern,
        'total_links_count': total_links_count,
    }
    
    return render(request, 'sys/link_patterns.html', context)


@application_admin_required
@log_execution_time
def sys_link_pattern_detail(request, link_pattern_id):
    """View details of a specific link pattern"""
    logger.info("Sys link pattern detail requested for ID '%s' by user '%s' [%s]", link_pattern_id, request.user.username, request.user.id)
    
    link_pattern = get_object_or_404(LinkPattern, id=link_pattern_id)
    recent_links = link_pattern.links.select_related('item', 'item__collection').order_by('-created')[:10]
    
    context = {
        'link_pattern': link_pattern,
        'recent_links': recent_links,
        'usage_count': link_pattern.links.count(),
    }
    
    return render(request, 'sys/link_pattern_detail.html', context)


@application_admin_required
@log_execution_time
def sys_link_pattern_create(request):
    """Create a new link pattern"""
    logger.info("Sys link pattern create requested by user '%s' [%s]", request.user.username, request.user.id)
    
    if request.method == 'POST':
        display_name = request.POST.get('display_name', '').strip()
        url_pattern = request.POST.get('url_pattern', '').strip()
        icon = request.POST.get('icon', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        if not display_name or not url_pattern:
            messages.error(request, 'Display name and URL pattern are required.')
            return render(request, 'sys/link_pattern_form.html', {
                'mode': 'create',
                'form_data': request.POST
            })
        
            return render(request, 'sys/link_pattern_form.html', {
                'mode': 'create',
                'form_data': request.POST
            })
        
        try:
            link_pattern = LinkPattern.objects.create(
                display_name=display_name,
                url_pattern=url_pattern,
                icon=icon if icon else None,
                description=description if description else None,
                is_active=is_active,
                created_by=request.user
            )
            logger.info("User '%s' [%s] created LinkPattern '%s' [%s]", request.user.username, request.user.id, link_pattern.display_name, link_pattern.id)
            messages.success(request, f'Link pattern "{display_name}" created successfully.')
            return redirect('sys_link_pattern_detail', link_pattern_id=link_pattern.id)
            
        except Exception as e:
            logger.error("Error creating link pattern: %s", str(e))
            messages.error(request, 'An error occurred while creating the link pattern.')
    
    return render(request, 'sys/link_pattern_form.html', {'mode': 'create'})


@application_admin_required
@log_execution_time
def sys_link_pattern_update(request, link_pattern_id):
    """Update an existing link pattern"""
    logger.info("Sys link pattern update requested for ID '%s' by user '%s' [%s]", link_pattern_id, request.user.username, request.user.id)
    
    link_pattern = get_object_or_404(LinkPattern, id=link_pattern_id)
    
    if request.method == 'POST':
        display_name = request.POST.get('display_name', '').strip()
        url_pattern = request.POST.get('url_pattern', '').strip()
        icon = request.POST.get('icon', '').strip()
        description = request.POST.get('description', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        
        if not display_name or not url_pattern:
            messages.error(request, 'Display name and URL pattern are required.')
            return render(request, 'sys/link_pattern_form.html', {
                'mode': 'update',
                'link_pattern': link_pattern,
                'form_data': request.POST
            })
        
            return render(request, 'sys/link_pattern_form.html', {
                'mode': 'update',
                'link_pattern': link_pattern,
                'form_data': request.POST
            })
        
        try:
            link_pattern.display_name = display_name
            link_pattern.url_pattern = url_pattern
            link_pattern.icon = icon if icon else None
            link_pattern.description = description if description else None
            link_pattern.is_active = is_active
            link_pattern.save()
            
            logger.info("User '%s' [%s] updated LinkPattern '%s' [%s]", request.user.username, request.user.id, link_pattern.display_name, link_pattern.id)
            messages.success(request, f'Link pattern "{display_name}" updated successfully.')
            return redirect('sys_link_pattern_detail', link_pattern_id=link_pattern.id)
            
        except Exception as e:
            logger.error("Error updating link pattern: %s", str(e))
            messages.error(request, 'An error occurred while updating the link pattern.')
    
    return render(request, 'sys/link_pattern_form.html', {
        'mode': 'update',
        'link_pattern': link_pattern
    })


@application_admin_required
@log_execution_time
def sys_link_pattern_delete(request, link_pattern_id):
    """Delete a link pattern"""
    logger.info("Sys link pattern delete requested for ID '%s' by user '%s' [%s]", link_pattern_id, request.user.username, request.user.id)
    
    link_pattern = get_object_or_404(LinkPattern, id=link_pattern_id)
    usage_count = link_pattern.links.count()
    
    if request.method == 'POST':
        if usage_count > 0:
            messages.error(request, f'Cannot delete link pattern "{link_pattern.display_name}" because it is used by {usage_count} links.')
            return redirect('sys_link_pattern_detail', link_pattern_id=link_pattern.id)
        
        pattern_name = link_pattern.display_name
        link_pattern.delete()
        logger.info("User '%s' [%s] deleted LinkPattern '%s' [%s]", request.user.username, request.user.id, pattern_name, link_pattern_id)
        messages.success(request, f'Link pattern "{pattern_name}" deleted successfully.')
        return redirect('sys_link_patterns')
    
    return render(request, 'sys/link_pattern_delete_confirm.html', {
        'link_pattern': link_pattern,
        'usage_count': usage_count
    })


@application_admin_required
@log_execution_time
def sys_settings(request):
    """System settings overview showing all configuration values"""
    logger.info("System settings accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
    # Import MediaFile to get media statistics
    from web.models import MediaFile
    
    # Django settings
    django_settings = {
        'DEBUG': getattr(settings, 'DEBUG', False),
        'SECRET_KEY': '***HIDDEN***' if getattr(settings, 'SECRET_KEY', None) else 'Not set',
        'ALLOWED_HOSTS': getattr(settings, 'ALLOWED_HOSTS', []),
        'TIME_ZONE': getattr(settings, 'TIME_ZONE', 'UTC'),
        'LANGUAGE_CODE': getattr(settings, 'LANGUAGE_CODE', 'en-us'),
        'USE_I18N': getattr(settings, 'USE_I18N', True),
        'USE_TZ': getattr(settings, 'USE_TZ', True),
        'SITE_ID': getattr(settings, 'SITE_ID', 1),
    }
    
    # Database settings
    database_config = getattr(settings, 'DATABASES', {}).get('default', {})
    database_settings = {
        'ENGINE': database_config.get('ENGINE', 'Not configured'),
        'NAME': database_config.get('NAME', 'Not configured'),
        'HOST': database_config.get('HOST', 'Not configured') if database_config.get('HOST') else 'localhost',
        'PORT': database_config.get('PORT', 'Default') if database_config.get('PORT') else 'Default',
        'USER': '***HIDDEN***' if database_config.get('USER') else 'Not set',
        'PASSWORD': '***HIDDEN***' if database_config.get('PASSWORD') else 'Not set',
    }
    
    # Email settings
    email_host = getattr(settings, 'EMAIL_HOST', 'Not configured')
    is_resend = email_host == 'smtp.resend.com'
    is_inbucket = 'inbucket' in email_host.lower() or getattr(settings, 'FEATURE_FLAGS', {}).get('USE_INBUCKET', False)
    
    email_settings = {
        'EMAIL_BACKEND': getattr(settings, 'EMAIL_BACKEND', 'Not configured'),
        'EMAIL_HOST': email_host,
        'EMAIL_PORT': getattr(settings, 'EMAIL_PORT', 'Not configured'),
        'EMAIL_USE_TLS': getattr(settings, 'EMAIL_USE_TLS', False),
        'EMAIL_USE_SSL': getattr(settings, 'EMAIL_USE_SSL', False),
        'EMAIL_HOST_USER': getattr(settings, 'EMAIL_HOST_USER', 'Not set') if not is_resend else '***HIDDEN***',
        'EMAIL_HOST_PASSWORD': '***HIDDEN***' if getattr(settings, 'EMAIL_HOST_PASSWORD', None) else 'Not set',
        'DEFAULT_FROM_EMAIL': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured'),
        
        # Email service detection
        'EMAIL_SERVICE': 'Resend' if is_resend else ('Inbucket' if is_inbucket else 'Custom SMTP'),
        'RESEND_CONFIGURED': is_resend,
        'INBUCKET_CONFIGURED': is_inbucket,
        
        # Legacy Inbucket settings (for backwards compatibility)
        'USE_INBUCKET': getattr(settings, 'FEATURE_FLAGS', {}).get('USE_INBUCKET', False),
        'INBUCKET_SMTP_PORT': getattr(settings, 'INBUCKET_SMTP_PORT', 2500),
    }
    
    # Media/Storage settings
    media_settings = {
        'USE_GCS_STORAGE': getattr(settings, 'FEATURE_FLAGS', {}).get('USE_GCS_STORAGE', False),
        'GCS_BUCKET_NAME': getattr(settings, 'GCS_BUCKET_NAME', 'Not configured'),
        'GCS_PROJECT_ID': getattr(settings, 'GCS_PROJECT_ID', 'Not configured'),
        'GCS_LOCATION': getattr(settings, 'GCS_LOCATION', 'media'),
        'GCS_CREDENTIALS_PATH': getattr(settings, 'GCS_CREDENTIALS_PATH', 'Not configured'),
        'GCS_CREDENTIALS': '***CONFIGURED***' if getattr(settings, 'GCS_CREDENTIALS', None) else 'Not set',
        'MEDIA_URL': getattr(settings, 'MEDIA_URL', '/media/'),
        'MEDIA_ROOT': getattr(settings, 'MEDIA_ROOT', 'Not configured'),
        'DEFAULT_FILE_STORAGE': getattr(settings, 'DEFAULT_FILE_STORAGE', 'django.core.files.storage.FileSystemStorage'),
    }
    
    # Authentication settings
    auth_settings = {
        'LOGIN_REDIRECT_URL': getattr(settings, 'LOGIN_REDIRECT_URL', '/'),
        'LOGOUT_REDIRECT_URL': getattr(settings, 'LOGOUT_REDIRECT_URL', '/'),
        'LOGIN_URL': getattr(settings, 'LOGIN_URL', '/accounts/login/'),
        'AUTHENTICATION_BACKENDS': getattr(settings, 'AUTHENTICATION_BACKENDS', []),
        'ACCOUNT_EMAIL_REQUIRED': getattr(settings, 'ACCOUNT_EMAIL_REQUIRED', False),
        'ACCOUNT_USERNAME_REQUIRED': getattr(settings, 'ACCOUNT_USERNAME_REQUIRED', True),
        'ACCOUNT_AUTHENTICATION_METHOD': getattr(settings, 'ACCOUNT_AUTHENTICATION_METHOD', 'username'),
        'ACCOUNT_EMAIL_VERIFICATION': getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'optional'),
        'ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE': getattr(settings, 'ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE', True),
        'ACCOUNT_PASSWORD_MIN_LENGTH': getattr(settings, 'ACCOUNT_PASSWORD_MIN_LENGTH', 8),
    }
    
    # Static files settings
    static_settings = {
        'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
        'STATIC_ROOT': getattr(settings, 'STATIC_ROOT', 'Not configured'),
        'STATICFILES_DIRS': getattr(settings, 'STATICFILES_DIRS', []),
    }
    
    # Installed apps (filtered to show only main apps)
    all_apps = getattr(settings, 'INSTALLED_APPS', [])
    custom_apps = [app for app in all_apps if not app.startswith('django.') and not app.startswith('allauth')]
    django_apps = [app for app in all_apps if app.startswith('django.')]
    allauth_apps = [app for app in all_apps if app.startswith('allauth')]
    
    app_settings = {
        'TOTAL_APPS': len(all_apps),
        'CUSTOM_APPS': custom_apps,
        'DJANGO_APPS': django_apps,
        'ALLAUTH_APPS': allauth_apps,
    }
    
    # Middleware settings
    middleware_settings = {
        'MIDDLEWARE': getattr(settings, 'MIDDLEWARE', []),
        'MIDDLEWARE_COUNT': len(getattr(settings, 'MIDDLEWARE', [])),
    }
    
    # Security settings
    security_settings = {
        'SECURE_SSL_REDIRECT': getattr(settings, 'SECURE_SSL_REDIRECT', False),
        'SECURE_HSTS_SECONDS': getattr(settings, 'SECURE_HSTS_SECONDS', 0),
        'SECURE_HSTS_INCLUDE_SUBDOMAINS': getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False),
        'SECURE_HSTS_PRELOAD': getattr(settings, 'SECURE_HSTS_PRELOAD', False),
        'SECURE_CONTENT_TYPE_NOSNIFF': getattr(settings, 'SECURE_CONTENT_TYPE_NOSNIFF', True),
        'SECURE_BROWSER_XSS_FILTER': getattr(settings, 'SECURE_BROWSER_XSS_FILTER', True),
        'SESSION_COOKIE_SECURE': getattr(settings, 'SESSION_COOKIE_SECURE', False),
        'CSRF_COOKIE_SECURE': getattr(settings, 'CSRF_COOKIE_SECURE', False),
        'CSRF_TRUSTED_ORIGINS': getattr(settings, 'CSRF_TRUSTED_ORIGINS', []),
    }
    
    # Logging settings
    logging_config = getattr(settings, 'LOGGING', {})
    logging_settings = {
        'VERSION': logging_config.get('version', 'Not configured'),
        'DISABLE_EXISTING_LOGGERS': logging_config.get('disable_existing_loggers', False),
        'FORMATTERS_COUNT': len(logging_config.get('formatters', {})),
        'HANDLERS_COUNT': len(logging_config.get('handlers', {})),
        'LOGGERS_COUNT': len(logging_config.get('loggers', {})),
        'ROOT_LEVEL': logging_config.get('root', {}).get('level', 'Not configured'),
    }
    
    # Staging fixes status
    csrf_trusted_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
    staging_fixes = {
        'CSRF_FIX_APPLIED': len(csrf_trusted_origins) > 0,
        'CSRF_TRUSTED_ORIGINS_COUNT': len(csrf_trusted_origins),
        'CSRF_HTTPS_CONFIGURED': any('https://' in origin for origin in csrf_trusted_origins),
        'CSRF_HTTP_CONFIGURED': any('http://' in origin for origin in csrf_trusted_origins),
        'LOGGING_FIX_APPLIED': True,  # This is always true now as we've applied the fix
        # Staging domain removed - using QA environment only
        'FIX_STATUS': 'Applied' if len(csrf_trusted_origins) > 0 else 'Not Applied',
        'CSRF_ORIGINS_LIST': csrf_trusted_origins,
    }
    
    # Get media file statistics if available
    media_stats = {}
    try:
        media_stats = MediaFile.get_storage_statistics()
    except Exception as e:
        logger.error("Error getting media statistics: %s", str(e))
        media_stats = {'error': 'Could not retrieve media statistics'}
    
    # Environment variables (filtered for security)
    env_vars = {}
    safe_env_vars = [
        'DEBUG', 'ALLOWED_HOSTS', 'FEATURE_FLAGS',
        'GCS_BUCKET_NAME', 'GCS_PROJECT_ID', 'GCS_LOCATION',
        'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USE_TLS', 'DEFAULT_FROM_EMAIL',
        'INBUCKET_SMTP_PORT', 'DB_ENGINE', 'PG_HOST', 'PG_PORT', 'PG_DB'
    ]
    
    for var in safe_env_vars:
        value = os.environ.get(var, 'Not set')
        if var in ['SECRET_KEY', 'PG_PASSWORD', 'PG_USER', 'EMAIL_HOST_PASSWORD', 'EMAIL_HOST_USER']:
            value = '***HIDDEN***' if value != 'Not set' else 'Not set'
        env_vars[var] = value
    
    # System information
    system_info = {
        'Python_Version': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
        'Django_Version': getattr(settings, 'DJANGO_VERSION', 'Unknown'),
        'BASE_DIR': str(settings.BASE_DIR),
        'Project_Dir': str(getattr(settings, 'PROJECT_DIR', 'Not configured')),
    }
    
    context = {
        'django_settings': django_settings,
        'database_settings': database_settings,
        'email_settings': email_settings,
        'media_settings': media_settings,
        'auth_settings': auth_settings,
        'static_settings': static_settings,
        'app_settings': app_settings,
        'middleware_settings': middleware_settings,
        'security_settings': security_settings,
        'logging_settings': logging_settings,
        'staging_fixes': staging_fixes,
        'env_vars': env_vars,
        'system_info': system_info,
        'media_stats': media_stats,
    }
    
    return render(request, 'sys/settings.html', context)


@application_admin_required
@log_execution_time
def sys_media_browser(request):
    """Media file browser and management"""
    logger.info("System media browser accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
    # Get filter parameters
    folder_filter = request.GET.get('folder', '')
    media_type_filter = request.GET.get('media_type', '')
    storage_filter = request.GET.get('storage', '')
    search = request.GET.get('search', '')
    
    # Build queryset
    media_files = MediaFile.objects.select_related('created_by')
    
    if folder_filter:
        media_files = media_files.filter(file_path__startswith=folder_filter)
    
    if media_type_filter:
        media_files = media_files.filter(media_type=media_type_filter)
        
    if storage_filter:
        media_files = media_files.filter(storage_backend=storage_filter)
    
    if search:
        media_files = media_files.filter(
            Q(original_filename__icontains=search) |
            Q(name__icontains=search) |
            Q(file_path__icontains=search)
        )
    
    media_files = media_files.order_by('-created')
    
    # Pagination
    paginator = Paginator(media_files, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get statistics
    stats = MediaFile.get_storage_statistics()
    
    # Get folder structure
    folders = []
    try:
        # Try to list directories in storage
        if hasattr(default_storage, 'listdir'):
            # For file system storage
            dirs, files = default_storage.listdir('')
            folders = [d for d in dirs if d in ['collections', 'items', 'avatars', 'test']]
        else:
            # Default folders for GCS
            folders = ['collections', 'items', 'avatars', 'test']
    except Exception:
        folders = ['collections', 'items', 'avatars', 'test']
    
    # Check for abandoned files
    abandoned_count = 0
    try:
        abandoned_count = check_abandoned_files()
    except Exception as e:
        logger.error("Error checking abandoned files: %s", str(e))
    
    context = {
        'page_obj': page_obj,
        'folder_filter': folder_filter,
        'media_type_filter': media_type_filter,
        'storage_filter': storage_filter,
        'search': search,
        'stats': stats,
        'folders': folders,
        'abandoned_count': abandoned_count,
        'media_types': MediaFile.MediaType.choices,
        'storage_backends': MediaFile.StorageBackend.choices,
        'total_count': media_files.count(),
    }
    
    return render(request, 'sys/media_browser.html', context)


@application_admin_required
@require_http_methods(["POST"])
def sys_media_upload(request):
    """Upload new media file"""
    try:
        folder = request.POST.get('folder', '').strip()
        file_obj = request.FILES.get('file')
        name = request.POST.get('name', '').strip()
        media_type = request.POST.get('media_type', MediaFile.MediaType.OTHER)
        
        if not file_obj:
            messages.error(request, 'No file provided')
            return redirect('sys_media_browser')
        
        if not folder:
            messages.error(request, 'Folder selection required')
            return redirect('sys_media_browser')
            
        # Validate media type
        if media_type not in dict(MediaFile.MediaType.choices):
            media_type = MediaFile.MediaType.OTHER
        
        # Clean filename
        original_filename = file_obj.name
        safe_filename = original_filename.replace(" ", "_").replace("/", "_")
        file_path = f"{folder}/{safe_filename}"
        
        # Save file to storage
        saved_path = default_storage.save(file_path, file_obj)
        
        # Get file info
        file_size = default_storage.size(saved_path)
        content_type = getattr(file_obj, 'content_type', 'application/octet-stream')
        
        # Create MediaFile record
        media_file = MediaFile.objects.create(
            name=name or original_filename,
            file_path=saved_path,
            original_filename=original_filename,
            file_size=file_size,
            content_type=content_type,
            media_type=media_type,
            created_by=request.user
        )
        
        logger.info("Admin user '%s' [%s] uploaded media file '%s' [%s] to '%s'", 
                   request.user.username, request.user.id, media_file.name, media_file.hash, saved_path)
        
        messages.success(request, f"File '{original_filename}' uploaded successfully")
        return redirect('sys_media_browser')
        
    except Exception as e:
        logger.error("Media upload failed: %s", str(e))
        messages.error(request, f'Upload failed: {str(e)}')
        return redirect('sys_media_browser')


@application_admin_required
@require_http_methods(["POST"])
def sys_media_delete(request, media_file_hash):
    """Delete media file and its storage along with all related records"""
    media_file = get_object_or_404(MediaFile, hash=media_file_hash)
    
    try:
        file_path = media_file.file_path
        filename = media_file.original_filename
        media_file_id = media_file.id
        
        # Check what will be cleaned up before deletion
        collection_images_count = media_file.collection_images.count()
        item_images_count = media_file.item_images.count()
        
        # Get names of affected collections/items for better logging
        affected_collections = list(media_file.collection_images.select_related('collection').values_list('collection__name', flat=True))
        affected_items = list(media_file.item_images.select_related('item').values_list('item__name', flat=True))
        
        # Delete from storage if it exists
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            logger.info("Deleted file from storage: %s", file_path)
        
        # Delete MediaFile record (CASCADE will automatically delete related records)
        media_file.delete()
        
        # Verify CASCADE deletions worked properly
        from web.models import CollectionImage, CollectionItemImage
        remaining_collection_images = CollectionImage.objects.filter(media_file_id=media_file_id).count()
        remaining_item_images = CollectionItemImage.objects.filter(media_file_id=media_file_id).count()
        
        if remaining_collection_images > 0 or remaining_item_images > 0:
            # Clean up orphaned records manually
            CollectionImage.objects.filter(media_file_id=media_file_id).delete()
            CollectionItemImage.objects.filter(media_file_id=media_file_id).delete()
            logger.warning("Had to manually clean up %d orphaned CollectionImage and %d orphaned CollectionItemImage records for media file ID %d", 
                          remaining_collection_images, remaining_item_images, media_file_id)
        
        # Build success message with cleanup info
        cleanup_info = []
        if collection_images_count > 0:
            cleanup_info.append(f"{collection_images_count} collection image references")
            logger.info("Cleaned up %d collection image references for collections: %s", 
                       collection_images_count, ', '.join(affected_collections))
        
        if item_images_count > 0:
            cleanup_info.append(f"{item_images_count} item image references")
            logger.info("Cleaned up %d item image references for items: %s", 
                       item_images_count, ', '.join(affected_items))
        
        success_message = f"File '{filename}' deleted successfully"
        if cleanup_info:
            success_message += f" (also cleaned up {', '.join(cleanup_info)})"
        
        logger.info("Admin user '%s' [%s] deleted media file '%s' at '%s'", 
                   request.user.username, request.user.id, filename, file_path)
        
        messages.success(request, success_message)
        return redirect('sys_media_browser')
        
    except Exception as e:
        logger.error("Media deletion failed: %s", str(e))
        messages.error(request, f'Deletion failed: {str(e)}')
        return redirect('sys_media_browser')


@application_admin_required
@require_http_methods(["POST"])
def sys_media_cleanup_abandoned(request):
    """Clean up abandoned files (files in storage without MediaFile records)"""
    try:
        cleaned_count = cleanup_abandoned_files()
        
        logger.info("Admin user '%s' [%s] cleaned up %d abandoned files", 
                   request.user.username, request.user.id, cleaned_count)
        
        messages.success(request, f"Cleaned up {cleaned_count} abandoned files")
        return redirect('sys_media_browser')
        
    except Exception as e:
        logger.error("Abandoned files cleanup failed: %s", str(e))
        messages.error(request, f'Cleanup failed: {str(e)}')
        return redirect('sys_media_browser')


@application_admin_required
@log_execution_time
def sys_media_verify_all(request):
    """Verify all media files exist in storage"""
    if request.method != 'POST':
        messages.error(request, 'Invalid request method')
        return redirect('sys_media_browser')
    
    try:
        # Get all media files
        all_files = MediaFile.objects.all()
        total_files = all_files.count()
        
        if total_files == 0:
            messages.info(request, 'No media files to verify')
            return redirect('sys_media_browser')
        
        # Verify each file
        verified_count = 0
        missing_count = 0
        error_count = 0
        
        for media_file in all_files:
            try:
                if media_file.verify_file_exists():
                    verified_count += 1
                else:
                    missing_count += 1
            except Exception as e:
                logger.error(f"Error verifying file {media_file.hash}: {str(e)}")
                error_count += 1
        
        # Log the verification results
        logger.info("Admin user '%s' [%s] verified %d files: %d found, %d missing, %d errors", 
                   request.user.username, request.user.id, total_files, 
                   verified_count, missing_count, error_count)
        
        # Create appropriate message based on results
        if missing_count == 0 and error_count == 0:
            messages.success(request, f"✅ All {verified_count} files verified successfully!")
        elif missing_count > 0 and error_count == 0:
            messages.warning(request, f"⚠️ Verified {total_files} files: {verified_count} found, {missing_count} missing")
        elif error_count > 0:
            messages.error(request, f"❌ Verified {total_files} files: {verified_count} found, {missing_count} missing, {error_count} errors")
        
        return redirect('sys_media_browser')
        
    except Exception as e:
        logger.error("Media file verification failed: %s", str(e))
        messages.error(request, f'Verification failed: {str(e)}')
        return redirect('sys_media_browser')


def check_abandoned_files():
    """Check for files in storage that don't have MediaFile records"""
    abandoned_count = 0
    
    try:
        # Get all files from storage
        storage_files = set()
        
        # For different storage backends, we need different approaches
        if hasattr(default_storage, 'bucket'):
            # GCS storage
            from google.cloud import storage
            try:
                blobs = default_storage.bucket.list_blobs()
                for blob in blobs:
                    # Remove the location prefix if present
                    path = blob.name
                    location = getattr(settings, 'GCS_LOCATION', 'media')
                    if path.startswith(f"{location}/"):
                        path = path[len(f"{location}/"):]
                    storage_files.add(path)
            except Exception as e:
                logger.error("Error listing GCS files: %s", str(e))
                return 0
                
        elif hasattr(default_storage, 'location'):
            # Local file system storage
            import os
            media_root = default_storage.location
            for root, dirs, files in os.walk(media_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, media_root)
                    storage_files.add(relative_path.replace('\\', '/'))
        
        # Get all MediaFile paths
        media_file_paths = set(MediaFile.objects.values_list('file_path', flat=True))
        
        # Find abandoned files
        abandoned_files = storage_files - media_file_paths
        abandoned_count = len(abandoned_files)
        
        return abandoned_count
        
    except Exception as e:
        logger.error("Error checking abandoned files: %s", str(e))
        return 0


def cleanup_abandoned_files():
    """Clean up abandoned files from storage"""
    cleaned_count = 0
    
    try:
        # Get all files from storage
        storage_files = set()
        
        if hasattr(default_storage, 'bucket'):
            # GCS storage
            from google.cloud import storage
            try:
                blobs = list(default_storage.bucket.list_blobs())
                for blob in blobs:
                    path = blob.name
                    location = getattr(settings, 'GCS_LOCATION', 'media')
                    if path.startswith(f"{location}/"):
                        path = path[len(f"{location}/"):]
                    storage_files.add(path)
            except Exception as e:
                logger.error("Error listing GCS files for cleanup: %s", str(e))
                return 0
                
        elif hasattr(default_storage, 'location'):
            # Local file system storage
            import os
            media_root = default_storage.location
            for root, dirs, files in os.walk(media_root):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, media_root)
                    storage_files.add(relative_path.replace('\\', '/'))
        
        # Get all MediaFile paths
        media_file_paths = set(MediaFile.objects.values_list('file_path', flat=True))
        
        # Find and delete abandoned files
        abandoned_files = storage_files - media_file_paths
        
        for file_path in abandoned_files:
            try:
                if default_storage.exists(file_path):
                    default_storage.delete(file_path)
                    cleaned_count += 1
                    logger.info("Cleaned up abandoned file: %s", file_path)
            except Exception as e:
                logger.error("Error deleting abandoned file %s: %s", file_path, str(e))
        
        return cleaned_count
        
    except Exception as e:
        logger.error("Error during abandoned files cleanup: %s", str(e))
        return 0


# Email Queue Management Views

@application_admin_required
def sys_email_queue(request):
    """
    Display email queue status and management interface.
    Shows pending, sent, failed emails and provides queue management tools.
    """
    logger.info("email_queue: SYS email queue accessed by user %s [%s]", 
        request.user.username, request.user.id,
        extra={
            'function': 'sys_email_queue',
            'action': 'admin_access',
            'result': 'success'
        })
    
    # Get email statistics - using numeric status values from STATUS_CHOICES
    # 0=sent, 1=failed, 2=queued, 3=requeued
    total_emails = Email.objects.count()
    pending_emails = Email.objects.filter(status__in=[2, 3]).count()  # queued + requeued
    sent_emails = Email.objects.filter(status=0).count()  # sent
    failed_emails = Email.objects.filter(status=1).count()  # failed
    
    # Get recent emails (last 100)
    recent_emails = Email.objects.select_related().order_by('-created')[:100]
    
    # Get queue processing statistics
    last_sent_email = Email.objects.filter(status=0).order_by('-last_updated').first()  # sent
    last_failed_email = Email.objects.filter(status=1).order_by('-last_updated').first()  # failed
    
    # Check for stale pending emails (older than 1 hour)
    stale_threshold = timezone.now() - timedelta(hours=1)
    stale_emails = Email.objects.filter(
        status__in=[2, 3],  # queued + requeued
        created__lt=stale_threshold
    ).count()
    
    context = {
        'total_emails': total_emails,
        'pending_emails': pending_emails,
        'sent_emails': sent_emails,
        'failed_emails': failed_emails,
        'stale_emails': stale_emails,
        'recent_emails': recent_emails,
        'last_sent_email': last_sent_email,
        'last_failed_email': last_failed_email,
        'queue_health': 'healthy' if stale_emails == 0 else 'warning' if stale_emails < 10 else 'critical',
    }
    
    return render(request, 'sys/email_queue.html', context)


@application_admin_required 
@require_http_methods(["POST"])
def sys_email_queue_process(request):
    """
    Manually trigger email queue processing via Django management command.
    """
    from django.core.management import call_command
    from io import StringIO
    import sys
    
    logger.info("email_queue_process: Manual queue processing triggered by user %s [%s]", 
        request.user.username, request.user.id,
        extra={
            'function': 'sys_email_queue_process',
            'action': 'manual_trigger',
            'result': 'started'
        })
    
    try:
        # Capture command output
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        # Run the send_queued_mail command
        call_command('send_queued_mail', verbosity=1)
        
        # Restore stdout and get output
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        
        # Count emails processed (basic parsing)
        lines = output.split('\n')
        processed_count = len([line for line in lines if 'sent' in line.lower()])
        
        logger.info("email_queue_process: Manual processing completed - %d emails processed", 
            processed_count,
            extra={
                'function': 'sys_email_queue_process',
                'action': 'manual_trigger',
                'result': 'success',
                'emails_processed': processed_count
            })
        
        messages.success(request, f'Queue processing completed. {processed_count} emails processed.')
        
    except Exception as e:
        logger.error("email_queue_process: Manual processing failed: %s", str(e),
            extra={
                'function': 'sys_email_queue_process',
                'action': 'manual_trigger',
                'result': 'error',
                'error': str(e)
            })
        
        messages.error(request, f'Queue processing failed: {str(e)}')
    
    return redirect('sys_email_queue')


@application_admin_required
@require_http_methods(["POST"])
def sys_email_queue_cleanup(request):
    """
    Clean up old emails from the queue (sent emails older than specified days).
    """
    from django.core.management import call_command
    from io import StringIO
    import sys
    
    days = int(request.POST.get('days', 30))
    
    logger.info("email_queue_cleanup: Cleanup triggered by user %s [%s] for %d days", 
        request.user.username, request.user.id, days,
        extra={
            'function': 'sys_email_queue_cleanup',
            'action': 'cleanup_trigger',
            'days': days
        })
    
    try:
        # Capture command output
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        # Run the cleanup_mail command
        call_command('cleanup_mail', days=days, verbosity=1)
        
        # Restore stdout and get output
        sys.stdout = old_stdout
        output = mystdout.getvalue()
        
        logger.info("email_queue_cleanup: Cleanup completed for %d days", days,
            extra={
                'function': 'sys_email_queue_cleanup', 
                'action': 'cleanup_trigger',
                'result': 'success',
                'days': days
            })
        
        messages.success(request, f'Email cleanup completed for emails older than {days} days.')
        
    except Exception as e:
        logger.error("email_queue_cleanup: Cleanup failed: %s", str(e),
            extra={
                'function': 'sys_email_queue_cleanup',
                'action': 'cleanup_trigger',
                'result': 'error',
                'error': str(e)
            })
        
        messages.error(request, f'Email cleanup failed: {str(e)}')
    
    return redirect('sys_email_queue')


@application_admin_required
@log_execution_time
def sys_marketing_consent(request):
    """Marketing email consent management interface"""
    logger.info("System marketing consent management accessed by admin user '%s' [%s]", 
               request.user.username, request.user.id)
    
    # Get filter parameters
    search = request.GET.get('search', '').strip()
    consent_filter = request.GET.get('consent', '')
    resend_status_filter = request.GET.get('resend_status', '')
    
    # Build queryset
    profiles = UserProfile.objects.select_related('user').order_by('-created_at')
    
    if search:
        profiles = profiles.filter(
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    
    if consent_filter == 'opted_in':
        profiles = profiles.filter(receive_marketing_emails=True)
    elif consent_filter == 'opted_out':
        profiles = profiles.filter(receive_marketing_emails=False)
    
    if resend_status_filter == 'synced':
        profiles = profiles.filter(resend_audience_id__isnull=False)
    elif resend_status_filter == 'not_synced':
        profiles = profiles.filter(resend_audience_id__isnull=True)
    
    # Pagination
    paginator = Paginator(profiles, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    total_profiles = UserProfile.objects.count()
    opted_in_count = UserProfile.objects.filter(receive_marketing_emails=True).count()
    opted_out_count = UserProfile.objects.filter(receive_marketing_emails=False).count()
    synced_count = UserProfile.objects.filter(resend_audience_id__isnull=False).count()
    
    # Check Resend API status
    resend_configured = bool(getattr(settings, 'RESEND_API_KEY', ''))
    resend_audience_id = getattr(settings, 'RESEND_MARKETING_AUDIENCE_ID', '')
    
    context = {
        'page_obj': page_obj,
        'search': search,
        'consent_filter': consent_filter,
        'resend_status_filter': resend_status_filter,
        'total_profiles': total_profiles,
        'opted_in_count': opted_in_count,
        'opted_out_count': opted_out_count,
        'synced_count': synced_count,
        'not_synced_count': total_profiles - synced_count,
        'resend_configured': resend_configured,
        'resend_audience_id': resend_audience_id,
        'opt_in_percentage': round((opted_in_count / total_profiles * 100) if total_profiles > 0 else 0, 1),
        'sync_percentage': round((synced_count / total_profiles * 100) if total_profiles > 0 else 0, 1),
    }
    
    return render(request, 'sys/marketing_consent.html', context)


@application_admin_required
@require_http_methods(["POST"])
def sys_marketing_consent_sync_user(request, user_id):
    """Manually sync a specific user's marketing consent with Resend"""
    user = get_object_or_404(User, id=user_id)
    
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Import the service
        from web.services.resend_service import ResendService
        resend_service = ResendService()
        
        if profile.receive_marketing_emails:
            # Subscribe to audience
            success = resend_service.subscribe_to_audience(
                email=user.email,
                first_name=user.first_name or "",
                last_name=user.last_name or ""
            )
            if success:
                profile.resend_audience_id = getattr(settings, 'RESEND_MARKETING_AUDIENCE_ID', '')
                profile.save()
                logger.info("Admin user '%s' [%s] manually synced user '%s' [%s] to Resend audience", 
                           request.user.username, request.user.id, user.email, user.id)
                messages.success(request, f"Successfully subscribed {user.email} to marketing emails")
            else:
                messages.error(request, f"Failed to subscribe {user.email} to marketing emails")
        else:
            # Unsubscribe from audience
            success = resend_service.unsubscribe_from_audience(user.email)
            if success:
                profile.resend_audience_id = None
                profile.save()
                logger.info("Admin user '%s' [%s] manually unsubscribed user '%s' [%s] from Resend audience", 
                           request.user.username, request.user.id, user.email, user.id)
                messages.success(request, f"Successfully unsubscribed {user.email} from marketing emails")
            else:
                messages.error(request, f"Failed to unsubscribe {user.email} from marketing emails")
                
    except Exception as e:
        logger.error("Marketing consent sync failed for user %s: %s", user.email, str(e))
        messages.error(request, f"Sync failed for {user.email}: {str(e)}")
    
    return redirect('sys_marketing_consent')


@application_admin_required
@require_http_methods(["POST"])
def sys_marketing_consent_bulk_sync(request):
    """Bulk sync all users' marketing consent with Resend"""
    try:
        from web.services.resend_service import ResendService
        resend_service = ResendService()
        
        # Get users that need syncing
        profiles_to_sync = UserProfile.objects.select_related('user').filter(
            Q(receive_marketing_emails=True, resend_audience_id__isnull=True) |
            Q(receive_marketing_emails=False, resend_audience_id__isnull=False)
        )
        
        total_count = profiles_to_sync.count()
        if total_count == 0:
            messages.info(request, "All users are already synced with Resend")
            return redirect('sys_marketing_consent')
        
        success_count = 0
        error_count = 0
        
        for profile in profiles_to_sync:
            try:
                if profile.receive_marketing_emails:
                    # Subscribe to audience
                    success = resend_service.subscribe_to_audience(
                        email=profile.user.email,
                        first_name=profile.user.first_name or "",
                        last_name=profile.user.last_name or ""
                    )
                    if success:
                        profile.resend_audience_id = getattr(settings, 'RESEND_MARKETING_AUDIENCE_ID', '')
                        profile.save()
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    # Unsubscribe from audience
                    success = resend_service.unsubscribe_from_audience(profile.user.email)
                    if success:
                        profile.resend_audience_id = None
                        profile.save()
                        success_count += 1
                    else:
                        error_count += 1
                        
            except Exception as e:
                logger.error("Bulk sync failed for user %s: %s", profile.user.email, str(e))
                error_count += 1
        
        logger.info("Admin user '%s' [%s] performed bulk sync: %d success, %d errors", 
                   request.user.username, request.user.id, success_count, error_count)
        
        if error_count == 0:
            messages.success(request, f"Successfully synced {success_count} users with Resend")
        else:
            messages.warning(request, f"Synced {success_count} users successfully, {error_count} failed")
            
    except Exception as e:
        logger.error("Bulk marketing consent sync failed: %s", str(e))
        messages.error(request, f"Bulk sync failed: {str(e)}")
    
    return redirect('sys_marketing_consent')


@application_admin_required
@require_http_methods(["POST"])
def sys_marketing_consent_remove_user(request, user_id):
    """Forcibly remove a user from Resend audience regardless of their preference"""
    user = get_object_or_404(User, id=user_id)
    
    try:
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Import the service
        from web.services.resend_service import ResendService
        resend_service = ResendService()
        
        # Force remove from Resend audience
        success = resend_service.unsubscribe_from_audience(user.email)
        
        if success:
            # Update profile to reflect removal
            profile.resend_audience_id = None
            profile.receive_marketing_emails = False  # Force opt-out
            profile.marketing_email_unsubscribed_at = timezone.now()
            profile.save()
            
            logger.warning("Admin user '%s' [%s] forcibly removed user '%s' [%s] from Resend audience", 
                          request.user.username, request.user.id, user.email, user.id)
            messages.success(request, f"Successfully removed {user.email} from Resend audience and updated preferences")
        else:
            messages.error(request, f"Failed to remove {user.email} from Resend audience")
                
    except Exception as e:
        logger.error("Marketing consent removal failed for user %s: %s", user.email, str(e))
        messages.error(request, f"Removal failed for {user.email}: {str(e)}")
    
    return redirect('sys_marketing_consent')


@application_admin_required
@require_http_methods(["POST"])
def sys_marketing_consent_bulk_remove_opted_out(request):
    """Bulk remove all opted-out users from Resend audience"""
    try:
        from web.services.resend_service import ResendService
        resend_service = ResendService()
        
        # Get opted-out users who are still in Resend audience
        profiles_to_remove = UserProfile.objects.select_related('user').filter(
            receive_marketing_emails=False,
            resend_audience_id__isnull=False
        )
        
        total_count = profiles_to_remove.count()
        if total_count == 0:
            messages.info(request, "No opted-out users found in Resend audience")
            return redirect('sys_marketing_consent')
        
        success_count = 0
        error_count = 0
        
        for profile in profiles_to_remove:
            try:
                # Remove from Resend audience
                success = resend_service.unsubscribe_from_audience(profile.user.email)
                if success:
                    profile.resend_audience_id = None
                    profile.marketing_email_unsubscribed_at = timezone.now()
                    profile.save()
                    success_count += 1
                else:
                    error_count += 1
                        
            except Exception as e:
                logger.error("Bulk removal failed for user %s: %s", profile.user.email, str(e))
                error_count += 1
        
        logger.info("Admin user '%s' [%s] performed bulk removal of opted-out users: %d success, %d errors", 
                   request.user.username, request.user.id, success_count, error_count)
        
        if error_count == 0:
            messages.success(request, f"Successfully removed {success_count} opted-out users from Resend audience")
        else:
            messages.warning(request, f"Removed {success_count} users successfully, {error_count} failed")
            
    except Exception as e:
        logger.error("Bulk removal of opted-out users failed: %s", str(e))
        messages.error(request, f"Bulk removal failed: {str(e)}")
    
    return redirect('sys_marketing_consent')


@application_admin_required
@require_http_methods(["POST"])
def sys_marketing_consent_full_sync(request):
    """Run full Resend audience sync using management command"""
    try:
        from django.core.management import call_command
        from io import StringIO
        
        # Capture command output
        out = StringIO()
        
        # Run the management command
        call_command('sync_resend_audience', '--batch-size=100', stdout=out)
        
        output = out.getvalue()
        
        # Parse output for summary
        lines = output.strip().split('\n')
        summary_line = lines[-1] if lines else ""
        
        logger.info("Admin user '%s' [%s] ran full Resend sync", 
                   request.user.username, request.user.id)
        
        if "Sync completed" in summary_line:
            messages.success(request, f"Full sync completed successfully. {summary_line}")
        else:
            messages.info(request, "Sync job started. Check logs for details.")
            
    except Exception as e:
        logger.error("Full Resend sync failed: %s", str(e))
        messages.error(request, f"Full sync failed: {str(e)}")
    
    return redirect('sys_marketing_consent')


@application_admin_required 
def sys_import_data(request):
    """Data import interface for administrators"""
    context = {
        'users': User.objects.filter(is_active=True).order_by('email'),
        'example_formats': {
            'json': 'application/json',
            'yaml': 'application/x-yaml', 
            'yml': 'application/x-yaml'
        }
    }
    
    if request.method == 'POST':
        try:
            # Get uploaded file
            import_file = request.FILES.get('import_file')
            target_user_id = request.POST.get('target_user')
            download_images = request.POST.get('download_images') == 'on'
            
            if not import_file:
                messages.error(request, "Please select a file to import")
                return render(request, 'sys/import_data.html', context)
            
            if not target_user_id:
                messages.error(request, "Please select a target user")
                return render(request, 'sys/import_data.html', context)
            
            # Get target user
            try:
                target_user = User.objects.get(id=target_user_id)
            except User.DoesNotExist:
                messages.error(request, "Selected user not found")
                return render(request, 'sys/import_data.html', context)
            
            # Validate file size (limit to 10MB)
            if import_file.size > 10 * 1024 * 1024:
                messages.error(request, "File size too large. Maximum 10MB allowed")
                return render(request, 'sys/import_data.html', context)
            
            # Get file extension
            file_name = import_file.name.lower()
            if file_name.endswith('.json'):
                file_extension = 'json'
            elif file_name.endswith('.yaml') or file_name.endswith('.yml'):
                file_extension = 'yaml'
            else:
                messages.error(request, "Unsupported file format. Use JSON or YAML files")
                return render(request, 'sys/import_data.html', context)
            
            # Read file content
            file_content = import_file.read().decode('utf-8')
            
            # Validate the import file
            from web.import_validator import ImportValidator
            validator = ImportValidator()
            data, errors = validator.validate_import_file(file_content, file_extension)
            
            if errors:
                error_report = validator.generate_validation_report(errors)
                context['validation_errors'] = errors
                context['error_report'] = error_report
                messages.error(request, f"Import validation failed with {len(errors)} error(s)")
                return render(request, 'sys/import_data.html', context)
            
            # Store validated data in session for confirmation
            request.session['import_data'] = {
                'data': data,
                'target_user_id': target_user_id,
                'download_images': download_images,
                'file_name': import_file.name
            }
            
            # Calculate total items for display
            total_items = sum(len(collection.get('items', [])) for collection in data.get('collections', []))
            
            # Show preview/confirmation page
            context.update({
                'import_data': data,
                'target_user': target_user,
                'download_images': download_images,
                'file_name': import_file.name,
                'ready_for_import': True,
                'total_items': total_items
            })
            
            messages.info(request, "Import file validated successfully. Review the data below and confirm to proceed.")
            return render(request, 'sys/import_data.html', context)
            
        except Exception as e:
            logger.error("Import validation error for user %s: %s", request.user.username, str(e))
            messages.error(request, f"Import validation failed: {str(e)}")
            return render(request, 'sys/import_data.html', context)
    
    return render(request, 'sys/import_data.html', context)


@application_admin_required
@require_http_methods(["POST"])
def sys_import_data_confirm(request):
    """Process the confirmed import"""
    # Get import data from session
    import_session_data = request.session.get('import_data')
    if not import_session_data:
        messages.error(request, "Import session expired. Please upload the file again.")
        return redirect('sys_import_data')
    
    try:
        from web.import_processor import ImportProcessor
        
        data = import_session_data['data']
        target_user_id = import_session_data['target_user_id']
        download_images = import_session_data['download_images']
        file_name = import_session_data['file_name']
        
        # Get target user
        target_user = User.objects.get(id=target_user_id)
        
        # Process the import
        processor = ImportProcessor()
        result = processor.process_import(
            data=data,
            target_user=target_user,
            download_images=download_images,
            admin_user=request.user
        )
        
        # Clear session data
        del request.session['import_data']
        
        # Log the import
        logger.info("Admin user '%s' [%s] imported data from '%s' for user '%s' [%s]: %d collections, %d items, %d errors", 
                   request.user.username, request.user.id, file_name,
                   target_user.username, target_user.id,
                   result['collections_created'], result['items_created'], len(result['errors']))
        
        if result['errors']:
            messages.warning(request, f"Import completed with warnings. Created {result['collections_created']} collections and {result['items_created']} items. {len(result['errors'])} errors occurred.")
        else:
            messages.success(request, f"Import completed successfully! Created {result['collections_created']} collections and {result['items_created']} items.")
        
        # Store detailed results for display (convert datetime objects to strings)
        serializable_result = result.copy()
        if 'start_time' in serializable_result and serializable_result['start_time']:
            serializable_result['start_time'] = serializable_result['start_time'].isoformat()
        if 'end_time' in serializable_result and serializable_result['end_time']:
            serializable_result['end_time'] = serializable_result['end_time'].isoformat()
        request.session['import_result'] = serializable_result
        return redirect('sys_import_result')
        
    except Exception as e:
        logger.error("Import processing error for user %s: %s", request.user.username, str(e))
        messages.error(request, f"Import processing failed: {str(e)}")
        return redirect('sys_import_data')


@application_admin_required
def sys_import_result(request):
    """Display import results"""
    result = request.session.get('import_result')
    if not result:
        messages.info(request, "No import results to display.")
        return redirect('sys_import_data')
    
    # Convert ISO datetime strings back to datetime objects for template rendering
    from datetime import datetime
    if 'start_time' in result and result['start_time']:
        try:
            result['start_time'] = datetime.fromisoformat(result['start_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    if 'end_time' in result and result['end_time']:
        try:
            result['end_time'] = datetime.fromisoformat(result['end_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    context = {
        'result': result
    }
    
    # Clear the result from session after displaying
    del request.session['import_result']
    
    return render(request, 'sys/import_result.html', context)


@application_admin_required
@login_required
def content_moderation_dashboard(request):
    """
    Content moderation dashboard showing flagged images and user violations
    """
    # Content moderation statistics
    total_images = MediaFile.objects.filter(content_type__startswith='image/').count()
    
    flagged_images = MediaFile.objects.filter(
        content_moderation_status=MediaFile.ContentModerationStatus.FLAGGED
    ).count()
    
    pending_review = MediaFile.objects.filter(
        content_moderation_status=MediaFile.ContentModerationStatus.PENDING,
        content_type__startswith='image/'
    ).count()
    
    # User violation statistics
    users_with_violations = UserProfile.objects.filter(
        content_moderation_violations__gt=0
    ).count()
    
    banned_users = UserProfile.objects.filter(
        is_content_banned=True
    ).count()
    
    # Recent flagged images
    recent_flagged = MediaFile.objects.filter(
        content_moderation_status=MediaFile.ContentModerationStatus.FLAGGED
    ).select_related('created_by').order_by('-content_moderation_checked_at')[:10]
    
    # Users with highest violation counts
    high_violation_users = UserProfile.objects.filter(
        content_moderation_violations__gt=0
    ).select_related('user').order_by('-content_moderation_violations')[:10]
    
    # Status statistics for the chart
    status_stats = MediaFile.objects.filter(
        content_type__startswith='image/'
    ).values('content_moderation_status').annotate(count=models.Count('id')).order_by('-count')
    
    context = {
        # Template expects these specific variable names
        'flagged_content_count': flagged_images,
        'pending_review_count': pending_review,
        'user_violations_count': users_with_violations,
        'banned_users_count': banned_users,
        'recent_flagged_content': recent_flagged,
        'recent_violations': high_violation_users,
        'status_stats': status_stats,
        
        # Additional stats for template
        'total_content': total_images,
        'total_analyzed_images': total_images,
        'analysis_success_rate': 100 if total_images > 0 else 0,
        'last_analysis_time': recent_flagged.first().content_moderation_checked_at if recent_flagged.exists() else None,
        
        # Settings for template
        'moderation_enabled': getattr(settings, 'CONTENT_MODERATION_ENABLED', False),
        'moderation_action': getattr(settings, 'CONTENT_MODERATION_ACTION', 'flag_only'),
        'ban_threshold': getattr(settings, 'CONTENT_MODERATION_SOFT_BAN_THRESHOLD', 3),
        'settings': settings,
    }
    
    return render(request, 'sys/content_moderation_dashboard.html', context)


@application_admin_required
@login_required
def flagged_images(request):
    """
    List of all flagged images requiring review
    """
    flagged_images_query = MediaFile.objects.filter(
        content_moderation_status=MediaFile.ContentModerationStatus.FLAGGED
    ).select_related('created_by').order_by('-content_moderation_checked_at')
    
    # Pagination
    paginator = Paginator(flagged_images_query, 50)
    page_number = request.GET.get('page')
    flagged_images_page = paginator.get_page(page_number)
    
    context = {
        'flagged_images': flagged_images_page,
        'is_paginated': flagged_images_page.has_other_pages(),
        'page_obj': flagged_images_page,
    }
    
    return render(request, 'sys/flagged_images.html', context)


@application_admin_required
@login_required
def user_violations(request):
    """
    List of users with content violations
    """
    users_query = UserProfile.objects.filter(
        Q(content_moderation_violations__gt=0) | Q(is_content_banned=True)
    ).select_related('user').order_by('-content_moderation_violations')
    
    # Pagination
    paginator = Paginator(users_query, 50)
    page_number = request.GET.get('page')
    users_page = paginator.get_page(page_number)
    
    context = {
        'users': users_page,
    }
    
    return render(request, 'sys/user_violations.html', context)


@application_admin_required
@login_required 
@require_http_methods(["POST"])
def batch_analyze_images(request):
    """
    Trigger batch analysis of pending images
    """
    try:
        from web.services.content_moderation import content_moderation_service
        
        if not content_moderation_service.is_enabled():
            messages.error(request, "Content moderation is not enabled")
            return redirect('sys_content_moderation_dashboard')
        
        batch_size = int(request.POST.get('batch_size', 50))
        
        # Process batch
        result = content_moderation_service.batch_analyze_pending_files(batch_size)
        
        if result['processed'] > 0:
            messages.success(
                request,
                f"Analyzed {result['processed']} images. "
                f"Approved: {result['approved']}, Flagged: {result['flagged']}"
            )
            
            if result['errors'] > 0:
                messages.warning(request, f"{result['errors']} images had errors during analysis")
        else:
            messages.info(request, "No pending images to analyze")
        
    except Exception as e:
        logger.error(f"Batch analysis error: {e}")
        messages.error(request, f"Analysis failed: {str(e)}")
    
    return redirect('sys_content_moderation_dashboard')


@application_admin_required
@login_required
@require_http_methods(["POST"])
def approve_flagged_image(request, file_id):
    """
    Manually approve a flagged image
    """
    try:
        media_file = get_object_or_404(MediaFile, id=file_id)
        
        media_file.content_moderation_status = MediaFile.ContentModerationStatus.APPROVED
        media_file.save(update_fields=['content_moderation_status'])
        
        messages.success(request, f"Image '{media_file.original_filename}' has been approved")
        
    except Exception as e:
        logger.error(f"Error approving image {file_id}: {e}")
        messages.error(request, f"Failed to approve image: {str(e)}")
    
    return redirect('sys_flagged_images')


@application_admin_required
@login_required
@require_http_methods(["POST"])
def reject_flagged_image(request, file_id):
    """
    Manually delete a flagged image and remove it completely from the system along with all related records
    """
    try:
        media_file = get_object_or_404(MediaFile, id=file_id)
        original_filename = media_file.original_filename
        file_path = media_file.file_path
        media_file_id = media_file.id
        
        # Check what will be cleaned up before deletion
        collection_images_count = media_file.collection_images.count()
        item_images_count = media_file.item_images.count()
        
        # Get names of affected collections/items for better logging
        affected_collections = list(media_file.collection_images.select_related('collection').values_list('collection__name', flat=True))
        affected_items = list(media_file.item_images.select_related('item').values_list('item__name', flat=True))
        
        # Delete the file from storage
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            logger.info("Deleted file from storage: %s", file_path)
        
        # Delete the MediaFile record completely from database (CASCADE will automatically delete related records)
        media_file.delete()
        
        # Verify CASCADE deletions worked properly
        from web.models import CollectionImage, CollectionItemImage
        remaining_collection_images = CollectionImage.objects.filter(media_file_id=media_file_id).count()
        remaining_item_images = CollectionItemImage.objects.filter(media_file_id=media_file_id).count()
        
        if remaining_collection_images > 0 or remaining_item_images > 0:
            # Clean up orphaned records manually
            CollectionImage.objects.filter(media_file_id=media_file_id).delete()
            CollectionItemImage.objects.filter(media_file_id=media_file_id).delete()
            logger.warning("Content moderation: Had to manually clean up %d orphaned CollectionImage and %d orphaned CollectionItemImage records for media file ID %d", 
                          remaining_collection_images, remaining_item_images, media_file_id)
        
        # Build cleanup message
        cleanup_info = []
        if collection_images_count > 0:
            cleanup_info.append(f"{collection_images_count} collection image references")
            logger.info("Content moderation deletion cleaned up %d collection image references for collections: %s", 
                       collection_images_count, ', '.join(affected_collections))
        
        if item_images_count > 0:
            cleanup_info.append(f"{item_images_count} item image references")
            logger.info("Content moderation deletion cleaned up %d item image references for items: %s", 
                       item_images_count, ', '.join(affected_items))
        
        success_message = f"Image '{original_filename}' has been permanently deleted from the system"
        if cleanup_info:
            success_message += f" (also cleaned up {', '.join(cleanup_info)})"
        
        logger.info("Admin user '%s' [%s] rejected and deleted flagged image '%s' at '%s'", 
                   request.user.username, request.user.id, original_filename, file_path)
        
        # Return JSON response for AJAX calls
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': True,
                'message': success_message
            })
        
        messages.success(request, success_message)
        
    except Exception as e:
        logger.error(f"Error deleting flagged image {file_id}: {e}")
        
        # Return JSON error response for AJAX calls
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': False,
                'message': f"Failed to delete image: {str(e)}"
            }, status=500)
            
        messages.error(request, f"Failed to delete image: {str(e)}")
    
    return redirect('sys_flagged_images')


@application_admin_required
@login_required
@require_http_methods(["POST"])
def approve_flagged_image(request, file_id):
    """
    Manually approve a flagged image
    """
    try:
        media_file = get_object_or_404(MediaFile, id=file_id)
        original_filename = media_file.original_filename
        
        # Set status to approved
        media_file.content_moderation_status = MediaFile.ContentModerationStatus.APPROVED
        media_file.save(update_fields=['content_moderation_status'])
        
        logger.info(f"Successfully approved image '{original_filename}' (ID: {file_id})")
        
        # Return JSON response for AJAX calls
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': True,
                'message': f"Image '{original_filename}' has been approved"
            })
        
        messages.success(request, f"Image '{original_filename}' has been approved")
        
    except Exception as e:
        logger.error(f"Error approving image {file_id}: {e}")
        
        # Return JSON error response for AJAX calls
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return JsonResponse({
                'success': False,
                'message': f"Failed to approve image: {str(e)}"
            }, status=500)
            
        messages.error(request, f"Failed to approve image: {str(e)}")
    
    return redirect('sys_flagged_images')


@application_admin_required
def content_moderation_settings(request):
    """Content moderation settings and configuration."""
    
    context = {
        'content_moderation_enabled': settings.CONTENT_MODERATION_ENABLED,
        'content_moderation_action': settings.CONTENT_MODERATION_ACTION,
        'soft_ban_threshold': settings.CONTENT_MODERATION_SOFT_BAN_THRESHOLD,
    }
    
    return render(request, 'sys/content_moderation_settings.html', context)



@application_admin_required
def review_content(request, file_id):
    """Detailed review of a specific piece of content."""
    
    media_file = get_object_or_404(MediaFile, id=file_id)
    
    # Get user's other flagged content
    other_flagged = MediaFile.objects.filter(
        uploaded_by=media_file.uploaded_by,
        content_moderation_status='FLAGGED'
    ).exclude(id=file_id)[:10]
    
    context = {
        'media_file': media_file,
        'other_flagged': other_flagged,
        'user_profile': media_file.uploaded_by.userprofile if media_file.uploaded_by else None,
    }
    
    return render(request, 'sys/review_content.html', context)


@application_admin_required
def user_detail(request, user_id):
    """Detailed view of a user including violation history."""
    
    user = get_object_or_404(User, id=user_id)
    profile = user.userprofile
    
    # Get user's flagged content
    flagged_content = MediaFile.objects.filter(
        uploaded_by=user,
        content_moderation_status__in=['FLAGGED', 'REJECTED']
    ).order_by('-content_moderation_checked_at')[:20]
    
    # Get user's activities
    recent_activities = Activity.objects.filter(
        created_by=user
    ).order_by('-created')[:20]
    
    context = {
        'user': user,
        'profile': profile,
        'flagged_content': flagged_content,
        'recent_activities': recent_activities,
        'total_violations': profile.content_moderation_violations,
        'is_content_banned': profile.is_content_banned,
        'last_violation': profile.last_violation_at,
    }
    
    return render(request, 'sys/user_detail.html', context)


@application_admin_required
def user_content(request, user_id):
    """View all content uploaded by a specific user."""

    user = get_object_or_404(User, id=user_id)

    # Get all user's media files with content moderation info
    media_files = MediaFile.objects.filter(
        uploaded_by=user
    ).order_by('-created')

    # Apply status filter if provided
    status_filter = request.GET.get('status')
    if status_filter:
        media_files = media_files.filter(content_moderation_status=status_filter)

    # Pagination
    paginator = Paginator(media_files, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'user': user,
        'media_files': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        'status_filter': status_filter,
    }

    return render(request, 'sys/user_content.html', context)


@application_admin_required
@log_execution_time
def sys_backups(request):
    """Display system backups stored in GCS."""
    logger.info("System backups view accessed by admin user '%s' [%s]", request.user.username, request.user.id)

    from google.cloud import storage

    backups = {
        'database': [],
        'media': [],
        'error': None
    }

    try:
        # Initialize GCS client
        credentials_path = settings.GCS_CREDENTIALS_PATH
        if credentials_path and os.path.exists(credentials_path):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

        storage_client = storage.Client(project=settings.GCS_PROJECT_ID)
        bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)

        # List database backups
        db_blobs = list(bucket.list_blobs(prefix='backups/database/'))
        db_blobs.sort(key=lambda x: x.time_created, reverse=True)

        for blob in db_blobs:
            backups['database'].append({
                'name': blob.name.split('/')[-1],
                'path': blob.name,
                'size': blob.size,
                'size_mb': round(blob.size / (1024 ** 2), 2),
                'created': blob.time_created,
                'download_url': blob.generate_signed_url(
                    version='v4',
                    expiration=timedelta(hours=1),
                    method='GET'
                )
            })

        # List media backups (group by timestamp)
        media_blobs = list(bucket.list_blobs(prefix='backups/media/'))

        # Group media backups by timestamp
        media_groups = {}
        for blob in media_blobs:
            # Extract timestamp from filename
            parts = blob.name.split('_')
            if len(parts) >= 3:
                timestamp_parts = []
                for i in range(2, len(parts)):
                    if 'part' in parts[i] or '.tar.gz' in parts[i]:
                        break
                    timestamp_parts.append(parts[i])

                timestamp = '_'.join(timestamp_parts)

                if timestamp not in media_groups:
                    media_groups[timestamp] = {
                        'timestamp': timestamp,
                        'files': [],
                        'total_size': 0,
                        'created': None
                    }

                media_groups[timestamp]['files'].append({
                    'name': blob.name.split('/')[-1],
                    'path': blob.name,
                    'size': blob.size,
                    'download_url': blob.generate_signed_url(
                        version='v4',
                        expiration=timedelta(hours=1),
                        method='GET'
                    )
                })
                media_groups[timestamp]['total_size'] += blob.size

                if media_groups[timestamp]['created'] is None or blob.time_created < media_groups[timestamp]['created']:
                    media_groups[timestamp]['created'] = blob.time_created

        # Convert to list and sort by created date
        for group_data in media_groups.values():
            group_data['total_size_mb'] = round(group_data['total_size'] / (1024 ** 2), 2)
            group_data['total_size_gb'] = round(group_data['total_size'] / (1024 ** 3), 2)
            group_data['part_count'] = len(group_data['files'])

        backups['media'] = sorted(media_groups.values(), key=lambda x: x['created'], reverse=True)

    except Exception as e:
        logger.error(f"Error listing backups: {e}", exc_info=True)
        backups['error'] = str(e)

    context = {
        'backups': backups,
    }

    return render(request, 'sys/backups.html', context)


@application_admin_required
@require_http_methods(['POST'])
def sys_backup_now(request):
    """Trigger a backup immediately."""
    logger.info("Backup triggered by admin user '%s' [%s]", request.user.username, request.user.id)

    from django.core.management import call_command
    import io

    try:
        # Capture command output
        out = io.StringIO()
        call_command('backup_system', stdout=out)
        output = out.getvalue()

        logger.info(f"Backup completed successfully. Output: {output}")
        messages.success(request, 'Backup completed successfully!')

    except Exception as e:
        logger.error(f"Backup failed: {e}", exc_info=True)
        messages.error(request, f'Backup failed: {str(e)}')

    return redirect('sys_backups')

