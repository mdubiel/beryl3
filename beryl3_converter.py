#!/usr/bin/env python3
"""
Beryl3 Data Converter
====================

Converts legacy Beryl datadump to Beryl3 import format with proper image URL handling.
Based on your examples:

Example 1: Aaricia
  database entry: https://beryl.mdubiel.org/media/home/mdubiel/public_html/media/beryl/images/14-80498250-780d-40fb-923e-d63654c4286cNone
  File: https://beryl.mdubiel.org/media/CACHE/images/674e98a67ed9a5afa8581e8bf52d4bdb.jpg

Example 2: Asteriks i Gladiator  
  database entry: https://beryl.mdubiel.org/media/home/mdubiel/public_html/media/beryl/images/363-0d01cfab-9836-4e3c-a41b-6c9ea8c57dd0.jpg
  File: https://beryl.mdubiel.org/media/CACHE/images/035a76b0d24687b495c8d8f2ebc52f9e.jpg

This means we need to create a manual mapping or use a different approach for image URLs.
"""

import json
import os
import hashlib
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

class BerylDataConverter:
    def __init__(self):
        self.load_extracted_data()
        self.setup_mappings()
        self.setup_manual_image_mappings()
    
    def load_extracted_data(self):
        """Load extracted data from analysis"""
        extracted_file = "/home/mdubiel/projects/beryl3/tmp/analysis/extracted_data.json"
        
        with open(extracted_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.collections = data['collections']
        self.things = data['things']
        self.thing_attributes = data['thing_attributes']
        self.thing_links = data['thing_links']
        self.thing_data = data['thing_data']
        self.image_paths = data['image_paths']
        
        print(f"📊 Loaded data:")
        print(f"  Collections: {len(self.collections)}")
        print(f"  Things: {len(self.things)}")
        print(f"  Thing attributes: {len(self.thing_attributes)}")
        print(f"  Things with images: {len(self.image_paths)}")
    
    def setup_mappings(self):
        """Setup type and attribute mappings"""
        
        # Item type mappings (legacy ID -> Beryl3 type)
        self.type_mappings = {
            1: 'generic',    # Default
            2: 'generic',    # Generic  
            3: 'book',       # Książka i komiks
            4: 'vinyl',      # Płyta winylowa
            5: 'generic',    # Generic
            6: 'lego_set'    # LEGO
        }
        
        # Status mappings
        self.status_mappings = {
            1: 'IN_COLLECTION',  # W kolekcji
            2: 'WANTED',         # Poszukiwane
            3: 'ORDERED',        # Zamówione
            4: 'IN_COLLECTION',  # Unknown -> default
            5: 'IN_COLLECTION'   # Duplicate
        }
        
        # Attribute mappings (Polish/German -> English)
        self.attribute_mappings = {
            'Seria': 'series',
            'Autor': 'author', 
            'Wydawca': 'publisher',
            'Wolumen': 'volume',
            'Przeczytane': 'read',
            'Numer zestawu': 'set_number',
            'Ilość części': 'piece_count',
            'Artist': 'artist',
            'Album': 'album',
            'Rok wydania': 'release_year',
            'Gatunek': 'genre',
            'Wytwórnia': 'label'
        }
        
        print("✅ Mappings configured")
    
    def setup_manual_image_mappings(self):
        """Setup manual image URL mappings based on known examples"""
        
        # Based on your examples, create manual mappings
        # This would need to be populated with actual mappings
        self.manual_image_mappings = {
            # Format: thing_id -> cache_filename
            # Example: 14: "674e98a67ed9a5afa8581e8bf52d4bdb.jpg" (Aaricia)
            # Example: 363: "035a76b0d24687b495c8d8f2ebc52f9e.jpg" (Asteriks i Gladiator)
        }
        
        # Since we don't have the complete mapping, we'll use a different strategy:
        # Generate URLs using the legacy path pattern but mark them for review
        print("📝 Manual image mappings loaded")
    
    def convert_image_url(self, thing_id: int, legacy_path: str, thing_name: str) -> Optional[str]:
        """Convert legacy image path to current cache URL"""
        
        if not legacy_path:
            return None
            
        # Check manual mappings first
        if thing_id in self.manual_image_mappings:
            cache_filename = self.manual_image_mappings[thing_id]
            return f"https://beryl.mdubiel.org/media/CACHE/images/{cache_filename}"
        
        # For items without manual mapping, we'll use the original approach
        # but mark it as needing review in the JSON comments
        
        # Extract filename from legacy path
        filename = os.path.basename(legacy_path)
        if filename.endswith('None'):
            filename = filename[:-4]
        
        # Add extension if missing
        if '.' not in filename:
            filename += '.jpg'
        
        # Return the legacy-based URL (this will likely need manual correction)
        legacy_url = f"https://beryl.mdubiel.org/media/images/{filename}"
        
        return {
            'url': legacy_url,
            'needs_manual_correction': True,
            'legacy_path': legacy_path,
            'note': 'Image URL needs manual verification and correction to CACHE path'
        }
    
    def convert_thing_attributes(self, thing_id: int) -> Dict[str, str]:
        """Convert thing attributes from legacy format"""
        
        attributes = {}
        
        if str(thing_id) in self.thing_data:
            for attr_id, attr_value in self.thing_data[str(thing_id)].items():
                if attr_id in self.thing_attributes:
                    legacy_name = self.thing_attributes[attr_id]['name']
                    english_name = self.attribute_mappings.get(legacy_name, legacy_name.lower())
                    
                    # Get the actual value from the description field
                    value = attr_value.get('description', '')
                    
                    # Handle boolean conversion
                    if english_name == 'read':
                        if value.lower() in ['true', '1', 'yes', 'tak']:
                            value = 'True'
                        else:
                            value = 'False'
                    
                    attributes[english_name] = value
        
        return attributes
    
    def convert_thing_links(self, thing_id: int) -> List[Dict[str, str]]:
        """Convert thing links from legacy format"""
        
        links = []
        
        if str(thing_id) in self.thing_links:
            for link_data in self.thing_links[str(thing_id)]:
                url = link_data.get('url', '')
                if url:
                    links.append({
                        'url': url,
                        'display_name': link_data.get('display_name', self.extract_domain(url))
                    })
        
        return links
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL for display name"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc or url
        except:
            return url
    
    def convert_collection(self, collection_id: int) -> Dict[str, Any]:
        """Convert a single collection with all its items"""
        
        collection_data = self.collections[str(collection_id)]  # Collections use string keys
        collection_name = collection_data['name']
        
        print(f"🔄 Converting collection: {collection_name}")
        
        # Find all things belonging to this collection
        collection_things = []
        for thing_id, thing_data in self.things.items():
            if thing_data.get('collection') == collection_id:
                collection_things.append(thing_id)
        
        print(f"  📦 Found {len(collection_things)} items")
        
        # Convert each thing
        items = []
        for thing_id in collection_things:
            thing_data = self.things[str(thing_id)]  # Things also use string keys
            
            # Determine item type
            thing_type_id = thing_data.get('type', 1)
            item_type = self.type_mappings.get(thing_type_id, 'generic')
            
            # Determine status
            thing_status_id = thing_data.get('status', 1)
            status = self.status_mappings.get(thing_status_id, 'IN_COLLECTION')
            
            # Convert attributes
            attributes = self.convert_thing_attributes(thing_id)
            
            # Convert links
            links = self.convert_thing_links(thing_id)
            
            # Handle image URL
            image_info = None
            legacy_image_path = thing_data.get('image')
            if legacy_image_path:
                image_info = self.convert_image_url(thing_id, legacy_image_path, thing_data['name'])
            
            # Build item
            item = {
                'name': thing_data['name'],
                'description': thing_data.get('description', ''),
                'status': status,
                'is_favorite': False,  # Legacy system doesn't have favorite field
                'item_type': item_type,
                'attributes': attributes
            }
            
            # Add image URL if available
            if image_info:
                if isinstance(image_info, dict) and 'needs_manual_correction' in image_info:
                    # This is a placeholder that needs manual correction
                    item['_image_needs_correction'] = image_info
                else:
                    # This is a proper URL
                    item['image_url'] = image_info
            
            # Add links if available
            if links:
                item['links'] = links
            
            items.append(item)
        
        # Build item type definitions based on items in collection
        item_types_used = set(item['item_type'] for item in items)
        item_type_definitions = []
        
        for item_type in item_types_used:
            definition = self.get_item_type_definition(item_type)
            item_type_definitions.append(definition)
        
        # Build collection structure
        beryl3_collection = {
            'version': '1.0',
            'metadata': {
                'title': f'Migration: {collection_name}',
                'description': 'Migrated collection from legacy Beryl system',
                'source': 'legacy_datadump',
                'created_at': datetime.now().isoformat(),
                'created_by': '',
                'import_notes': f'Original collection ID: {collection_id}, created: {collection_data.get("created", "unknown")}'
            },
            'options': {
                'download_images': True,
                'skip_existing': False,
                'default_visibility': 'PUBLIC'
            },
            'item_types': item_type_definitions,
            'collections': [{
                'name': collection_name,
                'description': collection_data.get('description', ''),
                'visibility': 'PUBLIC' if collection_data.get('is_visible', True) else 'PRIVATE',
                'items': items
            }]
        }
        
        return beryl3_collection
    
    def get_item_type_definition(self, item_type: str) -> Dict[str, Any]:
        """Get item type definition for Beryl3"""
        
        definitions = {
            'book': {
                'name': 'book',
                'display_name': 'Book',
                'description': 'Books and printed publications',
                'icon': 'book',
                'attributes': [
                    {'name': 'author', 'display_name': 'Author', 'attribute_type': 'TEXT', 'required': False, 'order': 1},
                    {'name': 'series', 'display_name': 'Series', 'attribute_type': 'TEXT', 'required': False, 'order': 2},
                    {'name': 'volume', 'display_name': 'Volume', 'attribute_type': 'TEXT', 'required': False, 'order': 3},
                    {'name': 'read', 'display_name': 'Read', 'attribute_type': 'BOOLEAN', 'required': False, 'order': 4},
                    {'name': 'publisher', 'display_name': 'Publisher', 'attribute_type': 'TEXT', 'required': False, 'order': 5}
                ]
            },
            'vinyl': {
                'name': 'vinyl',
                'display_name': 'Vinyl Record',
                'description': 'Vinyl records and albums',
                'icon': 'disc',
                'attributes': [
                    {'name': 'artist', 'display_name': 'Artist', 'attribute_type': 'TEXT', 'required': False, 'order': 1},
                    {'name': 'album', 'display_name': 'Album', 'attribute_type': 'TEXT', 'required': False, 'order': 2},
                    {'name': 'release_year', 'display_name': 'Release Year', 'attribute_type': 'NUMBER', 'required': False, 'order': 3},
                    {'name': 'genre', 'display_name': 'Genre', 'attribute_type': 'TEXT', 'required': False, 'order': 4},
                    {'name': 'label', 'display_name': 'Record Label', 'attribute_type': 'TEXT', 'required': False, 'order': 5}
                ]
            },
            'lego_set': {
                'name': 'lego_set',
                'display_name': 'LEGO Set',
                'description': 'LEGO building sets',
                'icon': 'cube',
                'attributes': [
                    {'name': 'set_number', 'display_name': 'Set Number', 'attribute_type': 'TEXT', 'required': False, 'order': 1},
                    {'name': 'piece_count', 'display_name': 'Piece Count', 'attribute_type': 'NUMBER', 'required': False, 'order': 2},
                    {'name': 'theme', 'display_name': 'Theme', 'attribute_type': 'TEXT', 'required': False, 'order': 3},
                    {'name': 'release_year', 'display_name': 'Release Year', 'attribute_type': 'NUMBER', 'required': False, 'order': 4}
                ]
            },
            'generic': {
                'name': 'generic',
                'display_name': 'Generic Item',
                'description': 'General collectible item',
                'icon': 'package',
                'attributes': []
            }
        }
        
        return definitions.get(item_type, definitions['generic'])
    
    def convert_all_collections(self, output_dir: str):
        """Convert all collections and save to separate files"""
        
        # Create iteration directory
        iteration_dir = f"{output_dir}/data-1"
        os.makedirs(iteration_dir, exist_ok=True)
        
        print(f"🚀 Converting all collections to {iteration_dir}")
        
        for collection_id_str, collection_data in self.collections.items():
            collection_id = int(collection_id_str)  # Convert string key to int for comparison
            collection_name = collection_data['name']
            
            # Convert collection
            converted = self.convert_collection(collection_id)
            
            # Create safe filename
            safe_name = self.create_safe_filename(collection_name)
            filename = f"{safe_name}_import.json"
            filepath = os.path.join(iteration_dir, filename)
            
            # Save file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(converted, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Created: {filename} ({len(converted['collections'][0]['items'])} items)")
        
        # Create summary report
        self.create_summary_report(iteration_dir)
        
        print(f"\n🎉 Conversion complete! Files saved to: {iteration_dir}")
    
    def create_safe_filename(self, name: str) -> str:
        """Create safe filename from collection name"""
        import re
        # Replace special characters with underscores
        safe = re.sub(r'[^\w\s-]', '', name)
        safe = re.sub(r'[\s_-]+', '_', safe)
        return safe.lower()
    
    def create_summary_report(self, output_dir: str):
        """Create summary report of conversion"""
        
        # Count image issues
        image_corrections_needed = 0
        total_items = 0
        
        for file in Path(output_dir).glob("*_import.json"):
            with open(file, 'r') as f:
                data = json.load(f)
            
            for item in data['collections'][0]['items']:
                total_items += 1
                if '_image_needs_correction' in item:
                    image_corrections_needed += 1
        
        report = {
            'conversion_summary': {
                'timestamp': datetime.now().isoformat(),
                'total_collections': len(self.collections),
                'total_items': total_items,
                'image_corrections_needed': image_corrections_needed,
                'notes': [
                    'All items have been converted with proper attributes and links',
                    'Items with _image_needs_correction field require manual image URL updates',
                    'Based on examples provided, images should map to /media/CACHE/images/ URLs',
                    'Manual verification and correction of image URLs is recommended before import'
                ]
            }
        }
        
        report_file = os.path.join(output_dir, 'conversion_report.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Summary: {total_items} items, {image_corrections_needed} need image correction")

if __name__ == "__main__":
    converter = BerylDataConverter()
    converter.convert_all_collections("/home/mdubiel/projects/beryl3/tmp")