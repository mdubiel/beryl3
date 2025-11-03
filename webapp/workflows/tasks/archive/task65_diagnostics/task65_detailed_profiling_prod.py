#!/usr/bin/env python
"""
Task 65 - Comprehensive profiling of public collection view
Measures timing of EVERY element including queries, template rendering, and all relationships

Usage on production:
    cd ~/beryl3
    source .virtualenvs/beryl3/bin/activate
    python task65_detailed_profiling_prod.py > profiling_results.txt
"""
import os
import sys
import time
import json
from collections import defaultdict

# Add project to path
sys.path.insert(0, '/home/mdubiel/beryl3')

# Setup Django for production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'production_settings')

import django
django.setup()

from django.db import connection, reset_queries
from django.test.utils import override_settings
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from django.template import Template, Context
from django.template.loader import render_to_string

User = get_user_model()

def time_block(label):
    """Context manager for timing code blocks"""
    class Timer:
        def __init__(self, label):
            self.label = label
            self.start = None
            self.duration = None

        def __enter__(self):
            self.start = time.time()
            reset_queries()
            return self

        def __exit__(self, *args):
            self.duration = (time.time() - self.start) * 1000  # ms
            query_count = len(connection.queries)
            print(f"  [{self.label:40s}] {self.duration:8.2f}ms ({query_count:3d} queries)")

    return Timer(label)

print("="*80)
print("COMPREHENSIVE PERFORMANCE PROFILING - Thorgal Collection")
print("="*80)
print()

# Get the collection
from web.models import Collection
collection = Collection.objects.get(hash='j6qJIB8loJ')
print(f"Collection: {collection.name}")
print(f"Total items: {collection.items.count()}")
print()

with override_settings(DEBUG=True):

    # =======================================================================
    print("="*80)
    print("PHASE 1: DATABASE QUERIES")
    print("="*80)

    # Test 1: Basic query without optimization
    with time_block("1.1 Basic query (no prefetch)"):
        items_basic = list(collection.items.all()[:25])

    # Test 2: With select_related
    with time_block("1.2 With select_related"):
        items_select = list(collection.items.select_related(
            'item_type',
            'location'
        )[:25])

    # Test 3: Full prefetch (current implementation)
    with time_block("1.3 Full prefetch (current)"):
        items_full = list(collection.items.select_related(
            'item_type',
            'location'
        ).prefetch_related(
            'links',
            'attribute_values__item_attribute',
            'item_type__attributes',
            'images__media_file'  # Testing with images
        )[:25])

    # Test 4: Without images prefetch
    with time_block("1.4 Without images prefetch"):
        items_no_img = list(collection.items.select_related(
            'item_type',
            'location'
        ).prefetch_related(
            'links',
            'attribute_values__item_attribute',
            'item_type__attributes'
        )[:25])

    print()

    # =======================================================================
    print("="*80)
    print("PHASE 2: PROPERTY/METHOD ACCESS (per item)")
    print("="*80)

    if items_full:
        item = items_full[0]

        with time_block("2.1 Access item.default_image"):
            _ = item.default_image

        with time_block("2.2 Access item.images.all()"):
            _ = list(item.images.all())

        with time_block("2.3 Access item.links.all()"):
            _ = list(item.links.all())

        with time_block("2.4 Access item.attribute_values.all()"):
            _ = list(item.attribute_values.all())

        with time_block("2.5 Call item.get_display_attributes()"):
            _ = item.get_display_attributes()

        with time_block("2.6 Call item.get_all_attributes_detailed()"):
            _ = item.get_all_attributes_detailed()

        with time_block("2.7 Access item.location"):
            _ = item.location

        with time_block("2.8 Access item.item_type"):
            _ = item.item_type

        if item.item_type:
            with time_block("2.9 Access item_type.attributes.all()"):
                _ = list(item.item_type.attributes.all())

    print()

    # =======================================================================
    print("="*80)
    print("PHASE 3: TEMPLATE RENDERING (single item)")
    print("="*80)

    if items_full:
        item = items_full[0]

        # Test rendering just the image lazy load partial
        with time_block("3.1 Render _item_image_lazy.html"):
            _ = render_to_string('partials/_item_image_lazy.html', {'item': item})

        # Test rendering the full item card
        with time_block("3.2 Render _item_public_card.html"):
            _ = render_to_string('partials/_item_public_card.html', {'item': item})

        # Test rendering item attributes detail
        with time_block("3.3 Render _item_attributes_detail.html"):
            _ = render_to_string('partials/_item_attributes_detail.html', {'item': item})

    print()

    # =======================================================================
    print("="*80)
    print("PHASE 4: FULL VIEW SIMULATION (25 items)")
    print("="*80)

    # Simulate the full view
    total_start = time.time()
    reset_queries()

    with time_block("4.1 Query all items with prefetch"):
        all_items = collection.items.select_related(
            'item_type',
            'location'
        ).prefetch_related(
            'links',
            'attribute_values__item_attribute',
            'item_type__attributes'
        ).order_by('name')

        # Simulate pagination
        from django.core.paginator import Paginator
        paginator = Paginator(all_items, 25)
        page = paginator.page(1)
        items_page = list(page.object_list)

    with time_block("4.2 Calculate stats"):
        from django.db.models import Count, Q
        from web.models import CollectionItem
        stats = all_items.aggregate(
            total_items=Count('id'),
            in_collection_count=Count('id', filter=Q(status=CollectionItem.Status.IN_COLLECTION)),
            wanted_count=Count('id', filter=Q(status=CollectionItem.Status.WANTED)),
            reserved_count=Count('id', filter=Q(status=CollectionItem.Status.RESERVED)),
        )

    with time_block("4.3 Access properties for all items"):
        for item in items_page:
            _ = item.default_image
            _ = item.get_display_attributes()

    with time_block("4.4 Render all 25 item cards"):
        rendered_cards = []
        for item in items_page:
            rendered_cards.append(
                render_to_string('partials/_item_public_card.html', {'item': item})
            )

    total_duration = (time.time() - total_start) * 1000
    total_queries = len(connection.queries)

    print()
    print(f"  {'TOTAL (25 items)':40s} {total_duration:8.2f}ms ({total_queries:3d} queries)")

    print()

    # =======================================================================
    print("="*80)
    print("PHASE 5: N+1 QUERY DETECTION")
    print("="*80)

    # Check for N+1 queries
    query_patterns = defaultdict(int)
    for q in connection.queries:
        sql = q['sql']
        # Normalize the query by removing specific IDs
        import re
        normalized = re.sub(r'\b\d+\b', 'N', sql)
        normalized = re.sub(r'IN \([N,\s]+\)', 'IN (...)', normalized)
        query_patterns[normalized] += 1

    print("\nQuery patterns (similar queries):")
    print("-" * 80)

    suspicious = []
    for pattern, count in sorted(query_patterns.items(), key=lambda x: -x[1]):
        if count > 5:  # Potential N+1
            suspicious.append((pattern[:100], count))
            print(f"  [{count:3d}x] {pattern[:100]}...")

    if suspicious:
        print("\n⚠️  POTENTIAL N+1 QUERIES DETECTED!")
        for pattern, count in suspicious:
            print(f"    - {count}x: {pattern}")
    else:
        print("\n✅ No obvious N+1 query patterns detected")

    print()

    # =======================================================================
    print("="*80)
    print("PHASE 6: PER-ITEM BREAKDOWN (detailed)")
    print("="*80)

    # Measure each item individually
    print("\nPer-item timing (first 5 items):")
    print("-" * 80)

    items_for_test = collection.items.select_related(
        'item_type',
        'location'
    ).prefetch_related(
        'links',
        'attribute_values__item_attribute',
        'item_type__attributes'
    ).order_by('name')[:5]

    for idx, item in enumerate(items_for_test, 1):
        print(f"\nItem {idx}: {item.name[:50]}")

        reset_queries()
        start = time.time()

        # Access properties
        _ = item.default_image
        _ = item.get_display_attributes()
        _ = list(item.links.all())

        property_time = (time.time() - start) * 1000
        property_queries = len(connection.queries)

        # Render template
        reset_queries()
        start = time.time()
        _ = render_to_string('partials/_item_public_card.html', {'item': item})
        render_time = (time.time() - start) * 1000
        render_queries = len(connection.queries)

        print(f"  Properties:  {property_time:6.2f}ms ({property_queries} queries)")
        print(f"  Rendering:   {render_time:6.2f}ms ({render_queries} queries)")
        print(f"  Total:       {property_time + render_time:6.2f}ms")

    print()

    # =======================================================================
    print("="*80)
    print("PHASE 7: RELATIONSHIP STATISTICS")
    print("="*80)

    print("\nRelationship counts for this collection:")
    print("-" * 80)

    total_items = collection.items.count()

    from web.models import CollectionItemAttributeValue, CollectionItemLink, CollectionItemImage

    total_attrs = CollectionItemAttributeValue.objects.filter(item__collection=collection).count()
    total_links = CollectionItemLink.objects.filter(item__collection=collection).count()
    total_images = CollectionItemImage.objects.filter(item__collection=collection).count()

    print(f"  Items:              {total_items:5d}")
    print(f"  Attributes:         {total_attrs:5d} (avg {total_attrs/max(total_items,1):.1f} per item)")
    print(f"  Links:              {total_links:5d} (avg {total_links/max(total_items,1):.1f} per item)")
    print(f"  Images:             {total_images:5d} (avg {total_images/max(total_items,1):.1f} per item)")

    # Check attribute values detail
    if total_items > 0:
        sample_item = collection.items.first()
        print(f"\nSample item: {sample_item.name}")
        print(f"  - Attributes: {sample_item.attribute_values.count()}")
        print(f"  - Links: {sample_item.links.count()}")
        print(f"  - Images: {sample_item.images.count()}")

    print()

    # =======================================================================
    print("="*80)
    print("SUMMARY & RECOMMENDATIONS")
    print("="*80)
    print()

    print("Key Findings:")
    print("-" * 80)
    print(f"1. Full view (25 items): {total_duration:.0f}ms with {total_queries} queries")
    print(f"2. Average per item: {total_duration/25:.0f}ms")
    print(f"3. Suspicious query patterns: {len(suspicious)}")
    print()

    if total_duration > 2000:
        print("⚠️  Performance issue detected (>2s for 25 items)")
        print("\nLikely causes:")
        if len(suspicious) > 0:
            print("  - N+1 queries detected")
        if total_queries > 50:
            print(f"  - High query count ({total_queries} queries)")
        if (total_duration / 25) > 50:
            print(f"  - Slow per-item processing ({total_duration/25:.0f}ms per item)")
    else:
        print("✅ Performance looks good (<2s for 25 items)")

    print()

print("="*80)
print("Profiling complete!")
print("="*80)
