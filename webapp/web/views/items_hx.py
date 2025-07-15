# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.http import Http404

from web.models import CollectionItem
from web.decorators import log_execution_time

logger = logging.getLogger('webapp')

@login_required
@require_POST
@log_execution_time
def update_item_status(request, hash):
    """
    Handles HTMX requests to update the status of a CollectionItem.
    """
    logger.info("HTMX request to update item status for item with hash '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to update item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        raise Http404("You do not have permission to edit this item.")

    new_status = request.POST.get('new_status')

    # Update the status if the new value is valid
    if new_status in CollectionItem.Status.values:
        item.status = new_status
        item.save(update_fields=['status'])
        logger.info("User '%s' updated item '%s' to status '%s'", request.user.username, item.name, new_status)

    # Return the updated list item HTML fragment to HTMX
    logger.info("Returning updated item list item for item: '%s' [%s]", item.name, item.hash)
    return render(request, 'partials/_item_list_item.html', {'item': item})

