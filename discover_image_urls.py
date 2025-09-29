#!/usr/bin/env python3
"""
Image URL Discovery Script
==========================

This script attempts to discover the mapping between legacy image paths
and current cached image URLs by checking what's actually available.
"""

import json
import requests
import os
import hashlib
from urllib.parse import urljoin
import time
from pathlib import Path
from typing import Dict, List

def load_extracted_data(file_path: str):
    """Load the extracted data from analysis"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_url_exists(url: str, timeout: int = 5) -> bool:
    """Check if a URL exists and is accessible"""
    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code == 200
    except:
        return False

def extract_uuid_from_legacy_path(legacy_path: str) -> str:
    """Extract UUID from legacy path"""
    # Pattern: /home/mdubiel/public_html/media/beryl/images/ID-UUID[None]
    if not legacy_path:
        return None
    
    filename = os.path.basename(legacy_path)
    
    # Remove 'None' suffix if present
    if filename.endswith('None'):
        filename = filename[:-4]
    
    # Extract UUID part (after the ID-)
    if '-' in filename:
        parts = filename.split('-', 1)
        if len(parts) > 1:
            return parts[1]  # Return UUID part
    
    return filename

def generate_possible_cache_names(thing_name: str, legacy_path: str) -> List[str]:
    """Generate possible cache file names based on various hashing methods"""
    
    possible_names = []
    
    # Method 1: Hash the thing name
    name_hash = hashlib.md5(thing_name.encode('utf-8')).hexdigest()
    possible_names.append(f"{name_hash}.jpg")
    
    # Method 2: Hash the legacy path
    path_hash = hashlib.md5(legacy_path.encode('utf-8')).hexdigest()
    possible_names.append(f"{path_hash}.jpg")
    
    # Method 3: Use UUID from legacy path
    uuid_part = extract_uuid_from_legacy_path(legacy_path)
    if uuid_part:
        uuid_hash = hashlib.md5(uuid_part.encode('utf-8')).hexdigest()
        possible_names.append(f"{uuid_hash}.jpg")
    
    # Method 4: Hash combination of name and UUID
    if uuid_part:
        combined = f"{thing_name}{uuid_part}"
        combined_hash = hashlib.md5(combined.encode('utf-8')).hexdigest()
        possible_names.append(f"{combined_hash}.jpg")
    
    return list(set(possible_names))  # Remove duplicates

def discover_image_mappings(extracted_data: Dict, base_url: str = "https://beryl.mdubiel.org") -> Dict:
    """Discover image URL mappings by testing different possibilities"""
    
    print("🔍 Discovering image URL mappings...")
    
    cache_base = f"{base_url}/media/CACHE/images/"
    image_paths = extracted_data['image_paths']
    
    mappings = {}
    found_count = 0
    total_count = len(image_paths)
    
    print(f"📊 Testing {total_count} image mappings...")
    
    for i, img_data in enumerate(image_paths):
        thing_id = img_data['thing_id']
        thing_name = img_data['thing_name']
        legacy_path = img_data['image_path']
        
        print(f"  [{i+1}/{total_count}] Testing: {thing_name}")
        
        # Generate possible cache names
        possible_names = generate_possible_cache_names(thing_name, legacy_path)
        
        found_url = None
        for cache_name in possible_names:
            test_url = urljoin(cache_base, cache_name)
            
            if check_url_exists(test_url):
                found_url = test_url
                found_count += 1
                print(f"    ✅ Found: {test_url}")
                break
        
        if found_url:
            mappings[thing_id] = {
                'legacy_path': legacy_path,
                'cache_url': found_url,
                'thing_name': thing_name
            }
        else:
            print(f"    ❌ Not found for: {thing_name}")
            # Still store the mapping but mark as unavailable
            mappings[thing_id] = {
                'legacy_path': legacy_path,
                'cache_url': None,
                'thing_name': thing_name,
                'note': 'Image not found in cache'
            }
        
        # Add small delay to avoid overwhelming the server
        time.sleep(0.1)
    
    print(f"\n📊 Discovery Results:")
    print(f"  ✅ Found: {found_count}/{total_count} ({found_count/total_count*100:.1f}%)")
    print(f"  ❌ Missing: {total_count - found_count}/{total_count}")
    
    return mappings

def save_image_mappings(mappings: Dict, output_file: str):
    """Save the discovered image mappings"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Image mappings saved to: {output_file}")

if __name__ == "__main__":
    extracted_data_path = "/home/mdubiel/projects/beryl3/tmp/analysis/extracted_data.json"
    output_path = "/home/mdubiel/projects/beryl3/tmp/analysis/image_mappings.json"
    
    # Load extracted data
    extracted_data = load_extracted_data(extracted_data_path)
    
    # Discover mappings
    mappings = discover_image_mappings(extracted_data)
    
    # Save results
    save_image_mappings(mappings, output_path)
    
    print("\n🎉 Image URL discovery complete!")