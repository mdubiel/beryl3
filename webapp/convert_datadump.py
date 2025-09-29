#!/usr/bin/env python3
"""
Django Datadump to Beryl3 Import Format Converter
=================================================

Converts Django datadump from old Beryl version to new import format.
Splits data per collection and creates individual import files.
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

def analyze_models(data):
    """Analyze the structure of the datadump"""
    models = defaultdict(int)
    for item in data:
        models[item.get('model', 'unknown')] += 1
    return dict(models)

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

def extract_thing_data_for_thing(data, thing_id):
    """Extract thing data (attributes) for a specific thing"""
    thing_data = []
    for item in data:
        if item.get('model') == 'cls.thingdata':
            if item['fields'].get('thing') == thing_id:
                thing_data.append(item)
    return thing_data

def extract_thing_links_for_thing(data, thing_id):
    """Extract thing links for a specific thing"""
    links = []
    for item in data:
        if item.get('model') == 'cls.thinglink':
            if item['fields'].get('thing') == thing_id:
                links.append(item)
    return links

def extract_thing_types(data):
    """Extract thing types from the datadump"""
    types = {}
    for item in data:
        if item.get('model') == 'cls.thingtype':
            types[item['pk']] = item
    return types

def extract_thing_statuses(data):
    """Extract thing statuses from the datadump"""
    statuses = {}
    for item in data:
        if item.get('model') == 'cls.thingstatus':
            statuses[item['pk']] = item
    return statuses

def extract_thing_attributes(data):
    """Extract thing attributes from the datadump"""
    attributes = {}
    for item in data:
        if item.get('model') == 'cls.thingattribute':
            attributes[item['pk']] = item
    return attributes

def extract_users(data):
    """Extract users from the datadump"""
    users = {}
    for item in data:
        if item.get('model') == 'auth.user':
            users[item['pk']] = item
    return users

def convert_visibility(is_visible):
    """Convert old visibility to new format"""
    return "PUBLIC" if is_visible else "PRIVATE"

def convert_status(old_status_id, statuses):
    """Convert old status ID to new status format"""
    if not old_status_id or old_status_id not in statuses:
        return "IN_COLLECTION"
    
    status_name = statuses[old_status_id]['fields']['name'].lower()
    
    # Map Polish statuses to English equivalents
    status_mapping = {
        'w kolekcji': 'IN_COLLECTION',
        'in collection': 'IN_COLLECTION', 
        'poszukiwane': 'WANTED',
        'zamówione': 'ORDERED',
        'nieznany': 'IN_COLLECTION'
    }
    
    return status_mapping.get(status_name, 'IN_COLLECTION')

def convert_image_path(image_path):
    """Convert old image path to URL format"""
    if not image_path:
        return None
    
    # Clean up the path and convert to URL
    if image_path.startswith('images/'):
        return f"https://example.com/legacy/{image_path}"
    elif image_path.startswith('/home/'):
        # Extract filename from full path
        filename = os.path.basename(image_path)
        return f"https://example.com/legacy/{filename}"
    
    return None

def create_item_type_name(type_id, thing_types):
    """Create item type name from old thing type"""
    if not type_id or type_id not in thing_types:
        return "generic"
    
    type_name = thing_types[type_id]['fields']['name']
    # Convert to snake_case
    return type_name.lower().replace(' ', '_').replace(':', '_').replace('ą', 'a').replace('ę', 'e').replace('ł', 'l').replace('ć', 'c').replace('ń', 'n').replace('ó', 'o').replace('ś', 's').replace('ź', 'z').replace('ż', 'z')

def convert_collection_to_import_format(collection_data, things, thing_data_map, 
                                      thing_links_map, thing_types, statuses, users, thing_attributes):
    """Convert a collection and its items to new import format"""
    
    collection = collection_data['fields']
    collection_id = collection_data['pk']
    
    # Convert collection
    import_data = {
        "version": "1.0",
        "metadata": {
            "title": f"Migration: {collection['name']}",
            "description": f"Migrated collection from legacy Beryl system",
            "source": "legacy_datadump",
            "created_at": datetime.now().isoformat(),
            "created_by": users.get(collection['created_by'], {}).get('fields', {}).get('email', 'unknown'),
            "import_notes": f"Original collection ID: {collection_id}, created: {collection.get('created', 'unknown')}"
        },
        "options": {
            "download_images": True,
            "skip_existing": True,
            "default_visibility": "PRIVATE"
        },
        "collections": [{
            "name": collection['name'],
            "description": collection.get('description', ''),
            "visibility": convert_visibility(collection.get('is_visible', False)),
            "items": []
        }]
    }
    
    # Add image if available
    image_url = convert_image_path(collection.get('image'))
    if image_url:
        import_data["collections"][0]["image_url"] = image_url
    
    # Convert things (items)
    for thing in things:
        thing_fields = thing['fields']
        thing_id = thing['pk']
        
        item = {
            "name": thing_fields['name'],
            "description": thing_fields.get('description', ''),
            "status": convert_status(thing_fields.get('status'), statuses),
            "is_favorite": False,  # Legacy system didn't have favorites
        }
        
        # Add item type
        item_type_name = create_item_type_name(thing_fields.get('type'), thing_types)
        if item_type_name != "generic":
            item["item_type"] = item_type_name
        
        # Add image if available
        image_url = convert_image_path(thing_fields.get('image'))
        if image_url:
            item["image_url"] = image_url
        
        # Add attributes from thing data
        attributes = {}
        if thing_id in thing_data_map:
            for data_item in thing_data_map[thing_id]:
                attr_id = data_item['fields']['attribute']
                attr_value = data_item['fields'].get('description', '')  # Use description field as value
                if attr_id and attr_value and attr_id in thing_attributes:
                    # Get attribute name from thing_attributes
                    attr_name = thing_attributes[attr_id]['fields']['name']
                    # Clean attribute name
                    clean_name = attr_name.lower().replace(' ', '_').replace(':', '').replace('-', '_')
                    attributes[clean_name] = str(attr_value)
        
        if attributes:
            item["attributes"] = attributes
        
        # Add links
        links = []
        if thing_id in thing_links_map:
            for link_item in thing_links_map[thing_id]:
                link_fields = link_item['fields']
                if link_fields.get('url'):
                    links.append({
                        "url": link_fields['url'],
                        "display_name": link_fields.get('name', ''),
                        "order": 0
                    })
        
        if links:
            item["links"] = links
        
        import_data["collections"][0]["items"].append(item)
    
    return import_data

def ensure_directory_exists(directory):
    """Ensure directory exists, create if not"""
    os.makedirs(directory, exist_ok=True)

def main():
    datadump_path = '/home/mdubiel/projects/beryl3/datadump.json'
    output_dir = '/home/mdubiel/projects/beryl3/tmp'
    
    print("Loading Django datadump...")
    data = load_datadump(datadump_path)
    
    print("Analyzing datadump structure...")
    models = analyze_models(data)
    print(f"Found models: {models}")
    
    print("Extracting reference data...")
    users = extract_users(data)
    thing_types = extract_thing_types(data)
    statuses = extract_thing_statuses(data)
    thing_attributes = extract_thing_attributes(data)
    
    print(f"Found {len(users)} users, {len(thing_types)} thing types, {len(statuses)} statuses, {len(thing_attributes)} attributes")
    
    print("Extracting collections...")
    collections = extract_collections(data)
    print(f"Found {len(collections)} collections")
    
    # Create output directory
    ensure_directory_exists(output_dir)
    
    # Build maps for efficient lookup
    print("Building data maps...")
    thing_data_map = defaultdict(list)
    thing_links_map = defaultdict(list)
    
    for item in data:
        if item.get('model') == 'cls.thingdata':
            thing_id = item['fields'].get('thing')
            if thing_id:
                thing_data_map[thing_id].append(item)
        elif item.get('model') == 'cls.thinglink':
            thing_id = item['fields'].get('thing')
            if thing_id:
                thing_links_map[thing_id].append(item)
    
    print(f"Found thing data for {len(thing_data_map)} items, links for {len(thing_links_map)} items")
    
    # Process each collection
    print("\nProcessing collections...")
    converted_count = 0
    
    for collection_data in collections:
        collection_id = collection_data['pk']
        collection_name = collection_data['fields']['name']
        
        print(f"Processing collection: {collection_name} (ID: {collection_id})")
        
        # Extract things for this collection
        things = extract_things_for_collection(data, collection_id)
        print(f"  Found {len(things)} items")
        
        if len(things) == 0:
            print(f"  Skipping empty collection: {collection_name}")
            continue
        
        # Convert to import format
        import_data = convert_collection_to_import_format(
            collection_data, things, thing_data_map, thing_links_map,
            thing_types, statuses, users, thing_attributes
        )
        
        # Create safe filename
        safe_filename = collection_name.lower()
        safe_filename = ''.join(c if c.isalnum() or c in '-_' else '_' for c in safe_filename)
        safe_filename = safe_filename.replace(' ', '_').strip('_')
        
        output_file = os.path.join(output_dir, f"{safe_filename}_import.json")
        
        # Write import file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(import_data, f, indent=2, ensure_ascii=False)
        
        print(f"  Saved: {output_file}")
        converted_count += 1
    
    print(f"\nConversion complete!")
    print(f"Converted {converted_count} collections to import format")
    print(f"Files saved in: {output_dir}")
    
    # Create summary file
    summary_file = os.path.join(output_dir, "conversion_summary.json")
    summary = {
        "conversion_date": datetime.now().isoformat(),
        "source_file": datadump_path,
        "total_collections": len(collections),
        "converted_collections": converted_count,
        "models_found": models,
        "output_directory": output_dir
    }
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Conversion summary saved: {summary_file}")

if __name__ == "__main__":
    main()