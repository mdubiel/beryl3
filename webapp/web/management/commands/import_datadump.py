"""
Management command to import data from a Django fixture datadump.json
and assign ownership to a specific user
"""

import json
import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from web.models import Collection, CollectionItem, ItemType, LinkPattern

User = get_user_model()
logger = logging.getLogger("webapp")


class Command(BaseCommand):
    help = 'Import data from datadump.json and assign to specified user'

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
        thing_types = [item for item in data if item['model'] == 'cls.thingtype']
        thing_statuses = [item for item in data if item['model'] == 'cls.thingstatus']

        self.stdout.write(f"Found:")
        self.stdout.write(f"  Collections: {len(collections)}")
        self.stdout.write(f"  Things/Items: {len(things)}")
        self.stdout.write(f"  Thing Types: {len(thing_types)}")
        self.stdout.write(f"  Thing Statuses: {len(thing_statuses)}")

        if dry_run:
            return

        # Import data
        with transaction.atomic():
            try:
                # Map old thing types to new item types
                type_mapping = {}
                
                # Import Collections
                collection_mapping = {}
                for col_data in collections:
                    fields = col_data['fields']
                    old_id = col_data['pk']
                    
                    # Skip collections that already have the same name and owner
                    existing = Collection.objects.filter(
                        name=fields['name'], 
                        created_by=target_user
                    ).first()
                    
                    if existing:
                        self.stdout.write(f"Collection '{fields['name']}' already exists, skipping")
                        collection_mapping[old_id] = existing.id
                        continue
                    
                    collection = Collection.objects.create(
                        name=fields['name'],
                        description=fields.get('description', ''),
                        visibility=Collection.Visibility.PRIVATE,  # Default to private
                        created_by=target_user,
                        created=timezone.now(),
                        updated=timezone.now()
                    )
                    collection_mapping[old_id] = collection.id
                    self.stdout.write(f"Created collection: {collection.name}")

                # Import Things as CollectionItems
                for thing_data in things:
                    fields = thing_data['fields']
                    old_collection_id = fields['collection']
                    
                    if old_collection_id not in collection_mapping:
                        self.stdout.write(f"Warning: Collection ID {old_collection_id} not found, skipping thing '{fields['name']}'")
                        continue
                    
                    new_collection_id = collection_mapping[old_collection_id]
                    collection = Collection.objects.get(id=new_collection_id)
                    
                    # Get or create generic item type
                    item_type, created = ItemType.objects.get_or_create(
                        name='generic',
                        defaults={
                            'display_name': 'Generic Item',
                            'icon': 'package'
                        }
                    )
                    
                    # Check if item already exists
                    existing_item = CollectionItem.objects.filter(
                        collection=collection,
                        name=fields['name']
                    ).first()
                    
                    if existing_item:
                        self.stdout.write(f"Item '{fields['name']}' already exists in collection, skipping")
                        continue
                    
                    item = CollectionItem.objects.create(
                        collection=collection,
                        name=fields['name'],
                        item_type=item_type,
                        description=fields.get('description', ''),
                        created_by=target_user,
                        created=timezone.now(),
                        updated=timezone.now()
                    )
                    
                    self.stdout.write(f"Created item: {item.name} in {collection.name}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully imported {len(collections)} collections and {len(things)} items "
                        f"for user {target_user.username}"
                    )
                )

            except Exception as e:
                logger.error(f"Import failed: {e}")
                raise CommandError(f"Import failed: {e}")