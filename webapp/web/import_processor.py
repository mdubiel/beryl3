"""
Import Processing Engine
========================

Processes validated import data and creates Collections, Items, Images, and Links.
Handles optional web image downloads and provides comprehensive error reporting.
"""

import logging
import os
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
from io import BytesIO
from PIL import Image as PILImage

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from .models import (
    Collection, CollectionItem, ItemType, ItemAttribute, 
    LinkPattern, CollectionItemLink, MediaFile,
    CollectionImage, CollectionItemImage, RecentActivity
)

User = get_user_model()
logger = logging.getLogger("webapp")


class ImportProcessingError(Exception):
    """Custom exception for import processing errors"""
    pass


class ImportProcessor:
    """
    Processes validated import data and creates database objects
    """
    
    def __init__(self):
        self.downloaded_images = {}  # Cache for downloaded images
        self.created_item_types = {}  # Cache for created item types
        self.errors = []
        self.warnings = []
        
    def process_import(self, data: Dict[str, Any], target_user: User, 
                      download_images: bool = False, admin_user: User = None) -> Dict[str, Any]:
        """
        Main import processing method
        
        Args:
            data: Validated import data
            target_user: User to import data for
            download_images: Whether to download web images
            admin_user: Admin user performing the import
            
        Returns:
            Import result summary
        """
        self.errors = []
        self.warnings = []
        self.downloaded_images = {}
        self.created_item_types = {}
        self.target_user = target_user
        self.admin_user = admin_user
        
        result = {
            'collections_created': 0,
            'items_created': 0,
            'images_downloaded': 0,
            'links_created': 0,
            'item_types_created': 0,
            'errors': [],
            'warnings': [],
            'start_time': timezone.now()
        }
        
        try:
            with transaction.atomic():
                # Process item types first if provided
                if 'item_types' in data:
                    result['item_types_created'] = self._process_item_types(
                        data['item_types'], target_user
                    )
                
                # Process collections
                for collection_data in data.get('collections', []):
                    try:
                        collection, collection_stats = self._process_collection(
                            collection_data, target_user, download_images
                        )
                        
                        result['collections_created'] += 1
                        result['items_created'] += collection_stats['items_created']
                        result['images_downloaded'] += collection_stats['images_downloaded']
                        result['links_created'] += collection_stats['links_created']
                        
                        logger.info("Import: Created collection '%s' with %d items for user %s", 
                                   collection.name, collection_stats['items_created'], target_user.email)
                        
                    except Exception as e:
                        error_msg = f"Failed to create collection '{collection_data.get('name', 'Unknown')}': {str(e)}"
                        self.errors.append(error_msg)
                        logger.error("Import error: %s", error_msg)
                
                # Create activity log entry
                if result['collections_created'] > 0:
                    RecentActivity.objects.create(
                        created_by=admin_user or target_user,
                        icon='upload',
                        message=f"**Admin import**: Created {result['collections_created']} collection(s) and {result['items_created']} item(s) for user **{target_user.display_name()}**"
                    )
                
        except Exception as e:
            logger.error("Import processing failed: %s", str(e))
            raise ImportProcessingError(f"Import processing failed: {str(e)}")
        
        result['errors'] = self.errors
        result['warnings'] = self.warnings
        result['end_time'] = timezone.now()
        result['duration'] = (result['end_time'] - result['start_time']).total_seconds()
        
        return result
    
    def _process_item_types(self, item_types_data: List[Dict], target_user: User) -> int:
        """Process item type definitions"""
        created_count = 0
        
        for item_type_data in item_types_data:
            try:
                item_type_name = item_type_data['name']
                
                # Check if item type already exists
                item_type, created = ItemType.objects.get_or_create(
                    name=item_type_name,
                    defaults={
                        'display_name': item_type_data['display_name'],
                        'description': item_type_data.get('description', ''),
                        'icon': item_type_data.get('icon', 'package'),
                        'created_by': target_user
                    }
                )
                
                if created:
                    created_count += 1
                    self.created_item_types[item_type_name] = item_type
                    
                    # Create attributes
                    for attr_data in item_type_data.get('attributes', []):
                        ItemAttribute.objects.create(
                            item_type=item_type,
                            name=attr_data['name'],
                            display_name=attr_data['display_name'],
                            attribute_type=attr_data['attribute_type'],
                            required=attr_data.get('required', False),
                            order=attr_data.get('order', 1),
                            choices=attr_data.get('choices', ''),
                            created_by=target_user
                        )
                else:
                    self.warnings.append(f"Item type '{item_type_name}' already exists, skipped creation")
                    
            except Exception as e:
                error_msg = f"Failed to create item type '{item_type_data.get('name', 'Unknown')}': {str(e)}"
                self.errors.append(error_msg)
        
        return created_count
    
    def _process_collection(self, collection_data: Dict, target_user: User, 
                          download_images: bool) -> Tuple['Collection', Dict]:
        """Process a single collection"""
        stats = {
            'items_created': 0,
            'images_downloaded': 0,
            'links_created': 0
        }
        
        # Create collection
        collection = Collection.objects.create(
            name=collection_data['name'],
            description=collection_data.get('description', ''),
            visibility=collection_data.get('visibility', 'PRIVATE'),
            image_url=collection_data.get('image_url', ''),
            created_by=target_user
        )
        
        # Process collection images
        if download_images and 'images' in collection_data:
            for image_data in collection_data['images']:
                try:
                    media_file = self._download_image(
                        image_data['url'], 
                        f"collection_{collection.hash}_{image_data.get('order', 0)}"
                    )
                    if media_file:
                        CollectionImage.objects.create(
                            collection=collection,
                            media_file=media_file,
                            is_default=image_data.get('is_default', False),
                            order=image_data.get('order', 0),
                            created_by=target_user
                        )
                        stats['images_downloaded'] += 1
                        
                except Exception as e:
                    self.warnings.append(f"Failed to download collection image from {image_data['url']}: {str(e)}")
        
        # Process items
        for item_data in collection_data.get('items', []):
            try:
                item, item_stats = self._process_item(item_data, collection, target_user, download_images)
                stats['items_created'] += 1
                stats['images_downloaded'] += item_stats['images_downloaded']
                stats['links_created'] += item_stats['links_created']
                
            except Exception as e:
                error_msg = f"Failed to create item '{item_data.get('name', 'Unknown')}': {str(e)}"
                self.errors.append(error_msg)
        
        return collection, stats
    
    def _process_item(self, item_data: Dict, collection: 'Collection', 
                     target_user: User, download_images: bool) -> Tuple['CollectionItem', Dict]:
        """Process a single collection item"""
        stats = {
            'images_downloaded': 0,
            'links_created': 0
        }
        
        # Get or create item type
        item_type = None
        if 'item_type' in item_data:
            item_type_name = item_data['item_type']
            try:
                item_type = ItemType.objects.get(name=item_type_name)
            except ItemType.DoesNotExist:
                # Create a basic item type
                item_type = ItemType.objects.create(
                    name=item_type_name,
                    display_name=item_type_name.replace('_', ' ').title(),
                    description=f"Auto-created from import",
                    icon='package',
                    created_by=target_user
                )
                self.created_item_types[item_type_name] = item_type
                self.warnings.append(f"Created basic item type '{item_type_name}' automatically")
        
        # Create item
        item = CollectionItem.objects.create(
            collection=collection,
            name=item_data['name'],
            description=item_data.get('description', ''),
            status=item_data.get('status', 'IN_COLLECTION'),
            is_favorite=item_data.get('is_favorite', False),
            item_type=item_type,
            attributes=item_data.get('attributes', {}),
            image_url=item_data.get('image_url', ''),
            created_by=target_user
        )
        
        # Handle reservation data
        if item.status == 'RESERVED' and 'reservation' in item_data:
            reservation = item_data['reservation']
            item.reserved_by_name = reservation.get('reserved_by_name', '')
            item.reserved_by_email = reservation.get('reserved_by_email', '')
            if 'reserved_date' in reservation:
                try:
                    item.reserved_date = datetime.fromisoformat(
                        reservation['reserved_date'].replace('Z', '+00:00')
                    )
                except ValueError:
                    self.warnings.append(f"Invalid reservation date format for item '{item.name}'")
            item.save()
        
        # Process item images
        if download_images and 'images' in item_data:
            for image_data in item_data['images']:
                try:
                    media_file = self._download_image(
                        image_data['url'],
                        f"item_{item.hash}_{image_data.get('order', 0)}"
                    )
                    if media_file:
                        CollectionItemImage.objects.create(
                            item=item,
                            media_file=media_file,
                            is_default=image_data.get('is_default', False),
                            order=image_data.get('order', 0),
                            created_by=target_user
                        )
                        stats['images_downloaded'] += 1
                        
                except Exception as e:
                    self.warnings.append(f"Failed to download item image from {image_data['url']}: {str(e)}")
        
        # Process image_url field (single image download)
        if download_images and item_data.get('image_url'):
            try:
                media_file = self._download_image(
                    item_data['image_url'],
                    f"item_{item.hash}_main"
                )
                if media_file:
                    CollectionItemImage.objects.create(
                        item=item,
                        media_file=media_file,
                        is_default=True,  # Single image is default
                        order=0,
                        created_by=target_user
                    )
                    stats['images_downloaded'] += 1
                    
            except Exception as e:
                self.warnings.append(f"Failed to download item image from {item_data['image_url']}: {str(e)}")
        
        # Process links
        for link_data in item_data.get('links', []):
            try:
                # Find matching link pattern
                link_pattern = LinkPattern.find_matching_pattern(link_data['url'])
                
                CollectionItemLink.objects.create(
                    item=item,
                    url=link_data['url'],
                    display_name=link_data.get('display_name', ''),
                    link_pattern=link_pattern,
                    order=link_data.get('order', 0),
                    created_by=target_user
                )
                stats['links_created'] += 1
                
            except Exception as e:
                self.warnings.append(f"Failed to create link for item '{item.name}': {str(e)}")
        
        return item, stats
    
    def _download_image(self, url: str, filename_prefix: str) -> Optional['MediaFile']:
        """Download image from URL and create MediaFile"""
        if url in self.downloaded_images:
            return self.downloaded_images[url]
        
        try:
            # Download the image
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Beryl3-Import/1.0'
            })
            response.raise_for_status()
            
            # Validate it's an image
            try:
                img = PILImage.open(BytesIO(response.content))
                img.verify()  # Verify it's a valid image
            except Exception:
                raise ValueError("Downloaded content is not a valid image")
            
            # Generate filename
            parsed_url = urlparse(url)
            original_name = os.path.basename(parsed_url.path)
            if not original_name or '.' not in original_name:
                # Guess extension from content type
                content_type = response.headers.get('content-type', '').lower()
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                elif 'png' in content_type:
                    ext = '.png'
                elif 'gif' in content_type:
                    ext = '.gif'
                elif 'webp' in content_type:
                    ext = '.webp'
                else:
                    ext = '.jpg'  # Default
                original_name = f"image{ext}"
            
            filename = f"{filename_prefix}_{original_name}"
            
            # Save file to storage
            from django.core.files.storage import default_storage
            content_file = ContentFile(response.content, name=filename)
            file_path = f"items/{filename}"
            saved_path = default_storage.save(file_path, content_file)
            
            # Get image dimensions
            try:
                img = PILImage.open(BytesIO(response.content))
                width, height = img.size
            except Exception:
                width, height = None, None
            
            # Determine storage backend based on Django storage backend
            storage_backend = MediaFile.StorageBackend.LOCAL
            if hasattr(default_storage, '__class__'):
                storage_class_name = default_storage.__class__.__name__
                if 'gcs' in storage_class_name.lower() or 'google' in storage_class_name.lower():
                    storage_backend = MediaFile.StorageBackend.GCS
                elif 's3' in storage_class_name.lower():
                    storage_backend = MediaFile.StorageBackend.S3
            
            # Create MediaFile
            media_file = MediaFile.objects.create(
                file_path=saved_path,
                original_filename=original_name,
                file_size=len(response.content),
                content_type=response.headers.get('content-type', 'image/jpeg'),
                media_type=MediaFile.MediaType.COLLECTION_ITEM,
                storage_backend=storage_backend,
                width=width,
                height=height,
                created_by=self.target_user
            )
            
            self.downloaded_images[url] = media_file
            return media_file
            
        except requests.RequestException as e:
            raise Exception(f"Failed to download image: Network error - {str(e)}")
        except Exception as e:
            raise Exception(f"Failed to process image: {str(e)}")
    
    def generate_summary_report(self, result: Dict[str, Any]) -> str:
        """Generate a human-readable import summary report"""
        duration = result.get('duration', 0)
        
        report = f"""
Import Summary Report
=====================

Duration: {duration:.2f} seconds
Status: {'✅ SUCCESS' if not result['errors'] else '⚠️ COMPLETED WITH ERRORS'}

Statistics:
- Collections created: {result['collections_created']}
- Items created: {result['items_created']}
- Item types created: {result['item_types_created']}
- Links created: {result['links_created']}
- Images downloaded: {result['images_downloaded']}

"""
        
        if result['warnings']:
            report += f"Warnings ({len(result['warnings'])}):\n"
            for i, warning in enumerate(result['warnings'], 1):
                report += f"{i}. {warning}\n"
            report += "\n"
        
        if result['errors']:
            report += f"Errors ({len(result['errors'])}):\n"
            for i, error in enumerate(result['errors'], 1):
                report += f"{i}. {error}\n"
        
        return report