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
from django.urls import reverse
from django.db.models import Count, Q
from web.models import Collection, CollectionItem
from web.decorators import log_execution_time
from web.forms import CollectionForm

logger = logging.getLogger('webapp')

@login_required
@log_execution_time
def collection_create(request):
    """
    Handles the creation of a new Collection using a function-based view.
    """
    logger.info("Collection creation view accessed by user: '%s' [%s]", request.user.username, request.user.id)

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
            messages.success(request, f"Collection '{new_collection.name}' was created successfully!")
            return redirect(reverse('dashboard'))

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
    collections = Collection.objects.filter(created_by=request.user).annotate(
        item_count=Count('items')
    ).order_by('-updated')

    context = {
        'collections': collections,
    }
    logger.info("Rendering collection list for user '%s' [%s]", request.user.username, request.user.id)
    return render(request, 'collection/collection_list.html', context)

@login_required
@log_execution_time
def collection_detail_view(request, hash):
    """
    Displays a single collection and all of its items,
    but ONLY if the collection belongs to the currently logged-in user.
    """
    logger.info("Collection detail view accessed by user: '%s [%s]'", request.user.username, request.user.id)

    collection = get_object_or_404(
        Collection.objects.annotate(item_count=Count('items')),
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

    context = {
        'collection': collection,
        'items': items,
        'stats': stats,
    }

    logger.info("Rendering collection detail for collection '%s' [%s] owned by user '%s' [%s]", collection.name, collection.hash, request.user.username, request.user.id)
    return render(request, 'collection/collection_detail.html', context)

@login_required
@log_execution_time
def collection_update_view(request, hash):
    """
    Handles editing an existing Collection using a function-based view.
    """
    logger.info("Collection update view accessed by user: '%s' [%s]", request.user.username, request.user.id)
    collection = get_object_or_404(Collection, hash=hash, created_by=request.user)

    if request.method == 'POST':
        logger.info("User '%s [%s]' is submitting an update for collection '%s' [%s]", request.user.username, request.user.id, collection.name, collection.hash)
        form = CollectionForm(request.POST, instance=collection)

        if form.is_valid():
            form.save()

            logger.info("User '%s [%s]' updated collection '%s [%s]'", request.user.username, request.user.id, collection.name, collection.hash)
            messages.success(request, f"Collection '{collection.name}' was updated successfully!")
            return redirect(collection.get_absolute_url())
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
        messages.error(request, "Cannot delete a collection that still contains items.")
        return redirect(collection.get_absolute_url())

    collection_name = collection.name
    collection.delete()

    logger.info("User '%s [%s]' deleted collection '%s [%s]'", request.user.username, request.user.id, collection_name, collection.hash)
    messages.success(request, "Collection '%s [%s]' was successfully deleted.", collection_name, collection.hash)

    return redirect('collection_list')