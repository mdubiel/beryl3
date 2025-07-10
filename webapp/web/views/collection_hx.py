# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long
import logging

from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from web.models import Collection
from web.decorators import log_execution_time

logger = logging.getLogger('webapp')

@login_required
@require_POST
@log_execution_time
def update_collection_visibility(request, hash):
    """
    Handles HTMX requests to update the visibility of a Collection.
    """
    logger.info("HTMX request to update collection '[%s]' visibility by user: '%s [%s]'", hash, request.user.username, request.user.id)

    collection = get_object_or_404(Collection, hash=hash, created_by=request.user)

    new_visibility = request.POST.get('new_visibility')

    if new_visibility in Collection.Visibility.values:
        collection.visibility = new_visibility
        collection.save(update_fields=['visibility'])
        logger.info(
            "User '%s [%s]' updated collection '%s [%s]' visibility to '%s'",
            request.user.username, request.user.id, collection.name, hash, new_visibility
        )

    # Re-render just the single collection list item and return it to HTMX
    # We must also re-annotate the item_count for the partial template
    collection = Collection.objects.annotate(item_count=Count('items')).get(pk=collection.pk)
    logger.info("Returning updated collection list item for collection: '%s [%s]'", collection.name, collection.hash)
    return render(request, 'partials/_collection_list_item.html', {'collection': collection})
