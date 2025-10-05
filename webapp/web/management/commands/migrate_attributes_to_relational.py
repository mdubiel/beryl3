"""
Management command to migrate CollectionItem attributes from JSON field to relational model.

This command:
1. Reads all CollectionItem.attributes (JSON field)
2. For each attribute in JSON, creates a CollectionItemAttributeValue record
3. Matches attribute names to ItemAttribute definitions
4. Handles orphaned attributes (no matching ItemAttribute)
5. Provides detailed migration report

Usage:
    python manage.py migrate_attributes_to_relational [options]

Options:
    --dry-run          Show what would be migrated without making changes
    --item-hash HASH   Migrate only specific item by hash
    --batch-size N     Process items in batches of N (default: 100)
    --skip-orphaned    Skip attributes that don't have ItemAttribute definitions
"""

import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from web.models import CollectionItem, CollectionItemAttributeValue, ItemAttribute

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Migrate item attributes from JSON field to relational CollectionItemAttributeValue model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes'
        )
        parser.add_argument(
            '--item-hash',
            type=str,
            help='Migrate only a specific item by hash'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Process items in batches of this size (default: 100)'
        )
        parser.add_argument(
            '--skip-orphaned',
            action='store_true',
            help='Skip attributes that don\'t have ItemAttribute definitions'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed progress'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        item_hash = options.get('item_hash')
        batch_size = options['batch_size']
        skip_orphaned = options['skip_orphaned']
        verbose = options['verbose']

        # Statistics counters
        stats = {
            'total_items': 0,
            'items_with_json_attrs': 0,
            'items_processed': 0,
            'attributes_migrated': 0,
            'attributes_skipped': 0,
            'orphaned_attributes': 0,
            'errors': 0,
            'error_details': []
        }

        # Get items to process
        if item_hash:
            items = CollectionItem.objects.filter(hash=item_hash)
            if not items.exists():
                self.stdout.write(self.style.ERROR(f'Item with hash "{item_hash}" not found'))
                return
        else:
            items = CollectionItem.objects.all()

        stats['total_items'] = items.count()

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))

        self.stdout.write(f'Found {stats["total_items"]} items to check\n')

        # Process items in batches
        batch_count = 0
        for i in range(0, stats['total_items'], batch_size):
            batch = items[i:i + batch_size]
            batch_count += 1

            if verbose:
                self.stdout.write(f'\nProcessing batch {batch_count} (items {i+1} to {min(i+batch_size, stats["total_items"])})')

            for item in batch:
                if not item.attributes or len(item.attributes) == 0:
                    continue

                stats['items_with_json_attrs'] += 1

                if verbose:
                    self.stdout.write(f'\n  Item: {item.name} ({item.hash})')
                    self.stdout.write(f'    JSON attributes: {len(item.attributes)}')

                # Check for existing relational attributes
                existing_attr_names = set(
                    item.attribute_values.values_list('item_attribute__name', flat=True)
                )

                for attr_name, attr_value in item.attributes.items():
                    # Skip if already migrated to relational
                    if attr_name in existing_attr_names:
                        if verbose:
                            self.stdout.write(f'    ⏭️  {attr_name}: already migrated')
                        stats['attributes_skipped'] += 1
                        continue

                    # Try to find ItemAttribute definition
                    item_attribute = None
                    if item.item_type:
                        try:
                            item_attribute = item.item_type.attributes.get(name=attr_name)
                        except ItemAttribute.DoesNotExist:
                            pass

                    # Handle orphaned attribute
                    if not item_attribute:
                        stats['orphaned_attributes'] += 1
                        if skip_orphaned:
                            if verbose:
                                self.stdout.write(
                                    self.style.WARNING(f'    ⚠️  {attr_name}: no ItemAttribute definition (skipped)')
                                )
                            stats['attributes_skipped'] += 1
                            continue
                        else:
                            if verbose:
                                self.stdout.write(
                                    self.style.WARNING(
                                        f'    ⚠️  {attr_name}: no ItemAttribute definition (will be left in JSON)'
                                    )
                                )
                            stats['attributes_skipped'] += 1
                            continue

                    # Create relational attribute value
                    if not dry_run:
                        try:
                            with transaction.atomic():
                                attr_value_obj = CollectionItemAttributeValue(
                                    item=item,
                                    item_attribute=item_attribute
                                )
                                attr_value_obj.set_typed_value(attr_value)
                                attr_value_obj.save()

                                if verbose:
                                    self.stdout.write(
                                        self.style.SUCCESS(f'    ✅ {attr_name}: migrated')
                                    )
                                stats['attributes_migrated'] += 1

                        except Exception as e:
                            error_msg = f'Error migrating {item.name} - {attr_name}: {str(e)}'
                            self.stdout.write(self.style.ERROR(f'    ❌ {error_msg}'))
                            stats['errors'] += 1
                            stats['error_details'].append(error_msg)
                            continue
                    else:
                        if verbose:
                            self.stdout.write(
                                self.style.SUCCESS(f'    ✓ {attr_name}: would migrate')
                            )
                        stats['attributes_migrated'] += 1

                if not dry_run and stats['attributes_migrated'] > 0:
                    stats['items_processed'] += 1

        # Print summary report
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('\n📊 MIGRATION SUMMARY\n'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'\nTotal items checked:              {stats["total_items"]}')
        self.stdout.write(f'Items with JSON attributes:       {stats["items_with_json_attrs"]}')
        self.stdout.write(f'Items processed:                  {stats["items_processed"]}')
        self.stdout.write(f'\nAttributes migrated:              {self.style.SUCCESS(str(stats["attributes_migrated"]))}')
        self.stdout.write(f'Attributes skipped:               {stats["attributes_skipped"]}')
        self.stdout.write(f'Orphaned attributes:              {self.style.WARNING(str(stats["orphaned_attributes"]))}')
        self.stdout.write(f'Errors:                           {self.style.ERROR(str(stats["errors"]))}')

        if stats['error_details']:
            self.stdout.write('\n' + '-' * 70)
            self.stdout.write(self.style.ERROR('\nERROR DETAILS:'))
            for error in stats['error_details']:
                self.stdout.write(f'  • {error}')

        if stats['orphaned_attributes'] > 0:
            self.stdout.write('\n' + '-' * 70)
            self.stdout.write(self.style.WARNING('\n⚠️  ORPHANED ATTRIBUTES:'))
            self.stdout.write(f'   {stats["orphaned_attributes"]} attributes found without ItemAttribute definitions')
            self.stdout.write('   These will remain in the JSON field')
            self.stdout.write('   Use --skip-orphaned to hide this warning')

        if dry_run:
            self.stdout.write('\n' + '-' * 70)
            self.stdout.write(self.style.WARNING('\n🔍 This was a DRY RUN - no changes were made'))
            self.stdout.write('   Run without --dry-run to perform the migration')

        self.stdout.write('\n' + '=' * 70 + '\n')
