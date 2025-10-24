#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Create a public collection with images for testing Task 62.

This script creates a public collection for user mdubiel with items
and downloads sample images to test the dynamic background feature.
"""

import os
import sys
import django
import requests
from pathlib import Path

# Setup Django environment
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'webapp'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from web.models import Collection, CollectionItem, MediaFile, ItemType
from django.db import transaction

User = get_user_model()


def download_image(url):
    """Download image from URL and return content"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return ContentFile(response.content)
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return None


@transaction.atomic
def create_public_collection():
    """Create a public collection with images"""

    # Get or create user mdubiel
    try:
        user = User.objects.get(email='mdubiel@mdubiel.org')
        print(f"Found user: {user.email}")
    except User.DoesNotExist:
        # Try to get by username
        try:
            user = User.objects.get(username='mdubiel')
            print(f"Found user by username: {user.username}")
        except User.DoesNotExist:
            print("User mdubiel not found. Creating...")
            user = User.objects.create_user(
                username='mdubiel',
                email='mdubiel@mdubiel.org',
                password='Test123!',
                first_name='Michal',
                is_active=True
            )
            print(f"Created user: {user.email}")

    # Get book item type
    book_type = ItemType.objects.filter(name='book').first()
    if not book_type:
        print("Warning: Book item type not found. Items will be created without type.")

    # Create public collection
    collection = Collection.objects.create(
        created_by=user,
        name="Fantasy Book Collection",
        description="A collection of classic fantasy novels and series. Perfect for testing dynamic backgrounds!",
        visibility=Collection.Visibility.PUBLIC
    )
    print(f"\nCreated PUBLIC collection: '{collection.name}' (hash: {collection.hash})")
    print(f"Public URL: /public/{collection.hash}/")

    # Sample books with Unsplash images (fantasy/book themed)
    books = [
        {
            'name': 'The Hobbit',
            'description': 'A classic fantasy adventure by J.R.R. Tolkien',
            'image_url': 'https://images.unsplash.com/photo-1621351183012-e2f9972dd9bf?w=800&h=600&fit=crop'
        },
        {
            'name': 'The Lord of the Rings',
            'description': 'Epic trilogy by J.R.R. Tolkien',
            'image_url': 'https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=800&h=600&fit=crop'
        },
        {
            'name': 'The Name of the Wind',
            'description': 'First book in The Kingkiller Chronicle by Patrick Rothfuss',
            'image_url': 'https://images.unsplash.com/photo-1495640452355-2f31a1334e0e?w=800&h=600&fit=crop'
        },
        {
            'name': 'A Game of Thrones',
            'description': 'First book in A Song of Ice and Fire by George R.R. Martin',
            'image_url': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=800&h=600&fit=crop'
        },
        {
            'name': 'The Way of Kings',
            'description': 'First book in The Stormlight Archive by Brandon Sanderson',
            'image_url': 'https://images.unsplash.com/photo-1516979187457-637abb4f9353?w=800&h=600&fit=crop'
        },
        {
            'name': 'Good Omens',
            'description': 'Comedic fantasy by Terry Pratchett and Neil Gaiman',
            'image_url': 'https://images.unsplash.com/photo-1497633762265-9d179a990aa6?w=800&h=600&fit=crop'
        },
    ]

    # Create items with images
    print("\nCreating items with images...")
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

        # Set image URL
        item.image_url = book_data['image_url']
        item.save()
        print(f"    - Set image URL")

    # Also add collection image
    print(f"\nAdding collection image...")
    collection.image_url = 'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=1200&h=800&fit=crop'
    collection.save()
    print(f"  - Collection image URL set")

    print(f"\n{'='*60}")
    print(f"SUCCESS! Public collection created with {len(books)} items")
    print(f"{'='*60}")
    print(f"\nCollection: {collection.name}")
    print(f"Hash: {collection.hash}")
    print(f"Visibility: {collection.visibility}")
    print(f"Items: {collection.items.count()}")
    print(f"Items with image URLs: {collection.items.exclude(image_url='').count()}")
    print(f"\nPublic URL: http://localhost:8000/public/{collection.hash}/")
    print(f"\nYou can now test Task 62 with this collection!")


if __name__ == '__main__':
    create_public_collection()
