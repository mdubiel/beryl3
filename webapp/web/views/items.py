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

    # Log form access
    logger.info('collection_item_create_view: Item creation form accessed for collection "%s" by user %s [%s]',
               collection.name, request.user.username, request.user.id,
               extra={'function': 'collection_item_create_view', 'action': 'form_access', 
                     'object_type': 'CollectionItem', 'collection_hash': collection.hash, 
                     'collection_name': collection.name, 'method': request.method,
                     'function_args': {'collection_hash': collection_hash, 'request_method': request.method}})

    if request.method == 'POST':
        logger.info("User '%s [%s]' is submitting a new item for collection '%s' [%s]", request.user.username, request.user.id, collection.name, collection.hash)
        form = CollectionItemForm(request.POST, user=request.user)
        
        if form.is_valid():
            try:
                # Get the new item object but don't save it to the DB yet
                new_item = form.save(commit=False)

                # Set the fields that were not on the form
                new_item.collection = collection
                new_item.created_by = request.user

                # Task 50: Handle location - either ID or name
                from web.models import Location
                location_value = request.POST.get('location', '').strip()
                location_name = request.POST.get('location_name', '').strip()

                if location_value:
                    # User selected from autocomplete - use existing location
                    try:
                        new_item.location = Location.objects.get(id=location_value, created_by=request.user)
                    except (Location.DoesNotExist, ValueError):
                        logger.warning("Invalid location ID %s during item creation", location_value)
                elif location_name:
                    # User typed a name - check if exists or create new
                    existing_location = Location.objects.filter(created_by=request.user, name=location_name).first()
                    if existing_location:
                        new_item.location = existing_location
                        logger.info("Using existing location '%s' for new item", location_name)
                    else:
                        # Create new location
                        new_location = Location.objects.create(
                            name=location_name,
                            description='',
                            created_by=request.user
                        )
                        new_item.location = new_location
                        logger.info("Created new location '%s' [%s] during item creation",
                                   new_location.name, new_location.hash)

                new_item.save()
                logger.info(
                    "User '%s [%s]' created new item '%s' in collection '%s' [%s]",
                    request.user.username, request.user.id, new_item.name, collection.name, collection.hash
                )

                # Handle attributes if item type was selected
                if new_item.item_type:
                    from web.models import CollectionItemAttributeValue
                    attributes_created = []
                    for key, value in request.POST.items():
                        if key.startswith('attr_') and value:
                            attr_name = key[5:]  # Remove 'attr_' prefix
                            try:
                                attribute = new_item.item_type.attributes.get(name=attr_name)
                                validated_value = attribute.validate_value(value)

                                # Create attribute value
                                attr_value_obj = CollectionItemAttributeValue(
                                    item=new_item,
                                    item_attribute=attribute,
                                    created_by=request.user
                                )
                                attr_value_obj.set_typed_value(validated_value)
                                attr_value_obj.save()
                                attributes_created.append(f"{attribute.display_name}: {validated_value}")
                            except Exception as e:
                                logger.warning("Failed to save attribute '%s' for new item '%s': %s",
                                             attr_name, new_item.name, str(e))

                    if attributes_created:
                        logger.info("Created %d attributes for new item '%s': %s",
                                   len(attributes_created), new_item.name, ', '.join(attributes_created))

                # Handle link if provided
                link_url = form.cleaned_data.get('link_url')
                if link_url:
                    from web.models import CollectionItemLink
                    link = CollectionItemLink.objects.create(
                        item=new_item,
                        url=link_url,
                        created_by=request.user
                    )
                    logger.info("Created link '%s' for new item '%s'", link_url, new_item.name)

                # Log successful creation
                logger.info('collection_item_create_view: Item "%s" created in collection "%s" by user %s [%s]',
                           new_item.name, collection.name, request.user.username, request.user.id,
                           extra={'function': 'collection_item_create_view', 'action': 'created',
                                 'object_type': 'CollectionItem', 'object_hash': new_item.hash,
                                 'object_name': new_item.name, 'collection_hash': collection.hash,
                                 'collection_name': collection.name, 'status': new_item.status,
                                 'result': 'success', 'function_args': {'collection_hash': collection_hash, 'request_method': request.method}})

                # Log user activity
                RecentActivity.log_item_added(
                    user=request.user,
                    item_name=new_item.name,
                    collection_name=collection.name
                )

                messages.success(request, f"Item '{new_item.name}' was added to your collection.")
                return redirect(new_item.get_absolute_url())
                
            except Exception as e:
                logger.error('collection_item_create_view: Item creation failed in collection "%s": %s by user %s [%s]',
                            collection.name, str(e), request.user.username, request.user.id,
                            extra={'function': 'collection_item_create_view', 'action': 'creation_error', 
                                  'object_type': 'CollectionItem', 'collection_hash': collection.hash, 
                                  'collection_name': collection.name, 'error': str(e), 'result': 'system_error'})
                raise
        else:
            # Log form validation errors
            logger.warning('collection_item_create_view: Item creation failed in collection "%s" due to validation errors by user %s [%s]',
                          collection.name, request.user.username, request.user.id,
                          extra={'function': 'collection_item_create_view', 'action': 'creation_failed', 
                                'object_type': 'CollectionItem', 'collection_hash': collection.hash, 
                                'collection_name': collection.name, 'errors': form.errors.as_json(),
                                'result': 'validation_error'})
    else:
        form = CollectionItemForm(user=request.user)

    # Task 50: Calculate suggested ID for new items
    temp_item = CollectionItem(collection=collection, created_by=request.user)
    suggested_id = temp_item.predict_next_id()

    # Get last used ID for display
    last_item_with_id = CollectionItem.objects.filter(
        collection=collection,
        your_id__isnull=False
    ).exclude(your_id='').order_by('-created').first()
    last_used_id = last_item_with_id.your_id if last_item_with_id else None

    context = {
        'form': form,
        'collection': collection,
        'suggested_id': suggested_id,
        'last_used_id': last_used_id,
    }
    return render(request, 'items/item_form.html', context)

@login_required
@log_execution_time
def collection_item_detail_view(request, hash):
    """
    Displays the detail page for a single CollectionItem, checking for ownership.
    """
    logger.info("Collection item detail view accessed by user: '%s' [%s]", request.user.username, request.user.id)
    
    try:
        item = get_object_or_404(
            CollectionItem.objects.select_related('collection', 'created_by').prefetch_related('images__media_file'),
            hash=hash,
            collection__created_by=request.user
        )

        # Get all item types for the dropdown
        item_types = ItemType.objects.filter(is_deleted=False).order_by('display_name')

        # Log successful detail view
        logger.info('collection_item_detail_view: Item "%s" detail viewed successfully by user %s [%s]',
                   item.name, request.user.username, request.user.id,
                   extra={'function': 'collection_item_detail_view', 'action': 'detail_view', 
                         'object_type': 'CollectionItem', 'object_hash': item.hash, 
                         'object_name': item.name, 'collection_hash': item.collection.hash, 
                         'collection_name': item.collection.name, 'status': item.status})

        context = {
            'item': item,
            'collection': item.collection, # Pass collection for convenience
            'item_types': item_types,
            'suggested_id': item.predict_next_id(),  # Task 50: Smart ID suggestion
        }
        logger.info("Rendering detail view for item '%s' in collection '%s'", item.name, item.collection.name)
        return render(request, 'items/item_detail.html', context)
        
    except Exception as e:
        logger.warning('collection_item_detail_view: Item detail access failed for hash "%s": %s by user %s [%s]',
                      hash, str(e), request.user.username, request.user.id,
                      extra={'function': 'collection_item_detail_view', 'action': 'detail_view_failed', 
                            'object_hash': hash, 'error': str(e), 'result': 'access_denied_or_error'})
        raise

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
        form = CollectionItemForm(request.POST, instance=item, user=request.user)
        if form.is_valid():
            # Task 50: Handle location - either ID or name
            from web.models import Location
            location_value = request.POST.get('location', '').strip()
            location_name = request.POST.get('location_name', '').strip()

            if location_value:
                # User selected from autocomplete - use existing location
                try:
                    item.location = Location.objects.get(id=location_value, created_by=request.user)
                except (Location.DoesNotExist, ValueError):
                    logger.warning("Invalid location ID %s during item update", location_value)
            elif location_name:
                # User typed a name - check if exists or create new
                existing_location = Location.objects.filter(created_by=request.user, name=location_name).first()
                if existing_location:
                    item.location = existing_location
                    logger.info("Using existing location '%s' for item update", location_name)
                else:
                    # Create new location
                    new_location = Location.objects.create(
                        name=location_name,
                        description='',
                        created_by=request.user
                    )
                    item.location = new_location
                    logger.info("Created new location '%s' [%s] during item update",
                               new_location.name, new_location.hash)
            else:
                # Clear location if both empty
                item.location = None

            form.save()
            logger.info("User '%s [%s]' updated item '%s' in collection '%s' [%s]", request.user.username, request.user.id, item.name, item.collection.name, item.collection.hash)
            
            # Log successful update
            logger.info('collection_item_update_view: Item "%s" updated successfully by user %s [%s]',
                       item.name, request.user.username, request.user.id,
                       extra={'function': 'collection_item_update_view', 'action': 'updated', 
                             'object_type': 'CollectionItem', 'object_hash': item.hash, 
                             'object_name': item.name, 'collection_hash': item.collection.hash, 
                             'result': 'success'})


            messages.success(request, f"Item '{item.name}' was updated successfully!")
            return redirect(item.get_absolute_url())
        else:
            # Log form validation errors
            logger.warning('collection_item_update_view: Item "%s" update failed due to validation errors by user %s [%s]',
                          item.name, request.user.username, request.user.id,
                          extra={'function': 'collection_item_update_view', 'action': 'update_failed', 
                                'object_type': 'CollectionItem', 'object_hash': item.hash, 
                                'object_name': item.name, 'errors': form.errors.as_json(), 
                                'result': 'validation_error'})
    else:
        logger.info("User '%s [%s]' is viewing the update form for item '%s' in collection '%s' [%s]", request.user.username, request.user.id, item.name, item.collection.name, item.collection.hash)
        form = CollectionItemForm(instance=item, user=request.user)

    # Task 50: Calculate suggested ID
    suggested_id = item.predict_next_id()

    # Get last used ID for display
    last_item_with_id = CollectionItem.objects.filter(
        collection=item.collection,
        your_id__isnull=False
    ).exclude(
        your_id='',
        pk=item.pk
    ).order_by('-created').first()
    last_used_id = last_item_with_id.your_id if last_item_with_id else None

    context = {
        'form': form,
        'item': item,
        'collection': item.collection, # Pass the collection for the breadcrumbs
        'suggested_id': suggested_id,
        'last_used_id': last_used_id,
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
    collection_name = collection.name
    item.delete()
    
    logger.info("User '%s [%s]' deleted item '%s' from collection '%s' [%s]", request.user.username, request.user.id, item_name, collection.name, collection.hash)
    
    # Log user activity
    RecentActivity.log_item_removed(
        user=request.user,
        item_name=item_name,
        collection_name=collection_name
    )
    
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
            RecentActivity.log_item_moved(
                user=request.user,
                item_name=item.name,
                from_collection=original_collection.name,
                to_collection=target_collection.name
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
            RecentActivity.log_item_copied(
                user=request.user,
                item_name=copied_item.name,
                from_collection=original_item.collection.name,
                to_collection=target_collection.name
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
