"""
Django management command to set up GCS bucket structure for Beryl3.

Creates the required folder structure in the GCS bucket:
- static/ (for CSS, JS, admin files)  
- media/ (for user uploads)
- media/collections/ (for collection images)
- media/items/ (for item images)
- media/avatars/ (for user avatars)
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from google.cloud import storage
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Set up GCS bucket folder structure for Beryl3 application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-folders',
            action='store_true',
            help='Create folder structure in GCS bucket',
        )
        parser.add_argument(
            '--test-access',
            action='store_true', 
            help='Test GCS bucket access and permissions',
        )
        parser.add_argument(
            '--list-contents',
            action='store_true',
            help='List current bucket contents',
        )

    def handle(self, *args, **options):
        if not settings.USE_GCS_STORAGE:
            self.stdout.write(
                self.style.WARNING('GCS storage is not enabled. Check USE_GCS_STORAGE setting.')
            )
            return

        if not settings.GCS_BUCKET_NAME:
            self.stdout.write(
                self.style.ERROR('GCS_BUCKET_NAME not configured')
            )
            return

        try:
            # Initialize GCS client
            if hasattr(settings, 'GCS_CREDENTIALS_PATH') and settings.GCS_CREDENTIALS_PATH:
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = settings.GCS_CREDENTIALS_PATH
            
            client = storage.Client(project=settings.GCS_PROJECT_ID)
            bucket = client.bucket(settings.GCS_BUCKET_NAME)

            self.stdout.write(f'Connected to GCS bucket: {settings.GCS_BUCKET_NAME}')
            self.stdout.write(f'Project: {settings.GCS_PROJECT_ID}')

            if options['test_access']:
                self._test_bucket_access(bucket)
            
            if options['list_contents']:
                self._list_bucket_contents(bucket)
            
            if options['create_folders']:
                self._create_folder_structure(bucket)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error connecting to GCS: {e}')
            )
            logger.error(f'GCS setup error: {e}')

    def _test_bucket_access(self, bucket):
        """Test bucket access and permissions"""
        self.stdout.write('Testing bucket access...')
        
        try:
            # Test if bucket exists
            if bucket.exists():
                self.stdout.write(self.style.SUCCESS('✅ Bucket exists and is accessible'))
            else:
                self.stdout.write(self.style.ERROR('❌ Bucket does not exist'))
                return

            # Test write permissions by creating a test file
            test_blob = bucket.blob('test_access.txt')
            test_blob.upload_from_string('Beryl3 GCS access test')
            self.stdout.write(self.style.SUCCESS('✅ Write permissions confirmed'))
            
            # Test read permissions
            content = test_blob.download_as_text()
            if 'Beryl3 GCS access test' in content:
                self.stdout.write(self.style.SUCCESS('✅ Read permissions confirmed'))
            
            # Clean up test file
            test_blob.delete()
            self.stdout.write('✅ Test file cleaned up')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Access test failed: {e}')
            )

    def _list_bucket_contents(self, bucket):
        """List current bucket contents"""
        self.stdout.write('Listing bucket contents...')
        
        try:
            blobs = list(bucket.list_blobs(max_results=100))
            if not blobs:
                self.stdout.write('Bucket is empty')
                return
            
            for blob in blobs:
                size_mb = blob.size / (1024 * 1024) if blob.size else 0
                self.stdout.write(f'  {blob.name} ({size_mb:.2f} MB)')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error listing contents: {e}')
            )

    def _create_folder_structure(self, bucket):
        """Create the required folder structure"""
        self.stdout.write('Creating GCS folder structure...')
        
        # Define folder structure
        folders = [
            'static/',           # Static files (CSS, JS, admin)
            'static/admin/',     # Django admin static files
            'static/css/',       # Application CSS files
            'static/js/',        # Application JavaScript files
            'static/images/',    # Static images
            'media/',           # User uploads root
            'media/collections/', # Collection images
            'media/items/',      # Item images
            'media/avatars/',    # User avatars
            'media/temp/',       # Temporary uploads
        ]
        
        created_count = 0
        
        for folder_path in folders:
            try:
                # Create folder marker (empty file with folder name)
                blob = bucket.blob(f'{folder_path}.keep')
                
                # Check if folder marker already exists
                if not blob.exists():
                    blob.upload_from_string(
                        f'Folder marker for {folder_path} - created by Beryl3 setup'
                    )
                    created_count += 1
                    self.stdout.write(f'  ✅ Created: {folder_path}')
                else:
                    self.stdout.write(f'  📁 Exists: {folder_path}')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Failed to create {folder_path}: {e}')
                )
        
        if created_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {created_count} new folders')
            )
        else:
            self.stdout.write('All folders already exist')
        
        self.stdout.write('\n' + '='*50)
        self.stdout.write('GCS bucket setup complete!')
        self.stdout.write(f'Bucket: {settings.GCS_BUCKET_NAME}')
        self.stdout.write(f'Media URL: https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/{settings.GCS_LOCATION}/')
        self.stdout.write(f'Static URL: https://storage.googleapis.com/{settings.GCS_BUCKET_NAME}/static/')
        self.stdout.write('='*50)