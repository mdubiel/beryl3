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
from web.models import Collection

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
        raise Http404("You do not have permission to edit this collection.")

    new_visibility = request.POST.get('new_visibility')

    if new_visibility in Collection.Visibility.values:
        collection.visibility = new_visibility
        collection.save(update_fields=['visibility'])
        logger.info("User '%s' updated collection '%s' to visibility '%s'", request.user.username, collection.name, new_visibility)

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
        return render(request, 'partials/_collection_list_item.html', context)

    # Default: request came from the collection detail page, return the dropdown.
    logger.info("Returning updated share dropdown for collection: '%s' [%s]", collection.name, collection.hash)
    return render(request, 'partials/_collection_share_hx_dropdown.html', context)
