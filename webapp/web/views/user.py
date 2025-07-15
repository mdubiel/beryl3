# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.core.paginator import Paginator
from web.models import Collection, CollectionItem, RecentActivity
from web.decorators import log_execution_time

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
    )

    stats_data['total_lists'] = collections_with_counts.count()

    timeline_events = RecentActivity.objects.filter(subject=request.user).select_related('created_by').order_by('-created')[:6]
    total_event_count = RecentActivity.objects.filter(subject=request.user).count()

    context = {
        "stats": stats_data,
        "collection_lists": collections_with_counts, # Pass the queryset directly to the template
        "timeline_events": timeline_events, # Pass the real data
        "total_event_count": total_event_count,
    }

    logger.debug("Rendering dashboard for user '%s'.", request.user.username)
    return render(request, "user/dashboard.html", context)

@login_required
@log_execution_time
def recent_activity_view(request):
    """
    Displays a paginated list of all activities for the logged-in user.
    """
    logger.info("Recent activity view accessed by user: '%s' (ID: %s)", request.user.username, request.user.id)

    activity_list = RecentActivity.objects.filter(subject=request.user).select_related('created_by')
    paginator = Paginator(activity_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    logger.info("Rendering recent activity list for user '%s'.", request.user.username)
    return render(request, 'user/recent_activity_list.html', context)