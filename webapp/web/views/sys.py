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
from core.lucide import LucideIcons

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
def sys_activity(request):
    """Activity logs management"""
    logger.info("System activity logs accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
    # Get filter parameters
    action_filter = request.GET.get('action', '')
    user_filter = request.GET.get('user', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Build queryset
    activities = RecentActivity.objects.select_related('created_by')
    
    if action_filter:
        activities = activities.filter(name=action_filter)
    
    if user_filter:
        try:
            user_id = int(user_filter)
            activities = activities.filter(created_by_id=user_id)
        except ValueError:
            pass
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            activities = activities.filter(created__date__gte=from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            activities = activities.filter(created__date__lte=to_date)
        except ValueError:
            pass
    
    activities = activities.order_by('-created')
    
    # Pagination
    paginator = Paginator(activities, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get distinct actions for filter
    distinct_actions = RecentActivity.objects.values_list('name', flat=True).distinct()
    
    # Get recent users for filter
    recent_users = User.objects.filter(
        recentactivity_created__isnull=False
    ).distinct().order_by('email')[:20]
    
    context = {
        'page_obj': page_obj,
        'action_filter': action_filter,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
        'distinct_actions': distinct_actions,
        'recent_users': recent_users,
        'total_count': activities.count(),
        'debug': settings.DEBUG,
    }
    
    return render(request, 'sys/activity.html', context)


@application_admin_required
@log_execution_time
def sys_metrics(request):
    """System metrics and analytics"""
    logger.info("System metrics accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
    # Time-based metrics
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    
    # User metrics
    user_metrics = {
        'total': User.objects.count(),
        'active_30d': User.objects.filter(last_login__gte=last_30_days).count(),
        'active_7d': User.objects.filter(last_login__gte=last_7_days).count(),
        'new_30d': User.objects.filter(date_joined__gte=last_30_days).count(),
        'new_7d': User.objects.filter(date_joined__gte=last_7_days).count(),
    }
    
    # Collection metrics
    collection_metrics = {
        'total': Collection.objects.count(),
        'public': Collection.objects.filter(visibility='PUBLIC').count(),
        'private': Collection.objects.filter(visibility='PRIVATE').count(),
        'unlisted': Collection.objects.filter(visibility='UNLISTED').count(),
        'created_30d': Collection.objects.filter(created__gte=last_30_days).count(),
        'created_7d': Collection.objects.filter(created__gte=last_7_days).count(),
    }
    
    # Item metrics
    item_metrics = {
        'total': CollectionItem.objects.count(),
        'favorites': CollectionItem.objects.filter(is_favorite=True).count(),
        'reserved': CollectionItem.objects.filter(status='RESERVED').count(),
        'wanted': CollectionItem.objects.filter(status='WANTED').count(),
        'created_30d': CollectionItem.objects.filter(created__gte=last_30_days).count(),
        'created_7d': CollectionItem.objects.filter(created__gte=last_7_days).count(),
    }
    
    # Activity metrics
    activity_metrics = {
        'total': RecentActivity.objects.count(),
        'last_30d': RecentActivity.objects.filter(created__gte=last_30_days).count(),
        'last_7d': RecentActivity.objects.filter(created__gte=last_7_days).count(),
        'top_actions': RecentActivity.objects.values('name').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
    }
    
    # Item type distribution
    item_type_distribution = CollectionItem.objects.values(
        'item_type__display_name'
    ).annotate(count=Count('id')).order_by('-count')
    
    # Media storage metrics
    media_stats = MediaFile.get_storage_statistics()
    media_metrics = {
        'total_files': media_stats.get('total_files', 0),
        'active_files': media_stats.get('active_files', 0),
        'missing_files': media_stats.get('missing_files', 0),
        'recent_uploads': media_stats.get('recent_uploads', 0),
        'total_size': media_stats.get('size_statistics', {}).get('total_size', 0),
        'average_size': media_stats.get('size_statistics', {}).get('average_size', 0),
        'storage_distribution': media_stats.get('storage_distribution', []),
        'type_distribution': media_stats.get('type_distribution', []),
    }
    
    context = {
        'user_metrics': user_metrics,
        'collection_metrics': collection_metrics,
        'item_metrics': item_metrics,
        'activity_metrics': activity_metrics,
        'item_type_distribution': item_type_distribution,
        'media_metrics': media_metrics,
        'debug': settings.DEBUG,
    }
    
    return render(request, 'sys/metrics.html', context)


def sys_prometheus_metrics(request):
    """Prometheus-compatible metrics endpoint for Grafana"""
    logger.info("Prometheus metrics accessed")
    
    # Time-based metrics
    now = timezone.now()
    last_30_days = now - timedelta(days=30)
    last_7_days = now - timedelta(days=7)
    last_24_hours = now - timedelta(hours=24)
    
    # Collect all metrics
    metrics = []
    
    # User metrics
    total_users = User.objects.count()
    active_users_30d = User.objects.filter(last_login__gte=last_30_days).count()
    active_users_7d = User.objects.filter(last_login__gte=last_7_days).count()
    active_users_24h = User.objects.filter(last_login__gte=last_24_hours).count()
    new_users_30d = User.objects.filter(date_joined__gte=last_30_days).count()
    new_users_7d = User.objects.filter(date_joined__gte=last_7_days).count()
    superusers = User.objects.filter(is_superuser=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    app_admin_users = User.objects.filter(groups__name='Application admin').count()
    
    metrics.extend([
        f'# HELP beryl_users_total Total number of users',
        f'# TYPE beryl_users_total gauge',
        f'beryl_users_total {total_users}',
        f'',
        f'# HELP beryl_users_active Active users by time period',
        f'# TYPE beryl_users_active gauge',
        f'beryl_users_active{{period="24h"}} {active_users_24h}',
        f'beryl_users_active{{period="7d"}} {active_users_7d}',
        f'beryl_users_active{{period="30d"}} {active_users_30d}',
        f'',
        f'# HELP beryl_users_new New users by time period',
        f'# TYPE beryl_users_new gauge',
        f'beryl_users_new{{period="7d"}} {new_users_7d}',
        f'beryl_users_new{{period="30d"}} {new_users_30d}',
        f'',
        f'# HELP beryl_users_permissions Users by permission level',
        f'# TYPE beryl_users_permissions gauge',
        f'beryl_users_permissions{{type="superuser"}} {superusers}',
        f'beryl_users_permissions{{type="staff"}} {staff_users}',
        f'beryl_users_permissions{{type="application_admin"}} {app_admin_users}',
        f'',
    ])
    
    # Collection metrics
    total_collections = Collection.objects.count()
    public_collections = Collection.objects.filter(visibility='PUBLIC').count()
    private_collections = Collection.objects.filter(visibility='PRIVATE').count()
    unlisted_collections = Collection.objects.filter(visibility='UNLISTED').count()
    collections_30d = Collection.objects.filter(created__gte=last_30_days).count()
    collections_7d = Collection.objects.filter(created__gte=last_7_days).count()
    
    metrics.extend([
        f'# HELP beryl_collections_total Total number of collections',
        f'# TYPE beryl_collections_total gauge',
        f'beryl_collections_total {total_collections}',
        f'',
        f'# HELP beryl_collections_by_visibility Collections by visibility type',
        f'# TYPE beryl_collections_by_visibility gauge',
        f'beryl_collections_by_visibility{{visibility="public"}} {public_collections}',
        f'beryl_collections_by_visibility{{visibility="private"}} {private_collections}',
        f'beryl_collections_by_visibility{{visibility="unlisted"}} {unlisted_collections}',
        f'',
        f'# HELP beryl_collections_new New collections by time period',
        f'# TYPE beryl_collections_new gauge',
        f'beryl_collections_new{{period="7d"}} {collections_7d}',
        f'beryl_collections_new{{period="30d"}} {collections_30d}',
        f'',
    ])
    
    # Item metrics
    total_items = CollectionItem.objects.count()
    favorite_items = CollectionItem.objects.filter(is_favorite=True).count()
    items_30d = CollectionItem.objects.filter(created__gte=last_30_days).count()
    items_7d = CollectionItem.objects.filter(created__gte=last_7_days).count()
    
    # Items by status
    status_counts = CollectionItem.objects.values('status').annotate(count=Count('id'))
    status_metrics = []
    for status_data in status_counts:
        status = status_data['status'].lower() if status_data['status'] else 'unknown'
        count = status_data['count']
        status_metrics.append(f'beryl_items_by_status{{status="{status}"}} {count}')
    
    metrics.extend([
        f'# HELP beryl_items_total Total number of items',
        f'# TYPE beryl_items_total gauge',
        f'beryl_items_total {total_items}',
        f'',
        f'# HELP beryl_items_favorites Total favorite items',
        f'# TYPE beryl_items_favorites gauge',
        f'beryl_items_favorites {favorite_items}',
        f'',
        f'# HELP beryl_items_new New items by time period',
        f'# TYPE beryl_items_new gauge',
        f'beryl_items_new{{period="7d"}} {items_7d}',
        f'beryl_items_new{{period="30d"}} {items_30d}',
        f'',
        f'# HELP beryl_items_by_status Items grouped by status',
        f'# TYPE beryl_items_by_status gauge',
    ])
    metrics.extend(status_metrics)
    metrics.append('')
    
    # Activity metrics
    total_activities = RecentActivity.objects.count()
    activities_24h = RecentActivity.objects.filter(created__gte=last_24_hours).count()
    activities_7d = RecentActivity.objects.filter(created__gte=last_7_days).count()
    activities_30d = RecentActivity.objects.filter(created__gte=last_30_days).count()
    
    # Top activities
    top_activities = RecentActivity.objects.values('name').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    activity_metrics = []
    for activity in top_activities:
        name = activity['name'].replace(' ', '_').lower() if activity['name'] else 'unknown'
        count = activity['count']
        activity_metrics.append(f'beryl_activities_by_type{{type="{name}"}} {count}')
    
    metrics.extend([
        f'# HELP beryl_activities_total Total number of activities',
        f'# TYPE beryl_activities_total gauge',
        f'beryl_activities_total {total_activities}',
        f'',
        f'# HELP beryl_activities_recent Recent activities by time period',
        f'# TYPE beryl_activities_recent gauge',
        f'beryl_activities_recent{{period="24h"}} {activities_24h}',
        f'beryl_activities_recent{{period="7d"}} {activities_7d}',
        f'beryl_activities_recent{{period="30d"}} {activities_30d}',
        f'',
        f'# HELP beryl_activities_by_type Activities grouped by type',
        f'# TYPE beryl_activities_by_type gauge',
    ])
    metrics.extend(activity_metrics)
    metrics.append('')
    
    # Item type distribution
    item_type_distribution = CollectionItem.objects.values(
        'item_type__display_name'
    ).annotate(count=Count('id')).order_by('-count')
    
    type_metrics = []
    for type_data in item_type_distribution:
        type_name = type_data['item_type__display_name']
        if type_name:
            type_name = type_name.replace(' ', '_').lower()
            count = type_data['count']
            type_metrics.append(f'beryl_items_by_type{{type="{type_name}"}} {count}')
    
    if type_metrics:
        metrics.extend([
            f'# HELP beryl_items_by_type Items grouped by type',
            f'# TYPE beryl_items_by_type gauge',
        ])
        metrics.extend(type_metrics)
        metrics.append('')
    
    # Media storage metrics
    media_stats = MediaFile.get_storage_statistics()
    
    # Basic media file counts
    metrics.extend([
        f'# HELP beryl_media_files_total Total number of media files',
        f'# TYPE beryl_media_files_total gauge',
        f'beryl_media_files_total {media_stats.get("total_files", 0)}',
        f'',
        f'# HELP beryl_media_files_active Active media files in storage',
        f'# TYPE beryl_media_files_active gauge',
        f'beryl_media_files_active {media_stats.get("active_files", 0)}',
        f'',
        f'# HELP beryl_media_files_missing Missing media files',
        f'# TYPE beryl_media_files_missing gauge',
        f'beryl_media_files_missing {media_stats.get("missing_files", 0)}',
        f'',
        f'# HELP beryl_media_uploads_recent Recent media uploads (7 days)',
        f'# TYPE beryl_media_uploads_recent gauge',
        f'beryl_media_uploads_recent {media_stats.get("recent_uploads", 0)}',
        f'',
    ])
    
    # Storage size metrics
    size_stats = media_stats.get('size_statistics', {})
    if size_stats.get('total_size'):
        metrics.extend([
            f'# HELP beryl_media_storage_bytes Total storage used by media files',
            f'# TYPE beryl_media_storage_bytes gauge',
            f'beryl_media_storage_bytes {size_stats.get("total_size", 0)}',
            f'',
            f'# HELP beryl_media_average_size_bytes Average media file size',
            f'# TYPE beryl_media_average_size_bytes gauge',
            f'beryl_media_average_size_bytes {size_stats.get("average_size", 0)}',
            f'',
        ])
    
    # Storage distribution by backend
    storage_metrics = []
    for storage_data in media_stats.get('storage_distribution', []):
        backend = storage_data.get('storage_backend', '').lower()
        count = storage_data.get('count', 0)
        total_size = storage_data.get('total_size', 0)
        if backend:
            storage_metrics.append(f'beryl_media_files_by_storage{{backend="{backend}"}} {count}')
            if total_size:
                storage_metrics.append(f'beryl_media_storage_by_backend{{backend="{backend}"}} {total_size}')
    
    if storage_metrics:
        metrics.extend([
            f'# HELP beryl_media_files_by_storage Media files by storage backend',
            f'# TYPE beryl_media_files_by_storage gauge',
        ])
        # Add file count metrics
        for metric in storage_metrics:
            if 'beryl_media_files_by_storage' in metric:
                metrics.append(metric)
        metrics.extend([
            f'',
            f'# HELP beryl_media_storage_by_backend Storage usage by backend',
            f'# TYPE beryl_media_storage_by_backend gauge',
        ])
        # Add storage size metrics
        for metric in storage_metrics:
            if 'beryl_media_storage_by_backend' in metric:
                metrics.append(metric)
        metrics.append('')
    
    # Media type distribution
    media_type_metrics = []
    for type_data in media_stats.get('type_distribution', []):
        media_type = type_data.get('media_type', '').lower()
        count = type_data.get('count', 0)
        total_size = type_data.get('total_size', 0)
        if media_type:
            media_type_metrics.append(f'beryl_media_files_by_type{{type="{media_type}"}} {count}')
            if total_size:
                media_type_metrics.append(f'beryl_media_storage_by_type{{type="{media_type}"}} {total_size}')
    
    if media_type_metrics:
        metrics.extend([
            f'# HELP beryl_media_files_by_type Media files by media type',
            f'# TYPE beryl_media_files_by_type gauge',
        ])
        # Add file count metrics
        for metric in media_type_metrics:
            if 'beryl_media_files_by_type' in metric:
                metrics.append(metric)
        metrics.extend([
            f'',
            f'# HELP beryl_media_storage_by_type Storage usage by media type',
            f'# TYPE beryl_media_storage_by_type gauge',
        ])
        # Add storage size metrics
        for metric in media_type_metrics:
            if 'beryl_media_storage_by_type' in metric:
                metrics.append(metric)
        metrics.append('')
    
    # System timestamp
    metrics.extend([
        f'# HELP beryl_metrics_timestamp_seconds Timestamp when metrics were generated',
        f'# TYPE beryl_metrics_timestamp_seconds gauge',
        f'beryl_metrics_timestamp_seconds {int(now.timestamp())}',
        f'',
    ])
    
    # Join all metrics with newlines
    response_content = '\n'.join(metrics)
    
    return HttpResponse(response_content, content_type='text/plain; version=0.0.4; charset=utf-8')


@application_admin_required
@log_execution_time
def sys_backup(request):
    """Backup and restore functionality"""
    logger.info("System backup/restore accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
    # Get backup directory info if configured
    backup_dir = getattr(settings, 'BACKUP_DIR', None)
    backup_files = []
    
    if backup_dir and os.path.exists(backup_dir):
        try:
            files = os.listdir(backup_dir)
            for file in files:
                if file.endswith(('.sql', '.json', '.tar.gz')):
                    file_path = os.path.join(backup_dir, file)
                    stat = os.stat(file_path)
                    backup_files.append({
                        'name': file,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime),
                    })
            backup_files.sort(key=lambda x: x['modified'], reverse=True)
        except Exception as e:
            logger.error("Error reading backup directory: %s", str(e))
    
    context = {
        'backup_dir': backup_dir,
        'backup_files': backup_files,
        'database_url': getattr(settings, 'DATABASE_URL', None),
        'debug': settings.DEBUG,
    }
    
    return render(request, 'sys/backup.html', context)


@application_admin_required
@require_http_methods(["POST"])
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
@require_http_methods(["DELETE"])
def sys_activity_cleanup(request):
    """Clean up old activity logs via HTMX"""
    days = int(request.GET.get('days', 90))
    cutoff_date = timezone.now() - timedelta(days=days)
    
    deleted_count, _ = RecentActivity.objects.filter(created__lt=cutoff_date).delete()
    
    logger.info("Admin user '%s' [%s] cleaned up %d activity logs older than %d days", 
                request.user.username, request.user.id, deleted_count, days)
    
    return JsonResponse({
        'success': True,
        'deleted_count': deleted_count,
        'message': f"Deleted {deleted_count} activity logs older than {days} days"
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
            
        # Validate icon name if provided
        if icon:
            is_valid, error_message = LucideIcons.validate(icon)
            if not is_valid:
                messages.error(request, error_message)
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
            
        # Validate icon name if provided
        if icon:
            is_valid, error_message = LucideIcons.validate(icon)
            if not is_valid:
                messages.error(request, error_message)
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
@require_http_methods(["GET"])
def sys_validate_lucide_icon(request):
    """Endpoint to validate Lucide icon names and provide suggestions"""
    icon_name = request.GET.get('icon', '').strip()
    
    if not icon_name:
        return JsonResponse({
            'valid': True,
            'message': '',
            'suggestions': []
        })
    
    is_valid, error_message = LucideIcons.validate(icon_name)
    
    response_data = {
        'valid': is_valid,
        'message': error_message or '',
        'suggestions': []
    }
    
    # If invalid, provide suggestions
    if not is_valid:
        suggestions = LucideIcons.get_suggestions(icon_name, limit=5)
        response_data['suggestions'] = suggestions
    
    return JsonResponse(response_data)


@application_admin_required
@require_http_methods(["GET"])
def sys_lucide_icon_search(request):
    """HTMX endpoint to search for Lucide icons for autocomplete"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 2:
        return JsonResponse({'icons': []})
    
    # Search for matching icons
    matching_icons = LucideIcons.search_icons(query)
    
    # Limit results for performance
    limited_results = matching_icons[:20]
    
    return JsonResponse({'icons': limited_results})


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
        
        # Validate icon if provided
        if icon and not LucideIcons.is_valid(icon):
            messages.error(request, f'Icon "{icon}" is not a valid Lucide icon.')
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
        
        # Validate icon if provided
        if icon and not LucideIcons.is_valid(icon):
            messages.error(request, f'Icon "{icon}" is not a valid Lucide icon.')
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
    is_inbucket = 'inbucket' in email_host.lower() or getattr(settings, 'USE_INBUCKET', False)
    
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
        'USE_INBUCKET': getattr(settings, 'USE_INBUCKET', False),
        'INBUCKET_SMTP_PORT': getattr(settings, 'INBUCKET_SMTP_PORT', 2500),
    }
    
    # Media/Storage settings
    media_settings = {
        'USE_GCS_STORAGE': getattr(settings, 'USE_GCS_STORAGE', False),
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
        'DEBUG', 'ALLOWED_HOSTS', 'USE_INBUCKET', 'USE_GCS_STORAGE', 
        'GCS_BUCKET_NAME', 'GCS_PROJECT_ID', 'GCS_LOCATION',
        'EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_USE_TLS', 'DEFAULT_FROM_EMAIL',
        'INBUCKET_SMTP_PORT', 'DB_ENGINE', 'PG_HOST', 'PG_PORT', 'PG_DB',
        'APPLICATION_ACTIVITY_LOGGING'
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
    """Delete media file and its storage"""
    media_file = get_object_or_404(MediaFile, hash=media_file_hash)
    
    try:
        file_path = media_file.file_path
        filename = media_file.original_filename
        
        # Delete from storage if it exists
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
            logger.info("Deleted file from storage: %s", file_path)
        
        # Delete MediaFile record
        media_file.delete()
        
        logger.info("Admin user '%s' [%s] deleted media file '%s' at '%s'", 
                   request.user.username, request.user.id, filename, file_path)
        
        messages.success(request, f"File '{filename}' deleted successfully")
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


