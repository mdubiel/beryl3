# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from web.decorators import log_execution_time
from web.models import Collection, ApplicationActivity, RecentActivity

logger = logging.getLogger('webapp')

@login_required
@require_POST
@log_execution_time
def update_collection_visibility(request, hash):
    """
    Handles HTMX requests to update the visibility of a Collection.
    """
    logger.info("HTMX request to update collection visibility for collection with hash '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    collection = get_object_or_404(Collection, hash=hash, created_by=request.user)

    if collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to update collection '%s' [%s] they do not own", request.user.username, request.user.id, collection.name, collection.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('update_collection_visibility', 
            f"Unauthorized attempt to update collection '{collection.name}' visibility", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'Collection',
                'object_hash': collection.hash, 'object_name': collection.name,
                'result': 'access_denied', 'function_args': {'hash': hash}
            })
        
        raise Http404("You do not have permission to edit this collection.")

    new_visibility = request.POST.get('new_visibility')

    if new_visibility in Collection.Visibility.values:
        collection.visibility = new_visibility
        collection.save(update_fields=['visibility'])
        logger.info("User '%s' updated collection '%s' to visibility '%s'", request.user.username, collection.name, new_visibility)
        
        # Log successful visibility update
        ApplicationActivity.log_info('update_collection_visibility', 
            f"Collection '{collection.name}' visibility updated to '{new_visibility}'", 
            user=request.user, meta={
                'action': 'visibility_updated', 'object_type': 'Collection',
                'object_hash': collection.hash, 'object_name': collection.name,
                'old_visibility': request.POST.get('old_visibility', 'unknown'),
                'new_visibility': new_visibility, 'result': 'success',
                'function_args': {'hash': hash, 'new_visibility': new_visibility}
            })
        
        # Log user activity
        RecentActivity.log_collection_visibility_changed(
            user=request.user,
            collection_name=collection.name,
            visibility=new_visibility
        )
    else:
        # Log invalid visibility value
        ApplicationActivity.log_warning('update_collection_visibility', 
            f"Invalid visibility '{new_visibility}' attempted for collection '{collection.name}'", 
            user=request.user, meta={
                'action': 'visibility_update_failed', 'object_type': 'Collection',
                'object_hash': collection.hash, 'object_name': collection.name,
                'invalid_visibility': new_visibility, 'result': 'validation_error',
                'function_args': {'hash': hash, 'new_visibility': new_visibility}
            })

    context = {
        'collection': collection,
        'visibility_choices': Collection.Visibility.choices,
    }

    # The HX-Target header tells us which element triggered the request.
    target_id = request.headers.get('HX-Target')

    if target_id and target_id.startswith('collection-row-'):
        # Request came from the collection list, return the full list item.
        # The template `_collection_list_item.html` expects `item_count`.
        collection_with_count = get_object_or_404(
            Collection.objects.annotate(item_count=Count('items')),
            hash=hash, created_by=request.user
        )
        context['collection'] = collection_with_count
        logger.info("Returning updated collection list item for collection: '%s' [%s]", collection.name, collection.hash)
        
        # Log successful list item response rendering
        ApplicationActivity.log_info('update_collection_visibility', 
            f"Collection '{collection.name}' visibility update completed - list item rendered", 
            user=request.user, meta={
                'action': 'response_rendered', 'object_type': 'Collection',
                'object_hash': collection.hash, 'object_name': collection.name,
                'response_type': 'list_item', 'result': 'success',
                'function_args': {'hash': hash, 'new_visibility': new_visibility}
            })
        
        return render(request, 'partials/_collection_list_item.html', context)

    # Default: request came from the collection detail page, return the dropdown.
    logger.info("Returning updated share dropdown for collection: '%s' [%s]", collection.name, collection.hash)
    
    # Log successful response rendering
    ApplicationActivity.log_info('update_collection_visibility', 
        f"Collection '{collection.name}' visibility update completed - dropdown rendered", 
        user=request.user, meta={
            'action': 'response_rendered', 'object_type': 'Collection',
            'object_hash': collection.hash, 'object_name': collection.name,
            'response_type': 'share_dropdown', 'result': 'success',
            'function_args': {'hash': hash, 'new_visibility': new_visibility}
        })
    
    return render(request, 'partials/_collection_share_hx_dropdown.html', context)
