# -*- coding: utf-8 -*-

"""
Django management command to create sample media files for testing.
"""

import io
import requests
from datetime import datetime
from PIL import Image

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from web.models import MediaFile


class Command(BaseCommand):
    help = 'Create sample media files for testing the media browser'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=6,
            help='Number of sample files to create per folder',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('🎨 Creating Sample Media Files'))
        self.stdout.write('=' * 50)
        
        count = options['count']
        
        # Sample images with different types
        sample_files = [
            {
                'folder': 'collections',
                'media_type': MediaFile.MediaType.COLLECTION_HEADER,
                'files': [
                    {'url': f'https://picsum.photos/400/300?random={i}', 'name': f'sample_collection_{i}.jpg'} 
                    for i in range(1, count + 1)
                ]
            },
            {
                'folder': 'items', 
                'media_type': MediaFile.MediaType.COLLECTION_ITEM,
                'files': [
                    {'url': f'https://picsum.photos/300/300?random={i+10}', 'name': f'sample_item_{i}.jpg'} 
                    for i in range(1, count + 1)
                ]
            },
            {
                'folder': 'avatars',
                'media_type': MediaFile.MediaType.AVATAR,
                'files': [
                    {'url': f'https://picsum.photos/200/200?random={i+20}', 'name': f'sample_avatar_{i}.jpg'} 
                    for i in range(1, count + 1)
                ]
            }
        ]
        
        total_created = 0
        
        for folder_info in sample_files:
            folder = folder_info['folder']
            media_type = folder_info['media_type']
            
            self.stdout.write(f'\n📁 Creating files for {folder}/ folder:')
            
            for file_info in folder_info['files']:
                try:
                    # Download image
                    response = requests.get(file_info['url'], timeout=10)
                    response.raise_for_status()
                    
                    # Verify it's an image
                    img = Image.open(io.BytesIO(response.content))
                    img.verify()
                    
                    # Create file path
                    file_path = f'{folder}/{file_info["name"]}'
                    
                    # Create ContentFile
                    content_file = ContentFile(response.content)
                    content_file.name = file_info['name']
                    
                    # Save to storage
                    saved_path = default_storage.save(file_path, content_file)
                    
                    # Get file info
                    file_size = default_storage.size(saved_path)
                    file_url = default_storage.url(saved_path)
                    
                    # Create MediaFile record
                    media_file = MediaFile.objects.create(
                        name=f'Sample {file_info["name"]}',
                        file_path=saved_path,
                        original_filename=file_info['name'],
                        file_size=file_size,
                        content_type='image/jpeg',
                        media_type=media_type,
                        width=img.width if hasattr(img, 'width') else None,
                        height=img.height if hasattr(img, 'height') else None,
                        metadata={
                            'sample_file': True,
                            'created_by_command': True,
                            'source_url': file_info['url']
                        }
                    )
                    
                    self.stdout.write(
                        f'   ✅ {file_info["name"]} → {file_url}'
                    )
                    total_created += 1
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Failed to create {file_info["name"]}: {str(e)}')
                    )
        
        self.stdout.write(f'\n🎉 Created {total_created} sample media files!')
        self.stdout.write('\nYou can now browse them at /sys/media/')
        
        # Show some stats
        stats = MediaFile.get_storage_statistics()
        self.stdout.write(f'\n📊 Current media statistics:')
        self.stdout.write(f'   Total files: {stats["total_files"]}')
        self.stdout.write(f'   Active files: {stats["active_files"]}')
        if stats['size_statistics']['total_size']:
            total_size = stats['size_statistics']['total_size']
            self.stdout.write(f'   Total size: {self.format_bytes(total_size)}')

    def format_bytes(self, bytes_value):
        """Format bytes in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"