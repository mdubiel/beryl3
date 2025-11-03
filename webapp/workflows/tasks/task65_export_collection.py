#!/usr/bin/env python
"""
Task 65 - Export collection data from production for local testing
"""
import os
import sys
import django
import json

# Setup Django
sys.path.insert(0, '/home/mdubiel/beryl3')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from django.core import serializers
from web.models import Collection, CollectionItem, CollectionItemAttributeValue, ItemAttribute, ItemType

# Get the collection
collection_hash = 'j6qJIB8loJ'
collection = Collection.objects.get(hash=collection_hash)

print(f"Exporting collection: {collection.name}")
print(f"Items: {collection.items.count()}")

# Gather all related objects
items = list(collection.items.all())
item_ids = [item.id for item in items]

# Get all attribute values for these items
attr_values = list(CollectionItemAttributeValue.objects.filter(item__in=items))
attr_value_ids = [av.id for av in attr_values]

# Get all item attributes referenced
item_attr_ids = set(av.item_attribute_id for av in attr_values)
item_attributes = list(ItemAttribute.objects.filter(id__in=item_attr_ids))

# Get all item types
item_type_ids = set(item.item_type_id for item in items if item.item_type_id)
item_types = list(ItemType.objects.filter(id__in=item_type_ids))

# Also get attributes for item types
for item_type in item_types:
    for attr in item_type.attributes.all():
        if attr not in item_attributes:
            item_attributes.append(attr)

print(f"Item types: {len(item_types)}")
print(f"Item attributes: {len(item_attributes)}")
print(f"Attribute values: {len(attr_values)}")

# Create export data structure
export_data = {
    'collection': {
        'hash': collection.hash,
        'name': collection.name,
        'description': collection.description,
        'visibility': collection.visibility,
        'group_by': collection.group_by,
        'sort_by': collection.sort_by,
    },
    'item_types': [
        {
            'id': it.id,
            'name': it.name,
            'display_name': it.display_name,
            'icon': it.icon,
            'attribute_ids': [a.id for a in it.attributes.all()]
        }
        for it in item_types
    ],
    'item_attributes': [
        {
            'id': ia.id,
            'name': ia.name,
            'display_name': ia.display_name,
            'attribute_type': ia.attribute_type,
            'help_text': ia.help_text,
        }
        for ia in item_attributes
    ],
    'items': [
        {
            'hash': item.hash,
            'name': item.name,
            'description': item.description,
            'status': item.status,
            'is_favorite': item.is_favorite,
            'item_type_id': item.item_type_id,
        }
        for item in items
    ],
    'attribute_values': [
        {
            'item_hash': av.item.hash,
            'item_attribute_id': av.item_attribute_id,
            'value': av.value,
        }
        for av in attr_values
    ]
}

# Write to JSON file
output_file = '/tmp/collection_j6qJIB8loJ_export.json'
with open(output_file, 'w') as f:
    json.dump(export_data, f, indent=2)

print(f"\nExported to: {output_file}")
print(f"File size: {os.path.getsize(output_file)} bytes")
