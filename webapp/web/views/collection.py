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
from web.models import Collection, CollectionItem, ItemType, ApplicationActivity, RecentActivity

logger = logging.getLogger('webapp')

@login_required
@log_execution_time
def collection_create(request):
    """
    Handles the creation of a new Collection using a function-based view.
    """
    logger.info("Collection creation view accessed by user: '%s' [%s]", request.user.username, request.user.id)
    
    # Log application activity
    ApplicationActivity.log(
        function_name='collection_create',
        message=f"User accessed collection creation form",
        user=request.user,
        meta={'action': 'view_form', 'method': request.method, 'function_args': {'request_method': request.method}}
    )

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
            ApplicationActivity.log(
                function_name='collection_create',
                message=f"Collection '{new_collection.name}' created successfully",
                user=request.user,
                meta={
                    'action': 'created',
                    'object_type': 'Collection',
                    'object_hash': new_collection.hash,
                    'object_name': new_collection.name,
                    'result': 'success',
                    'function_args': {'request_method': request.method}
                }
            )
            
            # Log user activity
            RecentActivity.log_collection_created(
                user=request.user,
                collection_name=new_collection.name
            )
            
            messages.success(request, f"Collection '{new_collection.name}' was created successfully!")
            return redirect(reverse('dashboard'))
        else:
            # Log form validation errors
            ApplicationActivity.log(
                function_name='collection_create',
                message=f"Collection creation failed due to form validation errors",
                user=request.user,
                level=ApplicationActivity.Level.WARNING,
                meta={
                    'action': 'form_validation_failed',
                    'errors': form.errors.as_json(),
                    'result': 'validation_error',
                    'function_args': {'request_method': request.method}
                }
            )

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
        ApplicationActivity.log_info('collection_list_view', 
            f"Collection list accessed - {collections.count()} collections found", 
            user=request.user, meta={
                'action': 'list_view', 'object_type': 'Collection', 
                'collection_count': collections.count(),
                'function_args': {'request_method': request.method}})

        context = {
            'collections': collections,
        }
        logger.info("Rendering collection list for user '%s' [%s]", request.user.username, request.user.id)
        return render(request, 'collection/collection_list.html', context)
        
    except Exception as e:
        ApplicationActivity.log_error('collection_list_view', 
            f"Collection list loading failed: {str(e)}", 
            user=request.user, meta={
                'action': 'list_view_failed', 'error': str(e), 'result': 'system_error',
                'function_args': {'request_method': request.method}})
        raise

@login_required
@log_execution_time
def collection_detail_view(request, hash):
    """
    Displays a single collection and all of its items,
    but ONLY if the collection belongs to the currently logged-in user.
    """
    logger.info("Collection detail view accessed by user: '%s [%s]'", request.user.username, request.user.id)

    try:
        collection = get_object_or_404(
            Collection.objects.annotate(item_count=Count('items')).prefetch_related('images__media_file'),
            hash=hash,
            created_by=request.user
        )
        items = collection.items.order_by('name')

        stats = items.aggregate(
            total_items=Count('id'),
            in_collection_count=Count('id', filter=Q(status=CollectionItem.Status.IN_COLLECTION)),
            wanted_count=Count('id', filter=Q(status=CollectionItem.Status.WANTED)),
            reserved_count=Count('id', filter=Q(status=CollectionItem.Status.RESERVED))
        )

        # Log successful detail view
        ApplicationActivity.log_info('collection_detail_view', 
            f"Collection '{collection.name}' viewed with {stats['total_items']} items", 
            user=request.user, meta={
                'action': 'detail_view', 'object_type': 'Collection',
                'object_hash': collection.hash, 'object_name': collection.name,
                'item_count': stats['total_items'], 'visibility': collection.visibility,
                'function_args': {'hash': hash, 'request_method': request.method}})

        context = {
            'collection': collection,
            'items': items,
            'stats': stats,
            'visibility_choices': Collection.Visibility.choices,
            'item_types': ItemType.objects.all(),
        }

        logger.info("Rendering collection detail for collection '%s' [%s] owned by user '%s' [%s]", collection.name, collection.hash, request.user.username, request.user.id)
        return render(request, 'collection/collection_detail.html', context)
        
    except Exception as e:
        ApplicationActivity.log_warning('collection_detail_view', 
            f"Collection detail access failed for hash '{hash}': {str(e)}", 
            user=request.user, meta={
                'action': 'detail_view_failed', 'object_hash': hash,
                'error': str(e), 'result': 'access_denied_or_error',
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
    ApplicationActivity.log_info('collection_update_view', 
        f"Collection '{collection.name}' update form accessed", 
        user=request.user, meta={
            'action': 'form_access', 'object_type': 'Collection',
            'object_hash': collection.hash, 'object_name': collection.name, 'method': request.method,
            'function_args': {'hash': hash, 'request_method': request.method}})

    if request.method == 'POST':
        logger.info("User '%s [%s]' is submitting an update for collection '%s' [%s]", request.user.username, request.user.id, collection.name, collection.hash)
        form = CollectionForm(request.POST, instance=collection)

        if form.is_valid():
            form.save()

            logger.info("User '%s [%s]' updated collection '%s [%s]'", request.user.username, request.user.id, collection.name, collection.hash)
            
            # Log successful update
            ApplicationActivity.log_info('collection_update_view', 
                f"Collection '{collection.name}' updated successfully", 
                user=request.user, meta={
                    'action': 'updated', 'object_type': 'Collection',
                    'object_hash': collection.hash, 'object_name': collection.name, 'result': 'success',
                    'function_args': {'hash': hash, 'request_method': request.method}})
            
            messages.success(request, f"Collection '{collection.name}' was updated successfully!")
            return redirect(collection.get_absolute_url())
        else:
            # Log form validation errors
            ApplicationActivity.log_warning('collection_update_view', 
                f"Collection '{collection.name}' update failed due to validation errors", 
                user=request.user, meta={
                    'action': 'update_failed', 'object_type': 'Collection',
                    'object_hash': collection.hash, 'object_name': collection.name,
                    'errors': form.errors.as_json(), 'result': 'validation_error',
                    'function_args': {'hash': hash, 'request_method': request.method}})
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
        ApplicationActivity.log_warning('collection_delete_view', 
            f"Collection '{collection.name}' deletion blocked - contains items", 
            user=request.user, meta={
                'action': 'deletion_blocked', 'object_type': 'Collection',
                'object_hash': collection.hash, 'object_name': collection.name, 'result': 'blocked',
                'function_args': {'hash': hash, 'request_method': request.method}})
        
        messages.error(request, "Cannot delete a collection that still contains items.")
        return redirect(collection.get_absolute_url())

    try:
        collection_name = collection.name
        collection_hash = collection.hash
        collection.delete()

        logger.info("User '%s [%s]' deleted collection '%s [%s]'", request.user.username, request.user.id, collection_name, collection_hash)
        
        # Log successful deletion
        ApplicationActivity.log_info('collection_delete_view', 
            f"Collection '{collection_name}' deleted successfully", 
            user=request.user, meta={
                'action': 'deleted', 'object_type': 'Collection',
                'object_hash': collection_hash, 'object_name': collection_name, 'result': 'success',
                'function_args': {'hash': hash, 'request_method': request.method}})
        
        # Log user activity
        RecentActivity.log_collection_deleted(
            user=request.user,
            collection_name=collection_name
        )
        
        messages.success(request, f"Collection '{collection_name}' was successfully deleted.")
        return redirect('collection_list')
        
    except Exception as e:
        ApplicationActivity.log_error('collection_delete_view', 
            f"Collection '{collection.name}' deletion failed: {str(e)}", 
            user=request.user, meta={
                'action': 'deletion_error', 'object_type': 'Collection',
                'object_hash': collection.hash, 'object_name': collection.name,
                'error': str(e), 'result': 'system_error',
                'function_args': {'hash': hash, 'request_method': request.method}})
        raise

