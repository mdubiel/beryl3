# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from post_office import mail
from django.core.validators import validate_email
from django.db import transaction
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from faker import Faker

from web.models import Collection, CollectionItem, RecentActivity, ItemType, ApplicationActivity

logger = logging.getLogger("webapp") # Ensure logger is initialized

def public_collection_view(request, hash):
    """
    Displays a collection to the public if its visibility is set to
    'PUBLIC' or 'UNLISTED'.
    """
    collection = get_object_or_404(Collection, hash=hash)

    # Only allow access if the collection is not private.
    if collection.visibility == Collection.Visibility.PRIVATE:
        # Log access denied to private collection
        ApplicationActivity.log_warning('public_collection_view', 
            f"Access denied to private collection '{collection.name}'", 
            user=None, meta={
                'action': 'access_denied', 'object_type': 'Collection',
                'object_hash': collection.hash, 'object_name': collection.name,
                'visibility': collection.visibility, 'result': 'access_denied',
                'function_args': {'hash': hash, 'request_method': request.method}})
        
        # We raise Http404 to avoid leaking the existence of private collections.
        raise Http404("Collection not found or is private.")
    
    # Log successful public collection access
    ApplicationActivity.log_info('public_collection_view', 
        f"Public collection '{collection.name}' viewed by anonymous user", 
        user=None, meta={
            'action': 'public_view', 'object_type': 'Collection',
            'object_hash': collection.hash, 'object_name': collection.name,
            'visibility': collection.visibility, 'viewer_type': 'anonymous',
            'function_args': {'hash': hash, 'request_method': request.method}})
    
    fake = Faker()
    dummy_name = fake.name()

    context = {
        "collection": collection,
        "items": collection.items.all().order_by("name"),
        "dummy_name": dummy_name,
        "item_types": ItemType.objects.all(),
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
