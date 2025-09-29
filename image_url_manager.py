#!/usr/bin/env python3
"""
Image URL Manager
================

This script helps manage image URL mapping by:
1. Testing candidate URLs to see which ones actually exist
2. Automatically updating JSON files with working URLs
3. Creating reports of successful mappings
4. Generating new iterations with fixed URLs

Usage:
python image_url_manager.py --check-candidates
python image_url_manager.py --auto-fix
python image_url_manager.py --generate-iteration-2
"""

import json
import requests
import os
import argparse
import time
from pathlib import Path
from typing import Dict, List, Tuple
import hashlib

class ImageURLManager:
    def __init__(self, data_dir: str = "/home/mdubiel/projects/beryl3/tmp/data-1"):
        self.data_dir = data_dir
        self.base_cache_url = "https://beryl.mdubiel.org/media/CACHE/images/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Beryl3-ImageManager/1.0'
        })
        
        # Known working manual mappings
        self.manual_mappings = {
            'Aaricia': '674e98a67ed9a5afa8581e8bf52d4bdb.jpg',
            'Asteriks Gladiator': '035a76b0d24687b495c8d8f2ebc52f9e.jpg'
        }
        
        # Statistics
        self.stats = {
            'total_items': 0,
            'items_needing_correction': 0,
            'successful_mappings': 0,
            'failed_mappings': 0,
            'already_fixed': 0
        }
    
    def check_url_exists(self, url: str, timeout: int = 10) -> bool:
        """Check if a URL exists and returns a valid image"""
        try:
            response = self.session.head(url, timeout=timeout, allow_redirects=True)
            
            # Check if response is successful
            if response.status_code != 200:
                return False
            
            # Check if it's an image
            content_type = response.headers.get('Content-Type', '').lower()
            if not content_type.startswith('image/'):
                return False
            
            # Check if it has reasonable size (not empty, not too large)
            content_length = response.headers.get('Content-Length')
            if content_length:
                size = int(content_length)
                if size < 100 or size > 10_000_000:  # 100 bytes to 10MB
                    return False
            
            return True
            
        except Exception as e:
            print(f"    Error checking {url}: {str(e)}")
            return False
    
    def generate_additional_candidates(self, item_name: str, legacy_path: str) -> List[str]:
        """Generate additional candidate filenames using different strategies"""
        candidates = []
        
        # Strategy 1: Clean name variations
        clean_name = item_name.lower().replace(' ', '').replace('-', '').replace('_', '')
        candidates.append(f"{hashlib.md5(clean_name.encode()).hexdigest()}.jpg")
        
        # Strategy 2: Name with common separators
        for sep in ['-', '_', '.']:
            name_sep = item_name.lower().replace(' ', sep)
            candidates.append(f"{hashlib.md5(name_sep.encode()).hexdigest()}.jpg")
        
        # Strategy 3: Legacy filename variations
        if legacy_path:
            filename = os.path.basename(legacy_path)
            
            # Remove common suffixes
            for suffix in ['None', '.jpg', '.jpeg', '.png']:
                if filename.endswith(suffix):
                    filename = filename[:-len(suffix)]
            
            # Try different hashing approaches
            candidates.append(f"{hashlib.md5(filename.encode()).hexdigest()}.jpg")
            candidates.append(f"{hashlib.sha1(filename.encode()).hexdigest()}.jpg")
        
        # Strategy 4: Sequential ID patterns (common in cache systems)
        if legacy_path and '-' in legacy_path:
            parts = os.path.basename(legacy_path).split('-')
            if parts and parts[0].isdigit():
                item_id = parts[0]
                # Try common cache patterns
                candidates.extend([
                    f"{item_id}.jpg",
                    f"item_{item_id}.jpg",
                    f"image_{item_id}.jpg",
                    f"{hashlib.md5(item_id.encode()).hexdigest()}.jpg"
                ])
        
        return list(set(candidates))  # Remove duplicates
    
    def check_candidates_for_item(self, item_name: str, correction_data: dict) -> Tuple[str, bool]:
        """Check all candidates for an item and return the first working URL"""
        
        print(f"  🔍 Checking: {item_name}")
        
        # Check manual mappings first
        if item_name in self.manual_mappings:
            cache_filename = self.manual_mappings[item_name]
            url = f"{self.base_cache_url}{cache_filename}"
            print(f"    ✅ FOUND in manual mappings!")
            return url, True
        
        # Get existing candidates
        candidates = correction_data.get('candidates', [])
        
        # Generate additional candidates
        additional_candidates = self.generate_additional_candidates(
            item_name, 
            correction_data.get('legacy_path', '')
        )
        
        # Combine all candidates (existing first, then additional)
        all_candidates = candidates + additional_candidates
        
        # Remove duplicates while preserving order
        seen = set()
        unique_candidates = []
        for candidate in all_candidates:
            if candidate not in seen:
                seen.add(candidate)
                unique_candidates.append(candidate)
        
        print(f"    Testing {len(unique_candidates)} candidates...")
        
        # Test each candidate
        for i, candidate in enumerate(unique_candidates):
            url = f"{self.base_cache_url}{candidate}"
            
            print(f"    [{i+1}/{len(unique_candidates)}] {candidate}...", end=' ')
            
            if self.check_url_exists(url):
                print("✅ FOUND!")
                return url, True
            else:
                print("❌")
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        print(f"    ❌ No working URL found for: {item_name}")
        return None, False
    
    def check_all_candidates(self) -> Dict[str, str]:
        """Check candidates for all items needing correction"""
        
        print("🔍 Checking candidate URLs for all items...")
        
        successful_mappings = {}
        
        for json_file in Path(self.data_dir).glob("*_import.json"):
            print(f"\n📁 Processing: {json_file.name}")
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for collection in data.get('collections', []):
                for item in collection.get('items', []):
                    self.stats['total_items'] += 1
                    
                    if '_manual_image_correction_needed' in item:
                        self.stats['items_needing_correction'] += 1
                        correction_data = item['_manual_image_correction_needed']
                        item_name = item['name']
                        
                        url, found = self.check_candidates_for_item(item_name, correction_data)
                        
                        if found:
                            successful_mappings[item_name] = url
                            self.stats['successful_mappings'] += 1
                        else:
                            self.stats['failed_mappings'] += 1
                    
                    elif 'image_url' in item:
                        self.stats['already_fixed'] += 1
        
        return successful_mappings
    
    def auto_fix_urls(self, mappings: Dict[str, str] = None) -> bool:
        """Automatically fix URLs based on successful mappings"""
        
        if mappings is None:
            print("🔍 First checking candidates to find working URLs...")
            mappings = self.check_all_candidates()
        
        if not mappings:
            print("❌ No working URLs found to fix automatically")
            return False
        
        print(f"\n🔧 Auto-fixing {len(mappings)} items with working URLs...")
        
        # Apply fixes to all JSON files
        for json_file in Path(self.data_dir).glob("*_import.json"):
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            modified = False
            
            for collection in data.get('collections', []):
                for item in collection.get('items', []):
                    
                    if '_manual_image_correction_needed' in item:
                        item_name = item['name']
                        
                        if item_name in mappings:
                            # Replace correction field with proper image_url
                            item['image_url'] = mappings[item_name]
                            del item['_manual_image_correction_needed']
                            modified = True
                            print(f"  ✅ Fixed: {item_name}")
            
            # Save modified file
            if modified:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"  💾 Updated: {json_file.name}")
        
        return True
    
    def generate_next_iteration(self) -> str:
        """Generate a new iteration with all fixes applied"""
        
        # Create new iteration directory
        iteration_num = 2
        while os.path.exists(f"/home/mdubiel/projects/beryl3/tmp/data-{iteration_num}"):
            iteration_num += 1
        
        new_dir = f"/home/mdubiel/projects/beryl3/tmp/data-{iteration_num}"
        os.makedirs(new_dir, exist_ok=True)
        
        print(f"📁 Creating iteration {iteration_num} in: {new_dir}")
        
        # Copy all files to new iteration
        for json_file in Path(self.data_dir).glob("*_import.json"):
            
            # Read current file
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update metadata
            if 'metadata' in data:
                data['metadata']['iteration'] = iteration_num
                data['metadata']['updated_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
            
            # Write to new iteration
            new_file = os.path.join(new_dir, json_file.name)
            with open(new_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Create iteration report
        self.create_iteration_report(new_dir, iteration_num)
        
        print(f"✅ Iteration {iteration_num} created successfully!")
        return new_dir
    
    def create_iteration_report(self, output_dir: str, iteration_num: int):
        """Create a report for the iteration"""
        
        total_images = 0
        fixed_images = 0
        remaining_corrections = 0
        
        # Count statistics
        for json_file in Path(output_dir).glob("*_import.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for collection in data.get('collections', []):
                for item in collection.get('items', []):
                    if 'image_url' in item:
                        fixed_images += 1
                        total_images += 1
                    elif '_manual_image_correction_needed' in item:
                        remaining_corrections += 1
                        total_images += 1
        
        report = f"""# Image URL Management Report - Iteration {iteration_num}

## Summary
- **Total Items with Images**: {total_images}
- **Fixed Automatically**: {fixed_images}
- **Still Need Manual Correction**: {remaining_corrections}
- **Success Rate**: {(fixed_images/total_images*100):.1f}% if total_images > 0 else 0

## Automatic Fixes Applied
{self.stats['successful_mappings']} items were automatically fixed by testing candidate URLs.

## Remaining Manual Work
{remaining_corrections} items still need manual image URL correction.

## Next Steps
{'✅ Ready for import!' if remaining_corrections == 0 else f'❌ {remaining_corrections} items still need manual correction'}

---
*Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        report_file = os.path.join(output_dir, f'IMAGE_URL_REPORT_ITERATION_{iteration_num}.md')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"📊 Report saved: {report_file}")
    
    def print_stats(self):
        """Print current statistics"""
        print(f"\n📊 Image URL Management Statistics:")
        print(f"  Total items processed: {self.stats['total_items']}")
        print(f"  Items needing correction: {self.stats['items_needing_correction']}")
        print(f"  Successfully mapped: {self.stats['successful_mappings']}")
        print(f"  Failed mappings: {self.stats['failed_mappings']}")
        print(f"  Already fixed: {self.stats['already_fixed']}")

def main():
    parser = argparse.ArgumentParser(description='Manage image URLs for Beryl3 import files')
    parser.add_argument('--check-candidates', action='store_true', 
                       help='Check all candidate URLs to find working ones')
    parser.add_argument('--auto-fix', action='store_true',
                       help='Automatically fix URLs with working candidates')
    parser.add_argument('--generate-iteration', action='store_true',
                       help='Generate new iteration with fixes applied')
    parser.add_argument('--data-dir', default="/home/mdubiel/projects/beryl3/tmp/data-1",
                       help='Directory containing JSON files')
    
    args = parser.parse_args()
    
    manager = ImageURLManager(args.data_dir)
    
    if args.check_candidates:
        mappings = manager.check_all_candidates()
        manager.print_stats()
        
        if mappings:
            print(f"\n✅ Found {len(mappings)} working image URLs!")
            for name, url in mappings.items():
                print(f"  {name} -> {url}")
        else:
            print("\n❌ No working image URLs found")
    
    elif args.auto_fix:
        success = manager.auto_fix_urls()
        manager.print_stats()
        
        if success:
            print("\n✅ Auto-fix completed!")
        else:
            print("\n❌ No URLs could be fixed automatically")
    
    elif args.generate_iteration:
        new_dir = manager.generate_next_iteration()
        manager.print_stats()
        print(f"\n✅ New iteration created: {new_dir}")
    
    else:
        # Default: check candidates and auto-fix if found
        print("🚀 Running full image URL management process...")
        
        mappings = manager.check_all_candidates()
        
        if mappings:
            manager.auto_fix_urls(mappings)
            new_dir = manager.generate_next_iteration()
            print(f"\n🎉 Process complete! New iteration: {new_dir}")
        else:
            print("\n❌ No working image URLs found - manual correction still needed")
        
        manager.print_stats()

if __name__ == "__main__":
    main()