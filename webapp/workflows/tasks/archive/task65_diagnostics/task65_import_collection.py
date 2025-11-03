#!/usr/bin/env python
"""
Task 65 - Import collection data to local environment for testing
"""
import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, '/home/mdubiel/projects/beryl3/webapp')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from web.models import (
    Collection, CollectionItem, CollectionItemAttributeValue,
    ItemAttribute, ItemType, UserProfile
)
from django.contrib.auth import get_user_model

User = get_user_model()

# Load export data
input_file = '/tmp/collection_j6qJIB8loJ_export.json'
with open(input_file, 'r') as f:
    data = json.load(f)

print(f"Loaded data from: {input_file}")
print(f"Collection: {data['collection']['name']}")
print(f"Items: {len(data['items'])}")
print(f"Item types: {len(data['item_types'])}")
print(f"Item attributes: {len(data['item_attributes'])}")
print(f"Attribute values: {len(data['attribute_values'])}")
print()

# Get or create a test user
user, created = User.objects.get_or_create(
    email='test@example.com',
    defaults={'username': 'testuser'}
)
if created:
    user.set_password('testpass123')
    user.save()
    print(f"Created test user: {user.email}")
else:
    print(f"Using existing user: {user.email}")

# Create or update item types with unique names for testing
item_type_map = {}  # old_id -> new ItemType
for it_data in data['item_types']:
    unique_name = f"{it_data['name']}_test65"
    item_type, created = ItemType.objects.get_or_create(
        name=unique_name,
        defaults={
            'display_name': it_data['display_name'],
            'icon': it_data['icon'],
            'created_by': user,
        }
    )
    item_type_map[it_data['id']] = item_type
    if created:
        print(f"Created item type: {item_type.name}")

# Create item attributes directly with item_type relationship
item_attr_map = {}  # old_id -> new ItemAttribute
for it_data in data['item_types']:
    item_type = item_type_map[it_data['id']]

    for attr_id in it_data['attribute_ids']:
        # Find the attribute data
        ia_data = next((a for a in data['item_attributes'] if a['id'] == attr_id), None)
        if not ia_data:
            continue

        # Create attribute with unique name
        unique_name = f"{ia_data['name']}_test65_{it_data['id']}"
        item_attr, created = ItemAttribute.objects.get_or_create(
            name=unique_name,
            defaults={
                'display_name': ia_data['display_name'],
                'attribute_type': ia_data['attribute_type'],
                'help_text': ia_data['help_text'],
                'item_type': item_type,
                'created_by': user,
            }
        )
        item_attr_map[attr_id] = item_attr
        if created:
            print(f"Created item attribute: {item_attr.name}")

# Create or update collection
collection, created = Collection.objects.get_or_create(
    hash=data['collection']['hash'],
    defaults={
        'name': data['collection']['name'],
        'description': data['collection']['description'],
        'visibility': data['collection']['visibility'],
        'group_by': data['collection']['group_by'],
        'sort_by': data['collection']['sort_by'],
        'created_by': user,
    }
)
if created:
    print(f"\nCreated collection: {collection.name}")
else:
    print(f"\nUpdating collection: {collection.name}")
    # Clear existing items
    collection.items.all().delete()

# Create items
item_map = {}  # hash -> CollectionItem
for item_data in data['items']:
    item_type_id = item_data.get('item_type_id')
    item = CollectionItem.objects.create(
        collection=collection,
        hash=item_data['hash'],
        name=item_data['name'],
        description=item_data['description'],
        status=item_data['status'],
        is_favorite=item_data['is_favorite'],
        item_type=item_type_map.get(item_type_id) if item_type_id else None,
        created_by=user,
    )
    item_map[item.hash] = item

print(f"Created {len(item_map)} items")

# Create attribute values
for av_data in data['attribute_values']:
    item = item_map.get(av_data['item_hash'])
    item_attr = item_attr_map.get(av_data['item_attribute_id'])

    if item and item_attr:
        CollectionItemAttributeValue.objects.create(
            item=item,
            item_attribute=item_attr,
            value=av_data['value'],
            created_by=user,
        )

print(f"Created {len(data['attribute_values'])} attribute values")

print(f"\n✓ Import complete!")
print(f"\nCollection hash: {collection.hash}")
print(f"Items: {collection.items.count()}")
print(f"Attribute values: {CollectionItemAttributeValue.objects.filter(item__collection=collection).count()}")
