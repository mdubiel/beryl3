"""
Management command to verify media file cleanup and find orphaned records
"""
from django.core.management.base import BaseCommand
from web.models import MediaFile, CollectionImage, CollectionItemImage


class Command(BaseCommand):
    help = 'Verify media file cleanup and find orphaned records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-orphaned',
            action='store_true',
            help='Actually delete orphaned records (dry run by default)',
        )

    def handle(self, *args, **options):
        self.stdout.write("=== Media Cleanup Verification ===")
        
        # Check for orphaned CollectionImage records
        orphaned_collection_images = CollectionImage.objects.filter(media_file__isnull=True)
        self.stdout.write(f"Found {orphaned_collection_images.count()} orphaned CollectionImage records")
        
        # Check for orphaned CollectionItemImage records  
        orphaned_item_images = CollectionItemImage.objects.filter(media_file__isnull=True)
        self.stdout.write(f"Found {orphaned_item_images.count()} orphaned CollectionItemImage records")
        
        # Check for CollectionImages pointing to non-existent MediaFiles
        collection_images_with_missing_media = []
        for ci in CollectionImage.objects.select_related('media_file').all():
            try:
                # Test if media file exists
                _ = ci.media_file.id
            except MediaFile.DoesNotExist:
                collection_images_with_missing_media.append(ci.id)
        
        self.stdout.write(f"Found {len(collection_images_with_missing_media)} CollectionImage records with missing MediaFiles")
        
        # Check for CollectionItemImages pointing to non-existent MediaFiles
        item_images_with_missing_media = []
        for cii in CollectionItemImage.objects.select_related('media_file').all():
            try:
                # Test if media file exists
                _ = cii.media_file.id
            except MediaFile.DoesNotExist:
                item_images_with_missing_media.append(cii.id)
                
        self.stdout.write(f"Found {len(item_images_with_missing_media)} CollectionItemImage records with missing MediaFiles")
        
        # Show totals
        total_media_files = MediaFile.objects.count()
        total_collection_images = CollectionImage.objects.count()
        total_item_images = CollectionItemImage.objects.count()
        
        self.stdout.write(f"\nDatabase totals:")
        self.stdout.write(f"MediaFiles: {total_media_files}")
        self.stdout.write(f"CollectionImages: {total_collection_images}")
        self.stdout.write(f"CollectionItemImages: {total_item_images}")
        
        # Fix orphaned records if requested
        if options['fix_orphaned']:
            if orphaned_collection_images.exists():
                deleted_count = orphaned_collection_images.count()
                orphaned_collection_images.delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} orphaned CollectionImage records"))
            
            if orphaned_item_images.exists():
                deleted_count = orphaned_item_images.count()
                orphaned_item_images.delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} orphaned CollectionItemImage records"))
                
            if collection_images_with_missing_media:
                CollectionImage.objects.filter(id__in=collection_images_with_missing_media).delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted {len(collection_images_with_missing_media)} CollectionImage records with missing MediaFiles"))
                
            if item_images_with_missing_media:
                CollectionItemImage.objects.filter(id__in=item_images_with_missing_media).delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted {len(item_images_with_missing_media)} CollectionItemImage records with missing MediaFiles"))
        else:
            if any([orphaned_collection_images.exists(), orphaned_item_images.exists(), 
                   collection_images_with_missing_media, item_images_with_missing_media]):
                self.stdout.write(self.style.WARNING("\nRun with --fix-orphaned to clean up orphaned records"))
            else:
                self.stdout.write(self.style.SUCCESS("\nNo cleanup needed - all records look good!"))