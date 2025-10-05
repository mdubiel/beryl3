# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_POST, require_http_methods

from web.decorators import log_execution_time
from web.models import CollectionItem, RecentActivity, ItemType, ItemAttribute, CollectionItemLink, LinkPattern, CollectionItemAttributeValue

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
        logger.warning("update_item_status: Unauthorized attempt to update item '%s' status by user '%s' [%s] - access denied", 
                      item.name, request.user.username, request.user.id, 
                      extra={'function': 'update_item_status', 'action': 'unauthorized_access', 
                            'object_type': 'CollectionItem', 'object_hash': item.hash, 
                            'object_name': item.name, 'result': 'access_denied', 
                            'function_args': {'hash': hash}})
        
        raise Http404("You do not have permission to edit this item.")

    new_status = request.POST.get('new_status')

    # Update the status if the new value is valid
    if new_status in CollectionItem.Status.values:
        old_status = item.status
        item.status = new_status
        item.save(update_fields=['status'])
        logger.info("User '%s' [%s] updated CollectionItem '%s' [%s] to status '%s'", request.user.username, request.user.id, item.name, item.hash, new_status)
        
        # Log successful status update
        logger.info("update_item_status: Item '%s' status updated from '%s' to '%s' by user '%s' [%s]", 
                   item.name, old_status, new_status, request.user.username, request.user.id,
                   extra={'function': 'update_item_status', 'action': 'status_updated', 
                         'object_type': 'CollectionItem', 'object_hash': item.hash, 
                         'object_name': item.name, 'collection_hash': item.collection.hash, 
                         'collection_name': item.collection.name, 'old_status': old_status, 
                         'new_status': new_status, 'result': 'success', 
                         'function_args': {'hash': hash, 'new_status': new_status}})
    else:
        # Log invalid status value
        logger.warning("update_item_status: Invalid status '%s' attempted for item '%s' by user '%s' [%s]", 
                      new_status, item.name, request.user.username, request.user.id,
                      extra={'function': 'update_item_status', 'action': 'status_update_failed', 
                            'object_type': 'CollectionItem', 'object_hash': item.hash, 
                            'object_name': item.name, 'invalid_status': new_status, 
                            'result': 'validation_error', 'function_args': {'hash': hash, 'new_status': new_status}})

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
        logger.warning("toggle_item_favorite: Unauthorized attempt to toggle favorite on item '%s' by user '%s' [%s] - access denied", 
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'toggle_item_favorite', 'action': 'unauthorized_access', 
                            'object_type': 'CollectionItem', 'object_hash': item.hash, 
                            'object_name': item.name, 'result': 'access_denied', 
                            'function_args': {'hash': hash}})
        
        raise Http404("You do not have permission to edit this item.")

    # Toggle the favorite status
    was_favorite = item.is_favorite
    item.is_favorite = not was_favorite
    item.save(update_fields=['is_favorite'])
    
    # Log the action
    action = "unfavorited" if was_favorite else "favorited"
    logger.info("User '%s' [%s] %s CollectionItem '%s' [%s]", request.user.username, request.user.id, action, item.name, item.hash)
    
    # Log favorite toggle
    logger.info("toggle_item_favorite: Item '%s' %s successfully by user '%s' [%s]", 
               item.name, action, request.user.username, request.user.id,
               extra={'function': 'toggle_item_favorite', 'action': 'favorite_toggled', 
                     'object_type': 'CollectionItem', 'object_hash': item.hash, 
                     'object_name': item.name, 'collection_hash': item.collection.hash, 
                     'collection_name': item.collection.name, 'was_favorite': was_favorite, 
                     'is_favorite': item.is_favorite, 'toggle_action': action, 
                     'result': 'success', 'function_args': {'hash': hash}})
    
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
        logger.warning("change_item_type: Unauthorized attempt to change item type on item '%s' by user '%s' [%s] - access denied", 
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'change_item_type', 'action': 'unauthorized_access', 
                            'object_type': 'CollectionItem', 'object_hash': item.hash, 
                            'object_name': item.name, 'result': 'access_denied', 
                            'function_args': {'hash': hash}})
        
        raise Http404("You do not have permission to edit this item.")

    item_type_id = request.POST.get('item_type_id')
    if not item_type_id:
        logger.error("No item_type_id provided in request")
        
        # Log missing item type ID
        logger.error("change_item_type: Item type change failed for item '%s' - missing item_type_id by user '%s' [%s]", 
                    item.name, request.user.username, request.user.id,
                    extra={'function': 'change_item_type', 'action': 'type_change_failed', 
                          'object_type': 'CollectionItem', 'object_hash': item.hash, 
                          'object_name': item.name, 'error': 'missing_item_type_id', 
                          'result': 'validation_error', 'function_args': {'hash': hash}})
        
        raise Http404("Item type ID is required.")

    try:
        new_item_type = ItemType.objects.get(id=item_type_id)
    except ItemType.DoesNotExist:
        logger.error("Item type with ID '%s' does not exist", item_type_id)
        
        # Log invalid item type ID
        logger.error("change_item_type: Item type change failed for item '%s' - invalid item_type_id '%s' by user '%s' [%s]", 
                    item.name, item_type_id, request.user.username, request.user.id,
                    extra={'function': 'change_item_type', 'action': 'type_change_failed', 
                          'object_type': 'CollectionItem', 'object_hash': item.hash, 
                          'object_name': item.name, 'invalid_item_type_id': item_type_id, 
                          'error': 'invalid_item_type', 'result': 'validation_error', 
                          'function_args': {'hash': hash, 'item_type_id': item_type_id}})
        
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
    logger.info("change_item_type: Item '%s' type changed from '%s' to '%s' by user '%s' [%s]", 
               item.name, old_type_name, new_item_type.display_name, request.user.username, request.user.id,
               extra={'function': 'change_item_type', 'action': 'type_changed', 
                     'object_type': 'CollectionItem', 'object_hash': item.hash, 
                     'object_name': item.name, 'collection_hash': item.collection.hash, 
                     'collection_name': item.collection.name, 'old_type': old_type_name, 
                     'new_type': new_item_type.display_name, 'new_type_id': new_item_type.id, 
                     'result': 'success', 'function_args': {'hash': hash, 'item_type_id': item_type_id}})

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
        logger.warning("item_add_attribute: Unauthorized attempt to add attribute to item '%s' by user '%s' [%s] - access denied", 
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'item_add_attribute', 'action': 'unauthorized_access', 
                            'object_type': 'CollectionItem', 'object_hash': item.hash, 
                            'object_name': item.name, 'result': 'access_denied', 
                            'function_args': {'hash': hash}})
        
        raise Http404("You do not have permission to edit this item.")

    # Get available attributes for this item type
    available_attributes = []
    if item.item_type:
        available_attributes = item.item_type.attributes.all()

    # Log add attribute form access
    logger.info("item_add_attribute: Add attribute form accessed for item '%s' by user '%s' [%s]", 
               item.name, request.user.username, request.user.id,
               extra={'function': 'item_add_attribute', 'action': 'form_access', 
                     'object_type': 'CollectionItem', 'object_hash': item.hash, 
                     'object_name': item.name, 'available_attributes_count': len(available_attributes), 
                     'function_args': {'hash': hash}})
    
    context = {
        'item': item,
        'available_attributes': available_attributes,
        'mode': 'add'
    }
    
    return render(request, 'partials/_attribute_form.html', context)


@login_required
@log_execution_time
def item_get_attribute_input(request, hash):
    """
    Handles GET request to return appropriate input field for selected attribute type.
    Used for dynamic form field rendering based on attribute data type.
    """
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        return HttpResponse('<input type="text" name="attribute_value" class="input input-bordered w-full" required>', content_type='text/html')

    # Get the selected attribute name from request
    attribute_name = request.GET.get('attribute_name', '')

    if not attribute_name or not item.item_type:
        return HttpResponse('<label class="label"><span class="label-text">Value</span></label><input type="text" name="attribute_value" class="input input-bordered w-full" required>', content_type='text/html')

    # Get the attribute definition
    try:
        attribute = item.item_type.attributes.get(name=attribute_name)
    except ItemAttribute.DoesNotExist:
        return HttpResponse('<label class="label"><span class="label-text">Value</span></label><input type="text" name="attribute_value" class="input input-bordered w-full" required>', content_type='text/html')

    context = {
        'attribute': attribute,
        'current_value': None,
    }

    return render(request, 'partials/_attribute_input_field.html', context)


@login_required
@log_execution_time
def item_edit_attribute_value(request, hash, attr_value_hash):
    """
    Handles GET request to show edit attribute form for a specific relational attribute value.
    """
    logger.info("Edit attribute value form requested for item hash '%s' attr_value_hash '%s' by user '%s' [%s]",
                hash, attr_value_hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to edit attribute value on item '%s' [%s] they do not own",
                    request.user.username, request.user.id, item.name, item.hash)

        # Log unauthorized access attempt
        logger.warning("item_edit_attribute_value: Unauthorized attempt to edit attribute value on item '%s' by user '%s' [%s] - access denied",
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'item_edit_attribute_value', 'action': 'unauthorized_access',
                            'object_type': 'CollectionItem', 'object_hash': item.hash,
                            'object_name': item.name, 'result': 'access_denied',
                            'function_args': {'hash': hash, 'attr_value_hash': attr_value_hash}})

        raise Http404("You do not have permission to edit this item.")

    # Get the attribute value
    try:
        attr_value = CollectionItemAttributeValue.objects.get(hash=attr_value_hash, item=item)
    except CollectionItemAttributeValue.DoesNotExist:
        logger.error("Attribute value with hash '%s' not found for item '%s'", attr_value_hash, item.hash)
        raise Http404("Attribute value not found.")

    attribute = attr_value.item_attribute
    current_value = attr_value.get_typed_value()

    # Log edit attribute value form access
    logger.info("item_edit_attribute_value: Edit attribute value form accessed for item '%s' attribute '%s' (hash: %s) by user '%s' [%s]",
               item.name, attribute.name, attr_value_hash, request.user.username, request.user.id,
               extra={'function': 'item_edit_attribute_value', 'action': 'edit_form_access',
                     'object_type': 'CollectionItem', 'object_hash': item.hash,
                     'object_name': item.name, 'attribute_name': attribute.name,
                     'attr_value_hash': attr_value_hash, 'current_value': str(current_value),
                     'function_args': {'hash': hash, 'attr_value_hash': attr_value_hash}})

    context = {
        'item': item,
        'attribute': attribute,
        'current_value': current_value,
        'attr_value_hash': attr_value_hash,
        'mode': 'edit'
    }

    return render(request, 'partials/_attribute_form.html', context)


@login_required
@require_POST
@log_execution_time
def item_save_attribute(request, hash):
    """
    Handles POST request to save an attribute for an item.
    Can create new attribute values or update existing ones (when attr_value_id is provided).
    """
    logger.info("Save attribute requested for item hash '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to save attribute on item '%s' [%s] they do not own", request.user.username, request.user.id, item.name, item.hash)

        # Log unauthorized access attempt
        logger.warning("item_save_attribute: Unauthorized attempt to save attribute on item '%s' by user '%s' [%s] - access denied",
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'item_save_attribute', 'action': 'unauthorized_access',
                            'object_type': 'CollectionItem', 'object_hash': item.hash,
                            'object_name': item.name, 'result': 'access_denied',
                            'function_args': {'hash': hash}})

        raise Http404("You do not have permission to edit this item.")

    attribute_name = request.POST.get('attribute_name')
    attribute_value = request.POST.get('attribute_value')
    attr_value_hash = request.POST.get('attr_value_hash')  # For editing existing values

    if not attribute_name:
        logger.error("No attribute name provided")

        # Log missing attribute name
        logger.error("item_save_attribute: Attribute save failed for item '%s' - missing attribute name by user '%s' [%s]",
                    item.name, request.user.username, request.user.id,
                    extra={'function': 'item_save_attribute', 'action': 'attribute_save_failed',
                          'object_type': 'CollectionItem', 'object_hash': item.hash,
                          'object_name': item.name, 'error': 'missing_attribute_name',
                          'result': 'validation_error', 'function_args': {'hash': hash}})

        raise Http404("Attribute name is required.")

    # Check if this is an update to an existing relational attribute value
    if attr_value_hash:
        try:
            attr_value_obj = CollectionItemAttributeValue.objects.get(
                hash=attr_value_hash,
                item=item
            )
            # Get the attribute definition for validation
            attribute = attr_value_obj.item_attribute
            validated_value = attribute.validate_value(attribute_value)
            attr_value_obj.set_typed_value(validated_value)
            attr_value_obj.save()

            logger.info("User '%s' [%s] updated relational attribute '%s' (hash: %s) = '%s' for CollectionItem '%s' [%s]",
                       request.user.username, request.user.id, attribute_name, attr_value_hash, validated_value, item.name, item.hash)

            # Log successful attribute update
            logger.info("item_save_attribute: Relational attribute '%s' updated for item '%s' with value '%s' by user '%s' [%s]",
                       attribute_name, item.name, validated_value, request.user.username, request.user.id,
                       extra={'function': 'item_save_attribute', 'action': 'relational_attribute_updated',
                             'object_type': 'CollectionItem', 'object_hash': item.hash,
                             'object_name': item.name, 'attribute_name': attribute_name,
                             'attr_value_hash': attr_value_hash, 'attribute_value': str(validated_value), 'result': 'success',
                             'function_args': {'hash': hash, 'attribute_name': attribute_name}})

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

        except CollectionItemAttributeValue.DoesNotExist:
            logger.error("Attribute value with hash '%s' not found for item '%s'", attr_value_hash, item.hash)
            return JsonResponse({'error': 'Attribute value not found'}, status=404)
        except ValidationError as e:
            logger.error("Validation error updating attribute '%s' for CollectionItem '%s' [%s]: %s", attribute_name, item.name, item.hash, str(e))
            return JsonResponse({'error': str(e)}, status=400)

    # Validate and save the attribute using relational model
    try:
        if item.item_type:
            try:
                attribute = item.item_type.attributes.get(name=attribute_name)
                validated_value = attribute.validate_value(attribute_value)
            except ItemAttribute.DoesNotExist:
                # Custom attribute not defined in item type - skip relational storage
                logger.warning("Attribute '%s' not defined in item type '%s', skipping relational storage",
                             attribute_name, item.item_type.name)
                item.attributes[attribute_name] = attribute_value
                item.save(update_fields=['attributes'])
                logger.info("User '%s' [%s] saved custom attribute '%s' = '%s' to JSON for CollectionItem '%s' [%s]",
                           request.user.username, request.user.id, attribute_name, attribute_value, item.name, item.hash)

                # Log successful custom attribute save
                logger.info("item_save_attribute: Custom attribute '%s' saved to JSON for item '%s' with value '%s' by user '%s' [%s]",
                           attribute_name, item.name, attribute_value, request.user.username, request.user.id,
                           extra={'function': 'item_save_attribute', 'action': 'custom_attribute_saved',
                                 'object_type': 'CollectionItem', 'object_hash': item.hash,
                                 'object_name': item.name, 'attribute_name': attribute_name,
                                 'attribute_value': str(attribute_value), 'result': 'success',
                                 'function_args': {'hash': hash, 'attribute_name': attribute_name}})

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
        else:
            # No item type, store in JSON
            item.attributes[attribute_name] = attribute_value
            item.save(update_fields=['attributes'])
            logger.info("User '%s' [%s] saved attribute '%s' = '%s' to JSON for CollectionItem '%s' [%s] (no item type)",
                       request.user.username, request.user.id, attribute_name, attribute_value, item.name, item.hash)

            # Log successful attribute save
            logger.info("item_save_attribute: Attribute '%s' saved to JSON for item '%s' with value '%s' by user '%s' [%s] (no item type)",
                       attribute_name, item.name, attribute_value, request.user.username, request.user.id,
                       extra={'function': 'item_save_attribute', 'action': 'attribute_saved',
                             'object_type': 'CollectionItem', 'object_hash': item.hash,
                             'object_name': item.name, 'attribute_name': attribute_name,
                             'attribute_value': str(attribute_value), 'result': 'success',
                             'function_args': {'hash': hash, 'attribute_name': attribute_name}})

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

        # For boolean attributes, delete any existing values (only one instance allowed)
        if attribute.attribute_type == 'BOOLEAN':
            existing_values = CollectionItemAttributeValue.objects.filter(
                item=item,
                item_attribute=attribute
            )
            if existing_values.exists():
                logger.info("Deleting %d existing boolean attribute value(s) for '%s' on item '%s'",
                           existing_values.count(), attribute_name, item.name)
                existing_values.delete()

        # Create relational attribute value (when item type and attribute definition exist)
        attr_value_obj = CollectionItemAttributeValue(
            item=item,
            item_attribute=attribute,
            created_by=request.user
        )
        attr_value_obj.set_typed_value(validated_value)
        attr_value_obj.save()

        logger.info("User '%s' [%s] saved relational attribute '%s' = '%s' for CollectionItem '%s' [%s]",
                    request.user.username, request.user.id, attribute_name, validated_value, item.name, item.hash)

        # Log successful attribute save
        logger.info("item_save_attribute: Relational attribute '%s' saved for item '%s' with value '%s' by user '%s' [%s]",
                   attribute_name, item.name, validated_value, request.user.username, request.user.id,
                   extra={'function': 'item_save_attribute', 'action': 'relational_attribute_saved',
                         'object_type': 'CollectionItem', 'object_hash': item.hash,
                         'object_name': item.name, 'attribute_name': attribute_name,
                         'attribute_value': str(validated_value), 'result': 'success',
                         'function_args': {'hash': hash, 'attribute_name': attribute_name}})

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
        logger.error("item_save_attribute: Validation error saving attribute '%s' for item '%s': %s by user '%s' [%s]", 
                    attribute_name, item.name, str(e), request.user.username, request.user.id,
                    extra={'function': 'item_save_attribute', 'action': 'attribute_save_failed', 
                          'object_type': 'CollectionItem', 'object_hash': item.hash, 
                          'object_name': item.name, 'attribute_name': attribute_name, 
                          'error': str(e), 'result': 'validation_error', 
                          'function_args': {'hash': hash, 'attribute_name': attribute_name}})
        
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
@log_execution_time
def item_remove_attribute_value(request, hash, attr_value_hash):
    """
    Handles DELETE request to remove a specific relational attribute value from an item.
    """
    logger.info("Remove attribute value requested for item hash '%s' attr_value_hash '%s' by user '%s' [%s]",
                hash, attr_value_hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to remove attribute value from item '%s' [%s] they do not own",
                    request.user.username, request.user.id, item.name, item.hash)

        # Log unauthorized access attempt
        logger.warning("item_remove_attribute_value: Unauthorized attempt to remove attribute value from item '%s' by user '%s' [%s] - access denied",
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'item_remove_attribute_value', 'action': 'unauthorized_access',
                            'object_type': 'CollectionItem', 'object_hash': item.hash,
                            'object_name': item.name, 'result': 'access_denied',
                            'function_args': {'hash': hash, 'attr_value_hash': attr_value_hash}})

        raise Http404("You do not have permission to edit this item.")

    # Remove the attribute value
    try:
        attr_value = CollectionItemAttributeValue.objects.get(hash=attr_value_hash, item=item)
        attribute_name = attr_value.item_attribute.name
        old_value = attr_value.get_typed_value()
        attr_value.delete()

        logger.info("User '%s' [%s] removed relational attribute value '%s' = '%s' (hash: %s) from CollectionItem '%s' [%s]",
                   request.user.username, request.user.id, attribute_name, old_value, attr_value_hash, item.name, item.hash)

        # Log successful attribute value removal
        logger.info("item_remove_attribute_value: Relational attribute value '%s' (hash: %s) removed from item '%s' by user '%s' [%s]",
                   attribute_name, attr_value_hash, item.name, request.user.username, request.user.id,
                   extra={'function': 'item_remove_attribute_value', 'action': 'relational_attribute_value_removed',
                         'object_type': 'CollectionItem', 'object_hash': item.hash,
                         'object_name': item.name, 'attribute_name': attribute_name,
                         'attr_value_hash': attr_value_hash, 'old_value': str(old_value), 'result': 'success',
                         'function_args': {'hash': hash, 'attr_value_hash': attr_value_hash}})

    except CollectionItemAttributeValue.DoesNotExist:
        # Log attempt to remove non-existent attribute value
        logger.warning("item_remove_attribute_value: Attempted to remove non-existent attribute value (hash: %s) from item '%s' by user '%s' [%s]",
                      attr_value_hash, item.name, request.user.username, request.user.id,
                      extra={'function': 'item_remove_attribute_value', 'action': 'attribute_value_remove_failed',
                            'object_type': 'CollectionItem', 'object_hash': item.hash,
                            'object_name': item.name, 'attr_value_hash': attr_value_hash,
                            'error': 'attribute_value_not_found', 'result': 'not_found',
                            'function_args': {'hash': hash, 'attr_value_hash': attr_value_hash}})

    # Return the updated attributes section
    return render(request, 'partials/_item_attributes.html', {
        'item': item,
        'item_types': ItemType.objects.all()
    })


@login_required
@require_POST
@log_execution_time
def item_toggle_boolean_attribute(request, hash, attr_value_hash):
    """
    Handles POST request to toggle a boolean attribute value (True <-> False).
    No confirmation needed, instant toggle with logging.
    """
    logger.info("Toggle boolean attribute requested for item hash '%s' attr_value_hash '%s' by user '%s' [%s]",
                hash, attr_value_hash, request.user.username, request.user.id)
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if user owns the collection
    if item.collection.created_by != request.user:
        logger.error("User '%s' [%s] attempted to toggle attribute on item '%s' [%s] they do not own",
                    request.user.username, request.user.id, item.name, item.hash)

        # Log unauthorized access attempt
        logger.warning("item_toggle_boolean_attribute: Unauthorized attempt to toggle attribute on item '%s' by user '%s' [%s] - access denied",
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'item_toggle_boolean_attribute', 'action': 'unauthorized_access',
                            'object_type': 'CollectionItem', 'object_hash': item.hash,
                            'object_name': item.name, 'result': 'access_denied',
                            'function_args': {'hash': hash, 'attr_value_hash': attr_value_hash}})

        raise Http404("You do not have permission to edit this item.")

    # Get the attribute value and toggle it
    try:
        attr_value = CollectionItemAttributeValue.objects.get(hash=attr_value_hash, item=item)
        attribute_name = attr_value.item_attribute.name

        # Verify it's a boolean attribute
        if attr_value.item_attribute.attribute_type != 'BOOLEAN':
            logger.error("User '%s' [%s] attempted to toggle non-boolean attribute '%s' on item '%s'",
                        request.user.username, request.user.id, attribute_name, item.name)
            raise Http404("Can only toggle boolean attributes.")

        # Get current value and toggle it
        old_value = attr_value.get_typed_value()
        new_value = not old_value

        # Update the value
        attr_value.value = '1' if new_value else '0'
        attr_value.save()

        logger.info("User '%s' [%s] toggled boolean attribute '%s' from %s to %s on CollectionItem '%s' [%s]",
                   request.user.username, request.user.id, attribute_name, old_value, new_value, item.name, item.hash)

        # Log successful toggle
        logger.info("item_toggle_boolean_attribute: Boolean attribute '%s' toggled from %s to %s on item '%s' by user '%s' [%s]",
                   attribute_name, old_value, new_value, item.name, request.user.username, request.user.id,
                   extra={'function': 'item_toggle_boolean_attribute', 'action': 'boolean_toggled',
                         'object_type': 'CollectionItem', 'object_hash': item.hash,
                         'object_name': item.name, 'attribute_name': attribute_name,
                         'attr_value_hash': attr_value_hash, 'old_value': str(old_value),
                         'new_value': str(new_value), 'result': 'success',
                         'function_args': {'hash': hash, 'attr_value_hash': attr_value_hash}})

        # Log to user activity timeline
        RecentActivity.objects.create(
            created_by=request.user,
            icon='arrow-left-right',
            message=f"Changed **{attr_value.item_attribute.display_name}** from **{old_value}** to **{new_value}** for **{item.name}**"
        )

    except CollectionItemAttributeValue.DoesNotExist:
        # Log attempt to toggle non-existent attribute value
        logger.warning("item_toggle_boolean_attribute: Attempted to toggle non-existent attribute value (hash: %s) on item '%s' by user '%s' [%s]",
                      attr_value_hash, item.name, request.user.username, request.user.id,
                      extra={'function': 'item_toggle_boolean_attribute', 'action': 'toggle_failed',
                            'object_type': 'CollectionItem', 'object_hash': item.hash,
                            'object_name': item.name, 'attr_value_hash': attr_value_hash,
                            'error': 'attribute_value_not_found', 'result': 'not_found',
                            'function_args': {'hash': hash, 'attr_value_hash': attr_value_hash}})

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
        logger.warning("item_add_link: Unauthorized attempt to add link to item '%s' by user '%s' [%s] - access denied", 
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'item_add_link', 'action': 'unauthorized_access', 
                            'object_type': 'CollectionItem', 'object_hash': item.hash, 
                            'object_name': item.name, 'result': 'access_denied', 
                            'function_args': {'hash': hash}})
        
        raise Http404("You do not have permission to edit this item.")

    # Log add link form access
    logger.info("item_add_link: Add link form accessed for item '%s' by user '%s' [%s]", 
               item.name, request.user.username, request.user.id,
               extra={'function': 'item_add_link', 'action': 'form_access', 
                     'object_type': 'CollectionItem', 'object_hash': item.hash, 
                     'object_name': item.name, 'function_args': {'hash': hash}})
    
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
        logger.warning("item_edit_link: Unauthorized attempt to edit link on item '%s' by user '%s' [%s] - access denied", 
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'item_edit_link', 'action': 'unauthorized_access', 
                            'object_type': 'CollectionItem', 'object_hash': item.hash, 
                            'object_name': item.name, 'result': 'access_denied', 
                            'function_args': {'hash': hash, 'link_id': link_id}})
        
        raise Http404("You do not have permission to edit this item.")

    # Log edit link form access
    logger.info("item_edit_link: Edit link form accessed for item '%s' link '%s' by user '%s' [%s]", 
               item.name, link.get_display_name(), request.user.username, request.user.id,
               extra={'function': 'item_edit_link', 'action': 'edit_form_access', 
                     'object_type': 'CollectionItem', 'object_hash': item.hash, 
                     'object_name': item.name, 'link_id': link_id, 'link_url': link.url, 
                     'function_args': {'hash': hash, 'link_id': link_id}})
    
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
        logger.warning("item_save_link: Unauthorized attempt to save link on item '%s' by user '%s' [%s] - access denied", 
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'item_save_link', 'action': 'unauthorized_access', 
                            'object_type': 'CollectionItem', 'object_hash': item.hash, 
                            'object_name': item.name, 'result': 'access_denied', 
                            'function_args': {'hash': hash}})
        
        raise Http404("You do not have permission to edit this item.")

    link_id = request.POST.get('link_id')
    url = request.POST.get('url')
    display_name = request.POST.get('display_name', '').strip()

    if not url:
        logger.error("No URL provided")
        
        # Log missing URL error
        logger.error("item_save_link: Link save failed for item '%s' - missing URL by user '%s' [%s]", 
                    item.name, request.user.username, request.user.id,
                    extra={'function': 'item_save_link', 'action': 'link_save_failed', 
                          'object_type': 'CollectionItem', 'object_hash': item.hash, 
                          'object_name': item.name, 'error': 'missing_url', 
                          'result': 'validation_error', 'function_args': {'hash': hash}})
        
        return JsonResponse({'error': 'URL is required.'}, status=400)

    # Validate URL
    try:
        from django.core.validators import URLValidator
        validator = URLValidator()
        validator(url)
    except ValidationError:
        logger.error("Invalid URL provided: %s", url)
        
        # Log invalid URL error
        logger.error("item_save_link: Link save failed for item '%s' - invalid URL: '%s' by user '%s' [%s]", 
                    item.name, url, request.user.username, request.user.id,
                    extra={'function': 'item_save_link', 'action': 'link_save_failed', 
                          'object_type': 'CollectionItem', 'object_hash': item.hash, 
                          'object_name': item.name, 'invalid_url': url, 'error': 'invalid_url', 
                          'result': 'validation_error', 'function_args': {'hash': hash, 'url': url}})
        
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
            logger.info("item_save_link: Link updated for item '%s': '%s' by user '%s' [%s]", 
                       item.name, url, request.user.username, request.user.id,
                       extra={'function': 'item_save_link', 'action': 'link_updated', 
                             'object_type': 'CollectionItem', 'object_hash': item.hash, 
                             'object_name': item.name, 'link_id': link_id, 'url': url, 
                             'display_name': display_name, 'result': 'success', 
                             'function_args': {'hash': hash, 'link_id': link_id}})
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
            logger.info("item_save_link: New link added to item '%s': '%s' by user '%s' [%s]", 
                       item.name, url, request.user.username, request.user.id,
                       extra={'function': 'item_save_link', 'action': 'link_created', 
                             'object_type': 'CollectionItem', 'object_hash': item.hash, 
                             'object_name': item.name, 'link_id': link.id, 'url': url, 
                             'display_name': display_name, 'result': 'success', 
                             'function_args': {'hash': hash}})

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
        logger.error("item_save_link: Error saving link for item '%s': %s by user '%s' [%s]", 
                    item.name, str(e), request.user.username, request.user.id,
                    extra={'function': 'item_save_link', 'action': 'link_save_failed', 
                          'object_type': 'CollectionItem', 'object_hash': item.hash, 
                          'object_name': item.name, 'error': str(e), 'result': 'system_error', 
                          'function_args': {'hash': hash, 'url': url}})
        
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
        logger.warning("item_remove_link: Unauthorized attempt to remove link from item '%s' by user '%s' [%s] - access denied", 
                      item.name, request.user.username, request.user.id,
                      extra={'function': 'item_remove_link', 'action': 'unauthorized_access', 
                            'object_type': 'CollectionItem', 'object_hash': item.hash, 
                            'object_name': item.name, 'result': 'access_denied', 
                            'function_args': {'hash': hash, 'link_id': link_id}})
        
        raise Http404("You do not have permission to edit this item.")

    link_display_name = link.get_display_name()
    link_url = link.url
    link.delete()
    logger.info("User '%s' [%s] removed link '%s' from CollectionItem '%s' [%s]", 
                request.user.username, request.user.id, link_display_name, item.name, item.hash)
    
    # Log successful link removal
    logger.info("item_remove_link: Link '%s' removed from item '%s' by user '%s' [%s]", 
               link_display_name, item.name, request.user.username, request.user.id,
               extra={'function': 'item_remove_link', 'action': 'link_removed', 
                     'object_type': 'CollectionItem', 'object_hash': item.hash, 
                     'object_name': item.name, 'link_id': link_id, 'link_url': link_url, 
                     'link_display_name': link_display_name, 'result': 'success', 
                     'function_args': {'hash': hash, 'link_id': link_id}})

    # Return the updated links section
    return render(request, 'partials/_item_links.html', {
        'item': item
    })