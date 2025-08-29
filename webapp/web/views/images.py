# -*- coding: utf-8 -*-

"""
Image management views for Collections and CollectionItems.
Handles image uploads, management, and HTMX dynamic operations.
"""

import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from ..models import Collection, CollectionItem, MediaFile, CollectionImage, CollectionItemImage, ApplicationActivity
from ..forms import ImageUploadForm
from ..decorators import owner_required

logger = logging.getLogger("webapp")


@login_required
@owner_required('collection')
def collection_manage_images(request, hash):
    """
    Manage images for a collection - show current images and upload form
    """
    collection = get_object_or_404(Collection, hash=hash)
    
    # Get existing images ordered by order field
    current_images = CollectionImage.objects.filter(collection=collection).order_by('order')
    can_add_more = CollectionImage.can_add_image(collection)
    
    if request.method == 'POST':
        if not can_add_more:
            messages.error(request, 'This collection already has the maximum of 3 images.')
            return redirect('collection_manage_images', hash=hash)
        
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create MediaFile
                    media_file = form.save_media_file(
                        user=request.user,
                        media_type=MediaFile.MediaType.COLLECTION_HEADER
                    )
                    
                    # Create CollectionImage relationship
                    next_order = current_images.count()
                    collection_image = CollectionImage.objects.create(
                        collection=collection,
                        media_file=media_file,
                        order=next_order
                    )
                    
                    messages.success(request, f'Image "{media_file.original_filename}" added successfully!')
                    logger.info(f"User {request.user.email} added image to Collection {collection.hash}")
                    
                    # Log application activity
                    ApplicationActivity.log_info(
                        'collection_image_upload',
                        f'Added image "{media_file.original_filename}" to Collection {collection.name}',
                        user=request.user,
                        meta={
                            'collection_hash': collection.hash,
                            'media_file_hash': media_file.hash,
                            'filename': media_file.original_filename,
                            'file_size': media_file.file_size,
                            'image_order': next_order
                        }
                    )
                    
                    return redirect('collection_manage_images', hash=hash)
                    
            except ValidationError as e:
                messages.error(request, str(e))
                ApplicationActivity.log_warning(
                    'collection_image_upload_validation_error',
                    f'Validation error uploading image to Collection {collection.name}: {str(e)}',
                    user=request.user,
                    meta={'collection_hash': collection.hash, 'error': str(e)}
                )
            except Exception as e:
                logger.error(f"Error uploading image for Collection {collection.hash}: {str(e)}")
                messages.error(request, 'An error occurred while uploading the image.')
                ApplicationActivity.log_error(
                    'collection_image_upload_error',
                    f'Error uploading image to Collection {collection.name}: {str(e)}',
                    user=request.user,
                    meta={'collection_hash': collection.hash, 'error': str(e)}
                )
    else:
        form = ImageUploadForm()
    
    return render(request, 'collection/manage_images.html', {
        'collection': collection,
        'current_images': current_images,
        'can_add_more': can_add_more,
        'form': form,
        'max_images': 3,
    })


@login_required
@owner_required('item')
def item_manage_images(request, hash):
    """
    Manage images for a collection item - show current images and upload form
    """
    item = get_object_or_404(CollectionItem, hash=hash)
    
    # Get existing images ordered by order field
    current_images = CollectionItemImage.objects.filter(item=item).order_by('order')
    can_add_more = CollectionItemImage.can_add_image(item)
    
    if request.method == 'POST':
        if not can_add_more:
            messages.error(request, 'This item already has the maximum of 3 images.')
            return redirect('item_manage_images', hash=hash)
        
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create MediaFile
                    media_file = form.save_media_file(
                        user=request.user,
                        media_type=MediaFile.MediaType.COLLECTION_ITEM
                    )
                    
                    # Create CollectionItemImage relationship
                    next_order = current_images.count()
                    item_image = CollectionItemImage.objects.create(
                        item=item,
                        media_file=media_file,
                        order=next_order
                    )
                    
                    messages.success(request, f'Image "{media_file.original_filename}" added successfully!')
                    logger.info(f"User {request.user.email} added image to CollectionItem {item.hash}")
                    
                    # Log application activity
                    ApplicationActivity.log_info(
                        'item_image_upload',
                        f'Added image "{media_file.original_filename}" to Item {item.name}',
                        user=request.user,
                        meta={
                            'item_hash': item.hash,
                            'collection_hash': item.collection.hash,
                            'media_file_hash': media_file.hash,
                            'filename': media_file.original_filename,
                            'file_size': media_file.file_size,
                            'image_order': next_order
                        }
                    )
                    
                    return redirect('item_manage_images', hash=hash)
                    
            except ValidationError as e:
                messages.error(request, str(e))
                ApplicationActivity.log_warning(
                    'item_image_upload_validation_error',
                    f'Validation error uploading image to Item {item.name}: {str(e)}',
                    user=request.user,
                    meta={'item_hash': item.hash, 'collection_hash': item.collection.hash, 'error': str(e)}
                )
            except Exception as e:
                logger.error(f"Error uploading image for CollectionItem {item.hash}: {str(e)}")
                messages.error(request, 'An error occurred while uploading the image.')
                ApplicationActivity.log_error(
                    'item_image_upload_error',
                    f'Error uploading image to Item {item.name}: {str(e)}',
                    user=request.user,
                    meta={'item_hash': item.hash, 'collection_hash': item.collection.hash, 'error': str(e)}
                )
    else:
        form = ImageUploadForm()
    
    return render(request, 'items/manage_images.html', {
        'item': item,
        'collection': item.collection,
        'current_images': current_images,
        'can_add_more': can_add_more,
        'form': form,
        'max_images': 3,
    })


@login_required
@require_POST
def set_default_image(request, hash):
    """
    HTMX endpoint to set an image as default for collection or item
    """
    try:
        # Try to find CollectionImage first
        try:
            collection_image = CollectionImage.objects.get(media_file__hash=hash)
            if collection_image.collection.created_by != request.user:
                raise PermissionDenied("You don't have permission to modify this collection.")
            
            # Set as default
            collection_image.is_default = True
            collection_image.save()
            
            # Log application activity
            ApplicationActivity.log_info(
                'collection_set_default_image',
                f'Set "{collection_image.media_file.original_filename}" as default image for Collection {collection_image.collection.name}',
                user=request.user,
                meta={
                    'collection_hash': collection_image.collection.hash,
                    'media_file_hash': collection_image.media_file.hash,
                    'filename': collection_image.media_file.original_filename
                }
            )
            
            # Return updated image gallery
            current_images = CollectionImage.objects.filter(collection=collection_image.collection).order_by('order')
            return render(request, 'partials/_image_gallery.html', {
                'images': current_images,
                'object': collection_image.collection,
                'object_type': 'collection'
            })
            
        except CollectionImage.DoesNotExist:
            # Try CollectionItemImage
            item_image = CollectionItemImage.objects.get(media_file__hash=hash)
            if item_image.item.collection.created_by != request.user:
                raise PermissionDenied("You don't have permission to modify this item.")
            
            # Set as default
            item_image.is_default = True
            item_image.save()
            
            # Log application activity
            ApplicationActivity.log_info(
                'item_set_default_image',
                f'Set "{item_image.media_file.original_filename}" as default image for Item {item_image.item.name}',
                user=request.user,
                meta={
                    'item_hash': item_image.item.hash,
                    'collection_hash': item_image.item.collection.hash,
                    'media_file_hash': item_image.media_file.hash,
                    'filename': item_image.media_file.original_filename
                }
            )
            
            # Return updated image gallery
            current_images = CollectionItemImage.objects.filter(item=item_image.item).order_by('order')
            return render(request, 'partials/_image_gallery.html', {
                'images': current_images,
                'object': item_image.item,
                'object_type': 'item'
            })
            
    except CollectionImage.DoesNotExist:
        logger.error(f"CollectionImage with media file hash {hash} not found")
        ApplicationActivity.log_error(
            'set_default_image_not_found',
            f'CollectionImage with hash {hash} not found',
            user=request.user,
            meta={'media_file_hash': hash}
        )
        return JsonResponse({'error': 'Image not found'}, status=404)
    except CollectionItemImage.DoesNotExist:
        logger.error(f"CollectionItemImage with media file hash {hash} not found")
        ApplicationActivity.log_error(
            'set_default_image_not_found',
            f'CollectionItemImage with hash {hash} not found',
            user=request.user,
            meta={'media_file_hash': hash}
        )
        return JsonResponse({'error': 'Image not found'}, status=404)
    except Exception as e:
        logger.error(f"Error setting default image {hash}: {str(e)}")
        ApplicationActivity.log_error(
            'set_default_image_error',
            f'Error setting default image {hash}: {str(e)}',
            user=request.user,
            meta={'media_file_hash': hash, 'error': str(e)}
        )
        return JsonResponse({'error': 'Failed to set default image'}, status=500)


@login_required
@require_POST
def delete_image(request, hash):
    """
    HTMX endpoint to delete an image from collection or item
    """
    try:
        # Try to find CollectionImage first
        try:
            collection_image = CollectionImage.objects.get(media_file__hash=hash)
            if collection_image.collection.created_by != request.user:
                raise PermissionDenied("You don't have permission to modify this collection.")
            
            collection = collection_image.collection
            media_file = collection_image.media_file
            was_default = collection_image.is_default
            filename = media_file.original_filename
            
            # Delete the relationship and media file
            with transaction.atomic():
                collection_image.delete()
                media_file.delete_file()  # Delete actual file
                media_file.delete()  # Delete database record
                
                # Reorder remaining images
                remaining_images = CollectionImage.objects.filter(collection=collection).order_by('order')
                for i, img in enumerate(remaining_images):
                    img.order = i
                    img.save(update_fields=['order'])
                
                # If we deleted the default image, set the first remaining image as default
                if was_default and remaining_images.exists():
                    first_image = remaining_images.first()
                    first_image.is_default = True
                    first_image.save(update_fields=['is_default'])
                    logger.info(f"Set new default image for Collection {collection.hash}: {first_image.media_file.original_filename}")
                
                # Log application activity
                ApplicationActivity.log_info(
                    'collection_delete_image',
                    f'Deleted image "{filename}" from Collection {collection.name}',
                    user=request.user,
                    meta={
                        'collection_hash': collection.hash,
                        'media_file_hash': hash,
                        'filename': filename,
                        'was_default': was_default,
                        'remaining_images_count': remaining_images.count()
                    }
                )
            
            # Return HTMX response to trigger page refresh
            response = HttpResponse()
            response['HX-Refresh'] = 'true'
            return response
            
        except CollectionImage.DoesNotExist:
            # Try CollectionItemImage
            item_image = CollectionItemImage.objects.get(media_file__hash=hash)
            if item_image.item.collection.created_by != request.user:
                raise PermissionDenied("You don't have permission to modify this item.")
            
            item = item_image.item
            media_file = item_image.media_file
            was_default = item_image.is_default
            filename = media_file.original_filename
            
            # Delete the relationship and media file
            with transaction.atomic():
                item_image.delete()
                media_file.delete_file()  # Delete actual file
                media_file.delete()  # Delete database record
                
                # Reorder remaining images
                remaining_images = CollectionItemImage.objects.filter(item=item).order_by('order')
                for i, img in enumerate(remaining_images):
                    img.order = i
                    img.save(update_fields=['order'])
                
                # If we deleted the default image, set the first remaining image as default
                if was_default and remaining_images.exists():
                    first_image = remaining_images.first()
                    first_image.is_default = True
                    first_image.save(update_fields=['is_default'])
                    logger.info(f"Set new default image for CollectionItem {item.hash}: {first_image.media_file.original_filename}")
                
                # Log application activity
                ApplicationActivity.log_info(
                    'item_delete_image',
                    f'Deleted image "{filename}" from Item {item.name}',
                    user=request.user,
                    meta={
                        'item_hash': item.hash,
                        'collection_hash': item.collection.hash,
                        'media_file_hash': hash,
                        'filename': filename,
                        'was_default': was_default,
                        'remaining_images_count': remaining_images.count()
                    }
                )
            
            # Return HTMX response to trigger page refresh
            response = HttpResponse()
            response['HX-Refresh'] = 'true'
            return response
            
    except CollectionImage.DoesNotExist:
        logger.error(f"CollectionImage with media file hash {hash} not found")
        ApplicationActivity.log_error(
            'delete_image_not_found',
            f'CollectionImage with hash {hash} not found for deletion',
            user=request.user,
            meta={'media_file_hash': hash}
        )
        return JsonResponse({'error': 'Image not found'}, status=404)
    except CollectionItemImage.DoesNotExist:
        logger.error(f"CollectionItemImage with media file hash {hash} not found")
        ApplicationActivity.log_error(
            'delete_image_not_found',
            f'CollectionItemImage with hash {hash} not found for deletion',
            user=request.user,
            meta={'media_file_hash': hash}
        )
        return JsonResponse({'error': 'Image not found'}, status=404)
    except Exception as e:
        logger.error(f"Error deleting image {hash}: {str(e)}")
        ApplicationActivity.log_error(
            'delete_image_error',
            f'Error deleting image {hash}: {str(e)}',
            user=request.user,
            meta={'media_file_hash': hash, 'error': str(e)}
        )
        return JsonResponse({'error': 'Failed to delete image'}, status=500)


@login_required
@require_POST
def reorder_images(request, hash):
    """
    HTMX endpoint to reorder images via drag and drop
    """
    import json
    
    try:
        # Get the new order from POST data
        image_hashes = json.loads(request.body).get('image_hashes', [])
        
        # Try to find if this is a collection or item
        try:
            collection = get_object_or_404(Collection, hash=hash)
            if collection.created_by != request.user:
                raise PermissionDenied("You don't have permission to modify this collection.")
            
            # Update order for collection images
            with transaction.atomic():
                for i, image_hash in enumerate(image_hashes):
                    try:
                        collection_image = CollectionImage.objects.get(
                            collection=collection,
                            media_file__hash=image_hash
                        )
                        collection_image.order = i
                        collection_image.save(update_fields=['order'])
                    except CollectionImage.DoesNotExist:
                        continue
            
            # Log application activity
            ApplicationActivity.log_info(
                'collection_reorder_images',
                f'Reordered images for Collection {collection.name}',
                user=request.user,
                meta={
                    'collection_hash': collection.hash,
                    'new_order': image_hashes,
                    'total_images': len(image_hashes)
                }
            )
            
            return JsonResponse({'success': True})
            
        except Collection.DoesNotExist:
            # Try with item
            item = get_object_or_404(CollectionItem, hash=hash)
            if item.collection.created_by != request.user:
                raise PermissionDenied("You don't have permission to modify this item.")
            
            # Update order for item images
            with transaction.atomic():
                for i, image_hash in enumerate(image_hashes):
                    try:
                        item_image = CollectionItemImage.objects.get(
                            item=item,
                            media_file__hash=image_hash
                        )
                        item_image.order = i
                        item_image.save(update_fields=['order'])
                    except CollectionItemImage.DoesNotExist:
                        continue
            
            # Log application activity
            ApplicationActivity.log_info(
                'item_reorder_images',
                f'Reordered images for Item {item.name}',
                user=request.user,
                meta={
                    'item_hash': item.hash,
                    'collection_hash': item.collection.hash,
                    'new_order': image_hashes,
                    'total_images': len(image_hashes)
                }
            )
            
            return JsonResponse({'success': True})
            
    except Exception as e:
        logger.error(f"Error reordering images for {hash}: {str(e)}")
        ApplicationActivity.log_error(
            'reorder_images_error',
            f'Error reordering images for {hash}: {str(e)}',
            user=request.user,
            meta={'object_hash': hash, 'error': str(e)}
        )
        return JsonResponse({'error': 'Failed to reorder images'}, status=500)


@login_required
@require_http_methods(["GET"])
def switch_image(request, hash):
    """
    HTMX endpoint to switch the main image display on detail pages
    """
    try:
        media_file = get_object_or_404(MediaFile, hash=hash)
        
        # Check if this image belongs to a collection or item the user owns
        collection_image = media_file.collection_images.first()
        item_image = media_file.item_images.first()
        
        if collection_image:
            if collection_image.collection.created_by != request.user:
                raise PermissionDenied("You don't have permission to view this collection.")
            return render(request, 'partials/_main_image.html', {
                'image_url': media_file.file_url,
                'image_name': media_file.original_filename
            })
            
        elif item_image:
            if item_image.item.collection.created_by != request.user:
                raise PermissionDenied("You don't have permission to view this item.")
            return render(request, 'partials/_main_image.html', {
                'image_url': media_file.file_url,
                'image_name': media_file.original_filename
            })
            
        else:
            raise PermissionDenied("Image not found or access denied.")
            
    except Exception as e:
        logger.error(f"Error switching image {hash}: {str(e)}")
        ApplicationActivity.log_error(
            'switch_image_error',
            f'Error switching image {hash}: {str(e)}',
            user=request.user,
            meta={'media_file_hash': hash, 'error': str(e)}
        )
        return JsonResponse({'error': 'Failed to switch image'}, status=500)