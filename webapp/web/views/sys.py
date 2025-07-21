# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
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
from allauth.account.models import EmailAddress
from django.contrib import messages
from django.conf import settings

from web.decorators import log_execution_time
from web.models import Collection, CollectionItem, RecentActivity, ItemType, ItemAttribute
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
    recent_activities = RecentActivity.objects.select_related('created_by', 'subject').order_by('-created')[:10]
    
    # User activity in last 24 hours
    recent_user_activity = User.objects.filter(
        last_login__gte=timezone.now() - timedelta(days=1)
    ).count()
    
    # Collection visibility breakdown
    visibility_stats = Collection.objects.values('visibility').annotate(count=Count('id'))
    
    # Item status breakdown
    status_stats = CollectionItem.objects.values('status').annotate(count=Count('id'))
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_collections': total_collections,
        'total_items': total_items,
        'recent_activities': recent_activities,
        'recent_user_activity': recent_user_activity,
        'visibility_stats': visibility_stats,
        'status_stats': status_stats,
        'EXTERNAL_DB_URL': getattr(settings, 'EXTERNAL_DB_URL', None),
        'EXTERNAL_INBUCKET_URL': getattr(settings, 'EXTERNAL_INBUCKET_URL', None),
        'EXTERNAL_MONITORING_URL': getattr(settings, 'EXTERNAL_MONITORING_URL', None),
        'debug': settings.DEBUG,
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
            Q(created_by=user) | Q(subject=user)
        ).count(),
        'activities_30d': RecentActivity.objects.filter(
            Q(created_by=user) | Q(subject=user),
            created__gte=last_30_days
        ).count(),
        'activities_7d': RecentActivity.objects.filter(
            Q(created_by=user) | Q(subject=user),
            created__gte=last_7_days
        ).count(),
        'last_activity': RecentActivity.objects.filter(
            Q(created_by=user) | Q(subject=user)
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
        Q(created_by=user) | Q(subject=user)
    ).select_related('created_by', 'subject').order_by('-created')[:10]
    
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
    activities = RecentActivity.objects.select_related('created_by', 'subject')
    
    if action_filter:
        activities = activities.filter(name=action_filter)
    
    if user_filter:
        try:
            user_id = int(user_filter)
            activities = activities.filter(Q(created_by_id=user_id) | Q(subject_id=user_id))
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
    
    context = {
        'user_metrics': user_metrics,
        'collection_metrics': collection_metrics,
        'item_metrics': item_metrics,
        'activity_metrics': activity_metrics,
        'item_type_distribution': item_type_distribution,
        'debug': settings.DEBUG,
    }
    
    return render(request, 'sys/metrics.html', context)


@application_admin_required
def sys_prometheus_metrics(request):
    """Prometheus-compatible metrics endpoint for Grafana"""
    logger.info("Prometheus metrics accessed by admin user '%s' [%s]", request.user.username, request.user.id)
    
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
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [email_address],
            html_message=html_message,
            fail_silently=False,
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