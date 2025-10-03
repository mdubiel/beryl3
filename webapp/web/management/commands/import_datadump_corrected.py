"""
Management command to import data from Django fixture datadump.json
with correct attribute mapping using existing ItemAttributes and JSON schema format
"""

import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from web.models import Collection, CollectionItem, ItemType, ItemAttribute, LinkPattern, CollectionItemLink

User = get_user_model()
logger = logging.getLogger("webapp")


class Command(BaseCommand):
    help = 'Import data from datadump.json with correct attribute mapping'

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

        # Create Polish to English attribute mapping
        polish_to_english = {
            'Seria': 'series',
            'Autor': 'author', 
            'Wydawca': 'publisher',
            'Wolumen': 'volume',
            'Przeczytane': 'read_status',
            'Numer zestawu': 'set_number',
            'Ilość części': 'piece_count'
        }

        # Get existing attributes by name
        existing_attributes = {}
        for attr in ItemAttribute.objects.all():
            existing_attributes[attr.name] = attr

        self.stdout.write(f"Polish attribute mapping:")
        for pol, eng in polish_to_english.items():
            status = "✓ EXISTS" if eng in existing_attributes else "✗ MISSING"
            self.stdout.write(f"  {pol} → {eng} ({status})")

        if dry_run:
            return

        # Clear existing data for user
        self.stdout.write("Clearing existing data for user...")
        CollectionItemLink.objects.filter(created_by=target_user).delete()
        CollectionItem.objects.filter(created_by=target_user).delete()
        Collection.objects.filter(created_by=target_user).delete()

        # Import data
        with transaction.atomic():
            try:
                collection_mapping = {}
                thing_mapping = {}
                
                # Import Collections
                for col_data in collections:
                    fields = col_data['fields']
                    old_id = col_data['pk']
                    
                    collection = Collection.objects.create(
                        name=fields['name'],
                        description=fields.get('description', ''),
                        visibility=Collection.Visibility.PRIVATE,
                        created_by=target_user,
                        created=timezone.now(),
                        updated=timezone.now()
                    )
                    collection_mapping[old_id] = collection.id
                    self.stdout.write(f"Created collection: {collection.name}")

                # Import Things as CollectionItems with proper attributes
                for thing_item in things:
                    fields = thing_item['fields']
                    old_collection_id = fields['collection']
                    old_thing_id = thing_item['pk']
                    
                    if old_collection_id not in collection_mapping:
                        continue
                    
                    new_collection_id = collection_mapping[old_collection_id]
                    collection = Collection.objects.get(id=new_collection_id)
                    
                    # Get or create book item type (most items appear to be books)
                    item_type = ItemType.objects.filter(name='book').first()
                    if not item_type:
                        item_type = ItemType.objects.filter(name='generic').first()
                    
                    # Collect attribute values for this thing
                    thing_attributes_data = {}
                    for data_item in thing_data:
                        if data_item['fields']['thing'] == old_thing_id:
                            old_attribute_id = data_item['fields']['attribute']
                            
                            # Find the Polish attribute name
                            polish_attr = next((attr for attr in thing_attributes if attr['pk'] == old_attribute_id), None)
                            if polish_attr:
                                polish_name = polish_attr['fields']['name']
                                english_name = polish_to_english.get(polish_name)
                                
                                if english_name:
                                    value = data_item['fields'].get('description', '')
                                    thing_attributes_data[english_name] = value
                    
                    item = CollectionItem.objects.create(
                        collection=collection,
                        name=fields['name'],
                        item_type=item_type,
                        description=fields.get('description', ''),
                        attributes=thing_attributes_data,  # Store as JSON
                        created_by=target_user,
                        created=timezone.now(),
                        updated=timezone.now()
                    )
                    thing_mapping[old_thing_id] = item.id
                    
                    if thing_attributes_data:
                        attrs_str = ', '.join([f"{k}={v}" for k, v in thing_attributes_data.items()])
                        self.stdout.write(f"Created item: {item.name} with attributes: {attrs_str}")
                    else:
                        self.stdout.write(f"Created item: {item.name}")

                # Import Thing Links as CollectionItemLinks
                link_count = 0
                for link_data in thing_links:
                    fields = link_data['fields']
                    old_thing_id = fields['thing']
                    
                    if old_thing_id not in thing_mapping:
                        continue
                        
                    new_item_id = thing_mapping[old_thing_id]
                    item = CollectionItem.objects.get(id=new_item_id)
                    
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
                        display_name=fields['name'],
                        created_by=target_user,
                        created=timezone.now(),
                        updated=timezone.now()
                    )
                    link_count += 1
                    if link_count <= 10:
                        self.stdout.write(f"Created link: {fields['name']} -> {fields['url'][:50]}...")

                self.stdout.write(f"Created {link_count} links")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully imported with corrected attributes: "
                        f"{len(collection_mapping)} collections, {len(thing_mapping)} items, {link_count} links "
                        f"for user {target_user.username}"
                    )
                )

            except Exception as e:
                logger.error(f"Import failed: {e}")
                raise CommandError(f"Import failed: {e}")