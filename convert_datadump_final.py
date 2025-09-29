#!/usr/bin/env python3
"""
Comprehensive Datadump Conversion Script for Beryl3
==================================================

Converts the legacy Django datadump.json from the original Beryl system
to the new Beryl3 import format with proper:
- Type mappings to existing database item types
- Polish/German to English attribute translation
- Image URL conversion from local paths to web URLs
- Status translation
- Proper relationship mapping

Author: Claude
Date: 2025-09-24
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional


class BerylDataConverter:
    def __init__(self, datadump_path: str):
        self.datadump_path = datadump_path
        self.raw_data = None
        
        # Load and parse the datadump
        self.load_datadump()
        
        # Extract structured data
        self.collections = {}
        self.things = {}
        self.thingtypes = {}
        self.thingstatuses = {}
        self.thingattributes = {}
        self.thingdata = {}
        self.thinglinks = {}
        
        self.parse_datadump()
        
        # Define mappings
        self.setup_mappings()
    
    def load_datadump(self):
        """Load the raw datadump JSON file"""
        with open(self.datadump_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
        print(f"Loaded {len(self.raw_data)} records from datadump")
    
    def parse_datadump(self):
        """Parse and organize datadump by model type"""
        for record in self.raw_data:
            model = record['model']
            pk = record['pk']
            fields = record['fields']
            
            if model == 'cls.collection':
                self.collections[pk] = fields
                self.collections[pk]['id'] = pk
            elif model == 'cls.thing':
                self.things[pk] = fields
                self.things[pk]['id'] = pk
            elif model == 'cls.thingtype':
                self.thingtypes[pk] = fields
                self.thingtypes[pk]['id'] = pk
            elif model == 'cls.thingstatus':
                self.thingstatuses[pk] = fields
                self.thingstatuses[pk]['id'] = pk
            elif model == 'cls.thingattribute':
                self.thingattributes[pk] = fields
                self.thingattributes[pk]['id'] = pk
            elif model == 'cls.thingdata':
                thing_id = fields['thing']
                if thing_id not in self.thingdata:
                    self.thingdata[thing_id] = {}
                attr_id = fields['attribute']
                self.thingdata[thing_id][attr_id] = fields['description']
            elif model == 'cls.thinglink':
                thing_id = fields['thing']
                if thing_id not in self.thinglinks:
                    self.thinglinks[thing_id] = []
                self.thinglinks[thing_id].append(fields)
        
        print(f"Parsed: {len(self.collections)} collections, {len(self.things)} things")
    
    def setup_mappings(self):
        """Set up all necessary mappings for conversion"""
        
        # Legacy type ID to new Beryl3 item type mapping
        self.type_mappings = {
            1: 'generic',  # Default -> Generic
            2: 'generic',  # Generic -> Generic  
            3: 'book',     # Książka i komiks -> Book (covers comics too)
            4: 'vinyl',    # Płyta winylowa -> Vinyl Record
            6: 'lego_set', # LEGO -> LEGO Set
        }
        
        # Legacy status ID to new status mapping
        self.status_mappings = {
            1: 'IN_COLLECTION',  # W kolekcji
            2: 'WANTED',         # Poszukiwane
            3: 'ORDERED',        # Zamówione
            4: 'IN_COLLECTION',  # Nieznany -> Default to IN_COLLECTION
            5: 'IN_COLLECTION',  # In collection (duplicate)
        }
        
        # Polish/German to English attribute name mapping
        self.attribute_mappings = {
            'Seria': 'series',
            'Autor': 'author', 
            'Wydawca': 'publisher',
            'Wolumen': 'volume',
            'Przeczytane': 'read',
            'Numer zestawu': 'set_number',
            'Ilość części': 'piece_count',
        }
        
        # Item type specific attribute mappings for proper validation
        self.type_attributes = {
            'book': ['author', 'series', 'volume', 'read', 'publisher'],
            'comic': ['series', 'volume', 'read', 'author', 'publisher'],
            'vinyl': ['artist', 'album', 'release_year', 'genre', 'label'],
            'lego_set': ['set_number', 'piece_count', 'theme', 'release_year'],
            'board_game': ['designer', 'publisher', 'year_published', 'min_players', 'max_players'],
            'generic': []
        }
    
    def convert_image_url(self, image_path: str) -> Optional[str]:
        """Convert legacy image path to web URL
        
        NOTE: Legacy image paths don't map directly to current cached images.
        The new system uses processed/cached images with different filenames in /media/CACHE/images/.
        For now, we'll skip image URLs and let the SYS Import system handle image discovery
        through the provided links or manual assignment after import.
        """
        # Skip image URL generation - let the import system handle it
        return None
    
    def convert_collection_to_beryl3(self, collection_id: int) -> Dict[str, Any]:
        """Convert a single collection with all its items"""
        collection_data = self.collections[collection_id]
        
        # Get all things belonging to this collection
        collection_things = [
            thing for thing in self.things.values() 
            if thing['collection'] == collection_id
        ]
        
        print(f"Converting collection '{collection_data['name']}' with {len(collection_things)} items")
        
        # Determine item types needed for this collection
        item_types_needed = set()
        for thing in collection_things:
            legacy_type_id = thing['type']
            new_type = self.type_mappings.get(legacy_type_id, 'generic')
            item_types_needed.add(new_type)
        
        # Create item type definitions
        item_types = []
        for item_type in item_types_needed:
            item_types.append(self.create_item_type_definition(item_type))
        
        # Convert items
        items = []
        for thing in collection_things:
            converted_item = self.convert_thing_to_item(thing)
            if converted_item:
                items.append(converted_item)
        
        # Create collection image URL if exists
        collection_image_url = None
        if collection_data.get('image'):
            collection_image_url = self.convert_image_url(collection_data['image'])
        
        # Build the collection structure
        beryl3_collection = {
            "name": collection_data['name'],
            "description": collection_data.get('description', ''),
            "visibility": "PUBLIC" if collection_data.get('is_visible', True) else "PRIVATE",
            "items": items
        }
        
        if collection_image_url:
            beryl3_collection["image_url"] = collection_image_url
        
        return {
            "version": "1.0",
            "metadata": {
                "title": f"Migration: {collection_data['name']}",
                "description": "Migrated collection from legacy Beryl system",
                "source": "legacy_datadump",
                "created_at": datetime.now().isoformat(),
                "created_by": "",
                "import_notes": f"Original collection ID: {collection_id}, created: {collection_data.get('created', 'unknown')}"
            },
            "options": {
                "download_images": True,
                "skip_existing": False,
                "default_visibility": "PUBLIC"
            },
            "item_types": item_types,
            "collections": [beryl3_collection]
        }
    
    def create_item_type_definition(self, item_type: str) -> Dict[str, Any]:
        """Create item type definition based on type"""
        definitions = {
            'generic': {
                "name": "generic",
                "display_name": "Generic Item",
                "description": "General collectible item",
                "icon": "package",
                "attributes": []
            },
            'book': {
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
            },
            'vinyl': {
                "name": "vinyl",
                "display_name": "Vinyl Record",
                "description": "Vinyl records and albums",
                "icon": "disc",
                "attributes": [
                    {"name": "artist", "display_name": "Artist", "attribute_type": "TEXT", "required": False, "order": 1},
                    {"name": "album", "display_name": "Album", "attribute_type": "TEXT", "required": False, "order": 2},
                    {"name": "release_year", "display_name": "Release Year", "attribute_type": "NUMBER", "required": False, "order": 3},
                    {"name": "genre", "display_name": "Genre", "attribute_type": "TEXT", "required": False, "order": 4},
                    {"name": "label", "display_name": "Record Label", "attribute_type": "TEXT", "required": False, "order": 5}
                ]
            },
            'lego_set': {
                "name": "lego_set",
                "display_name": "LEGO Set",
                "description": "LEGO building sets and models",
                "icon": "blocks",
                "attributes": [
                    {"name": "set_number", "display_name": "Set Number", "attribute_type": "TEXT", "required": False, "order": 1},
                    {"name": "piece_count", "display_name": "Piece Count", "attribute_type": "NUMBER", "required": False, "order": 2},
                    {"name": "theme", "display_name": "Theme", "attribute_type": "TEXT", "required": False, "order": 3},
                    {"name": "release_year", "display_name": "Release Year", "attribute_type": "NUMBER", "required": False, "order": 4}
                ]
            },
            'board_game': {
                "name": "board_game",
                "display_name": "Board Game",
                "description": "Board games and tabletop games",
                "icon": "dices",
                "attributes": [
                    {"name": "designer", "display_name": "Designer", "attribute_type": "TEXT", "required": False, "order": 1},
                    {"name": "publisher", "display_name": "Publisher", "attribute_type": "TEXT", "required": False, "order": 2},
                    {"name": "year_published", "display_name": "Year Published", "attribute_type": "NUMBER", "required": False, "order": 3},
                    {"name": "min_players", "display_name": "Min Players", "attribute_type": "NUMBER", "required": False, "order": 4},
                    {"name": "max_players", "display_name": "Max Players", "attribute_type": "NUMBER", "required": False, "order": 5}
                ]
            }
        }
        
        return definitions.get(item_type, definitions['generic'])
    
    def convert_thing_to_item(self, thing: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert a legacy 'thing' to a Beryl3 item"""
        thing_id = thing['id']
        
        # Map type
        legacy_type_id = thing['type']
        item_type = self.type_mappings.get(legacy_type_id, 'generic')
        
        # Map status
        legacy_status_id = thing['status']
        status = self.status_mappings.get(legacy_status_id, 'IN_COLLECTION')
        
        # Convert image
        image_url = self.convert_image_url(thing.get('image', ''))
        
        # Get attributes
        attributes = {}
        if thing_id in self.thingdata:
            for attr_id, value in self.thingdata[thing_id].items():
                if attr_id in self.thingattributes:
                    legacy_attr_name = self.thingattributes[attr_id]['name']
                    english_attr_name = self.attribute_mappings.get(legacy_attr_name, legacy_attr_name.lower())
                    
                    # Convert boolean values
                    if english_attr_name == 'read':
                        # Convert various Polish boolean representations
                        value = value.lower() if isinstance(value, str) else str(value)
                        if value in ['true', '1', 'tak', 'yes', 'prawda']:
                            value = 'True'
                        elif value in ['false', '0', 'nie', 'no', 'fałsz']:
                            value = 'False'
                    
                    # Handle numeric fields
                    elif english_attr_name in ['piece_count', 'release_year', 'year_published']:
                        # Try to convert to number, fallback to string
                        try:
                            if '.' in str(value):
                                value = str(int(float(value)))
                            else:
                                value = str(int(value))
                        except (ValueError, TypeError):
                            value = str(value) if value else ''
                    
                    # Clean string values
                    else:
                        value = str(value).strip() if value else ''
                    
                    if value:  # Only add non-empty values
                        attributes[english_attr_name] = value
        
        # Get links
        links = []
        if thing_id in self.thinglinks:
            for link_data in self.thinglinks[thing_id]:
                if link_data.get('url'):
                    links.append({
                        "url": link_data['url'],
                        "display_name": link_data.get('name', '') or link_data.get('description', '') or 'Link'
                    })
        
        # Build the item
        item = {
            "name": thing['name'],
            "description": thing.get('description', ''),
            "status": status,
            "is_favorite": False,  # Legacy system didn't have favorites
            "item_type": item_type,
            "attributes": attributes
        }
        
        if image_url:
            item["image_url"] = image_url
        
        if links:
            item["links"] = links
        
        return item
    
    def convert_all_collections(self, output_dir: str = "tmp"):
        """Convert all collections to separate import files"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        print(f"Converting all collections to {output_dir}/")
        
        for collection_id, collection_data in self.collections.items():
            # Skip collections without items
            collection_things = [
                thing for thing in self.things.values() 
                if thing['collection'] == collection_id
            ]
            
            if not collection_things:
                print(f"Skipping empty collection: {collection_data['name']}")
                continue
            
            # Convert collection
            beryl3_data = self.convert_collection_to_beryl3(collection_id)
            
            # Generate filename
            safe_name = collection_data['name'].lower()
            # Replace Polish/special characters
            replacements = {
                'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 
                'ś': 's', 'ź': 'z', 'ż': 'z', 'ä': 'a', 'ö': 'o', 'ü': 'u',
                ':': '', ',': '', '(': '', ')': '', "'": '', '"': ''
            }
            for old, new in replacements.items():
                safe_name = safe_name.replace(old, new)
            
            # Clean up and make filesystem safe
            safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in safe_name)
            safe_name = safe_name.replace(' ', '_').replace('__', '_').strip('_')
            
            filename = f"{safe_name}_import.json"
            filepath = os.path.join(output_dir, filename)
            
            # Write file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(beryl3_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Created {filename} ({len(collection_things)} items)")
        
        print(f"\n🎉 Conversion complete! All import files created in {output_dir}/")
        print("Files are ready for import via the Beryl3 SYS Import process")


def main():
    """Main conversion process"""
    datadump_path = "/home/mdubiel/projects/beryl3/datadump.json"
    
    if not os.path.exists(datadump_path):
        print(f"❌ Datadump file not found: {datadump_path}")
        return
    
    print("🔄 Starting comprehensive Beryl datadump conversion...")
    
    # Initialize converter
    converter = BerylDataConverter(datadump_path)
    
    # Convert all collections
    converter.convert_all_collections()
    
    print("\n✨ Conversion process completed successfully!")
    print("Next steps:")
    print("1. Review the generated import files in tmp/")
    print("2. Test import with one file first")
    print("3. Import all collections via SYS Import process")


if __name__ == "__main__":
    main()