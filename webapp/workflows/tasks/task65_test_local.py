#!/usr/bin/env python
"""
Task 65 - Test local performance with imported collection
"""
import os
import sys
import django
import time

# Setup Django
sys.path.insert(0, '/home/mdubiel/projects/beryl3/webapp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.db import connection, reset_queries
from django.test.utils import override_settings
from django.test import RequestFactory, Client
from django.contrib.auth import get_user_model
from web.models import Collection
from web.views.public import public_collection_view

User = get_user_model()

# Load the collection
collection = Collection.objects.get(hash='j6qJIB8loJ')
print(f"Collection: {collection.name}")
print(f"Items: {collection.items.count()}")
print(f"Grouping: {collection.group_by}")
print(f"Sorting: {collection.sort_by}")
print()

# Create request
factory = RequestFactory()
request = factory.get(f'/share/collections/{collection.hash}/')
request.user = User.objects.filter(is_active=True).first()

print("="*80)
print("TEST 1: View Performance with DEBUG=False (production-like)")
print("="*80)

with override_settings(DEBUG=False, ALLOWED_HOSTS=['*']):
    reset_queries()
    start_time = time.time()

    try:
        response = public_collection_view(request, collection.hash)
        view_time = time.time() - start_time

        print(f"\nView execution time: {view_time:.3f}s")
        print(f"Response status: {response.status_code}")

        # Render the template
        start_render = time.time()
        content = response.content
        render_time = time.time() - start_render

        print(f"Template rendering time: {render_time:.3f}s")
        print(f"Total time: {view_time + render_time:.3f}s")
        print(f"Content size: {len(content):,} bytes")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

print()
print("="*80)
print("TEST 2: View Performance with DEBUG=True (query logging)")
print("="*80)

with override_settings(DEBUG=True, ALLOWED_HOSTS=['*']):
    reset_queries()
    start_time = time.time()

    try:
        response = public_collection_view(request, collection.hash)
        view_time = time.time() - start_time

        print(f"\nView execution time: {view_time:.3f}s")
        print(f"Total queries: {len(connection.queries)}")

        # Show first 10 queries
        print("\nFirst 10 queries:")
        print("-" * 80)
        for i, query in enumerate(connection.queries[:10], 1):
            sql = query['sql'][:150]
            query_time = query['time']
            print(f"{i}. [{query_time}s] {sql}...")

        if len(connection.queries) > 10:
            print(f"\n... and {len(connection.queries) - 10} more queries")

        # Show slowest queries
        slow_queries = sorted(connection.queries, key=lambda q: float(q['time']), reverse=True)[:5]
        if slow_queries:
            print(f"\n\nSlowest 5 queries:")
            print("-" * 80)
            for i, query in enumerate(slow_queries, 1):
                sql = query['sql'][:150]
                query_time = query['time']
                print(f"{i}. [{query_time}s] {sql}...")

        # Render template
        start_render = time.time()
        content = response.content
        render_time = time.time() - start_render

        print(f"\nTemplate rendering time: {render_time:.3f}s")
        print(f"Total time: {view_time + render_time:.3f}s")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

print()
print("="*80)
print("TEST 3: Test Client Request (simulates full HTTP request)")
print("="*80)

client = Client()
start_time = time.time()
response = client.get(f'/share/collections/{collection.hash}/')
total_time = time.time() - start_time

print(f"\nTest client request time: {total_time:.3f}s")
print(f"Response status: {response.status_code}")
print(f"Content size: {len(response.content):,} bytes")
