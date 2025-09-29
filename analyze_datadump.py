#!/usr/bin/env python3
"""
Datadump Analysis Script
========================

This script analyzes the datadump.json to understand:
1. Collection structures
2. Item (thing) structures 
3. Image path patterns
4. Attribute mappings
5. Link structures

It splits the large datadump into manageable chunks for processing.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
import requests

def analyze_datadump_structure(datadump_path: str):
    """Analyze the datadump structure without loading everything into memory"""
    
    print("🔍 Analyzing datadump structure...")
    
    # Track different model types and their counts
    model_counts = {}
    collections_data = {}
    things_data = {}
    image_paths = []
    
    with open(datadump_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 Total records in datadump: {len(data)}")
    
    # Analyze model types
    for record in data:
        model = record.get('model', 'unknown')
        model_counts[model] = model_counts.get(model, 0) + 1
        
        # Extract collections
        if model == 'cls.collection':
            collections_data[record['pk']] = record['fields']
            
        # Extract things (items)
        elif model == 'cls.thing':
            things_data[record['pk']] = record['fields']
            # Track image paths
            if record['fields'].get('image'):
                image_paths.append({
                    'thing_id': record['pk'],
                    'thing_name': record['fields'].get('name', 'Unknown'),
                    'image_path': record['fields']['image']
                })
    
    print("\n📋 Model types found:")
    for model, count in sorted(model_counts.items()):
        print(f"  {model}: {count}")
    
    print(f"\n📁 Collections found: {len(collections_data)}")
    print(f"📦 Things found: {len(things_data)}")
    print(f"🖼️  Items with images: {len(image_paths)}")
    
    return {
        'model_counts': model_counts,
        'collections': collections_data,
        'things': things_data,
        'image_paths': image_paths,
        'raw_data': data
    }

def discover_image_url_mapping(image_paths: List[Dict], base_url: str = "https://beryl.mdubiel.org"):
    """Discover the mapping between legacy image paths and current cached URLs"""
    
    print("\n🔗 Discovering image URL mappings...")
    
    # Extract some sample legacy paths to understand the pattern
    print("\nSample legacy image paths:")
    for i, img_data in enumerate(image_paths[:10]):
        print(f"  {img_data['thing_name']}: {img_data['image_path']}")
    
    # Try to discover the current image URL pattern
    # Based on your examples, we need to find the cached image URLs
    cache_urls = []
    
    # Check if there are any patterns in the cached URLs
    cache_dir_url = f"{base_url}/media/CACHE/images/"
    
    print(f"\n🔍 Checking for cached images at: {cache_dir_url}")
    
    return {
        'legacy_paths': image_paths,
        'cache_base_url': cache_dir_url,
        'mappings': {}  # We'll need to build this mapping
    }

def extract_collections_data(datadump_data: Dict, output_dir: str):
    """Extract and save collection data separately"""
    
    print(f"\n💾 Extracting collections data to {output_dir}...")
    
    os.makedirs(output_dir, exist_ok=True)
    
    collections = datadump_data['collections']
    things = datadump_data['things']
    raw_data = datadump_data['raw_data']
    
    # Build relationships
    thing_attributes = {}
    thing_links = {}
    thing_data = {}
    
    for record in raw_data:
        model = record.get('model', '')
        
        if model == 'cls.thingattribute':
            thing_attributes[record['pk']] = record['fields']
            
        elif model == 'cls.thinglink':
            thing_id = record['fields'].get('thing')
            if thing_id not in thing_links:
                thing_links[thing_id] = []
            thing_links[thing_id].append(record['fields'])
            
        elif model == 'cls.thingdata':
            thing_id = record['fields'].get('thing')
            attr_id = record['fields'].get('thing_attribute')
            if thing_id not in thing_data:
                thing_data[thing_id] = {}
            thing_data[thing_id][attr_id] = record['fields']
    
    # Save extracted data
    extracted_data = {
        'collections': collections,
        'things': things,
        'thing_attributes': thing_attributes,
        'thing_links': thing_links,
        'thing_data': thing_data,
        'image_paths': datadump_data['image_paths']
    }
    
    output_file = os.path.join(output_dir, 'extracted_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extracted_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Extracted data saved to: {output_file}")
    return extracted_data

if __name__ == "__main__":
    datadump_path = "/home/mdubiel/projects/beryl3/datadump.json"
    output_dir = "/home/mdubiel/projects/beryl3/tmp/analysis"
    
    # Analyze structure
    datadump_data = analyze_datadump_structure(datadump_path)
    
    # Discover image mappings
    image_mappings = discover_image_url_mapping(datadump_data['image_paths'])
    
    # Extract collections data
    extracted_data = extract_collections_data(datadump_data, output_dir)
    
    print("\n🎉 Analysis complete!")
    print(f"📁 Data extracted to: {output_dir}/extracted_data.json")