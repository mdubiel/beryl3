# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from web.decorators import log_execution_time
from web.forms import CollectionForm
from web.models import Collection, CollectionItem, ItemType, RecentActivity

logger = logging.getLogger('webapp')


def get_attribute_statistics(items_queryset, collection):
    """
    Task 52: Calculate aggregate statistics for attributes in the collection.
    Returns list of dicts with attribute name, value, count.
    Limits to top 20 most common attribute values.

    Args:
        items_queryset: QuerySet of CollectionItem objects
        collection: Collection object

    Returns:
        list: List of dicts with keys: attribute_name, attribute_id, value, count
    """
    from collections import defaultdict
    from web.models import CollectionItemAttributeValue

    # Get all attribute values for items in queryset
    attribute_values = CollectionItemAttributeValue.objects.filter(
        item__in=items_queryset
    ).select_related('item_attribute').values(
        'item_attribute__display_name',
        'item_attribute__id',
        'value'
    )

    # Aggregate by attribute and value
    stats = defaultdict(lambda: defaultdict(int))

    for av in attribute_values:
        attr_name = av['item_attribute__display_name']
        attr_id = av['item_attribute__id']
        value = av['value']

        # Truncate long values for display
        display_value = value
        if len(display_value) > 30:
            display_value = display_value[:27] + '...'

        stats[(attr_name, attr_id)][value] += 1

    # Convert to list format for template
    result = []
    for (attr_name, attr_id), values in stats.items():
        for value, count in values.items():
            # Truncate value if needed
            display_value = value
            if len(display_value) > 30:
                display_value = display_value[:27] + '...'

            result.append({
                'attribute_name': attr_name,
                'attribute_id': attr_id,
                'value': value,
                'display_value': display_value,
                'count': count
            })

    # Sort by count descending, then by attribute name, limit to top 20
    result.sort(key=lambda x: (-x['count'], x['attribute_name'], x['value']))
    return result[:20]


@login_required
@log_execution_time
def collection_create(request):
    """
    Handles the creation of a new Collection using a function-based view.
    """
    logger.info("Collection creation view accessed by user: '%s' [%s]", request.user.username, request.user.id)
    
    # Log application activity
    logger.info('collection_create: User %s [%s] accessed collection creation form',
               request.user.username, request.user.id,
               extra={'function': 'collection_create', 'action': 'view_form', 
                     'method': request.method, 'function_args': {'request_method': request.method}})

    if request.method == 'POST':
        logger.info("User '%s [%s]' is submitting a new collection form", request.user.username, request.user.id)
        form = CollectionForm(request.POST)

        if form.is_valid():
            new_collection = form.save(commit=False)

            new_collection.owner = request.user
            new_collection.created_by = request.user

            new_collection.save()

            logger.info(
                "User '%s [%s]' created new collection '%s [%s]'",
                request.user.username, request.user.id, new_collection.name, new_collection.hash
            )
            
            # Log successful collection creation
            logger.info('collection_create: Collection "%s" created successfully by user %s [%s]',
                       new_collection.name, request.user.username, request.user.id,
                       extra={'function': 'collection_create', 'action': 'created',
                             'object_type': 'Collection', 'object_hash': new_collection.hash,
                             'object_name': new_collection.name, 'result': 'success',
                             'function_args': {'request_method': request.method}})
            
            # Log user activity
            RecentActivity.log_collection_created(
                user=request.user,
                collection_name=new_collection.name
            )
            
            messages.success(request, f"Collection '{new_collection.name}' was created successfully!")
            return redirect(reverse('dashboard'))
        else:
            # Log form validation errors
            logger.warning('collection_create: Collection creation failed due to form validation errors by user %s [%s]',
                          request.user.username, request.user.id,
                          extra={'function': 'collection_create', 'action': 'form_validation_failed',
                                'errors': form.errors.as_json(), 'result': 'validation_error',
                                'function_args': {'request_method': request.method}})

    # If it's a GET request (or if the form was invalid), display a blank or bound form
    else:
        logger.info("User '%s [%s]' is viewing the collection creation form", request.user.username, request.user.id)
        form = CollectionForm()

    context = {
        'form': form
    }

    logger.info("Rendering collection creation form for user '%s' [%s]", request.user.username, request.user.id)
    return render(request, 'collection/collection_form.html', context)

@login_required
@log_execution_time
def collection_list_view(request):
    """
    Displays a list of all collections owned by the logged-in user.
    """
    logger.info("Collection list view accessed by user: '%s [%s]'", request.user.username, request.user.id)
    
    try:
        collections = Collection.objects.filter(created_by=request.user).annotate(
            item_count=Count('items')
        ).order_by('-updated')

        # Log successful list view
        logger.info('collection_list_view: Collection list accessed - %d collections found by user %s [%s]',
                   collections.count(), request.user.username, request.user.id,
                   extra={'function': 'collection_list_view', 'action': 'list_view', 
                         'object_type': 'Collection', 'collection_count': collections.count(),
                         'function_args': {'request_method': request.method}})

        context = {
            'collections': collections,
        }
        logger.info("Rendering collection list for user '%s' [%s]", request.user.username, request.user.id)
        return render(request, 'collection/collection_list.html', context)
        
    except Exception as e:
        logger.error('collection_list_view: Collection list loading failed: %s by user %s [%s]',
                    str(e), request.user.username, request.user.id,
                    extra={'function': 'collection_list_view', 'action': 'list_view_failed', 
                          'error': str(e), 'result': 'system_error',
                          'function_args': {'request_method': request.method}})
        raise

@login_required
@log_execution_time
def collection_detail_view(request, hash):
    """
    Displays a single collection and all of its items,
    but ONLY if the collection belongs to the currently logged-in user.
    Supports filtering by status, item type, and search query.
    Supports pagination.
    """
    logger.info("Collection detail view accessed by user: '%s [%s]'", request.user.username, request.user.id)

    try:
        collection = get_object_or_404(
            Collection.objects.annotate(item_count=Count('items')).prefetch_related('images__media_file'),
            hash=hash,
            created_by=request.user
        )

        # Start with base queryset
        items = collection.items.all()

        # Task 45: Apply filters
        filter_status = request.GET.get('status', '')
        filter_item_type = request.GET.get('item_type', '')
        filter_search = request.GET.get('search', '')

        # Task 52: Add attribute filter
        filter_attribute = request.GET.get('attribute', '')
        filter_attribute_value = request.GET.get('attribute_value', '')

        if filter_status and filter_status in dict(CollectionItem.Status.choices):
            items = items.filter(status=filter_status)

        if filter_item_type:
            if filter_item_type == 'none':
                items = items.filter(item_type__isnull=True)
            else:
                items = items.filter(item_type_id=filter_item_type)

        if filter_search:
            items = items.filter(
                Q(name__icontains=filter_search) |
                Q(description__icontains=filter_search)
            )

        # Task 52: Apply attribute filter
        if filter_attribute and filter_attribute_value:
            from web.models import CollectionItemAttributeValue
            items = items.filter(
                attribute_values__item_attribute_id=filter_attribute,
                attribute_values__value=filter_attribute_value
            ).distinct()

        # Order items
        items = items.order_by('name')

        # Calculate stats before pagination
        stats = items.aggregate(
            total_items=Count('id'),
            in_collection_count=Count('id', filter=Q(status=CollectionItem.Status.IN_COLLECTION)),
            wanted_count=Count('id', filter=Q(status=CollectionItem.Status.WANTED)),
            reserved_count=Count('id', filter=Q(status=CollectionItem.Status.RESERVED))
        )

        # Task 52: Calculate attribute statistics
        attribute_stats = get_attribute_statistics(items, collection)

        # Task 45: Get available statuses and item types in collection (before filtering)
        all_items = collection.items.all()
        available_statuses = list(all_items.values_list('status', flat=True).distinct())
        available_item_types = ItemType.objects.filter(
            id__in=all_items.exclude(item_type__isnull=True).values_list('item_type_id', flat=True).distinct()
        ).order_by('display_name')
        has_items_without_type = all_items.filter(item_type__isnull=True).exists()

        # Task 45: Get available attributes for filtering
        from web.models import ItemAttribute
        available_attributes = ItemAttribute.objects.filter(
            id__in=all_items.values_list('attribute_values__item_attribute_id', flat=True).distinct()
        ).order_by('display_name')

        # Task 45: Get available values for selected attribute
        available_attribute_values = []
        if filter_attribute:
            from web.models import CollectionItemAttributeValue
            available_attribute_values = CollectionItemAttributeValue.objects.filter(
                item__collection=collection,
                item_attribute_id=filter_attribute
            ).values_list('value', flat=True).distinct().order_by('value')

        # Task 47: Apply grouping if enabled
        grouped_items = None
        if collection.group_by != Collection.GroupBy.NONE:
            from collections import defaultdict
            from web.models import CollectionItemAttributeValue

            groups = defaultdict(list)
            ungrouped_items = []

            if collection.group_by == Collection.GroupBy.ITEM_TYPE:
                # Group by item type
                for item in items:
                    if item.item_type:
                        groups[item.item_type.display_name].append(item)
                    else:
                        ungrouped_items.append(item)

                grouped_items = [
                    {'attribute_name': 'Item Type', 'attribute_value': group_name, 'items': group_items}
                    for group_name, group_items in groups.items()
                ]

            elif collection.group_by == Collection.GroupBy.STATUS:
                # Group by status
                for item in items:
                    status_label = dict(CollectionItem.Status.choices).get(item.status, item.status)
                    groups[item.status].append(item)

                grouped_items = [
                    {'attribute_name': 'Status', 'attribute_value': dict(CollectionItem.Status.choices).get(status, status), 'items': group_items}
                    for status, group_items in groups.items()
                ]

            elif collection.group_by == Collection.GroupBy.ATTRIBUTE and collection.grouping_attribute:
                # Group by specific attribute
                for item in items:
                    try:
                        attr_value = CollectionItemAttributeValue.objects.get(
                            item=item,
                            item_attribute=collection.grouping_attribute
                        )
                        group_key = attr_value.value
                        groups[group_key].append(item)
                    except CollectionItemAttributeValue.DoesNotExist:
                        ungrouped_items.append(item)

                grouped_items = [
                    {'attribute_name': collection.grouping_attribute.display_name, 'attribute_value': group_key, 'items': group_items}
                    for group_key, group_items in groups.items()
                ]

            # Sort groups
            if grouped_items:
                grouped_items.sort(key=lambda x: str(x['attribute_value']))

            # Sort items within each group
            if grouped_items:
                for group in grouped_items:
                    if collection.sort_by == Collection.SortBy.NAME:
                        group['items'].sort(key=lambda x: x.name.lower())
                    elif collection.sort_by == Collection.SortBy.CREATED:
                        group['items'].sort(key=lambda x: x.created, reverse=True)
                    elif collection.sort_by == Collection.SortBy.UPDATED:
                        group['items'].sort(key=lambda x: x.updated, reverse=True)
                    elif collection.sort_by == Collection.SortBy.ATTRIBUTE and collection.sort_attribute:
                        # Sort by attribute value
                        def get_attr_value(item):
                            try:
                                attr_val = CollectionItemAttributeValue.objects.get(
                                    item=item,
                                    item_attribute=collection.sort_attribute
                                )
                                value = attr_val.get_typed_value()
                                # Handle different types for sorting
                                if isinstance(value, (int, float)):
                                    return (0, value)  # Numbers first, sorted numerically
                                elif isinstance(value, str):
                                    # Try to convert to number for numeric strings
                                    try:
                                        return (0, float(value))
                                    except (ValueError, TypeError):
                                        return (1, value.lower())  # Strings second, case-insensitive
                                else:
                                    return (2, str(value))  # Others last
                            except CollectionItemAttributeValue.DoesNotExist:
                                return (3, '')  # Items without the attribute at the end
                        group['items'].sort(key=get_attr_value)

            # Add ungrouped items as a special group if any exist
            if ungrouped_items:
                if collection.sort_by == Collection.SortBy.NAME:
                    ungrouped_items.sort(key=lambda x: x.name.lower())
                grouped_items.append({
                    'attribute_name': 'Other Items',
                    'attribute_value': None,
                    'items': ungrouped_items
                })

        # Task 46: Add pagination
        from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

        items_per_page = request.GET.get('per_page', '25')
        try:
            items_per_page = int(items_per_page)
            if items_per_page not in [10, 25, 50, 100]:
                items_per_page = 25
        except (ValueError, TypeError):
            items_per_page = 25

        paginator = Paginator(items, items_per_page)
        page_number = request.GET.get('page', 1)

        try:
            items_page = paginator.page(page_number)
        except PageNotAnInteger:
            items_page = paginator.page(1)
        except EmptyPage:
            items_page = paginator.page(paginator.num_pages)

        # Log successful detail view
        logger.info('collection_detail_view: Collection "%s" viewed with %d items (page %s of %s) by user %s [%s]',
                   collection.name, stats['total_items'], items_page.number, paginator.num_pages,
                   request.user.username, request.user.id,
                   extra={'function': 'collection_detail_view', 'action': 'detail_view',
                         'object_type': 'Collection', 'object_hash': collection.hash,
                         'object_name': collection.name, 'item_count': stats['total_items'],
                         'visibility': collection.visibility, 'function_args': {'hash': hash, 'request_method': request.method}})

        context = {
            'collection': collection,
            'items': items_page,
            'stats': stats,
            'visibility_choices': Collection.Visibility.choices,
            'item_types': ItemType.objects.all(),
            'available_statuses': available_statuses,
            'available_item_types': available_item_types,
            'has_items_without_type': has_items_without_type,
            'available_attributes': available_attributes,
            'available_attribute_values': available_attribute_values,
            'filter_status': filter_status,
            'filter_item_type': filter_item_type,
            'filter_search': filter_search,
            'filter_attribute': filter_attribute,
            'filter_attribute_value': filter_attribute_value,
            'items_per_page': items_per_page,
            'grouped_items': grouped_items,
            'attribute_stats': attribute_stats,
        }

        logger.info("Rendering collection detail for collection '%s' [%s] owned by user '%s' [%s]", collection.name, collection.hash, request.user.username, request.user.id)
        return render(request, 'collection/collection_detail.html', context)
        
    except Exception as e:
        logger.warning('collection_detail_view: Collection detail access failed for hash "%s": %s by user %s [%s]',
                      hash, str(e), request.user.username, request.user.id,
                      extra={'function': 'collection_detail_view', 'action': 'detail_view_failed', 
                            'object_hash': hash, 'error': str(e), 'result': 'access_denied_or_error',
                            'function_args': {'hash': hash, 'request_method': request.method}})
        raise

@login_required
@log_execution_time
def collection_update_view(request, hash):
    """
    Handles editing an existing Collection using a function-based view.
    """
    logger.info("Collection update view accessed by user: '%s' [%s]", request.user.username, request.user.id)
    collection = get_object_or_404(Collection, hash=hash, created_by=request.user)

    # Log form access
    logger.info('collection_update_view: Collection "%s" update form accessed by user %s [%s]',
               collection.name, request.user.username, request.user.id,
               extra={'function': 'collection_update_view', 'action': 'form_access', 
                     'object_type': 'Collection', 'object_hash': collection.hash, 
                     'object_name': collection.name, 'method': request.method,
                     'function_args': {'hash': hash, 'request_method': request.method}})

    if request.method == 'POST':
        logger.info("User '%s [%s]' is submitting an update for collection '%s' [%s]", request.user.username, request.user.id, collection.name, collection.hash)
        form = CollectionForm(request.POST, instance=collection)

        if form.is_valid():
            form.save()

            logger.info("User '%s [%s]' updated collection '%s [%s]'", request.user.username, request.user.id, collection.name, collection.hash)
            
            # Log successful update
            logger.info('collection_update_view: Collection "%s" updated successfully by user %s [%s]',
                       collection.name, request.user.username, request.user.id,
                       extra={'function': 'collection_update_view', 'action': 'updated', 
                             'object_type': 'Collection', 'object_hash': collection.hash, 
                             'object_name': collection.name, 'result': 'success',
                             'function_args': {'hash': hash, 'request_method': request.method}})
            
            messages.success(request, f"Collection '{collection.name}' was updated successfully!")
            return redirect(collection.get_absolute_url())
        else:
            # Log form validation errors
            logger.warning('collection_update_view: Collection "%s" update failed due to validation errors by user %s [%s]',
                          collection.name, request.user.username, request.user.id,
                          extra={'function': 'collection_update_view', 'action': 'update_failed', 
                                'object_type': 'Collection', 'object_hash': collection.hash, 
                                'object_name': collection.name, 'errors': form.errors.as_json(), 
                                'result': 'validation_error', 'function_args': {'hash': hash, 'request_method': request.method}})
    else:
        logger.info("User '%s [%s]' is viewing the update form for collection '%s' [%s]", request.user.username, request.user.id, collection.name, collection.hash)
        form = CollectionForm(instance=collection)

    context = {
        'form': form,
        'collection': collection, 
    }
    logger.info("Rendering collection update form for collection '%s' [%s] owned by user '%s' [%s]", collection.name, collection.hash, request.user.username, request.user.id)
    return render(request, 'collection/collection_form.html', context)

@login_required
@require_POST
@log_execution_time
def collection_delete_view(request, hash):
    """
    Handles the soft-deletion of a Collection object.
    """
    logger.info("Collection delete view accessed by user: '%s [%s]'", request.user.username, request.user.id)

    collection = get_object_or_404(Collection, hash=hash, created_by=request.user)

    if not collection.can_be_deleted:
        logger.warning("User '%s [%s]' attempted to delete collection '%s [%s]' with items.", request.user.username, request.user.id, collection.name, collection.hash)
        
        # Log deletion blocked
        logger.warning('collection_delete_view: Collection "%s" deletion blocked - contains items by user %s [%s]',
                      collection.name, request.user.username, request.user.id,
                      extra={'function': 'collection_delete_view', 'action': 'deletion_blocked', 
                            'object_type': 'Collection', 'object_hash': collection.hash, 
                            'object_name': collection.name, 'result': 'blocked',
                            'function_args': {'hash': hash, 'request_method': request.method}})
        
        messages.error(request, "Cannot delete a collection that still contains items.")
        return redirect(collection.get_absolute_url())

    try:
        collection_name = collection.name
        collection_hash = collection.hash
        collection.delete()

        logger.info("User '%s [%s]' deleted collection '%s [%s]'", request.user.username, request.user.id, collection_name, collection_hash)
        
        # Log successful deletion
        logger.info('collection_delete_view: Collection "%s" deleted successfully by user %s [%s]',
                   collection_name, request.user.username, request.user.id,
                   extra={'function': 'collection_delete_view', 'action': 'deleted', 
                         'object_type': 'Collection', 'object_hash': collection_hash, 
                         'object_name': collection_name, 'result': 'success',
                         'function_args': {'hash': hash, 'request_method': request.method}})
        
        # Log user activity
        RecentActivity.log_collection_deleted(
            user=request.user,
            collection_name=collection_name
        )
        
        messages.success(request, f"Collection '{collection_name}' was successfully deleted.")
        return redirect('collection_list')
        
    except Exception as e:
        logger.error('collection_delete_view: Collection "%s" deletion failed: %s by user %s [%s]',
                    collection.name, str(e), request.user.username, request.user.id,
                    extra={'function': 'collection_delete_view', 'action': 'deletion_error', 
                          'object_type': 'Collection', 'object_hash': collection.hash, 
                          'object_name': collection.name, 'error': str(e), 'result': 'system_error',
                          'function_args': {'hash': hash, 'request_method': request.method}})
        raise

