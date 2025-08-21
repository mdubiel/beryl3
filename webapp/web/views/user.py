# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import render

from web.decorators import log_execution_time
from web.models import Collection, CollectionItem, RecentActivity, ApplicationActivity

logger = logging.getLogger('webapp')

@login_required
@log_execution_time
def dashboard_view(request):
    """Displays the user's dashboard with statistics, recent activities, and collections.
    This view aggregates data about the user's collections and items, and renders the dashboard template.
    """
    logger.info("Dashboard view accessed by user: '%s' (ID: %s)", request.user.username, request.user.id)

    collections_with_counts = Collection.objects.filter(created_by=request.user).annotate(
        item_count=Count('items')
    ).order_by('-updated')[:5]

    user_items = CollectionItem.objects.filter(collection__created_by=request.user)

    stats_data = user_items.aggregate(
        total_items=Count('id'),
        in_collection_count=Count('id', filter=Q(status=CollectionItem.Status.IN_COLLECTION)),
        wanted_count=Count('id', filter=Q(status=CollectionItem.Status.WANTED)),
        reserved_count=Count('id', filter=Q(status=CollectionItem.Status.RESERVED)),
        favourite_count=Count('id', filter=Q(is_favorite=True)),
    )

    stats_data['total_lists'] = collections_with_counts.count()

    timeline_events = RecentActivity.objects.filter(subject=request.user).select_related('created_by').order_by('-created')[:6]
    total_event_count = RecentActivity.objects.filter(subject=request.user).count()
    
    # Get favorite items for the favorites card
    favorite_items = user_items.filter(is_favorite=True).select_related('collection').order_by('-updated')[:6]

    # Log successful dashboard access
    ApplicationActivity.log_info('dashboard_view', 
        f"Dashboard accessed - {stats_data['total_items']} items across {stats_data['total_lists']} collections", 
        user=request.user, meta={
            'action': 'dashboard_view', 'total_items': stats_data['total_items'],
            'total_collections': stats_data['total_lists'], 'favorite_items': stats_data['favourite_count'],
            'in_collection': stats_data['in_collection_count'], 'wanted': stats_data['wanted_count'],
            'function_args': {}})

    context = {
        "stats": stats_data,
        "collection_lists": collections_with_counts, # Pass the queryset directly to the template
        "timeline_events": timeline_events, # Pass the real data
        "total_event_count": total_event_count,
        "favorite_items": favorite_items,
    }

    logger.debug("Rendering dashboard for user '%s'.", request.user.username)
    return render(request, "user/dashboard.html", context)

@login_required
@log_execution_time
def favorites_view(request):
    """
    Displays all favorite items for the logged-in user.
    """
    logger.info("Favorites view accessed by user: '%s' (ID: %s)", request.user.username, request.user.id)

    favorite_items = CollectionItem.objects.filter(
        collection__created_by=request.user,
        is_favorite=True
    ).select_related('collection').order_by('-updated')

    # Get item types for the dropdown functionality
    from web.models import ItemType
    item_types = ItemType.objects.all()
    
    total_favorites = favorite_items.count()
    
    # Log favorites view access
    ApplicationActivity.log_info('favorites_view', 
        f"Favorites list accessed - {total_favorites} favorite items", 
        user=request.user, meta={
            'action': 'favorites_view', 'favorite_count': total_favorites,
            'function_args': {}})

    context = {
        "favorite_items": favorite_items,
        "total_favorites": total_favorites,
        "item_types": item_types,
    }

    logger.debug("Rendering favorites for user '%s'.", request.user.username)
    return render(request, "user/favorites.html", context)

@login_required
@log_execution_time
def recent_activity_view(request):
    """
    Displays a paginated list of all activities for the logged-in user.
    """
    logger.info("Recent activity view accessed by user: '%s' (ID: %s)", request.user.username, request.user.id)

    activity_list = RecentActivity.objects.filter(subject=request.user).select_related('created_by')
    paginator = Paginator(activity_list, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Log activity view access
    ApplicationActivity.log_info('recent_activity_view', 
        f"Recent activity list accessed - page {page_number}", 
        user=request.user, meta={
            'action': 'activity_view', 'page': page_number, 'total_activities': activity_list.count(),
            'function_args': {'page': page_number}})

    context = {
        'page_obj': page_obj,
    }
    logger.info("Rendering recent activity list for user '%s'.", request.user.username)
    return render(request, 'user/recent_activity_list.html', context)