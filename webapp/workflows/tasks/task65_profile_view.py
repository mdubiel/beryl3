#!/usr/bin/env python
"""
Task 65 - Profile the public collection view to find bottlenecks
"""
import os
import sys
import django
import time

# Setup Django
sys.path.insert(0, '/home/mdubiel/beryl3')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.db import connection, reset_queries
from django.test.utils import override_settings
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from web.models import Collection

User = get_user_model()

collection = Collection.objects.get(hash='j6qJIB8loJ')
print(f"Collection: {collection.name}")
print(f"Items: {collection.items.count()}")
print()

factory = RequestFactory()
request = factory.get(f'/share/collections/{collection.hash}/')
request.user = User.objects.filter(is_active=True).first()

print("="*80)
print("PROFILING PUBLIC COLLECTION VIEW")
print("="*80)

with override_settings(DEBUG=False):
    reset_queries()

    # Import the view components inline to profile each step
    from django.db.models import Count, Q
    from web.models import CollectionItem, ItemType
    import random

    timings = {}

    # Step 1: Query items
    start = time.time()
    all_items = collection.items.select_related(
        'item_type',
        'location'
    ).prefetch_related(
        'links',
        'attribute_values__item_attribute',
        'item_type__attributes'
    ).order_by('name')
    timings['query_definition'] = time.time() - start

    # Step 2: Execute query
    start = time.time()
    items_list = list(all_items)
    timings['query_execution'] = time.time() - start

    # Step 3: Calculate stats
    start = time.time()
    stats = all_items.aggregate(
        total_items=Count('id'),
        in_collection_count=Count('id', filter=Q(status=CollectionItem.Status.IN_COLLECTION)),
        wanted_count=Count('id', filter=Q(status=CollectionItem.Status.WANTED)),
        reserved_count=Count('id', filter=Q(status=CollectionItem.Status.RESERVED)),
    )
    timings['stats_calculation'] = time.time() - start

    # Step 4: Item type distribution
    start = time.time()
    item_type_distribution = all_items.values('item_type__display_name').annotate(
        count=Count('id')
    ).order_by('-count')
    list(item_type_distribution)  # Force evaluation
    timings['item_type_distribution'] = time.time() - start

    # Step 5: Grouping logic (if enabled)
    start = time.time()
    grouped_items = []
    if collection.group_by == 'ATTRIBUTE' and collection.grouping_attribute:
        from collections import defaultdict
        from web.models import CollectionItemAttributeValue

        groups = defaultdict(list)
        ungrouped_items = []

        # Pre-fetch grouping attribute values
        attr_lookup = {}
        for attr_val in CollectionItemAttributeValue.objects.filter(
            item__in=items_list,
            item_attribute=collection.grouping_attribute
        ).select_related('item'):
            attr_lookup[attr_val.item_id] = attr_val.value

        # Group items
        for item in items_list:
            if item.id in attr_lookup:
                group_key = attr_lookup[item.id]
                groups[group_key].append(item)
            else:
                ungrouped_items.append(item)

        # Sort groups
        for group_name in sorted(groups.keys()):
            group_items = groups[group_name]

            # Sort within group
            if collection.sort_by == 'ATTRIBUTE' and collection.sort_attribute:
                sort_lookup = {}
                for attr_val in CollectionItemAttributeValue.objects.filter(
                    item__in=group_items,
                    item_attribute=collection.sort_attribute
                ).select_related('item'):
                    sort_lookup[attr_val.item_id] = attr_val.get_typed_value()

                def get_attr_value(item):
                    value = sort_lookup.get(item.id)
                    if value is None:
                        return (1, '')
                    if isinstance(value, (int, float)):
                        return (0, value)
                    return (0, str(value).lower())

                group_items = sorted(group_items, key=get_attr_value)

            grouped_items.append({
                'attribute_name': collection.grouping_attribute.display_name,
                'attribute_value': group_name,
                'items': group_items
            })

        if ungrouped_items:
            grouped_items.append({
                'attribute_name': 'Other',
                'attribute_value': None,
                'items': ungrouped_items
            })

    timings['grouping_sorting'] = time.time() - start

    # Step 6: Template rendering
    start = time.time()
    from django.shortcuts import render

    context = {
        "collection": collection,
        "items": items_list if not grouped_items else None,
        "page_obj": None,
        "stats": stats,
        "item_type_distribution": item_type_distribution,
        "dummy_name": "Anonymous",
        "item_types": ItemType.objects.all(),
        "grouped_items": grouped_items,
        "items_per_page": 25,
        "background_image_url": None,
    }

    response = render(request, "public/collection_public_detail.html", context)
    timings['template_definition'] = time.time() - start

    # Step 7: Render content (force evaluation)
    start = time.time()
    content = response.content
    timings['template_rendering'] = time.time() - start

    # Step 8: Try actual HTTP-like test
    start = time.time()
    from django.test import Client
    client = Client()
    http_response = client.get(f'/share/collections/{collection.hash}/')
    timings['full_http_request'] = time.time() - start

    # Print results
    print("\nTiming Breakdown:")
    print("-" * 80)
    total = 0
    for step, duration in timings.items():
        print(f"{step:30s}: {duration:8.3f}s ({duration*100:.1f}%)")
        total += duration
    print("-" * 80)
    print(f"{'TOTAL':30s}: {total:8.3f}s (100.0%)")

    print(f"\nContent size: {len(content):,} bytes")
    print(f"Grouped items: {len(grouped_items)}")
    print(f"Total items: {len(items_list)}")
