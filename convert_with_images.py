#!/usr/bin/env python3
"""
Django Datadump to Beryl3 Import Format Converter WITH IMAGES
==============================================================

Converts Django datadump from old Beryl version to new import format.
Includes proper image URL conversion from database paths to beryl.mdubiel.org URLs.
"""

import os
import json
import sys
from datetime import datetime
from collections import defaultdict

def load_datadump(filepath):
    """Load Django datadump JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def convert_image_url(original_path):
    """Convert database image path to beryl.mdubiel.org URL"""
    if not original_path:
        return None
    
    # Extract filename from path like "/home/mdubiel/public_html/media/beryl/images/1-54bdb67a-01b8-4928-867e-47697414cb40None"
    if "/beryl/images/" in original_path:
        filename = original_path.split("/beryl/images/")[-1]
        return f"https://beryl.mdubiel.org/media/images/{filename}"
    
    return None

def extract_collections(data):
    """Extract collections from the datadump"""
    collections = []
    for item in data:
        if item.get('model') == 'cls.collection':
            collections.append(item)
    return collections

def extract_things_for_collection(data, collection_id):
    """Extract things (items) for a specific collection"""
    things = []
    for item in data:
        if item.get('model') == 'cls.thing':
            if item['fields'].get('collection') == collection_id:
                things.append(item)
    return things

def extract_attributes_mappings(data):
    """Extract attribute name mappings"""
    mappings = {}
    for item in data:
        if item.get('model') == 'cls.thingattribute':
            attr_id = item['pk']
            attr_name = item['fields']['name']
            mappings[attr_id] = attr_name
    return mappings

def extract_thing_data_for_thing(data, thing_id):
    """Extract thing data (attributes) for a specific thing"""
    thing_data = []
    for item in data:
        if item.get('model') == 'cls.thingdata':
            if item['fields'].get('thing') == thing_id:
                thing_data.append(item)
    return thing_data

def extract_status_mappings(data):
    """Extract status mappings"""
    mappings = {}
    for item in data:
        if item.get('model') == 'cls.thingstatus':
            status_id = item['pk']
            status_name = item['fields']['name']
            mappings[status_id] = status_name
    return mappings

def extract_type_mappings(data):
    """Extract type mappings"""
    mappings = {}
    for item in data:
        if item.get('model') == 'cls.thingtype':
            type_id = item['pk']
            type_name = item['fields']['name']
            mappings[type_id] = type_name
    return mappings

def convert_status_to_english(status_name):
    """Convert Polish/German status to English constants"""
    status_mapping = {
        'W kolekcji': 'IN_COLLECTION',
        'In collection': 'IN_COLLECTION', 
        'Poszukiwane': 'WANTED',
        'Zamówione': 'ORDERED',
        'Nieznany': 'UNKNOWN'
    }
    return status_mapping.get(status_name, 'UNKNOWN')

def convert_type_to_english(type_name):
    """Convert Polish type to English"""
    type_mapping = {
        'Książka i komiks': 'book',
        'Płyta winylowa': 'vinyl',
        'LEGO': 'lego_set',
        'Default': 'generic',
        'Generic': 'generic'
    }
    return type_mapping.get(type_name, 'generic')

def convert_attribute_name(attr_name):
    """Convert Polish attribute names to English"""
    attr_mapping = {
        'Seria': 'series',
        'Autor': 'author', 
        'Wydawca': 'publisher',
        'Wolumen': 'volume',
        'Przeczytane': 'read',
        'Numer zestawu': 'set_number',
        'Ilość części': 'piece_count'
    }
    return attr_mapping.get(attr_name, attr_name.lower().replace(' ', '_'))

def process_collection(data, collection, attr_mappings, status_mappings, type_mappings):
    """Process a single collection and its items"""
    collection_id = collection['pk']
    collection_name = collection['fields']['name']
    
    # Get collection image URL
    collection_image_url = None
    collection_image_path = collection['fields'].get('image', '')
    if collection_image_path:
        # Convert collection image path
        if collection_image_path.startswith('images/collections/'):
            filename = collection_image_path.split('/')[-1]
            collection_image_url = f"https://beryl.mdubiel.org/media/images/collections/{filename}"
    
    print(f"Processing collection: {collection_name} (ID: {collection_id})")
    
    # Get all things (items) for this collection
    things = extract_things_for_collection(data, collection_id)
    print(f"  Found {len(things)} items")
    
    items = []
    for thing in things:
        thing_id = thing['pk']
        thing_fields = thing['fields']
        
        # Convert status
        status_id = thing_fields.get('status')
        status_name = status_mappings.get(status_id, 'Unknown')
        english_status = convert_status_to_english(status_name)
        
        # Convert type
        type_id = thing_fields.get('type')
        type_name = type_mappings.get(type_id, 'Generic')
        english_type = convert_type_to_english(type_name)
        
        # Convert image URL
        image_url = convert_image_url(thing_fields.get('image'))
        
        # Get attributes for this thing
        thing_data = extract_thing_data_for_thing(data, thing_id)
        attributes = {}
        for td in thing_data:
            attr_id = td['fields']['attribute']
            attr_value = td['fields']['description']
            attr_name = attr_mappings.get(attr_id, f'unknown_{attr_id}')
            english_attr_name = convert_attribute_name(attr_name)
            attributes[english_attr_name] = attr_value
        
        item = {
            "name": thing_fields['name'],
            "description": thing_fields.get('description', ''),
            "status": english_status,
            "is_favorite": False,
            "item_type": english_type,
            "attributes": attributes
        }
        
        # Add image URL if available
        if image_url:
            item["image_url"] = image_url
            
        items.append(item)
    
    # Create collection object
    collection_obj = {
        "name": collection_name,
        "description": collection['fields'].get('description', ''),
        "visibility": "PUBLIC",
        "items": items
    }
    
    # Add collection image URL if available
    if collection_image_url:
        collection_obj["image_url"] = collection_image_url
    
    return collection_obj

def main():
    if len(sys.argv) != 2:
        print("Usage: python convert_with_images.py <datadump.json>")
        sys.exit(1)
    
    datadump_path = sys.argv[1]
    
    print(f"Loading datadump from: {datadump_path}")
    data = load_datadump(datadump_path)
    
    # Extract mappings
    print("Extracting mappings...")
    attr_mappings = extract_attributes_mappings(data)
    status_mappings = extract_status_mappings(data)
    type_mappings = extract_type_mappings(data)
    
    print(f"Found {len(attr_mappings)} attributes")
    print(f"Found {len(status_mappings)} statuses") 
    print(f"Found {len(type_mappings)} types")
    
    # Extract collections
    collections = extract_collections(data)
    print(f"Found {len(collections)} collections")
    
    # Create output directory
    output_dir = "tmp"
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each collection
    for collection in collections:
        collection_data = process_collection(data, collection, attr_mappings, status_mappings, type_mappings)
        
        # Skip empty collections
        if not collection_data['items']:
            print(f"  Skipping empty collection: {collection_data['name']}")
            continue
            
        # Determine item types used in this collection
        item_types_used = set()
        for item in collection_data['items']:
            item_types_used.add(item['item_type'])
        
        # Create item type definitions
        item_types = []
        for item_type in item_types_used:
            if item_type == 'lego_set':
                item_types.append({
                    "name": "lego_set",
                    "display_name": "LEGO Set",
                    "description": "LEGO building sets and models",
                    "icon": "blocks",
                    "attributes": [
                        {"name": "set_number", "display_name": "Set Number", "attribute_type": "TEXT", "required": False, "order": 1},
                        {"name": "piece_count", "display_name": "Piece Count", "attribute_type": "NUMBER", "required": False, "order": 2},
                        {"name": "series", "display_name": "Series", "attribute_type": "TEXT", "required": False, "order": 3}
                    ]
                })
            elif item_type == 'book':
                item_types.append({
                    "name": "book",
                    "display_name": "Book",
                    "description": "Books and printed publications",
                    "icon": "book",
                    "attributes": [
                        {"name": "author", "display_name": "Author", "attribute_type": "TEXT", "required": False, "order": 1},
                        {"name": "series", "display_name": "Series", "attribute_type": "TEXT", "required": False, "order": 2},
                        {"name": "volume", "display_name": "Volume", "attribute_type": "TEXT", "required": False, "order": 3},
                        {"name": "read", "display_name": "Read", "attribute_type": "BOOLEAN", "required": False, "order": 4},
                        {"name": "publisher", "display_name": "Publisher", "attribute_type": "TEXT", "required": False, "order": 5}
                    ]
                })
            elif item_type == 'vinyl':
                item_types.append({
                    "name": "vinyl",
                    "display_name": "Vinyl Record",
                    "description": "Vinyl records and albums",
                    "icon": "disc",
                    "attributes": [
                        {"name": "artist", "display_name": "Artist", "attribute_type": "TEXT", "required": False, "order": 1},
                        {"name": "album", "display_name": "Album", "attribute_type": "TEXT", "required": False, "order": 2},
                        {"name": "year", "display_name": "Year", "attribute_type": "NUMBER", "required": False, "order": 3}
                    ]
                })
            elif item_type == 'generic':
                item_types.append({
                    "name": "generic", 
                    "display_name": "Generic Item",
                    "description": "General collectible item",
                    "icon": "package",
                    "attributes": []
                })
        
        # Create import file
        import_data = {
            "version": "1.0",
            "metadata": {
                "title": f"Migration: {collection_data['name']}",
                "description": "Migrated collection from legacy Beryl system",
                "source": "legacy_datadump",
                "created_at": datetime.now().isoformat(),
                "created_by": "",
                "import_notes": f"Original collection ID: {collection['pk']}, created: {collection['fields']['created']}"
            },
            "options": {
                "download_images": True,
                "skip_existing": False,
                "default_visibility": "PUBLIC"
            },
            "item_types": item_types,
            "collections": [collection_data]
        }
        
        # Generate filename
        safe_name = "".join(c for c in collection_data['name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_name = safe_name.replace(' ', '_').lower()
        filename = f"{output_dir}/{safe_name}_import.json"
        
        # Write file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(import_data, f, indent=2, ensure_ascii=False)
        
        print(f"  Created: {filename} ({len(collection_data['items'])} items)")

if __name__ == "__main__":
    main()