# -*- coding: utf-8 -*-

"""
Django management command to test GCS storage configuration and functionality.
"""

import io
import logging
import os
import requests
from datetime import datetime
from PIL import Image

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from web.models import MediaFile

logger = logging.getLogger('webapp')


class Command(BaseCommand):
    help = 'Test GCS storage configuration and upload/download functionality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed configuration information',
        )
        parser.add_argument(
            '--skip-upload',
            action='store_true',
            help='Skip the file upload test',
        )
        parser.add_argument(
            '--test-images',
            action='store_true',
            help='Test image upload with stock images',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('🔍 Testing GCS Storage Configuration'))
        self.stdout.write('=' * 60)
        
        # Test 1: Configuration Check
        self.test_configuration(detailed=options['detailed'])
        
        # Test 2: Storage Backend Check
        self.test_storage_backend()
        
        # Test 3: Credentials and Connection
        self.test_credentials()
        
        # Test 4: File Operations (if not skipped)
        if not options['skip_upload']:
            self.test_file_operations()
        else:
            self.stdout.write(self.style.WARNING('⚠️  Skipping file upload test'))
        
        # Test 5: MediaFile Model Integration
        self.test_media_file_model()
        
        # Test 6: Image Upload (if requested)
        if options['test_images']:
            self.test_image_upload()
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ GCS Storage test completed'))

    def test_configuration(self, detailed=False):
        """Test if GCS configuration is properly set"""
        self.stdout.write('\n📋 Configuration Check:')
        
        use_gcs = getattr(settings, 'FEATURE_FLAGS', {}).get('USE_GCS_STORAGE', False)
        
        self.stdout.write(f'   DEBUG mode: {settings.DEBUG}')
        self.stdout.write(f'   USE_GCS_STORAGE feature flag: {use_gcs}')
        self.stdout.write(f'   Should use GCS: {use_gcs}')
        
        if detailed:
            gcs_settings = {
                'GCS_BUCKET_NAME': getattr(settings, 'GCS_BUCKET_NAME', 'Not set'),
                'GCS_PROJECT_ID': getattr(settings, 'GCS_PROJECT_ID', 'Not set'),
                'GCS_LOCATION': getattr(settings, 'GCS_LOCATION', 'media'),
                'GCS_CREDENTIALS_PATH': getattr(settings, 'GCS_CREDENTIALS_PATH', 'Not set'),
                'GCS_CREDENTIALS': 'Configured' if getattr(settings, 'GCS_CREDENTIALS', None) else 'Not set'
            }
            
            for key, value in gcs_settings.items():
                self.stdout.write(f'   {key}: {value}')
        
        # Check required settings
        required_settings = ['GCS_BUCKET_NAME', 'GCS_PROJECT_ID']
        missing_settings = []
        
        for setting in required_settings:
            if not getattr(settings, setting, None):
                missing_settings.append(setting)
        
        if missing_settings:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Missing required settings: {", ".join(missing_settings)}')
            )
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ All required settings present'))

    def test_storage_backend(self):
        """Test the storage backend type"""
        self.stdout.write('\n🔧 Storage Backend Check:')
        
        storage_class = default_storage.__class__.__name__
        self.stdout.write(f'   Storage class: {storage_class}')
        
        # Check if we're using the expected storage type based on feature flag
        use_gcs = getattr(settings, 'FEATURE_FLAGS', {}).get('USE_GCS_STORAGE', False)
        
        if use_gcs:
            if 'GoogleCloudStorage' in storage_class:
                self.stdout.write(self.style.SUCCESS('   ✅ Using Google Cloud Storage'))
            else:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Expected GCS but got {storage_class}')
                )
        else:
            if 'FileSystemStorage' in storage_class:
                self.stdout.write(self.style.SUCCESS('   ✅ Using Local File System'))
            else:
                self.stdout.write(
                    self.style.WARNING(f'   ⚠️  Using {storage_class}')
                )

    def test_credentials(self):
        """Test GCS credentials and connection"""
        self.stdout.write('\n🔑 Credentials & Connection Test:')
        
        try:
            # Try to access the storage - this will test credentials
            if hasattr(default_storage, 'bucket'):
                bucket_name = default_storage.bucket.name
                self.stdout.write(f'   Bucket name: {bucket_name}')
                self.stdout.write(self.style.SUCCESS('   ✅ Successfully connected to GCS'))
            else:
                self.stdout.write('   Using local storage - no GCS credentials needed')
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'   ❌ Failed to connect to GCS: {str(e)}')
            )
            
        # Check credentials file
        creds_path = getattr(settings, 'GCS_CREDENTIALS_PATH', None)
        if creds_path:
            if os.path.exists(creds_path):
                self.stdout.write(self.style.SUCCESS(f'   ✅ Credentials file found: {creds_path}'))
            else:
                self.stdout.write(
                    self.style.ERROR(f'   ❌ Credentials file not found: {creds_path}')
                )

    def test_file_operations(self):
        """Test actual file upload and download operations"""
        self.stdout.write('\n📁 File Operations Test:')
        
        test_filename = f'test/gcs_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        test_content = f'GCS Storage Test\nTimestamp: {datetime.now()}\nBucket: {getattr(settings, "GCS_BUCKET_NAME", "unknown")}'
        
        try:
            # Test 1: Upload file
            self.stdout.write('   Testing file upload...')
            content_file = ContentFile(test_content.encode('utf-8'))
            saved_path = default_storage.save(test_filename, content_file)
            self.stdout.write(self.style.SUCCESS(f'   ✅ File uploaded: {saved_path}'))
            
            # Test 2: Check if file exists
            self.stdout.write('   Testing file existence...')
            if default_storage.exists(saved_path):
                self.stdout.write(self.style.SUCCESS('   ✅ File exists in storage'))
            else:
                self.stdout.write(self.style.ERROR('   ❌ File not found in storage'))
                return
            
            # Test 3: Get file URL
            self.stdout.write('   Testing file URL generation...')
            try:
                file_url = default_storage.url(saved_path)
                self.stdout.write(f'   File URL: {file_url}')
                self.stdout.write(self.style.SUCCESS('   ✅ File URL generated successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Failed to generate URL: {str(e)}'))
            
            # Test 4: Download and verify content
            self.stdout.write('   Testing file download...')
            with default_storage.open(saved_path, 'r') as f:
                downloaded_content = f.read()
                if test_content in downloaded_content:
                    self.stdout.write(self.style.SUCCESS('   ✅ File content verified'))
                else:
                    self.stdout.write(self.style.ERROR('   ❌ File content mismatch'))
            
            # Test 5: Get file size
            file_size = default_storage.size(saved_path)
            self.stdout.write(f'   File size: {file_size} bytes')
            
            # Test 6: Clean up - delete test file
            self.stdout.write('   Cleaning up test file...')
            default_storage.delete(saved_path)
            
            if not default_storage.exists(saved_path):
                self.stdout.write(self.style.SUCCESS('   ✅ Test file cleaned up successfully'))
            else:
                self.stdout.write(self.style.WARNING('   ⚠️  Test file may still exist'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ File operations failed: {str(e)}'))
            # Try to clean up on error
            try:
                if default_storage.exists(test_filename):
                    default_storage.delete(test_filename)
            except:
                pass

    def test_media_file_model(self):
        """Test MediaFile model integration"""
        self.stdout.write('\n🗃️  MediaFile Model Test:')
        
        try:
            # Create a test MediaFile record
            test_media = MediaFile.objects.create(
                name='GCS Test File',
                file_path='test/model_test.txt',
                original_filename='model_test.txt',
                file_size=100,
                content_type='text/plain',
                media_type=MediaFile.MediaType.OTHER,
                created_by=None
            )
            
            self.stdout.write(f'   Created MediaFile: {test_media.hash}')
            self.stdout.write(f'   Storage backend: {test_media.storage_backend}')
            
            # Test storage statistics
            stats = MediaFile.get_storage_statistics()
            self.stdout.write(f'   Total media files: {stats["total_files"]}')
            self.stdout.write(f'   Active files: {stats["active_files"]}')
            
            # Clean up
            test_media.delete()
            self.stdout.write(self.style.SUCCESS('   ✅ MediaFile model working correctly'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ MediaFile model error: {str(e)}'))

    def test_subdirectories(self):
        """Test subdirectory structure"""
        self.stdout.write('\n📂 Subdirectory Structure Test:')
        
        test_paths = [
            'collections/test_collection.jpg',
            'items/test_item.jpg'
        ]
        
        for path in test_paths:
            try:
                content = b'test image data'
                content_file = ContentFile(content)
                saved_path = default_storage.save(path, content_file)
                
                if default_storage.exists(saved_path):
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Created: {saved_path}'))
                    default_storage.delete(saved_path)  # Clean up
                else:
                    self.stdout.write(self.style.ERROR(f'   ❌ Failed to create: {path}'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error with {path}: {str(e)}'))

    def test_image_upload(self):
        """Test uploading actual images to GCS"""
        self.stdout.write('\n🖼️  Image Upload Test:')
        
        # List of free stock image URLs (small sizes for testing)
        test_images = [
            {
                'url': 'https://picsum.photos/300/200?random=1',
                'filename': 'test_collection_header.jpg',
                'path': 'test/collections/test_collection_header.jpg',
                'media_type': MediaFile.MediaType.COLLECTION_HEADER
            },
            {
                'url': 'https://picsum.photos/250/250?random=2', 
                'filename': 'test_item_image.jpg',
                'path': 'test/items/test_item_image.jpg',
                'media_type': MediaFile.MediaType.COLLECTION_ITEM
            },
            {
                'url': 'https://picsum.photos/200/200?random=3',
                'filename': 'test_avatar.jpg', 
                'path': 'test/avatars/test_avatar.jpg',
                'media_type': MediaFile.MediaType.AVATAR
            }
        ]
        
        uploaded_files = []
        
        for img_info in test_images:
            try:
                self.stdout.write(f'   📥 Downloading: {img_info["filename"]}')
                
                # Download the image
                response = requests.get(img_info['url'], timeout=10)
                response.raise_for_status()
                
                # Verify it's actually an image
                try:
                    img = Image.open(io.BytesIO(response.content))
                    img.verify()  # Verify it's a valid image
                    self.stdout.write(f'      ✅ Valid image: {img.format} {img.size}')
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'      ❌ Invalid image: {str(e)}'))
                    continue
                
                # Create ContentFile from downloaded data
                content_file = ContentFile(response.content)
                content_file.name = img_info['filename']
                
                # Upload to storage
                self.stdout.write(f'   📤 Uploading to: {img_info["path"]}')
                saved_path = default_storage.save(img_info['path'], content_file)
                
                # Verify upload
                if default_storage.exists(saved_path):
                    file_size = default_storage.size(saved_path)
                    file_url = default_storage.url(saved_path)
                    
                    self.stdout.write(self.style.SUCCESS(f'      ✅ Uploaded: {saved_path}'))
                    self.stdout.write(f'      📏 Size: {file_size} bytes')
                    self.stdout.write(f'      🔗 URL: {file_url}')
                    
                    # Create MediaFile record
                    media_file = MediaFile.objects.create(
                        name=f'Test {img_info["filename"]}',
                        file_path=saved_path,
                        original_filename=img_info['filename'],
                        file_size=file_size,
                        content_type=f'image/jpeg',
                        media_type=img_info['media_type'],
                        width=None,  # Could extract from PIL Image if needed
                        height=None,
                        metadata={
                            'test_upload': True,
                            'source_url': img_info['url'],
                            'upload_timestamp': datetime.now().isoformat()
                        }
                    )
                    
                    self.stdout.write(f'      🗃️  MediaFile created: {media_file.hash}')
                    uploaded_files.append({
                        'path': saved_path,
                        'media_file': media_file,
                        'url': file_url
                    })
                    
                else:
                    self.stdout.write(self.style.ERROR(f'      ❌ Upload failed: {saved_path}'))
                    
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Download failed for {img_info["filename"]}: {str(e)}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Upload failed for {img_info["filename"]}: {str(e)}'))
        
        # Summary
        if uploaded_files:
            self.stdout.write(f'\n   📊 Upload Summary:')
            self.stdout.write(f'      ✅ Successfully uploaded {len(uploaded_files)} images')
            
            for file_info in uploaded_files:
                self.stdout.write(f'      • {file_info["path"]} → {file_info["url"]}')
            
            # Test accessing the images
            self.stdout.write(f'\n   🔍 Verifying uploaded images:')
            for file_info in uploaded_files:
                try:
                    # Test if we can access the file
                    with default_storage.open(file_info['path'], 'rb') as f:
                        data = f.read(100)  # Read first 100 bytes
                        if data:
                            self.stdout.write(self.style.SUCCESS(f'      ✅ Can read: {file_info["path"]}'))
                        else:
                            self.stdout.write(self.style.ERROR(f'      ❌ Empty file: {file_info["path"]}'))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'      ❌ Read error: {file_info["path"]} - {str(e)}'))
            
            # Option to clean up test files
            self.stdout.write(f'\n   🧹 Cleaning up test files...')
            for file_info in uploaded_files:
                try:
                    default_storage.delete(file_info['path'])
                    file_info['media_file'].delete()
                    self.stdout.write(f'      ✅ Cleaned: {file_info["path"]}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'      ⚠️  Cleanup issue: {file_info["path"]} - {str(e)}'))
        else:
            self.stdout.write(self.style.ERROR('   ❌ No images were successfully uploaded'))