# -*- coding: utf-8 -*-

"""
Media storage backends configuration for Beryl.

This module provides configurable storage backends for media files:
- Local filesystem storage for development
- Google Cloud Storage for production
- Configurable via environment variables
"""

import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.gcloud import GoogleCloudStorage


class BerylMediaStorage:
    """
    Configurable media storage backend that switches between local and GCS storage
    based on environment configuration.
    """
    
    @staticmethod
    def get_storage():
        """
        Returns the appropriate storage backend based on configuration.
        
        Logic:
        - Development + USE_GCS=False: Local filesystem storage
        - Development + USE_GCS=True: Google Cloud Storage
        - Production: Always Google Cloud Storage
        """
        # Check if we should use GCS
        use_gcs = getattr(settings, 'USE_GCS_STORAGE', False)
        is_production = not getattr(settings, 'DEBUG', True)
        
        if is_production or use_gcs:
            return GoogleCloudStorage(
                bucket_name=getattr(settings, 'GCS_BUCKET_NAME'),
                project_id=getattr(settings, 'GCS_PROJECT_ID', None),
                credentials=getattr(settings, 'GCS_CREDENTIALS', None),
                default_acl='publicRead',
                querystring_auth=False,
                location=getattr(settings, 'GCS_LOCATION', ''),
            )
        else:
            # Local filesystem storage
            return FileSystemStorage(
                location=os.path.join(settings.BASE_DIR, 'local_cdn', 'media'),
                base_url='/media/'
            )


class BerylCollectionImageStorage(BerylMediaStorage):
    """Storage backend for collection header images."""
    
    @staticmethod
    def get_storage():
        base_storage = BerylMediaStorage.get_storage()
        if isinstance(base_storage, GoogleCloudStorage):
            base_storage.location = 'collections/'
        else:
            base_storage.location = os.path.join(base_storage.location, 'collections')
        return base_storage


class BerylItemImageStorage(BerylMediaStorage):
    """Storage backend for collection item images."""
    
    @staticmethod
    def get_storage():
        base_storage = BerylMediaStorage.get_storage()
        if isinstance(base_storage, GoogleCloudStorage):
            base_storage.location = 'items/'
        else:
            base_storage.location = os.path.join(base_storage.location, 'items')
        return base_storage


# Storage instances
default_media_storage = BerylMediaStorage.get_storage()
collection_image_storage = BerylCollectionImageStorage.get_storage()
item_image_storage = BerylItemImageStorage.get_storage()