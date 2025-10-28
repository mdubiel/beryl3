"""
Management command to remove placeholder image URLs from collections and items.
Removes URLs from placehold.co, picsum.photos, and other placeholder services.
"""

from django.core.management.base import BaseCommand
from web.models import Collection, CollectionItem


class Command(BaseCommand):
    help = 'Remove placeholder image URLs from collections and items'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be removed without actually removing',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Placeholder patterns to remove
        placeholder_patterns = [
            'picsum.photos',
            'placehold.co',
            'placeholder.com',
            'via.placeholder.com',
            'dummyimage.com',
            'lorempixel.com',
        ]

        # Remove placeholder URLs from Collections
        self.stdout.write('\nScanning Collections...')
        collection_count = 0

        for collection in Collection.objects.exclude(image_url__isnull=True).exclude(image_url=''):
            if any(pattern in collection.image_url for pattern in placeholder_patterns):
                self.stdout.write(f'  Collection "{collection.name}" ({collection.hash}): {collection.image_url}')
                if not dry_run:
                    collection.image_url = None
                    collection.save(update_fields=['image_url'])
                collection_count += 1

        if collection_count > 0:
            if dry_run:
                self.stdout.write(self.style.WARNING(f'Would remove placeholder URLs from {collection_count} collections'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ Removed placeholder URLs from {collection_count} collections'))
        else:
            self.stdout.write('  No placeholder URLs found in collections')

        # Remove placeholder URLs from Items
        self.stdout.write('\nScanning Items...')
        item_count = 0

        for item in CollectionItem.objects.exclude(image_url__isnull=True).exclude(image_url=''):
            if any(pattern in item.image_url for pattern in placeholder_patterns):
                self.stdout.write(f'  Item "{item.name}" ({item.hash}): {item.image_url}')
                if not dry_run:
                    item.image_url = None
                    item.save(update_fields=['image_url'])
                item_count += 1

        if item_count > 0:
            if dry_run:
                self.stdout.write(self.style.WARNING(f'Would remove placeholder URLs from {item_count} items'))
            else:
                self.stdout.write(self.style.SUCCESS(f'✓ Removed placeholder URLs from {item_count} items'))
        else:
            self.stdout.write('  No placeholder URLs found in items')

        # Summary
        self.stdout.write('\n' + '='*60)
        total = collection_count + item_count
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would remove {total} placeholder URLs'))
            self.stdout.write('Run without --dry-run to actually remove them')
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Successfully removed {total} placeholder URLs'))
        self.stdout.write('='*60 + '\n')
