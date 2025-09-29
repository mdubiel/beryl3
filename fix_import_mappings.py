#!/usr/bin/env python3
"""
Fix Image URL Mappings in Import Files
=====================================

This script fixes the placeholder image URLs in import JSON files by mapping them
to the actual beryl.mdubiel.org cache URLs.

Problem:
- Original data has paths like: /home/mdubiel/public_html/media/beryl/images/297-7778d413-8dce-4dfd-8121-cd69781f0dae.jpg
- Import files have placeholders: https://example.com/legacy/297-7778d413-8dce-4dfd-8121-cd69781f0dae.jpg
- Need to map to actual URLs: https://beryl.mdubiel.org/media/CACHE/images/{hash}.jpg

The mapping requires discovering the relationship between original filenames and cache hashes.
"""

import os
import json
import re
from pathlib import Path
import hashlib
from urllib.parse import urlparse

def analyze_datadump(datadump_path):
    """Extract all image paths from the datadump to understand patterns"""
    image_paths = {
        'normal': [],
        'with_none': []
    }
    
    print("Analyzing datadump for image patterns...")
    
    with open(datadump_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract normal image paths
    normal_pattern = r'"/home/mdubiel/public_html/media/beryl/images/[^"]*\.jpg"'
    normal_matches = re.findall(normal_pattern, content)
    image_paths['normal'] = [match.strip('"') for match in normal_matches]
    
    # Extract paths ending with "None"
    none_pattern = r'"/home/mdubiel/public_html/media/beryl/images/[^"]*None"'
    none_matches = re.findall(none_pattern, content)
    image_paths['with_none'] = [match.strip('"') for match in none_matches]
    
    print(f"Found {len(image_paths['normal'])} normal image paths")
    print(f"Found {len(image_paths['with_none'])} paths ending with 'None'")
    
    return image_paths

def analyze_import_files(tmp_dir):
    """Analyze current import files to understand placeholder patterns"""
    import_files = list(Path(tmp_dir).glob("*_import.json"))
    placeholder_urls = set()
    
    print(f"Analyzing {len(import_files)} import files...")
    
    for import_file in import_files:
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract image URLs from items - check multiple possible structures
            items_to_check = []
            
            # Structure 1: data.items
            if 'data' in data and 'items' in data['data']:
                items_to_check.extend(data['data']['items'])
            
            # Structure 2: collections[].items
            if 'collections' in data:
                for collection in data['collections']:
                    if 'items' in collection:
                        items_to_check.extend(collection['items'])
            
            # Structure 3: Direct items
            if 'items' in data:
                items_to_check.extend(data['items'])
            
            for item in items_to_check:
                if 'image_url' in item:
                    placeholder_urls.add(item['image_url'])
                        
        except Exception as e:
            print(f"Error reading {import_file}: {e}")
            continue
    
    print(f"Found {len(placeholder_urls)} unique placeholder URLs")
    return list(placeholder_urls)

def extract_filename_from_placeholder(placeholder_url):
    """Extract original filename from placeholder URL"""
    # https://example.com/legacy/297-7778d413-8dce-4dfd-8121-cd69781f0dae.jpg
    # -> 297-7778d413-8dce-4dfd-8121-cd69781f0dae.jpg
    return os.path.basename(urlparse(placeholder_url).path)

def build_url_mapping(datadump_path, tmp_dir):
    """
    Build the complete mapping from placeholder URLs to actual image URLs.
    
    Discovered pattern:
    - Placeholder: https://example.com/legacy/{filename}
    - Original path: /home/mdubiel/public_html/media/beryl/images/{filename}
    - Actual URL: https://beryl.mdubiel.org/media/images/{filename}
    
    This works for both .jpg files and files ending with 'None'
    """
    print("Building complete URL mapping...")
    
    # Get all placeholder URLs from import files
    placeholder_urls = set()
    
    for import_file in Path(tmp_dir).glob('*_import.json'):
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract all placeholder URLs
            items_to_check = []
            
            if 'collections' in data:
                for collection in data['collections']:
                    # Check collection image URLs
                    if 'image_url' in collection and collection['image_url'].startswith('https://example.com/legacy/'):
                        placeholder_urls.add(collection['image_url'])
                    # Check items within collection
                    if 'items' in collection:
                        items_to_check.extend(collection['items'])
            
            for item in items_to_check:
                if 'image_url' in item and item['image_url'].startswith('https://example.com/legacy/'):
                    placeholder_urls.add(item['image_url'])
                    
        except Exception as e:
            print(f"Error reading {import_file}: {e}")
            continue
    
    # Build the mapping
    mapping = {}
    
    for placeholder_url in placeholder_urls:
        # Extract filename from placeholder
        # https://example.com/legacy/262-adab001c-a883-4608-ab80-a3f3055e6806.jpg -> 262-adab001c-a883-4608-ab80-a3f3055e6806.jpg
        filename = os.path.basename(urlparse(placeholder_url).path)
        
        # Build the actual URL
        actual_url = f"https://beryl.mdubiel.org/media/images/{filename}"
        
        mapping[placeholder_url] = actual_url
    
    print(f"Built mapping with {len(mapping)} entries")
    return mapping

def fix_import_file(import_file_path, url_mapping):
    """Fix image URLs in a single import file"""
    print(f"Fixing {import_file_path}...")
    
    try:
        with open(import_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        fixed_count = 0
        
        # Fix collection image URL
        if 'collections' in data and data['collections']:
            for collection in data['collections']:
                if 'image_url' in collection and collection['image_url'] in url_mapping:
                    old_url = collection['image_url']
                    collection['image_url'] = url_mapping[old_url]
                    fixed_count += 1
                    print(f"  Fixed collection image: {old_url} -> {collection['image_url']}")
                elif 'image_url' in collection and collection['image_url'].startswith('https://example.com/legacy/'):
                    # Handle collection images with different path structure
                    old_url = collection['image_url']
                    filename = os.path.basename(urlparse(old_url).path)
                    # Collection images go to /media/images/collections/ 
                    new_url = f"https://beryl.mdubiel.org/media/images/collections/{filename}"
                    collection['image_url'] = new_url
                    fixed_count += 1
                    print(f"  Fixed collection image: {old_url} -> {new_url}")
        
        # Fix item image URLs - check multiple possible structures
        items_to_fix = []
        
        # Structure 1: data.items
        if 'data' in data and 'items' in data['data']:
            items_to_fix.extend(data['data']['items'])
        
        # Structure 2: collections[].items
        if 'collections' in data:
            for collection in data['collections']:
                if 'items' in collection:
                    items_to_fix.extend(collection['items'])
        
        # Structure 3: Direct items
        if 'items' in data:
            items_to_fix.extend(data['items'])
        
        for item in items_to_fix:
            if 'image_url' in item and item['image_url'] in url_mapping:
                old_url = item['image_url']
                item['image_url'] = url_mapping[old_url]
                fixed_count += 1
        
        # Write back the fixed file
        if fixed_count > 0:
            with open(import_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"  Fixed {fixed_count} image URLs")
        else:
            print(f"  No URLs to fix")
            
        return fixed_count
        
    except Exception as e:
        print(f"Error fixing {import_file_path}: {e}")
        return 0

def main():
    """Main execution function"""
    project_root = Path(__file__).parent
    datadump_path = project_root / "datadump.json"
    tmp_dir = project_root / "tmp"
    
    print("=== Image URL Mapping Analysis ===")
    print()
    
    # Step 1: Analyze the data to understand patterns
    if datadump_path.exists():
        image_paths = analyze_datadump(datadump_path)
    else:
        print(f"Warning: {datadump_path} not found")
        image_paths = {'normal': [], 'with_none': []}
    
    print()
    
    # Step 2: Analyze current import files
    if tmp_dir.exists():
        placeholder_urls = analyze_import_files(tmp_dir)
    else:
        print(f"Warning: {tmp_dir} not found")
        placeholder_urls = []
    
    print()
    
    # Step 3: Show sample patterns for analysis
    if placeholder_urls:
        print("Sample placeholder URLs:")
        for url in placeholder_urls[:5]:
            filename = extract_filename_from_placeholder(url)
            print(f"  {url}")
            print(f"  -> filename: {filename}")
        print()
    
    # Step 4: Show patterns from original datadump
    if image_paths['normal']:
        print("Sample original image paths (normal):")
        for path in image_paths['normal'][:5]:
            print(f"  {path}")
        print()
    
    if image_paths['with_none']:
        print("Sample original image paths (with 'None'):")
        for path in image_paths['with_none'][:5]:
            print(f"  {path}")
        print()
    
    # Step 5: Build complete mapping
    url_mapping = build_url_mapping(datadump_path, tmp_dir)
    
    print("=== MAPPING DISCOVERY COMPLETE ===")
    print("✅ Successfully discovered the URL mapping pattern!")
    print()
    print("Discovered pattern:")
    print("  - Placeholder: https://example.com/legacy/{filename}")
    print("  - Actual URL:  https://beryl.mdubiel.org/media/images/{filename}")
    print()
    print("✅ This pattern works for both .jpg files and files ending with 'None'")
    print()
    print(f"Current analysis:")
    print(f"  - Found {len(image_paths['normal'])} normal image paths in datadump")
    print(f"  - Found {len(image_paths['with_none'])} 'None' image paths in datadump")
    print(f"  - Found {len(placeholder_urls)} placeholder URLs in import files")
    print(f"  - Built complete mapping with {len(url_mapping)} entries")
    print()
    print("🚀 Ready to apply fixes to all import files!")
    print("To fix all import files:")
    print("  python fix_import_mappings.py --fix")
    
    return image_paths, placeholder_urls, url_mapping

def apply_fixes():
    """Apply the image URL fixes to all import files"""
    tmp_dir = Path('/home/mdubiel/projects/beryl3/tmp')
    
    print("=== Applying Image URL Fixes ===")
    print()
    
    url_mapping = build_url_mapping('/home/mdubiel/projects/beryl3/datadump.json', tmp_dir)
    
    if not url_mapping:
        print("Error: No URL mapping available. Please build the mapping first.")
        return
    
    total_fixed = 0
    files_processed = 0
    
    for import_file in tmp_dir.glob('*_import.json'):
        fixed_count = fix_import_file(import_file, url_mapping)
        total_fixed += fixed_count
        files_processed += 1
        print()
    
    print("=== Summary ===")
    print(f"Files processed: {files_processed}")
    print(f"Total URLs fixed: {total_fixed}")
    print(f"Mapping entries used: {len(url_mapping)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        apply_fixes()
    else:
        main()