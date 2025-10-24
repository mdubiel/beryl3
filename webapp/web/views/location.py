# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

"""
Task 50: Location management views.
Provides CRUD operations for user-defined locations.
"""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods

from web.decorators import log_execution_time
from web.models import Location, CollectionItem

logger = logging.getLogger('webapp')


@login_required
@log_execution_time
def location_list_view(request):
    """
    List all user's locations with item counts.
    """
    logger.info("Location list view accessed by user: '%s' [%s]", request.user.username, request.user.id)

    locations = Location.objects.filter(
        created_by=request.user
    ).annotate(
        item_count=Count('items')
    ).order_by('name')

    logger.info('location_list_view: User %s [%s] viewing %d locations',
               request.user.username, request.user.id, locations.count(),
               extra={'function': 'location_list_view', 'action': 'list_view',
                     'count': locations.count()})

    return render(request, 'location/location_list.html', {
        'locations': locations
    })


@login_required
@log_execution_time
def location_items_view(request, hash):
    """
    View all items in a specific location.
    """
    logger.info("Location items view accessed by user: '%s' [%s] for hash: %s",
               request.user.username, request.user.id, hash)

    location = get_object_or_404(
        Location,
        hash=hash,
        created_by=request.user
    )

    items = CollectionItem.objects.filter(
        location=location,
        collection__created_by=request.user
    ).select_related('collection', 'item_type', 'location').order_by('name')

    logger.info('location_items_view: User %s [%s] viewing location "%s" with %d items',
               request.user.username, request.user.id, location.name, items.count(),
               extra={'function': 'location_items_view', 'action': 'items_view',
                     'location_hash': location.hash, 'item_count': items.count()})

    return render(request, 'location/location_items.html', {
        'location': location,
        'items': items
    })


@login_required
@log_execution_time
@require_http_methods(["GET", "POST"])
def location_create_view(request):
    """
    Create a new location.
    """
    logger.info("Location create view accessed by user: '%s' [%s]", request.user.username, request.user.id)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Location name is required.')
            return render(request, 'location/location_form.html', {
                'name': name,
                'description': description
            })

        # Check for duplicate name
        if Location.objects.filter(created_by=request.user, name=name).exists():
            messages.error(request, f'You already have a location named "{name}".')
            return render(request, 'location/location_form.html', {
                'name': name,
                'description': description
            })

        location = Location.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )

        logger.info('location_create_view: User %s [%s] created location "%s" [%s]',
                   request.user.username, request.user.id, location.name, location.hash,
                   extra={'function': 'location_create_view', 'action': 'created',
                         'location_hash': location.hash, 'location_name': location.name})

        messages.success(request, f'Location "{location.name}" created successfully.')
        return redirect('location_list')

    return render(request, 'location/location_form.html')


@login_required
@log_execution_time
@require_http_methods(["GET", "POST"])
def location_update_view(request, hash):
    """
    Update an existing location.
    """
    logger.info("Location update view accessed by user: '%s' [%s] for hash: %s",
               request.user.username, request.user.id, hash)

    location = get_object_or_404(
        Location,
        hash=hash,
        created_by=request.user
    )

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if not name:
            messages.error(request, 'Location name is required.')
            return render(request, 'location/location_form.html', {
                'location': location,
                'name': name,
                'description': description
            })

        # Check for duplicate name (excluding current location)
        if Location.objects.filter(created_by=request.user, name=name).exclude(hash=hash).exists():
            messages.error(request, f'You already have a location named "{name}".')
            return render(request, 'location/location_form.html', {
                'location': location,
                'name': name,
                'description': description
            })

        location.name = name
        location.description = description
        location.save()

        logger.info('location_update_view: User %s [%s] updated location "%s" [%s]',
                   request.user.username, request.user.id, location.name, location.hash,
                   extra={'function': 'location_update_view', 'action': 'updated',
                         'location_hash': location.hash, 'location_name': location.name})

        messages.success(request, f'Location "{location.name}" updated successfully.')
        return redirect('location_list')

    return render(request, 'location/location_form.html', {
        'location': location
    })


@login_required
@log_execution_time
@require_POST
def location_delete_view(request, hash):
    """
    Delete a location. Items are not deleted, just unassigned.
    Since Location uses soft delete, we need to manually unassign items.
    """
    logger.info("Location delete view accessed by user: '%s' [%s] for hash: %s",
               request.user.username, request.user.id, hash)

    location = get_object_or_404(
        Location,
        hash=hash,
        created_by=request.user
    )

    location_name = location.name
    item_count = location.get_item_count()

    # Unassign all items from this location before soft delete
    # (on_delete=SET_NULL only works for hard deletes, not soft deletes)
    CollectionItem.objects.filter(location=location).update(location=None)

    # Now soft delete the location
    location.delete()

    logger.info('location_delete_view: User %s [%s] deleted location "%s" [%s] (%d items unassigned)',
               request.user.username, request.user.id, location_name, hash, item_count,
               extra={'function': 'location_delete_view', 'action': 'deleted',
                     'location_hash': hash, 'location_name': location_name, 'item_count': item_count})

    messages.success(request, f'Location "{location_name}" deleted. {item_count} item(s) unassigned from this location.')
    return redirect('location_list')


@login_required
@log_execution_time
def location_autocomplete_view(request):
    """
    HTMX autocomplete endpoint for location search.
    Returns filtered locations as user types.
    """
    query = request.GET.get('q', '').strip()

    logger.info("Location autocomplete requested by user: '%s' [%s] with query: '%s'",
               request.user.username, request.user.id, query)

    # Only return results if query is not empty
    if query:
        locations = Location.objects.filter(
            created_by=request.user,
            name__icontains=query
        ).order_by('name')

        # Get count before slicing
        location_count = locations.count()

        # Limit to 10 results for performance
        locations = locations[:10]
    else:
        # Empty query - return no results
        locations = Location.objects.none()
        location_count = 0

    logger.info('location_autocomplete_view: Returning %d locations for query "%s" by user %s [%s]',
               location_count, query, request.user.username, request.user.id,
               extra={'function': 'location_autocomplete_view', 'action': 'autocomplete',
                     'query': query, 'result_count': location_count})

    return render(request, 'partials/_location_autocomplete_results.html', {
        'locations': locations,
        'query': query
    })


@login_required
@log_execution_time
@require_POST
def location_quick_create_view(request):
    """
    HTMX endpoint to quickly create a location from autocomplete.
    Returns JSON with the new location's ID and name.
    """
    name = request.POST.get('name', '').strip()

    logger.info("Quick location create requested by user: '%s' [%s] with name: '%s'",
               request.user.username, request.user.id, name)

    if not name:
        return JsonResponse({'error': 'Location name is required'}, status=400)

    if len(name) < 1:
        return JsonResponse({'error': 'Location name must be at least 1 character'}, status=400)

    # Check for duplicate name
    if Location.objects.filter(created_by=request.user, name=name).exists():
        existing_location = Location.objects.get(created_by=request.user, name=name)
        logger.info('location_quick_create_view: Location "%s" already exists for user %s [%s], returning existing',
                   name, request.user.username, request.user.id)
        return JsonResponse({
            'id': existing_location.id,
            'name': existing_location.name,
            'exists': True
        })

    # Create new location
    location = Location.objects.create(
        name=name,
        description='',
        created_by=request.user
    )

    logger.info('location_quick_create_view: User %s [%s] created location "%s" [%s] via quick create',
               request.user.username, request.user.id, location.name, location.hash,
               extra={'function': 'location_quick_create_view', 'action': 'created',
                     'location_hash': location.hash, 'location_name': location.name})

    return JsonResponse({
        'id': location.id,
        'name': location.name,
        'exists': False
    })
