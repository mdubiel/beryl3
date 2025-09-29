"""
Management command to check media file integrity and database consistency.
"""
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from web.models import MediaFile, CollectionImage, CollectionItemImage


class Command(BaseCommand):
    help = 'Check media file integrity and database consistency'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-orphaned',
            action='store_true',
            help='Show files in storage without database records',
        )
        parser.add_argument(
            '--show-missing',
            action='store_true',
            help='Show database records without storage files',
        )
        parser.add_argument(
            '--hash',
            type=str,
            help='Check specific file by hash',
        )
        parser.add_argument(
            '--cleanup-orphaned',
            action='store_true',
            help='Clean up orphaned CollectionImage and CollectionItemImage records',
        )

    def handle(self, *args, **options):
        if options['hash']:
            self.check_specific_file(options['hash'])
            return
            
        self.check_database_consistency()
        
        if options['cleanup_orphaned']:
            self.cleanup_orphaned_records()
        
        if options['show_orphaned']:
            self.check_orphaned_files()
            
        if options['show_missing']:
            self.check_missing_files()

    def check_specific_file(self, file_hash):
        """Check a specific file by hash"""
        self.stdout.write(f"\nChecking file with hash: {file_hash}")
        
        try:
            media_file = MediaFile.objects.get(hash=file_hash)
            self.stdout.write(self.style.SUCCESS(f"✓ MediaFile record exists: {media_file.original_filename}"))
            
            # Check storage
            if default_storage.exists(media_file.file_path):
                self.stdout.write(self.style.SUCCESS(f"✓ File exists in storage: {media_file.file_path}"))
            else:
                self.stdout.write(self.style.ERROR(f"✗ File missing from storage: {media_file.file_path}"))
            
            # Check relationships
            collection_images = media_file.collection_images.count()
            item_images = media_file.item_images.count()
            
            self.stdout.write(f"  - Collection images: {collection_images}")
            self.stdout.write(f"  - Item images: {item_images}")
            
            if collection_images > 0:
                for ci in media_file.collection_images.select_related('collection'):
                    self.stdout.write(f"    * Collection: {ci.collection.name}")
                    
            if item_images > 0:
                for ii in media_file.item_images.select_related('item'):
                    self.stdout.write(f"    * Item: {ii.item.name}")
            
        except MediaFile.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ MediaFile record not found for hash: {file_hash}"))

    def check_database_consistency(self):
        """Check basic database consistency"""
        self.stdout.write("\n=== Database Consistency Check ===")
        
        total_media_files = MediaFile.objects.count()
        total_collection_images = CollectionImage.objects.count()
        total_item_images = CollectionItemImage.objects.count()
        
        self.stdout.write(f"Total MediaFile records: {total_media_files}")
        self.stdout.write(f"Total CollectionImage records: {total_collection_images}")
        self.stdout.write(f"Total ItemImage records: {total_item_images}")
        
        # Check for orphaned CollectionImage records
        orphaned_collection_images = CollectionImage.objects.filter(media_file__isnull=True).count()
        if orphaned_collection_images > 0:
            self.stdout.write(self.style.WARNING(f"⚠ Found {orphaned_collection_images} orphaned CollectionImage records"))
        
        # Check for orphaned CollectionItemImage records  
        orphaned_item_images = CollectionItemImage.objects.filter(media_file__isnull=True).count()
        if orphaned_item_images > 0:
            self.stdout.write(self.style.WARNING(f"⚠ Found {orphaned_item_images} orphaned CollectionItemImage records"))
        
        if orphaned_collection_images == 0 and orphaned_item_images == 0:
            self.stdout.write(self.style.SUCCESS("✓ No orphaned image references found"))

    def check_orphaned_files(self):
        """Check for files in storage without database records"""
        self.stdout.write("\n=== Checking for orphaned files in storage ===")
        
        # This is a simplified check - in reality you'd need to scan the storage
        self.stdout.write("Note: Full storage scan would require more complex logic")
        
    def check_missing_files(self):
        """Check for database records without storage files"""
        self.stdout.write("\n=== Checking for missing files in storage ===")
        
        missing_count = 0
        for media_file in MediaFile.objects.all():
            if not default_storage.exists(media_file.file_path):
                self.stdout.write(self.style.ERROR(f"✗ Missing: {media_file.original_filename} ({media_file.file_path})"))
                missing_count += 1
                
        if missing_count == 0:
            self.stdout.write(self.style.SUCCESS("✓ All database records have corresponding storage files"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠ Found {missing_count} missing files"))
            
    def cleanup_orphaned_records(self):
        """Clean up orphaned CollectionImage and CollectionItemImage records"""
        self.stdout.write("\n=== Cleaning up orphaned records ===")
        
        # Find orphaned CollectionImage records
        orphaned_collection_images = CollectionImage.objects.extra(
            where=['media_file_id NOT IN (SELECT id FROM web_mediafile)']
        )
        ci_count = orphaned_collection_images.count()
        
        # Find orphaned CollectionItemImage records
        orphaned_item_images = CollectionItemImage.objects.extra(
            where=['media_file_id NOT IN (SELECT id FROM web_mediafile)']
        )
        cii_count = orphaned_item_images.count()
        
        if ci_count > 0:
            self.stdout.write(f"Found {ci_count} orphaned CollectionImage records")
            for ci in orphaned_collection_images[:5]:  # Show first 5
                self.stdout.write(f"  - CollectionImage {ci.id}: media_file_id={ci.media_file_id}, collection={ci.collection.name if ci.collection else 'None'}")
            if ci_count > 5:
                self.stdout.write(f"  ... and {ci_count - 5} more")
            
            orphaned_collection_images.delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {ci_count} orphaned CollectionImage records"))
        
        if cii_count > 0:
            self.stdout.write(f"Found {cii_count} orphaned CollectionItemImage records")
            for cii in orphaned_item_images[:5]:  # Show first 5
                self.stdout.write(f"  - CollectionItemImage {cii.id}: media_file_id={cii.media_file_id}, item={cii.item.name if cii.item else 'None'}")
            if cii_count > 5:
                self.stdout.write(f"  ... and {cii_count - 5} more")
                
            orphaned_item_images.delete()
            self.stdout.write(self.style.SUCCESS(f"✓ Deleted {cii_count} orphaned CollectionItemImage records"))
        
        if ci_count == 0 and cii_count == 0:
            self.stdout.write(self.style.SUCCESS("✓ No orphaned image records found"))