"""
Management command to import complete data from a Django fixture datadump.json
including collections, items, attributes, links, and attribute values
"""

import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from web.models import (
    Collection, CollectionItem, ItemType, ItemAttribute, 
    CollectionItemLink, LinkPattern
)

User = get_user_model()
logger = logging.getLogger("webapp")


class Command(BaseCommand):
    help = 'Import complete data from datadump.json including attributes and links'

    def add_arguments(self, parser):
        parser.add_argument('datadump_file', type=str, help='Path to datadump.json file')
        parser.add_argument('--user', type=str, required=True, help='Username to assign imported data to')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without making changes')

    def handle(self, *args, **options):
        datadump_file = options['datadump_file']
        username = options['user']
        dry_run = options['dry_run']

        # Get target user
        try:
            target_user = User.objects.get(username=username)
            self.stdout.write(f"Target user: {target_user.username} (ID: {target_user.id})")
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found")

        # Load datadump file
        try:
            with open(datadump_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.stdout.write(f"Loaded {len(data)} records from {datadump_file}")
        except FileNotFoundError:
            raise CommandError(f"File '{datadump_file}' not found")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON in file: {e}")

        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")

        # Analyze data
        collections = [item for item in data if item['model'] == 'cls.collection']
        things = [item for item in data if item['model'] == 'cls.thing']
        thing_attributes = [item for item in data if item['model'] == 'cls.thingattribute']
        thing_links = [item for item in data if item['model'] == 'cls.thinglink']
        thing_data = [item for item in data if item['model'] == 'cls.thingdata']

        self.stdout.write(f"Found:")
        self.stdout.write(f"  Collections: {len(collections)}")
        self.stdout.write(f"  Things/Items: {len(things)}")
        self.stdout.write(f"  Thing Attributes: {len(thing_attributes)}")
        self.stdout.write(f"  Thing Links: {len(thing_links)}")
        self.stdout.write(f"  Thing Data (attribute values): {len(thing_data)}")

        if dry_run:
            return

        # Import data
        with transaction.atomic():
            try:
                collection_mapping = {}
                thing_mapping = {}  # Maps old thing ID to new CollectionItem ID
                attribute_mapping = {}  # Maps old attribute ID to new ItemAttribute ID
                
                # Get existing collections and items (assume they were already imported)
                existing_collections = Collection.objects.filter(created_by=target_user)
                self.stdout.write(f"Found {existing_collections.count()} existing collections")
                
                # Build collection mapping by name
                for collection in existing_collections:
                    # Find matching old collection by name
                    for col_data in collections:
                        if col_data['fields']['name'] == collection.name:
                            collection_mapping[col_data['pk']] = collection.id
                            break
                
                # Build thing/item mapping
                for thing_data_item in things:
                    fields = thing_data_item['fields']
                    old_collection_id = fields['collection']
                    
                    if old_collection_id in collection_mapping:
                        new_collection_id = collection_mapping[old_collection_id]
                        collection = Collection.objects.get(id=new_collection_id)
                        
                        # Find matching item by name
                        item = CollectionItem.objects.filter(
                            collection=collection,
                            name=fields['name']
                        ).first()
                        
                        if item:
                            thing_mapping[thing_data_item['pk']] = item.id

                self.stdout.write(f"Mapped {len(thing_mapping)} things to collection items")

                # Import Thing Attributes as Item Attributes
                for attr_data in thing_attributes:
                    fields = attr_data['fields']
                    old_id = attr_data['pk']
                    
                    # Check if attribute already exists
                    existing_attr = ItemAttribute.objects.filter(
                        name=fields['name']
                    ).first()
                    
                    if existing_attr:
                        attribute_mapping[old_id] = existing_attr.id
                        continue
                    
                    # Get a generic item type for the attribute
                    generic_item_type = ItemType.objects.filter(name='generic').first()
                    if not generic_item_type:
                        generic_item_type, created = ItemType.objects.get_or_create(
                            name='generic',
                            defaults={
                                'display_name': 'Generic Item',
                                'icon': 'package'
                            }
                        )
                    
                    attribute = ItemAttribute.objects.create(
                        name=fields['name'],
                        display_name=fields['name'],
                        item_type=generic_item_type,
                        attribute_type='text',
                        required=False,
                        help_text='',
                        created_by=target_user,
                        created=timezone.now(),
                        updated=timezone.now()
                    )
                    attribute_mapping[old_id] = attribute.id
                    self.stdout.write(f"Created attribute: {attribute.name}")

                # Import Thing Links as CollectionItemLinks
                link_count = 0
                for link_data in thing_links:
                    fields = link_data['fields']
                    old_thing_id = fields['thing']
                    
                    if old_thing_id not in thing_mapping:
                        continue
                        
                    new_item_id = thing_mapping[old_thing_id]
                    item = CollectionItem.objects.get(id=new_item_id)
                    
                    # Check if link already exists
                    existing_link = CollectionItemLink.objects.filter(
                        item=item,
                        url=fields['url']
                    ).first()
                    
                    if existing_link:
                        continue
                    
                    # Try to find matching link pattern or create generic one
                    link_pattern = LinkPattern.objects.filter(name__icontains='generic').first()
                    if not link_pattern:
                        link_pattern, created = LinkPattern.objects.get_or_create(
                            name='generic',
                            defaults={
                                'display_name': 'Generic Link',
                                'url_pattern': '{url}',
                                'icon': 'link',
                                'description': 'Generic external link',
                                'is_active': True
                            }
                        )
                    
                    link = CollectionItemLink.objects.create(
                        item=item,
                        link_pattern=link_pattern,
                        url=fields['url'],
                        name=fields['name'],
                        display_name=fields['name'],
                        created_by=target_user,
                        created=timezone.now(),
                        updated=timezone.now()
                    )
                    link_count += 1
                    if link_count <= 10:  # Show first few links
                        self.stdout.write(f"Created link: {fields['name']} -> {fields['url'][:50]}...")

                self.stdout.write(f"Created {link_count} links")

                # Import Thing Data as Item Attribute Values
                data_count = 0
                for data_item in thing_data:
                    fields = data_item['fields']
                    old_thing_id = fields['thing']
                    old_attribute_id = fields['attribute']
                    
                    if old_thing_id not in thing_mapping or old_attribute_id not in attribute_mapping:
                        continue
                        
                    new_item_id = thing_mapping[old_thing_id]
                    new_attribute_id = attribute_mapping[old_attribute_id]
                    
                    item = CollectionItem.objects.get(id=new_item_id)
                    attribute = ItemAttribute.objects.get(id=new_attribute_id)
                    
                    # Check if attribute value already exists
                    if hasattr(item, 'attribute_values') and item.attribute_values.filter(attribute=attribute).exists():
                        continue
                    
                    # Create attribute value (this depends on your model structure)
                    # For now, store in description or create a separate model
                    value_text = fields.get('description', '')
                    if value_text:
                        # Add to item description with attribute name
                        if item.description:
                            item.description += f"\n{attribute.name}: {value_text}"
                        else:
                            item.description = f"{attribute.name}: {value_text}"
                        item.save()
                        data_count += 1

                self.stdout.write(f"Processed {data_count} attribute values")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully imported complete data: "
                        f"{len(attribute_mapping)} attributes, {link_count} links, {data_count} values "
                        f"for user {target_user.username}"
                    )
                )

            except Exception as e:
                logger.error(f"Import failed: {e}")
                raise CommandError(f"Import failed: {e}")