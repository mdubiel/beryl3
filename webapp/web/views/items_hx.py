# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_http_methods

from web.decorators import log_execution_time
from web.models import CollectionItem, RecentActivity, ItemType, ItemAttribute, CollectionItemLink, LinkPattern, ApplicationActivity

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
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('update_item_status', 
            f"Unauthorized attempt to update item '{item.name}' status", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash}
            })
        
        raise Http404("You do not have permission to edit this item.")

    new_status = request.POST.get('new_status')

    # Update the status if the new value is valid
    if new_status in CollectionItem.Status.values:
        old_status = item.status
        item.status = new_status
        item.save(update_fields=['status'])
        logger.info("User '%s' [%s] updated CollectionItem '%s' [%s] to status '%s'", request.user.username, request.user.id, item.name, item.hash, new_status)
        
        # Log successful status update
        ApplicationActivity.log_info('update_item_status', 
            f"Item '{item.name}' status updated from '{old_status}' to '{new_status}'", 
            user=request.user, meta={
                'action': 'status_updated', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'collection_hash': item.collection.hash, 'collection_name': item.collection.name,
                'old_status': old_status, 'new_status': new_status, 'result': 'success',
                'function_args': {'hash': hash, 'new_status': new_status}
            })
    else:
        # Log invalid status value
        ApplicationActivity.log_warning('update_item_status', 
            f"Invalid status '{new_status}' attempted for item '{item.name}'", 
            user=request.user, meta={
                'action': 'status_update_failed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'invalid_status': new_status, 'result': 'validation_error',
                'function_args': {'hash': hash, 'new_status': new_status}
            })

    # Check if this is coming from item detail page
    referer = request.META.get('HTTP_REFERER', '')
    is_item_detail_page = '/items/' in referer and referer.endswith('/') and not '/collections/' in referer
    
    if is_item_detail_page:
        # Use HTMX redirect for item detail page
        from django.http import HttpResponse
        response = HttpResponse()
        response['HX-Redirect'] = item.get_absolute_url()
        return response
    
    # Return the updated list item HTML fragment to HTMX (for collection detail)
    logger.info("Returning updated item list item for item: '%s' [%s]", item.name, item.hash)
    return render(request, 'partials/_item_list_item.html', {
        'item': item,
        'item_types': ItemType.objects.all()
    })


@login_required
@require_POST
@log_execution_time
def toggle_item_favorite(request, hash):
    """
    Handles HTMX requests to toggle the favorite status of a CollectionItem.
    """
    logger.info("HTMX request to toggle favorite status for item with hash '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to toggle favorite on item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('toggle_item_favorite', 
            f"Unauthorized attempt to toggle favorite on item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash}
            })
        
        raise Http404("You do not have permission to edit this item.")

    # Toggle the favorite status
    was_favorite = item.is_favorite
    item.is_favorite = not was_favorite
    item.save(update_fields=['is_favorite'])
    
    # Log the action
    action = "unfavorited" if was_favorite else "favorited"
    logger.info("User '%s' [%s] %s CollectionItem '%s' [%s]", request.user.username, request.user.id, action, item.name, item.hash)
    
    # Log favorite toggle
    ApplicationActivity.log_info('toggle_item_favorite', 
        f"Item '{item.name}' {action} successfully", 
        user=request.user, meta={
            'action': 'favorite_toggled', 'object_type': 'CollectionItem',
            'object_hash': item.hash, 'object_name': item.name,
            'collection_hash': item.collection.hash, 'collection_name': item.collection.name,
            'was_favorite': was_favorite, 'is_favorite': item.is_favorite,
            'toggle_action': action, 'result': 'success',
            'function_args': {'hash': hash}
        })
    
    # Create activity log entry using simplified RecentActivity
    if was_favorite:
        RecentActivity.objects.create(
            created_by=request.user,
            message=f"Unfavorited **{item.name}**",
            icon="heart"
        )
    else:
        RecentActivity.objects.create(
            created_by=request.user,
            message=f"Favorited **{item.name}**", 
            icon="star"
        )
    logger.info("Created activity log entry for %s CollectionItem '%s' [%s] by user '%s' [%s]", action, item.name, item.hash, request.user.username, request.user.id)

    # Check if this is coming from item detail page or favorites page
    referer = request.META.get('HTTP_REFERER', '')
    is_item_detail_page = '/items/' in referer and referer.endswith('/') and not '/collections/' in referer
    is_favorites_page = '/favorites/' in referer
    
    if is_item_detail_page or is_favorites_page:
        # Use HTMX redirect for page refresh
        from django.http import HttpResponse
        from django.urls import reverse
        response = HttpResponse()
        if is_favorites_page:
            response['HX-Redirect'] = reverse('favorites_list')
        else:
            response['HX-Redirect'] = item.get_absolute_url()
        return response
    
    # Return the updated list item HTML fragment to HTMX (for collection detail)
    logger.info("Returning updated item list item for item: '%s' [%s]", item.name, item.hash)
    return render(request, 'partials/_item_list_item.html', {
        'item': item,
        'item_types': ItemType.objects.all()
    })

@login_required
@require_POST
@log_execution_time
def change_item_type(request, hash):
    """
    Handles HTMX requests to change the item type of a CollectionItem.
    """
    logger.info("HTMX request to change item type for item with hash '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to change item type on item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('change_item_type', 
            f"Unauthorized attempt to change item type on item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash}
            })
        
        raise Http404("You do not have permission to edit this item.")

    item_type_id = request.POST.get('item_type_id')
    if not item_type_id:
        logger.error("No item_type_id provided in request")
        
        # Log missing item type ID
        ApplicationActivity.log_error('change_item_type', 
            f"Item type change failed for item '{item.name}' - missing item_type_id", 
            user=request.user, meta={
                'action': 'type_change_failed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'error': 'missing_item_type_id', 'result': 'validation_error',
                'function_args': {'hash': hash}
            })
        
        raise Http404("Item type ID is required.")

    try:
        new_item_type = ItemType.objects.get(id=item_type_id)
    except ItemType.DoesNotExist:
        logger.error("Item type with ID '%s' does not exist", item_type_id)
        
        # Log invalid item type ID
        ApplicationActivity.log_error('change_item_type', 
            f"Item type change failed for item '{item.name}' - invalid item_type_id '{item_type_id}'", 
            user=request.user, meta={
                'action': 'type_change_failed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'invalid_item_type_id': item_type_id, 'error': 'invalid_item_type',
                'result': 'validation_error', 'function_args': {'hash': hash, 'item_type_id': item_type_id}
            })
        
        raise Http404("Invalid item type.")

    # Store the old item type for logging
    old_item_type = item.item_type
    
    # Keep old attributes - only display will be filtered by item type
    # No need to clear attributes as they will be filtered in display methods
    
    # Update the item type
    item.item_type = new_item_type
    item.save(update_fields=['item_type'])
    
    # Log the action
    old_type_name = old_item_type.display_name if old_item_type else "Generic"
    logger.info("User '%s' [%s] changed CollectionItem '%s' [%s] type from '%s' to '%s'", 
                request.user.username, request.user.id, item.name, item.hash, old_type_name, new_item_type.display_name)
    
    # Log item type change
    ApplicationActivity.log_info('change_item_type', 
        f"Item '{item.name}' type changed from '{old_type_name}' to '{new_item_type.display_name}'", 
        user=request.user, meta={
            'action': 'type_changed', 'object_type': 'CollectionItem',
            'object_hash': item.hash, 'object_name': item.name,
            'collection_hash': item.collection.hash, 'collection_name': item.collection.name,
            'old_type': old_type_name, 'new_type': new_item_type.display_name,
            'new_type_id': new_item_type.id, 'result': 'success',
            'function_args': {'hash': hash, 'item_type_id': item_type_id}
        })

    # Check if this is coming from item detail page
    referer = request.META.get('HTTP_REFERER', '')
    is_item_detail_page = '/items/' in referer and referer.endswith('/') and not '/collections/' in referer
    
    if is_item_detail_page:
        # Use HTMX redirect for item detail page
        from django.http import HttpResponse
        response = HttpResponse()
        response['HX-Redirect'] = item.get_absolute_url()
        return response

    # Return the updated list item HTML fragment to HTMX (for collection detail)
    logger.info("Returning updated item list item for item: '%s' [%s]", item.name, item.hash)
    return render(request, 'partials/_item_list_item.html', {
        'item': item,
        'item_types': ItemType.objects.all()
    })
@login_required
@log_execution_time
def item_add_attribute(request, hash):
    """
    Handles GET request to show add attribute form for an item.
    """
    logger.info("Add attribute form requested for item hash '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to add attribute to item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('item_add_attribute', 
            f"Unauthorized attempt to add attribute to item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash}
            })
        
        raise Http404("You do not have permission to edit this item.")

    # Get available attributes for this item type
    available_attributes = []
    if item.item_type:
        available_attributes = item.item_type.attributes.all()

    # Log add attribute form access
    ApplicationActivity.log_info('item_add_attribute', 
        f"Add attribute form accessed for item '{item.name}'", 
        user=request.user, meta={
            'action': 'form_access', 'object_type': 'CollectionItem',
            'object_hash': item.hash, 'object_name': item.name,
            'available_attributes_count': len(available_attributes),
            'function_args': {'hash': hash}
        })
    
    context = {
        'item': item,
        'available_attributes': available_attributes,
        'mode': 'add'
    }
    
    return render(request, 'partials/_attribute_form.html', context)


@login_required
@log_execution_time
def item_edit_attribute(request, hash, attribute_name):
    """
    Handles GET request to show edit attribute form for an item.
    """
    logger.info("Edit attribute form requested for item hash '%s' attribute '%s' by user '%s' [%s]", hash, attribute_name, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to edit attribute on item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('item_edit_attribute', 
            f"Unauthorized attempt to edit attribute on item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash, 'attribute_name': attribute_name}
            })
        
        raise Http404("You do not have permission to edit this item.")

    # Get the attribute definition
    attribute = None
    if item.item_type:
        try:
            attribute = item.item_type.attributes.get(name=attribute_name)
        except ItemAttribute.DoesNotExist:
            logger.error("Attribute '%s' not found for item type '%s'", attribute_name, item.item_type.name)
            
            # Log attribute not found error
            ApplicationActivity.log_error('item_edit_attribute', 
                f"Attribute '{attribute_name}' not found for item '{item.name}' with type '{item.item_type.name}'", 
                user=request.user, meta={
                    'action': 'edit_form_failed', 'object_type': 'CollectionItem',
                    'object_hash': item.hash, 'object_name': item.name,
                    'attribute_name': attribute_name, 'error': 'attribute_not_found',
                    'result': 'not_found', 'function_args': {'hash': hash, 'attribute_name': attribute_name}
                })
            
            raise Http404("Attribute not found.")

    current_value = item.attributes.get(attribute_name, "")

    # Log edit attribute form access
    ApplicationActivity.log_info('item_edit_attribute', 
        f"Edit attribute form accessed for item '{item.name}' attribute '{attribute_name}'", 
        user=request.user, meta={
            'action': 'edit_form_access', 'object_type': 'CollectionItem',
            'object_hash': item.hash, 'object_name': item.name,
            'attribute_name': attribute_name, 'current_value': str(current_value),
            'function_args': {'hash': hash, 'attribute_name': attribute_name}
        })
    
    context = {
        'item': item,
        'attribute': attribute,
        'current_value': current_value,
        'mode': 'edit'
    }
    
    return render(request, 'partials/_attribute_form.html', context)


@login_required
@require_POST
@log_execution_time
def item_save_attribute(request, hash):
    """
    Handles POST request to save an attribute for an item.
    """
    logger.info("Save attribute requested for item hash '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to save attribute on item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('item_save_attribute', 
            f"Unauthorized attempt to save attribute on item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash}
            })
        
        raise Http404("You do not have permission to edit this item.")

    attribute_name = request.POST.get('attribute_name')
    attribute_value = request.POST.get('attribute_value')

    if not attribute_name:
        logger.error("No attribute name provided")
        
        # Log missing attribute name
        ApplicationActivity.log_error('item_save_attribute', 
            f"Attribute save failed for item '{item.name}' - missing attribute name", 
            user=request.user, meta={
                'action': 'attribute_save_failed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'error': 'missing_attribute_name', 'result': 'validation_error',
                'function_args': {'hash': hash}
            })
        
        raise Http404("Attribute name is required.")

    # Validate and save the attribute
    try:
        if item.item_type:
            try:
                attribute = item.item_type.attributes.get(name=attribute_name)
                validated_value = attribute.validate_value(attribute_value)
                item.attributes[attribute_name] = validated_value
            except ItemAttribute.DoesNotExist:
                # Custom attribute not defined in item type
                item.attributes[attribute_name] = attribute_value
        else:
            # No item type, just store the value
            item.attributes[attribute_name] = attribute_value

        item.save(update_fields=['attributes'])
        logger.info("User '%s' [%s] saved attribute '%s' = '%s' for CollectionItem '%s' [%s]", 
                    request.user.username, request.user.id, attribute_name, attribute_value, item.name, item.hash)
        
        # Log successful attribute save
        ApplicationActivity.log_info('item_save_attribute', 
            f"Attribute '{attribute_name}' saved for item '{item.name}' with value '{attribute_value}'", 
            user=request.user, meta={
                'action': 'attribute_saved', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'attribute_name': attribute_name, 'attribute_value': str(attribute_value),
                'result': 'success', 'function_args': {'hash': hash, 'attribute_name': attribute_name}
            })

        # Check if this is coming from item detail page
        referer = request.META.get('HTTP_REFERER', '')
        is_item_detail_page = '/items/' in referer and referer.endswith('/') and not '/collections/' in referer
        
        if is_item_detail_page:
            # Use HTMX redirect for item detail page
            from django.http import HttpResponse
            response = HttpResponse()
            response['HX-Redirect'] = item.get_absolute_url()
            return response

        # Return the updated attributes section for collection detail
        return render(request, 'partials/_item_attributes.html', {
            'item': item,
            'item_types': ItemType.objects.all()
        })

    except ValidationError as e:
        logger.error("Validation error saving attribute '%s' for CollectionItem '%s' [%s]: %s", attribute_name, item.name, item.hash, str(e))
        
        # Log validation error
        ApplicationActivity.log_error('item_save_attribute', 
            f"Validation error saving attribute '{attribute_name}' for item '{item.name}': {str(e)}", 
            user=request.user, meta={
                'action': 'attribute_save_failed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'attribute_name': attribute_name, 'error': str(e),
                'result': 'validation_error', 'function_args': {'hash': hash, 'attribute_name': attribute_name}
            })
        
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
@log_execution_time
def item_remove_attribute(request, hash, attribute_name):
    """
    Handles DELETE request to remove an attribute from an item.
    """
    logger.info("Remove attribute requested for item hash '%s' attribute '%s' by user '%s' [%s]", hash, attribute_name, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to remove attribute from item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('item_remove_attribute', 
            f"Unauthorized attempt to remove attribute from item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash, 'attribute_name': attribute_name}
            })
        
        raise Http404("You do not have permission to edit this item.")

    # Remove the attribute
    if attribute_name in item.attributes:
        old_value = item.attributes[attribute_name]
        del item.attributes[attribute_name]
        item.save(update_fields=['attributes'])
        logger.info("User '%s' [%s] removed attribute '%s' from CollectionItem '%s' [%s]", 
                    request.user.username, request.user.id, attribute_name, item.name, item.hash)
        
        # Log successful attribute removal
        ApplicationActivity.log_info('item_remove_attribute', 
            f"Attribute '{attribute_name}' removed from item '{item.name}'", 
            user=request.user, meta={
                'action': 'attribute_removed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'attribute_name': attribute_name, 'old_value': str(old_value),
                'result': 'success', 'function_args': {'hash': hash, 'attribute_name': attribute_name}
            })
    else:
        # Log attempt to remove non-existent attribute
        ApplicationActivity.log_warning('item_remove_attribute', 
            f"Attempted to remove non-existent attribute '{attribute_name}' from item '{item.name}'", 
            user=request.user, meta={
                'action': 'attribute_remove_failed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'attribute_name': attribute_name, 'error': 'attribute_not_found',
                'result': 'not_found', 'function_args': {'hash': hash, 'attribute_name': attribute_name}
            })

    # Return the updated attributes section
    return render(request, 'partials/_item_attributes.html', {
        'item': item,
        'item_types': ItemType.objects.all()
    })


@login_required
@log_execution_time
def item_add_link(request, hash):
    """
    Handles GET request to show add link form for an item.
    """
    logger.info("Add link form requested for item hash '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to add link to item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('item_add_link', 
            f"Unauthorized attempt to add link to item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash}
            })
        
        raise Http404("You do not have permission to edit this item.")

    # Log add link form access
    ApplicationActivity.log_info('item_add_link', 
        f"Add link form accessed for item '{item.name}'", 
        user=request.user, meta={
            'action': 'form_access', 'object_type': 'CollectionItem',
            'object_hash': item.hash, 'object_name': item.name,
            'function_args': {'hash': hash}
        })
    
    context = {
        'item': item,
        'mode': 'add'
    }
    
    return render(request, 'partials/_link_form.html', context)


@login_required
@log_execution_time
def item_edit_link(request, hash, link_id):
    """
    Handles GET request to show edit link form for an item.
    """
    logger.info("Edit link form requested for item hash '%s' link '%s' by user '%s' [%s]", hash, link_id, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)
    link = get_object_or_404(CollectionItemLink, id=link_id, item=item)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to edit link on item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('item_edit_link', 
            f"Unauthorized attempt to edit link on item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash, 'link_id': link_id}
            })
        
        raise Http404("You do not have permission to edit this item.")

    # Log edit link form access
    ApplicationActivity.log_info('item_edit_link', 
        f"Edit link form accessed for item '{item.name}' link '{link.get_display_name()}'", 
        user=request.user, meta={
            'action': 'edit_form_access', 'object_type': 'CollectionItem',
            'object_hash': item.hash, 'object_name': item.name,
            'link_id': link_id, 'link_url': link.url,
            'function_args': {'hash': hash, 'link_id': link_id}
        })
    
    context = {
        'item': item,
        'link': link,
        'mode': 'edit'
    }
    
    return render(request, 'partials/_link_form.html', context)


@login_required
@require_POST
@log_execution_time
def item_save_link(request, hash):
    """
    Handles POST request to save a link for an item.
    """
    logger.info("Save link requested for item hash '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to save link on item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('item_save_link', 
            f"Unauthorized attempt to save link on item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash}
            })
        
        raise Http404("You do not have permission to edit this item.")

    link_id = request.POST.get('link_id')
    url = request.POST.get('url')
    display_name = request.POST.get('display_name', '').strip()

    if not url:
        logger.error("No URL provided")
        
        # Log missing URL error
        ApplicationActivity.log_error('item_save_link', 
            f"Link save failed for item '{item.name}' - missing URL", 
            user=request.user, meta={
                'action': 'link_save_failed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'error': 'missing_url', 'result': 'validation_error',
                'function_args': {'hash': hash}
            })
        
        return JsonResponse({'error': 'URL is required.'}, status=400)

    # Validate URL
    try:
        from django.core.validators import URLValidator
        validator = URLValidator()
        validator(url)
    except ValidationError:
        logger.error("Invalid URL provided: %s", url)
        
        # Log invalid URL error
        ApplicationActivity.log_error('item_save_link', 
            f"Link save failed for item '{item.name}' - invalid URL: '{url}'", 
            user=request.user, meta={
                'action': 'link_save_failed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'invalid_url': url, 'error': 'invalid_url',
                'result': 'validation_error', 'function_args': {'hash': hash, 'url': url}
            })
        
        return JsonResponse({'error': 'Please enter a valid URL.'}, status=400)

    try:
        if link_id:
            # Edit existing link
            link = get_object_or_404(CollectionItemLink, id=link_id, item=item)
            link.url = url
            link.display_name = display_name if display_name else None
            # Let the model's save method handle pattern matching
            link.link_pattern = None  # Reset to trigger pattern matching
            link.save()
            logger.info("User '%s' [%s] updated link '%s' for CollectionItem '%s' [%s]", 
                        request.user.username, request.user.id, url, item.name, item.hash)
            
            # Log successful link update
            ApplicationActivity.log_info('item_save_link', 
                f"Link updated for item '{item.name}': '{url}'", 
                user=request.user, meta={
                    'action': 'link_updated', 'object_type': 'CollectionItem',
                    'object_hash': item.hash, 'object_name': item.name,
                    'link_id': link_id, 'url': url, 'display_name': display_name,
                    'result': 'success', 'function_args': {'hash': hash, 'link_id': link_id}
                })
        else:
            # Create new link
            link = CollectionItemLink.objects.create(
                item=item,
                url=url,
                display_name=display_name if display_name else None,
                created_by=request.user
            )
            logger.info("User '%s' [%s] added link '%s' to CollectionItem '%s' [%s]", 
                        request.user.username, request.user.id, url, item.name, item.hash)
            
            # Log successful link creation
            ApplicationActivity.log_info('item_save_link', 
                f"New link added to item '{item.name}': '{url}'", 
                user=request.user, meta={
                    'action': 'link_created', 'object_type': 'CollectionItem',
                    'object_hash': item.hash, 'object_name': item.name,
                    'link_id': link.id, 'url': url, 'display_name': display_name,
                    'result': 'success', 'function_args': {'hash': hash}
                })

        # Check if this is coming from item detail page
        referer = request.META.get('HTTP_REFERER', '')
        is_item_detail_page = '/items/' in referer and referer.endswith('/') and not '/collections/' in referer
        
        if is_item_detail_page:
            # Use HTMX redirect for item detail page
            from django.http import HttpResponse
            response = HttpResponse()
            response['HX-Redirect'] = item.get_absolute_url()
            return response

        # Return the updated links section for collection detail
        return render(request, 'partials/_item_links.html', {
            'item': item
        })

    except Exception as e:
        logger.error("Error saving link for CollectionItem '%s' [%s]: %s", item.name, item.hash, str(e))
        
        # Log link save error
        ApplicationActivity.log_error('item_save_link', 
            f"Error saving link for item '{item.name}': {str(e)}", 
            user=request.user, meta={
                'action': 'link_save_failed', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'error': str(e), 'result': 'system_error',
                'function_args': {'hash': hash, 'url': url}
            })
        
        return JsonResponse({'error': 'An error occurred while saving the link.'}, status=500)


@login_required
@require_http_methods(["DELETE"])
@log_execution_time
def item_remove_link(request, hash, link_id):
    """
    Handles DELETE request to remove a link from an item.
    """
    logger.info("Remove link requested for item hash '%s' link '%s' by user '%s' [%s]", hash, link_id, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)
    link = get_object_or_404(CollectionItemLink, id=link_id, item=item)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to remove link from item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)
        
        # Log unauthorized access attempt
        ApplicationActivity.log_warning('item_remove_link', 
            f"Unauthorized attempt to remove link from item '{item.name}'", 
            user=request.user, meta={
                'action': 'unauthorized_access', 'object_type': 'CollectionItem',
                'object_hash': item.hash, 'object_name': item.name,
                'result': 'access_denied', 'function_args': {'hash': hash, 'link_id': link_id}
            })
        
        raise Http404("You do not have permission to edit this item.")

    link_display_name = link.get_display_name()
    link_url = link.url
    link.delete()
    logger.info("User '%s' [%s] removed link '%s' from CollectionItem '%s' [%s]", 
                request.user.username, request.user.id, link_display_name, item.name, item.hash)
    
    # Log successful link removal
    ApplicationActivity.log_info('item_remove_link', 
        f"Link '{link_display_name}' removed from item '{item.name}'", 
        user=request.user, meta={
            'action': 'link_removed', 'object_type': 'CollectionItem',
            'object_hash': item.hash, 'object_name': item.name,
            'link_id': link_id, 'link_url': link_url,
            'link_display_name': link_display_name, 'result': 'success',
            'function_args': {'hash': hash, 'link_id': link_id}
        })

    # Return the updated links section
    return render(request, 'partials/_item_links.html', {
        'item': item
    })