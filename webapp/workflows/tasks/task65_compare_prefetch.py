#!/usr/bin/env python
"""
Task 65 - Compare prefetch effectiveness
"""
import os
import sys
import django

# Setup Django
if 'beryl3/webapp' in os.getcwd():
    # Local
    sys.path.insert(0, '/home/mdubiel/projects/beryl3/webapp')
else:
    # Production
    sys.path.insert(0, '/home/mdubiel/beryl3')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.db import connection, reset_queries
from django.test.utils import override_settings
from web.models import Collection

with override_settings(DEBUG=True):
    reset_queries()

    collection = Collection.objects.get(hash='j6qJIB8loJ')

    # Test the exact prefetch from public.py
    items = collection.items.select_related(
        'item_type',
        'location'
    ).prefetch_related(
        'images__media_file',
        'links',
        'default_image__media_file',
        'attribute_values__item_attribute',
        'item_type__attributes'
    ).order_by('name')

    # Force evaluation
    items_list = list(items)

    print(f"Environment: {'Production' if '/beryl3' in sys.path[0] else 'Local'}")
    print(f"Items fetched: {len(items_list)}")
    print(f"Queries for initial fetch: {len(connection.queries)}")
    print()

    # Now test accessing attributes that should be prefetched
    reset_queries()

    test_item = items_list[0]

    # Access images
    images = list(test_item.images.all())
    q1 = len(connection.queries)
    print(f"Queries for item.images.all(): {q1}")

    # Access image media files
    if images:
        _ = images[0].media_file.file_path
        q2 = len(connection.queries) - q1
        print(f"Queries for image.media_file.file_path: {q2}")

    # Access links
    reset_queries()
    links = list(test_item.links.all())
    q3 = len(connection.queries)
    print(f"Queries for item.links.all(): {q3}")

    # Access attribute values
    reset_queries()
    attrs = list(test_item.attribute_values.all())
    q4 = len(connection.queries)
    print(f"Queries for item.attribute_values.all(): {q4}")

    # Access item attribute from attribute value
    if attrs:
        _ = attrs[0].item_attribute.name
        q5 = len(connection.queries) - q4
        print(f"Queries for attr_value.item_attribute.name: {q5}")

    # Access item type attributes
    reset_queries()
    if test_item.item_type:
        type_attrs = list(test_item.item_type.attributes.all())
        q6 = len(connection.queries)
        print(f"Queries for item.item_type.attributes.all(): {q6}")

    print()
    print("Expected: All should be 0 queries (prefetched)")
