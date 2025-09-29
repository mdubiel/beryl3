#!/usr/bin/env python3
"""
Image URL Fix Script
===================

This script fixes the image URLs in the converted JSON files based on the examples provided:

Example 1: Aaricia
  database entry: https://beryl.mdubiel.org/media/home/mdubiel/public_html/media/beryl/images/14-80498250-780d-40fb-923e-d63654c4286cNone
  File: https://beryl.mdubiel.org/media/CACHE/images/674e98a67ed9a5afa8581e8bf52d4bdb.jpg

Example 2: Asteriks i Gladiator
  database entry: https://beryl.mdubiel.org/media/home/mdubiel/public_html/media/beryl/images/363-0d01cfab-9836-4e3c-a41b-6c9ea8c57dd0.jpg
  File: https://beryl.mdubiel.org/media/CACHE/images/035a76b0d24687b495c8d8f2ebc52f9e.jpg

Since we don't have the complete mapping, this script will:
1. Load the converted files
2. Add proper image_url fields where images exist
3. Use manual mappings where available
4. Create placeholder URLs for manual correction
"""

import json
import os
from pathlib import Path
import hashlib
import re
from typing import List

def setup_manual_mappings():
    """Setup manual image mappings based on known examples"""
    
    # Manual mappings from your examples
    # Format: item_name -> cache_filename
    manual_mappings = {
        'Aaricia': '674e98a67ed9a5afa8581e8bf52d4bdb.jpg',
        'Asteriks i Gladiator': '035a76b0d24687b495c8d8f2ebc52f9e.jpg'
    }
    
    return manual_mappings

def generate_cache_url_candidates(legacy_path: str, item_name: str) -> List[str]:
    """Generate possible cache URL candidates"""
    
    candidates = []
    base_url = "https://beryl.mdubiel.org/media/CACHE/images/"
    
    # Method 1: Hash the item name
    name_clean = re.sub(r'[^\w\s-]', '', item_name).strip()
    name_hash = hashlib.md5(name_clean.encode('utf-8')).hexdigest()
    candidates.append(f"{name_hash}.jpg")
    
    # Method 2: Extract UUID from legacy path and hash it
    if legacy_path:
        filename = os.path.basename(legacy_path)
        if filename.endswith('None'):
            filename = filename[:-4]
        
        # Extract UUID part
        if '-' in filename:
            parts = filename.split('-', 1)
            if len(parts) > 1:
                uuid_part = parts[1]
                uuid_hash = hashlib.md5(uuid_part.encode('utf-8')).hexdigest()
                candidates.append(f"{uuid_hash}.jpg")
    
    # Method 3: Hash the full legacy path
    if legacy_path:
        path_hash = hashlib.md5(legacy_path.encode('utf-8')).hexdigest()
        candidates.append(f"{path_hash}.jpg")
    
    return candidates

def fix_image_urls_in_file(file_path: str, manual_mappings: dict):
    """Fix image URLs in a single JSON file"""
    
    print(f"🔧 Fixing image URLs in: {os.path.basename(file_path)}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items_with_images = 0
    items_fixed = 0
    items_need_manual = 0
    
    for collection in data.get('collections', []):
        for item in collection.get('items', []):
            
            # Check if item has image correction info
            if '_image_needs_correction' in item:
                items_with_images += 1
                image_info = item['_image_needs_correction']
                item_name = item['name']
                legacy_path = image_info.get('legacy_path', '')
                
                # Check manual mappings first
                if item_name in manual_mappings:
                    cache_filename = manual_mappings[item_name]
                    item['image_url'] = f"https://beryl.mdubiel.org/media/CACHE/images/{cache_filename}"
                    del item['_image_needs_correction']
                    items_fixed += 1
                    print(f"  ✅ Fixed: {item_name}")
                else:
                    # Generate candidates for manual review
                    candidates = generate_cache_url_candidates(legacy_path, item_name)
                    
                    # Use the first candidate as a placeholder
                    placeholder_url = f"https://beryl.mdubiel.org/media/CACHE/images/{candidates[0]}"
                    
                    # Store as comment for manual correction
                    item['_manual_image_correction_needed'] = {
                        'item_name': item_name,
                        'legacy_path': legacy_path,
                        'placeholder_url': placeholder_url,
                        'candidates': candidates,
                        'note': 'MANUAL_CORRECTION_REQUIRED: This image URL needs to be manually verified and corrected'
                    }
                    
                    del item['_image_needs_correction']
                    items_need_manual += 1
    
    # Save fixed file
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  📊 Images: {items_with_images}, Fixed: {items_fixed}, Need manual: {items_need_manual}")
    
    return items_with_images, items_fixed, items_need_manual

def fix_all_image_urls(directory: str):
    """Fix image URLs in all JSON files in the directory"""
    
    print(f"🔧 Fixing image URLs in all files in: {directory}")
    
    manual_mappings = setup_manual_mappings()
    
    total_images = 0
    total_fixed = 0
    total_manual = 0
    
    for json_file in Path(directory).glob("*_import.json"):
        images, fixed, manual = fix_image_urls_in_file(str(json_file), manual_mappings)
        total_images += images
        total_fixed += fixed
        total_manual += manual
    
    print(f"\n📊 Summary:")
    print(f"  Total images: {total_images}")
    print(f"  Fixed automatically: {total_fixed}")
    print(f"  Need manual correction: {total_manual}")
    
    if total_manual > 0:
        print(f"\n⚠️  MANUAL CORRECTION REQUIRED:")
        print(f"  {total_manual} items have '_manual_image_correction_needed' field")
        print(f"  These need to be manually corrected with actual CACHE URLs")
        print(f"  Remove the '_manual_image_correction_needed' field after adding 'image_url'")

if __name__ == "__main__":
    directory = "/home/mdubiel/projects/beryl3/tmp/data-1"
    fix_all_image_urls(directory)