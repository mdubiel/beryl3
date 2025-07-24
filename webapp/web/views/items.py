# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.http import require_POST
from django.db import transaction

from web.decorators import log_execution_time
from web.forms import CollectionItemForm
from web.models import Collection, CollectionItem, RecentActivity, ItemType

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

    # Get all item types for the dropdown
    item_types = ItemType.objects.filter(is_deleted=False).order_by('display_name')

    context = {
        'item': item,
        'collection': item.collection, # Pass collection for convenience
        'item_types': item_types,
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


@login_required
@require_POST
@log_execution_time
def move_item_to_collection(request, item_hash):
    """
    Move an item from one collection to another.
    """
    item = get_object_or_404(CollectionItem, hash=item_hash, collection__created_by=request.user)
    target_collection_id = request.POST.get('target_collection_id')
    
    if not target_collection_id:
        return JsonResponse({'success': False, 'error': 'Target collection is required'}, status=400)
    
    target_collection = get_object_or_404(Collection, id=target_collection_id, created_by=request.user)
    
    if item.collection.id == target_collection.id:
        return JsonResponse({'success': False, 'error': 'Item is already in this collection'}, status=400)
    
    try:
        with transaction.atomic():
            original_collection = item.collection
            item.collection = target_collection
            item.save()
            
            # Log the activity
            RecentActivity.objects.create(
                name='ITEM_ADDED',
                subject=request.user,
                created_by=request.user,
                target_repr=f"{item.name} moved to {target_collection.name}",
                details={
                    'item_name': item.name,
                    'item_hash': item.hash,
                    'from_collection': original_collection.name,
                    'from_collection_hash': original_collection.hash,
                    'to_collection': target_collection.name,
                    'to_collection_hash': target_collection.hash,
                }
            )
            
            logger.info(
                "User '%s [%s]' moved item '%s' [%s] from collection '%s' [%s] to '%s' [%s]",
                request.user.username, request.user.id,
                item.name, item.hash,
                original_collection.name, original_collection.hash,
                target_collection.name, target_collection.hash
            )
            
            return JsonResponse({
                'success': True,
                'message': f"'{item.name}' moved to '{target_collection.name}'",
                'new_collection_url': target_collection.get_absolute_url(),
                'new_collection_name': target_collection.name
            })
            
    except Exception as e:
        logger.error("Error moving item '%s' [%s]: %s", item.name, item.hash, str(e))
        return JsonResponse({'success': False, 'error': 'Failed to move item'}, status=500)


@login_required
@require_POST
@log_execution_time
def copy_item_to_collection(request, item_hash):
    """
    Copy an item to another collection with basic info, status, and favorite status.
    Does not copy guest reservations.
    """
    original_item = get_object_or_404(CollectionItem, hash=item_hash, collection__created_by=request.user)
    target_collection_id = request.POST.get('target_collection_id')
    
    if not target_collection_id:
        return JsonResponse({'success': False, 'error': 'Target collection is required'}, status=400)
    
    target_collection = get_object_or_404(Collection, id=target_collection_id, created_by=request.user)
    
    if original_item.collection.id == target_collection.id:
        return JsonResponse({'success': False, 'error': 'Item is already in this collection'}, status=400)
    
    try:
        with transaction.atomic():
            # Create a copy of the item
            copied_item = CollectionItem.objects.create(
                collection=target_collection,
                created_by=request.user,
                name=original_item.name,
                description=original_item.description,
                status=original_item.status,  # Copy status
                is_favorite=original_item.is_favorite,  # Copy favorite status
                item_type=original_item.item_type,
                attributes=original_item.attributes.copy() if original_item.attributes else {},
                # Note: guest_reservation_token is NOT copied (will be None)
            )
            
            # Log the activity
            RecentActivity.objects.create(
                name='ITEM_ADDED',
                subject=request.user,
                created_by=request.user,
                target_repr=f"{copied_item.name} copied to {target_collection.name}",
                details={
                    'item_name': copied_item.name,
                    'item_hash': copied_item.hash,
                    'original_item_hash': original_item.hash,
                    'from_collection': original_item.collection.name,
                    'from_collection_hash': original_item.collection.hash,
                    'to_collection': target_collection.name,
                    'to_collection_hash': target_collection.hash,
                }
            )
            
            logger.info(
                "User '%s [%s]' copied item '%s' [%s] from collection '%s' [%s] to '%s' [%s] as '%s' [%s]",
                request.user.username, request.user.id,
                original_item.name, original_item.hash,
                original_item.collection.name, original_item.collection.hash,
                target_collection.name, target_collection.hash,
                copied_item.name, copied_item.hash
            )
            
            return JsonResponse({
                'success': True,
                'message': f"'{original_item.name}' copied to '{target_collection.name}'",
                'new_collection_url': target_collection.get_absolute_url(),
                'new_collection_name': target_collection.name,
                'copied_item_hash': copied_item.hash
            })
            
    except Exception as e:
        logger.error("Error copying item '%s' [%s]: %s", original_item.name, original_item.hash, str(e))
        return JsonResponse({'success': False, 'error': 'Failed to copy item'}, status=500)


@login_required
@log_execution_time
def get_user_collections_for_move_copy(request, item_hash):
    """
    Get user's collections for move/copy dropdown, excluding the current collection.
    """
    item = get_object_or_404(CollectionItem, hash=item_hash, collection__created_by=request.user)
    
    # Get all user's collections except the current one
    collections = Collection.objects.filter(
        created_by=request.user,
        is_deleted=False
    ).exclude(id=item.collection.id).order_by('name')
    
    collections_data = [
        {
            'id': collection.id,
            'name': collection.name,
            'hash': collection.hash,
            'item_count': collection.items.filter(is_deleted=False).count()
        }
        for collection in collections
    ]
    
    return JsonResponse({
        'collections': collections_data,
        'current_collection': {
            'id': item.collection.id,
            'name': item.collection.name,
            'hash': item.collection.hash
        }
    })
