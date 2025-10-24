#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create a public collection with REAL uploaded images for testing Task 62.

This script creates a public collection and uploads actual image files
from URLs to test the dynamic background feature properly.
"""

import os
import sys
import django
import requests
from pathlib import Path
from io import BytesIO
from PIL import Image

# Setup Django environment
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'webapp'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import InMemoryUploadedFile
from web.models import Collection, CollectionItem, ItemType, MediaFile, CollectionImage, CollectionItemImage
from django.db import transaction

User = get_user_model()


def download_and_prepare_image(url, name):
    """Download image from URL and prepare for upload"""
    try:
        print(f"    Downloading {name}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Open image with PIL
        img = Image.open(BytesIO(response.content))

        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            img = img.convert('RGB')

        # Save to BytesIO
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        output.seek(0)

        # Create InMemoryUploadedFile
        uploaded_file = InMemoryUploadedFile(
            output,
            'ImageField',
            f"{name}.jpg",
            'image/jpeg',
            output.getbuffer().nbytes,
            None
        )

        return uploaded_file, img.size
    except Exception as e:
        print(f"    Error downloading {name}: {e}")
        return None, None


@transaction.atomic
def create_collection_with_images():
    """Create a public collection with real uploaded images"""

    # Get or create user mdubiel
    try:
        user = User.objects.get(email='mdubiel@mdubiel.org')
        print(f"Found user: {user.email}")
    except User.DoesNotExist:
        try:
            user = User.objects.get(username='mdubiel')
            print(f"Found user by username: {user.username}")
        except User.DoesNotExist:
            print("User mdubiel not found. Please create user first.")
            return

    # Get book item type
    book_type = ItemType.objects.filter(name='book').first()

    # Delete old test collection if exists
    old_collections = Collection.objects.filter(
        created_by=user,
        name="Fantasy Book Collection - Test"
    )
    if old_collections.exists():
        print(f"\nDeleting {old_collections.count()} old test collection(s)...")
        for col in old_collections:
            col.items.all().delete()
            col.delete()

    # Create public collection
    collection = Collection.objects.create(
        created_by=user,
        name="Fantasy Book Collection - Test",
        description="A beautiful collection of fantasy books with real uploaded images for testing dynamic backgrounds.",
        visibility=Collection.Visibility.PUBLIC
    )
    print(f"\nCreated PUBLIC collection: '{collection.name}' (hash: {collection.hash})")
    print(f"Public URL: /public/{collection.hash}/")

    # Sample books with Unsplash images
    books = [
        {
            'name': 'The Hobbit',
            'description': 'A classic fantasy adventure by J.R.R. Tolkien',
            'image_url': 'https://images.unsplash.com/photo-1621351183012-e2f9972dd9bf?w=800&h=600&fit=crop&q=80'
        },
        {
            'name': 'The Lord of the Rings',
            'description': 'Epic trilogy by J.R.R. Tolkien',
            'image_url': 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=800&h=600&fit=crop&q=80'
        },
        {
            'name': 'The Name of the Wind',
            'description': 'First book in The Kingkiller Chronicle',
            'image_url': 'https://images.unsplash.com/photo-1495640452355-2f31a1334e0e?w=800&h=600&fit=crop&q=80'
        },
        {
            'name': 'A Game of Thrones',
            'description': 'First book in A Song of Ice and Fire',
            'image_url': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800&h=600&fit=crop&q=80'
        },
        {
            'name': 'The Way of Kings',
            'description': 'First book in The Stormlight Archive',
            'image_url': 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=800&h=600&fit=crop&q=80'
        },
    ]

    print("\nCreating items with REAL uploaded images...")
    for book_data in books:
        item = CollectionItem.objects.create(
            collection=collection,
            created_by=user,
            name=book_data['name'],
            description=book_data['description'],
            item_type=book_type,
            status=CollectionItem.Status.IN_COLLECTION
        )
        print(f"\n  Created item: '{item.name}'")

        # Download and upload actual image
        uploaded_file, size = download_and_prepare_image(
            book_data['image_url'],
            item.name.replace(' ', '_').lower()
        )

        if uploaded_file and size:
            # Create MediaFile with actual file upload
            from django.core.files.storage import default_storage

            # Generate proper file path
            file_name = f"items/{uploaded_file.name}"
            file_path = default_storage.save(file_name, uploaded_file)

            # Create MediaFile record
            media_file = MediaFile.objects.create(
                created_by=user,
                file_path=file_path,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                content_type='image/jpeg',
                media_type=MediaFile.MediaType.COLLECTION_ITEM,
                storage_backend=MediaFile.StorageBackend.LOCAL,
                width=size[0],
                height=size[1],
                file_exists=True
            )

            # Link to item
            CollectionItemImage.objects.create(
                item=item,
                media_file=media_file,
                is_default=True
            )

            print(f"    ✓ Uploaded image: {file_path} ({size[0]}x{size[1]})")
        else:
            print(f"    ✗ Failed to upload image")

    # Add collection header image
    print(f"\nAdding collection header image...")
    collection_image_url = 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=1200&h=800&fit=crop&q=80'
    uploaded_file, size = download_and_prepare_image(collection_image_url, 'fantasy_collection_header')

    if uploaded_file and size:
        from django.core.files.storage import default_storage

        file_name = f"collections/{uploaded_file.name}"
        file_path = default_storage.save(file_name, uploaded_file)

        media_file = MediaFile.objects.create(
            created_by=user,
            file_path=file_path,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            content_type='image/jpeg',
            media_type=MediaFile.MediaType.COLLECTION_HEADER,
            storage_backend=MediaFile.StorageBackend.LOCAL,
            width=size[0],
            height=size[1],
            file_exists=True
        )

        CollectionImage.objects.create(
            collection=collection,
            media_file=media_file,
            is_default=True
        )

        print(f"  ✓ Uploaded collection image: {file_path} ({size[0]}x{size[1]})")

    # Count actual uploaded images
    item_images = MediaFile.objects.filter(
        item_images__item__collection=collection
    ).count()

    collection_images = MediaFile.objects.filter(
        collection_images__collection=collection
    ).count()

    print(f"\n{'='*60}")
    print(f"SUCCESS! Public collection created with REAL images!")
    print(f"{'='*60}")
    print(f"\nCollection: {collection.name}")
    print(f"Hash: {collection.hash}")
    print(f"Visibility: {collection.visibility}")
    print(f"Items: {collection.items.count()}")
    print(f"Item images uploaded: {item_images}")
    print(f"Collection images uploaded: {collection_images}")
    print(f"Total images: {item_images + collection_images}")
    print(f"\n🎨 Public URL: http://localhost:8000/public/{collection.hash}/")
    print(f"\n✨ Background images are now available for Task 62 testing!")


if __name__ == '__main__':
    print("="*60)
    print("Creating PUBLIC collection with REAL uploaded images...")
    print("="*60)
    create_collection_with_images()
