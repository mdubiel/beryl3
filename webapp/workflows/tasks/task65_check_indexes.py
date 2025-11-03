#!/usr/bin/env python
"""
Task 65 - Check database indexes and analyze N-N relationship performance
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/mdubiel/projects/beryl3/webapp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.db import connection
from web.models import CollectionItem, CollectionItemImage, MediaFile

print("=" * 80)
print("DATABASE INDEX ANALYSIS")
print("=" * 80)

# Get table names
item_table = CollectionItem._meta.db_table
image_link_table = CollectionItemImage._meta.db_table
media_table = MediaFile._meta.db_table

print(f"\nTable names:")
print(f"  CollectionItem: {item_table}")
print(f"  CollectionItemImage: {image_link_table}")
print(f"  MediaFile: {media_table}")

# Check indexes on each table
with connection.cursor() as cursor:
    print("\n" + "=" * 80)
    print(f"INDEXES ON {item_table}")
    print("=" * 80)
    cursor.execute(f"PRAGMA index_list('{item_table}')")
    indexes = cursor.fetchall()
    for idx in indexes:
        print(f"\nIndex: {idx[1]} (unique={idx[2]})")
        cursor.execute(f"PRAGMA index_info('{idx[1]}')")
        cols = cursor.fetchall()
        for col in cols:
            print(f"  - {col[2]}")

    print("\n" + "=" * 80)
    print(f"INDEXES ON {image_link_table}")
    print("=" * 80)
    cursor.execute(f"PRAGMA index_list('{image_link_table}')")
    indexes = cursor.fetchall()
    for idx in indexes:
        print(f"\nIndex: {idx[1]} (unique={idx[2]})")
        cursor.execute(f"PRAGMA index_info('{idx[1]}')")
        cols = cursor.fetchall()
        for col in cols:
            print(f"  - {col[2]}")

    print("\n" + "=" * 80)
    print(f"INDEXES ON {media_table}")
    print("=" * 80)
    cursor.execute(f"PRAGMA index_list('{media_table}')")
    indexes = cursor.fetchall()
    for idx in indexes:
        print(f"\nIndex: {idx[1]} (unique={idx[2]})")
        cursor.execute(f"PRAGMA index_info('{idx[1]}')")
        cols = cursor.fetchall()
        for col in cols:
            print(f"  - {col[2]}")

# Check relationship statistics
print("\n" + "=" * 80)
print("RELATIONSHIP STATISTICS")
print("=" * 80)

# Get a sample collection with images
from web.models import Collection
collection = Collection.objects.get(hash='j6qJIB8loJ')

print(f"\nCollection: {collection.name} ({collection.hash})")
print(f"Total items: {collection.items.count()}")

# Count items with images
items_with_images = CollectionItem.objects.filter(
    collection=collection,
    images__isnull=False
).distinct().count()

print(f"Items with images: {items_with_images}")

# Count total image links
total_image_links = CollectionItemImage.objects.filter(
    item__collection=collection
).count()

print(f"Total image links: {total_image_links}")
print(f"Average images per item: {total_image_links / max(items_with_images, 1):.2f}")

# Check for default images
items_with_default = CollectionItem.objects.filter(
    collection=collection,
    images__is_default=True
).distinct().count()

print(f"Items with default image: {items_with_default}")

# Sample query pattern analysis
print("\n" + "=" * 80)
print("QUERY PATTERN ANALYSIS")
print("=" * 80)

from django.db import reset_queries, connection as db_conn
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    reset_queries()

    # Simulate the default_image property access pattern
    item = collection.items.first()
    if item:
        print(f"\nTesting property access for item: {item.name}")
        print("\n1. Accessing item.default_image property:")
        reset_queries()
        default_img = item.default_image  # This runs: images.filter(is_default=True).first()
        print(f"   Queries executed: {len(db_conn.queries)}")
        if db_conn.queries:
            print(f"   SQL: {db_conn.queries[0]['sql']}")

        print("\n2. Accessing item.images.all():")
        reset_queries()
        all_imgs = list(item.images.all())
        print(f"   Queries executed: {len(db_conn.queries)}")
        if db_conn.queries:
            print(f"   SQL: {db_conn.queries[0]['sql']}")

        print("\n3. With prefetch_related from view:")
        reset_queries()
        item_prefetched = CollectionItem.objects.prefetch_related(
            'images__media_file'
        ).get(pk=item.pk)
        _ = item_prefetched.default_image  # Should use prefetch cache
        print(f"   Queries executed: {len(db_conn.queries)}")
        for q in db_conn.queries:
            print(f"   SQL: {q['sql']}")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

print("\n1. Check if these indexes exist and are being used:")
print("   - web_collectionitemimage.item_id (for reverse lookups)")
print("   - web_collectionitemimage.media_file_id (for joins)")
print("   - web_collectionitemimage.is_default (for default_image property)")
print("   - web_mediafile.id (primary key)")

print("\n2. The default_image property runs a query EVERY time it's accessed")
print("   - This is not using prefetch_related cache!")
print("   - Solution: Add a method that uses prefetched data")

print("\n3. Check if template is calling default_image multiple times per item")
print("   - Each call = 1 database query (even with prefetch)")
