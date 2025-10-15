# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging
import random

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from post_office import mail
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from faker import Faker

from web.models import Collection, CollectionItem, RecentActivity, ItemType

logger = logging.getLogger("webapp") # Ensure logger is initialized

def public_collection_view(request, hash):
    """
    Displays a collection to the public if its visibility is set to
    'PUBLIC' or 'UNLISTED'.
    """
    collection = get_object_or_404(
        Collection.objects.select_related('created_by__profile'), 
        hash=hash
    )

    # Only allow access if the collection is not private.
    if collection.visibility == Collection.Visibility.PRIVATE:
        # Log access denied to private collection
        logger.warning('public_collection_view: Access denied to private collection "%s" by anonymous user',
                      collection.name,
                      extra={'function': 'public_collection_view', 'action': 'access_denied', 
                            'object_type': 'Collection', 'object_hash': collection.hash, 
                            'object_name': collection.name, 'visibility': collection.visibility, 
                            'result': 'access_denied', 'function_args': {'hash': hash, 'request_method': request.method}})
        
        # We raise Http404 to avoid leaking the existence of private collections.
        raise Http404("Collection not found or is private.")
    
    # Log successful public collection access
    logger.info('public_collection_view: Public collection "%s" viewed by anonymous user',
               collection.name,
               extra={'function': 'public_collection_view', 'action': 'public_view', 
                     'object_type': 'Collection', 'object_hash': collection.hash, 
                     'object_name': collection.name, 'visibility': collection.visibility, 
                     'viewer_type': 'anonymous', 'function_args': {'hash': hash, 'request_method': request.method}})
    
    # Get items and calculate stats similar to private view
    all_items = collection.items.select_related('item_type').prefetch_related(
        'images__media_file',
        'links',
        'default_image__media_file'
    ).order_by('name')

    stats = all_items.aggregate(
        total_items=Count('id'),
        in_collection_count=Count('id', filter=Q(status=CollectionItem.Status.IN_COLLECTION)),
        wanted_count=Count('id', filter=Q(status=CollectionItem.Status.WANTED)),
        reserved_count=Count('id', filter=Q(status=CollectionItem.Status.RESERVED))
    )

    # Get item type distribution for all items (not paginated)
    item_type_distribution = all_items.values('item_type__display_name', 'item_type__icon').annotate(
        count=Count('id')
    ).order_by('-count')

    # Task 47: Apply grouping if enabled (same logic as collection_detail_view)
    grouped_items = None
    if collection.group_by != Collection.GroupBy.NONE:
        from collections import defaultdict
        from web.models import CollectionItemAttributeValue

        groups = defaultdict(list)
        ungrouped_items = []

        for item in all_items:
            if collection.group_by == Collection.GroupBy.ITEM_TYPE:
                if item.item_type:
                    groups[item.item_type.display_name].append(item)
                else:
                    ungrouped_items.append(item)
            elif collection.group_by == Collection.GroupBy.STATUS:
                status_label = dict(CollectionItem.Status.choices).get(item.status, item.status)
                groups[item.status].append(item)
            elif collection.group_by == Collection.GroupBy.ATTRIBUTE and collection.grouping_attribute:
                try:
                    attr_value = CollectionItemAttributeValue.objects.get(
                        item=item,
                        item_attribute=collection.grouping_attribute
                    )
                    groups[attr_value.value].append(item)
                except CollectionItemAttributeValue.DoesNotExist:
                    ungrouped_items.append(item)

        # Create grouped items list
        if collection.group_by == Collection.GroupBy.ITEM_TYPE:
            grouped_items = [
                {'attribute_name': 'Item Type', 'attribute_value': group_name, 'items': group_items}
                for group_name, group_items in groups.items()
            ]
        elif collection.group_by == Collection.GroupBy.STATUS:
            grouped_items = [
                {'attribute_name': 'Status', 'attribute_value': dict(CollectionItem.Status.choices).get(status, status), 'items': group_items}
                for status, group_items in groups.items()
            ]
        elif collection.group_by == Collection.GroupBy.ATTRIBUTE and collection.grouping_attribute:
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

        # Add ungrouped items
        if ungrouped_items:
            if collection.sort_by == Collection.SortBy.NAME:
                ungrouped_items.sort(key=lambda x: x.name.lower())
            grouped_items.append({
                'attribute_name': 'Other Items',
                'attribute_value': None,
                'items': ungrouped_items
            })

    # Pagination - handle both grouped and ungrouped views
    items_per_page = request.GET.get('per_page', '25')
    try:
        items_per_page = int(items_per_page)
        if items_per_page not in [10, 25, 50, 100]:
            items_per_page = 25
    except (ValueError, TypeError):
        items_per_page = 25

    # If grouping is enabled, don't paginate (show all groups)
    if grouped_items:
        page_obj = None
    else:
        # Regular pagination for ungrouped items
        paginator = Paginator(all_items, items_per_page)
        page_number = request.GET.get('page', 1)

        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

    fake = Faker()
    dummy_name = fake.name()

    # Task 62: Collect all available images for random background selection
    background_image_url = None
    available_images = []

    # Add collection images from MediaFile (uploaded images)
    for collection_image in collection.images.all():
        if collection_image.media_file and collection_image.media_file.file_exists:
            available_images.append(collection_image.media_file.file_url)

    # Add collection image_url if exists (fallback for URL-based images)
    # Skip placeholder images from placehold.co
    if collection.image_url and 'placehold.co' not in collection.image_url:
        available_images.append(collection.image_url)

    # Add all item images from MediaFile (uploaded images)
    for item in all_items:
        for item_image in item.images.all():
            if item_image.media_file and item_image.media_file.file_exists:
                available_images.append(item_image.media_file.file_url)

        # Also add item image_url if exists (fallback for URL-based images)
        # Skip placeholder images from placehold.co
        if item.image_url and 'placehold.co' not in item.image_url:
            available_images.append(item.image_url)

    # Select random image for background
    if available_images:
        background_image_url = random.choice(available_images)
        logger.info(
            'public_collection_view: Selected random background image for collection "%s"',
            collection.name,
            extra={
                'function': 'public_collection_view',
                'action': 'select_background_image',
                'collection_hash': collection.hash,
                'total_images': len(available_images),
                'selected_image': background_image_url
            }
        )

    context = {
        "collection": collection,
        "items": page_obj if page_obj else all_items,  # Paginated or all items
        "page_obj": page_obj,  # For pagination controls (None if grouped)
        "stats": stats,
        "item_type_distribution": item_type_distribution,
        "dummy_name": dummy_name,
        "item_types": ItemType.objects.all(),
        "grouped_items": grouped_items,
        "items_per_page": items_per_page,
        "background_image_url": background_image_url,  # Task 62
    }
    return render(request, "public/collection_public_detail.html", context)

@require_POST
@login_required
@transaction.atomic
def book_item_authenticated(request, hash):
    """
    Handles HTMX POST request to book an item for the authenticated user.
    Replaces the item element with its new status on success.
    """
    logger.info("Authenticated booking request for CollectionItem '%s' by user '%s' [%s]", hash, request.user.username, request.user.id)
    
    item = get_object_or_404(CollectionItem, hash=hash)

    # Check if the item is still bookable (race condition check)
    if not item.is_bookable:
        logger.warning("Attempt to book non-bookable CollectionItem '%s' [%s] by user '%s' [%s]", item.name, item.hash, request.user.username, request.user.id)
        response = render(request, 'partials/_item_status_and_button.html', {'item': item, 'request': request})
        response.status_code = 400
        return response

    # Update item status and reservation details
    item.status = CollectionItem.Status.RESERVED
    item.reserved_date = timezone.now()
    item.reserved_by_name = request.user.get_full_name() or request.user.username
    item.reserved_by_email = request.user.email
    item.save()

    # Log activity
    RecentActivity.log_item_reserved_by_user(
        collection_owner=item.collection.created_by,
        item_name=item.name
    )

    logger.info("User '%s' [%s] successfully reserved CollectionItem '%s' [%s]", request.user.username, request.user.id, item.name, item.hash)
    
    # Return the updated item partial for HTMX to replace
    return render(request, 'partials/_item_status_and_button.html', {'item': item, 'request': request})

@require_POST
@transaction.atomic
def book_item_guest(request, hash):
    """
    Handles guest booking using email address with confirmation email.
    """
    logger.info("Guest booking request for CollectionItem '%s'", hash)
    
    item = get_object_or_404(CollectionItem, hash=hash)
    guest_email = request.POST.get('email', '').strip()

    # Email validation
    if not guest_email:
        logger.warning("Guest booking attempted without email for item '%s' [%s]", item.name, item.hash)
        response = HttpResponseBadRequest("Email is required.")
        return response
    
    # Basic email format validation
    try:
        validate_email(guest_email)
    except ValidationError:
        logger.warning("Invalid email '%s' provided for guest booking of item '%s' [%s]", guest_email, item.name, item.hash)
        return HttpResponseBadRequest("Please provide a valid email address.")

    if not item.is_bookable:
        logger.warning("Attempt to book non-bookable item '%s' [%s] by guest email '%s'", item.name, item.hash, guest_email)
        response = render(request, 'partials/_item_status_and_button.html', {'item': item})
        response.status_code = 400
        return response

    # Generate reservation token and update item
    reservation_token = item.generate_guest_reservation_token()
    item.status = CollectionItem.Status.RESERVED
    item.reserved_date = timezone.now()
    item.reserved_by_email = guest_email
    item.guest_reservation_token = reservation_token
    item.save()

    # Log activity for guest user
    RecentActivity.log_item_reserved_by_guest(
        collection_owner=item.collection.created_by,
        item_name=item.name
    )
    
    # Send confirmation email
    _send_guest_reservation_confirmation(item, guest_email, reservation_token, request)
    
    logger.info("Guest '%s' successfully reserved CollectionItem '%s' [%s]", guest_email, item.name, item.hash)
    
    return render(request, 'partials/_item_status_and_button.html', {'item': item})


def _send_guest_reservation_confirmation(item, guest_email, reservation_token, request):
    """
    Send confirmation email to guest with unreservation link
    """
    try:
        unreserve_url = request.build_absolute_uri(
            reverse('unreserve_guest_item', kwargs={
                'hash': item.hash, 
                'token': reservation_token
            })
        )
        
        subject = f"Reservation Confirmation: {item.name}"
        
        # Plain text email content
        message = f"""
Hi there!

Your reservation for "{item.name}" from the collection "{item.collection.name}" has been confirmed.

If you need to cancel your reservation, you can do so by clicking this link:
{unreserve_url}

Collection Owner: {item.collection.created_by.username}

Thank you!
"""
        
        # HTML email content
        html_message = render_to_string('emails/guest_reservation_confirmation.html', {
            'item': item,
            'collection': item.collection,
            'unreserve_url': unreserve_url,
            'guest_email': guest_email,
        })
        
        mail.send(
            recipients=[guest_email],
            sender=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            subject=subject,
            message=message,
            html_message=html_message,
            priority='high',  # High priority for reservation confirmations
        )
        
        logger.info("Confirmation email sent to '%s' for reservation of item '%s' [%s]", guest_email, item.name, item.hash)
        
    except Exception as e:
        logger.error("Failed to send confirmation email to '%s' for item '%s' [%s]: %s", guest_email, item.name, item.hash, str(e))


def unreserve_guest_item(request, hash, token):
    """
    Allows guests to unreserve items using the token from their email
    """
    logger.info("Guest unreservation attempt for item '%s' with token '%s'", hash, token)
    
    item = get_object_or_404(CollectionItem, hash=hash)
    
    # Verify token and that item is reserved by guest
    if (item.status != CollectionItem.Status.RESERVED or 
        item.guest_reservation_token != token or 
        not item.guest_reservation_token):
        logger.warning("Invalid unreservation attempt for item '%s' [%s] with token '%s'", item.name, item.hash, token)
        return render(request, 'public/unreserve_error.html', {
            'item': item,
            'error': 'Invalid or expired reservation link.'
        })
    
    # Unreserve the item
    guest_email = item.reserved_by_email
    if item.unreserve_guest():
        # Log the unreservation
        RecentActivity.log_item_unreserved(
            collection_owner=item.collection.created_by,
            item_name=item.name
        )
        
        logger.info("Guest '%s' successfully unreserved item '%s' [%s]", guest_email, item.name, item.hash)
        
        return render(request, 'public/unreserve_success.html', {
            'item': item,
            'collection': item.collection,
            'guest_email': guest_email,
        })
    else:
        logger.error("Failed to unreserve item '%s' [%s] for guest '%s'", item.name, item.hash, guest_email)
        return render(request, 'public/unreserve_error.html', {
            'item': item,
            'error': 'Unable to cancel reservation. Please contact the collection owner.'
        })
