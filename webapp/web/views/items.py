# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from web.models import Collection, CollectionItem
from web.decorators import log_execution_time
from web.forms import CollectionItemForm

logger = logging.getLogger('webapp')

@login_required
@log_execution_time
def collection_item_create_view(request, collection_hash):
    """
    Handles creating a new CollectionItem within a specific Collection.
    """
    logger.info("Collection item creation view accessed by user: '%s' [%s]", request.user.username, request.user.id)
    collection = get_object_or_404(Collection, hash=collection_hash, created_by=request.user)

    if request.method == 'POST':
        logger.info("User '%s [%s]' is submitting a new item for collection '%s' [%s]", request.user.username, request.user.id, collection.name, collection.hash) 
        form = CollectionItemForm(request.POST)
        if form.is_valid():
            # Get the new item object but don't save it to the DB yet
            new_item = form.save(commit=False)
            
            # Set the fields that were not on the form
            new_item.collection = collection
            new_item.created_by = request.user
            
            new_item.save()
            logger.info(
                "User '%s [%s]' created new item '%s' in collection '%s' [%s]",
                request.user.username, request.user.id, new_item.name, collection.name, collection.hash
            )
            messages.success(request, f"Item '{new_item.name}' was added to your collection.")
            
            # Redirect back to the collection's detail page
            return redirect(collection.get_absolute_url())
    else:
        form = CollectionItemForm()

    context = {
        'form': form,
        'collection': collection,
    }
    return render(request, 'items/item_form.html', context)

@login_required
@log_execution_time
def collection_item_detail_view(request, hash):
    """
    Displays the detail page for a single CollectionItem, checking for ownership.
    """
    logger.info("Collection item detail view accessed by user: '%s' [%s]", request.user.username, request.user.id)
    item = get_object_or_404(
        CollectionItem.objects.select_related('collection', 'created_by'),
        hash=hash,
        collection__created_by=request.user
    )

    context = {
        'item': item,
        'collection': item.collection, # Pass collection for convenience
    }
    logger.info("Rendering detail view for item '%s' in collection '%s'", item.name, item.collection.name)
    return render(request, 'items/item_detail.html', context)

@login_required
@log_execution_time
def collection_item_update_view(request, hash):
    """
    Handles editing an existing CollectionItem.
    """
    logger.info("Collection item update view accessed by user: '%s' [%s]", request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash, collection__created_by=request.user)

    if request.method == 'POST':
        logger.info("User '%s [%s]' is submitting an update for item '%s' in collection '%s' [%s]", request.user.username, request.user.id, item.name, item.collection.name, item.collection.hash)
        form = CollectionItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            logger.info("User '%s [%s]' updated item '%s' in collection '%s' [%s]", request.user.username, request.user.id, item.name, item.collection.name, item.collection.hash)
            messages.success(request, f"Item '{item.name}' was updated successfully!")
            return redirect(item.collection.get_absolute_url())
    else:
        logger.info("User '%s [%s]' is viewing the update form for item '%s' in collection '%s' [%s]", request.user.username, request.user.id, item.name, item.collection.name, item.collection.hash)
        form = CollectionItemForm(instance=item)

    context = {
        'form': form,
        'item': item,
        'collection': item.collection, # Pass the collection for the breadcrumbs
    }
    return render(request, 'items/item_form.html', context)

@login_required
@require_POST
@log_execution_time
def collection_item_delete_view(request, hash):
    """
    Handles the soft-deletion of a CollectionItem object.
    """
    logger.info("Collection item delete view accessed by user: '%s' [%s]", request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash, collection__created_by=request.user)
    
    collection = item.collection
    if not item.can_be_deleted:
        logger.warning("User '%s [%s]' attempted to delete item '%s' [%s] that is not deletable.", request.user.username, request.user.id, item.name, item.hash)
        messages.error(request, "Cannot delete an item that is not deletable.")
        return redirect(collection.get_absolute_url())
    
    item_name = item.name
    item.delete()
    
    logger.info("User '%s [%s]' deleted item '%s' from collection '%s' [%s]", request.user.username, request.user.id, item_name, collection.name, collection.hash)
    messages.success(request, f"Item '{item_name}' was successfully deleted.")
    return redirect(collection.get_absolute_url())
