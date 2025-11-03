#!/usr/bin/env python
"""
Task 65 - Diagnose why collection is still slow
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/mdubiel/beryl3')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.db import connection, reset_queries
from django.test.utils import override_settings
from web.models import Collection

# Enable query logging
reset_queries()

# Load the slow collection
collection = Collection.objects.get(hash='j6qJIB8loJ')

print(f"Collection: {collection.name}")
print(f"Items: {collection.items.count()}")
print(f"Grouping: {collection.group_by}")
print(f"Sorting: {collection.sort_by}")
print()

# Simulate the view code
from web.views.collection import collection_detail_view
from django.contrib.auth import get_user_model
from django.test import RequestFactory

User = get_user_model()
user = collection.created_by

factory = RequestFactory()
request = factory.get(f'/collections/{collection.hash}/')
request.user = user

print("="*80)
print("SIMULATING COLLECTION DETAIL VIEW")
print("="*80)

# Reset query counter
reset_queries()

# Call the view (this will execute all the queries)
try:
    with override_settings(DEBUG=True):
        response = collection_detail_view(request, collection.hash)

        print(f"\nTotal Queries: {len(connection.queries)}")
        print()

        # Group queries by type
        prefetch_queries = [q for q in connection.queries if 'attribute_values' in q['sql'].lower()]
        grouping_queries = [q for q in connection.queries if 'item_attribute' in q['sql'].lower() and 'WHERE' in q['sql']]

        print(f"Queries with 'attribute_values': {len(prefetch_queries)}")
        print(f"Queries with 'item_attribute' WHERE clause: {len(grouping_queries)}")
        print()

        # Show first 20 queries
        print("First 20 queries:")
        print("-" * 80)
        for i, query in enumerate(connection.queries[:20], 1):
            sql = query['sql'][:150]
            time = query['time']
            print(f"{i}. [{time}s] {sql}...")

        if len(connection.queries) > 20:
            print(f"\n... and {len(connection.queries) - 20} more queries")

        # Show queries that took longer than 0.01s
        slow_queries = [q for q in connection.queries if float(q['time']) > 0.01]
        if slow_queries:
            print(f"\n\nSlow queries (>0.01s): {len(slow_queries)}")
            print("-" * 80)
            for i, query in enumerate(slow_queries[:10], 1):
                sql = query['sql'][:150]
                time = query['time']
                print(f"{i}. [{time}s] {sql}...")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
