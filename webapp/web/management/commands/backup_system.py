"""
Django management command to backup database and media files to Google Cloud Storage.

Usage:
    python manage.py backup_system
    python manage.py backup_system --database-only
    python manage.py backup_system --media-only
"""
import os
import tempfile
import gzip
import shutil
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from google.cloud import storage
import subprocess


class Command(BaseCommand):
    help = 'Create backup of database and media files to Google Cloud Storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--database-only',
            action='store_true',
            help='Only backup database',
        )
        parser.add_argument(
            '--media-only',
            action='store_true',
            help='Only backup media files',
        )

    def handle(self, *args, **options):
        database_only = options.get('database_only', False)
        media_only = options.get('media_only', False)

        if database_only and media_only:
            self.stdout.write(self.style.ERROR('Cannot use both --database-only and --media-only'))
            return

        # Initialize GCS client
        try:
            credentials_path = settings.GCS_CREDENTIALS_PATH
            if credentials_path and os.path.exists(credentials_path):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path

            storage_client = storage.Client(project=settings.GCS_PROJECT_ID)
            bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize GCS client: {e}'))
            return

        # Backup database
        if not media_only:
            self.stdout.write('Starting database backup...')
            success = self.backup_database(bucket)
            if success:
                self.stdout.write(self.style.SUCCESS('✅ Database backup completed'))
            else:
                self.stdout.write(self.style.ERROR('❌ Database backup failed'))
                return

        # Backup media
        if not database_only:
            self.stdout.write('Starting media backup...')
            success = self.backup_media(bucket)
            if success:
                self.stdout.write(self.style.SUCCESS('✅ Media backup completed'))
            else:
                self.stdout.write(self.style.ERROR('❌ Media backup failed'))
                return

        # Cleanup old backups
        self.stdout.write('Cleaning up old backups...')
        self.cleanup_old_backups(bucket)
        self.stdout.write(self.style.SUCCESS('✅ Backup cleanup completed'))

    def backup_database(self, bucket):
        """Create compressed database dump and upload to GCS"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Create temporary file for database dump
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
                dump_file = temp_file.name

            # Use Django's dumpdata command
            with open(dump_file, 'w') as f:
                call_command('dumpdata',
                           '--natural-foreign',
                           '--natural-primary',
                           '--exclude=contenttypes',
                           '--exclude=auth.permission',
                           '--exclude=sessions.session',
                           stdout=f)

            # Compress the dump
            compressed_file = f"{dump_file}.gz"
            with open(dump_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Upload to GCS
            blob_name = f'backups/database/db_backup_{timestamp}.json.gz'
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(compressed_file)

            # Cleanup temp files
            os.unlink(dump_file)
            os.unlink(compressed_file)

            self.stdout.write(f'  Uploaded: {blob_name}')
            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error backing up database: {e}'))
            return False

    def backup_media(self, bucket):
        """Create compressed media archive and upload to GCS"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Get media root
            media_root = Path(settings.MEDIA_ROOT)
            if not media_root.exists():
                self.stdout.write('  No media directory found, skipping')
                return True

            # Calculate total size
            total_size = sum(f.stat().st_size for f in media_root.rglob('*') if f.is_file())
            size_gb = total_size / (1024 ** 3)

            self.stdout.write(f'  Media size: {size_gb:.2f} GB')

            # Split into chunks if > 1GB
            max_size_gb = 1.0

            if size_gb > max_size_gb:
                # Split media into multiple archives
                return self.backup_media_split(bucket, timestamp, media_root, total_size, max_size_gb)
            else:
                # Single archive
                return self.backup_media_single(bucket, timestamp, media_root)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error backing up media: {e}'))
            return False

    def backup_media_single(self, bucket, timestamp, media_root):
        """Create single media archive"""
        try:
            # Create temporary archive
            with tempfile.TemporaryDirectory() as temp_dir:
                archive_base = os.path.join(temp_dir, f'media_backup_{timestamp}')

                # Create tar.gz archive
                shutil.make_archive(archive_base, 'gztar', media_root)
                archive_file = f"{archive_base}.tar.gz"

                # Upload to GCS
                blob_name = f'backups/media/media_backup_{timestamp}.tar.gz'
                blob = bucket.blob(blob_name)
                blob.upload_from_filename(archive_file)

                file_size = os.path.getsize(archive_file) / (1024 ** 2)  # MB
                self.stdout.write(f'  Uploaded: {blob_name} ({file_size:.2f} MB)')

            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error creating single archive: {e}'))
            return False

    def backup_media_split(self, bucket, timestamp, media_root, total_size, max_size_gb):
        """Create split media archives when total size > 1GB"""
        try:
            max_size_bytes = int(max_size_gb * 1024 ** 3)

            # Get all files sorted by size
            all_files = [(f, f.stat().st_size) for f in media_root.rglob('*') if f.is_file()]
            all_files.sort(key=lambda x: x[1], reverse=True)

            # Split into chunks
            chunks = []
            current_chunk = []
            current_size = 0

            for file_path, size in all_files:
                if current_size + size > max_size_bytes and current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = []
                    current_size = 0

                current_chunk.append(file_path)
                current_size += size

            if current_chunk:
                chunks.append(current_chunk)

            self.stdout.write(f'  Splitting into {len(chunks)} archives')

            # Create archive for each chunk
            with tempfile.TemporaryDirectory() as temp_dir:
                for i, chunk in enumerate(chunks, 1):
                    chunk_dir = os.path.join(temp_dir, f'chunk_{i}')
                    os.makedirs(chunk_dir, exist_ok=True)

                    # Copy files to chunk directory preserving structure
                    for file_path in chunk:
                        rel_path = file_path.relative_to(media_root)
                        dest_path = os.path.join(chunk_dir, str(rel_path))
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.copy2(file_path, dest_path)

                    # Create archive
                    archive_base = os.path.join(temp_dir, f'media_backup_{timestamp}_part{i}')
                    shutil.make_archive(archive_base, 'gztar', chunk_dir)
                    archive_file = f"{archive_base}.tar.gz"

                    # Upload to GCS
                    blob_name = f'backups/media/media_backup_{timestamp}_part{i}.tar.gz'
                    blob = bucket.blob(blob_name)
                    blob.upload_from_filename(archive_file)

                    file_size = os.path.getsize(archive_file) / (1024 ** 2)  # MB
                    self.stdout.write(f'  Uploaded part {i}/{len(chunks)}: {blob_name} ({file_size:.2f} MB)')

                    # Cleanup chunk directory
                    shutil.rmtree(chunk_dir)

            return True

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error creating split archives: {e}'))
            return False

    def cleanup_old_backups(self, bucket):
        """Keep only 7 most recent database backups and 1 most recent media backup"""
        try:
            # Cleanup old database backups (keep 7)
            db_blobs = list(bucket.list_blobs(prefix='backups/database/'))
            db_blobs.sort(key=lambda x: x.time_created, reverse=True)

            if len(db_blobs) > 7:
                for blob in db_blobs[7:]:
                    blob.delete()
                    self.stdout.write(f'  Deleted old database backup: {blob.name}')

            # Cleanup old media backups (keep only most recent set)
            media_blobs = list(bucket.list_blobs(prefix='backups/media/'))

            if not media_blobs:
                return

            # Group by timestamp
            media_groups = {}
            for blob in media_blobs:
                # Extract timestamp from filename
                parts = blob.name.split('_')
                if len(parts) >= 3:
                    # Format: media_backup_TIMESTAMP[_partN].tar.gz
                    timestamp = '_'.join(parts[2:4])  # YYYYMMDD_HHMMSS
                    if timestamp not in media_groups:
                        media_groups[timestamp] = []
                    media_groups[timestamp].append(blob)

            # Sort groups by timestamp and keep only the most recent
            sorted_groups = sorted(media_groups.items(), key=lambda x: x[0], reverse=True)

            if len(sorted_groups) > 1:
                for timestamp, blobs in sorted_groups[1:]:
                    for blob in blobs:
                        blob.delete()
                        self.stdout.write(f'  Deleted old media backup: {blob.name}')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Error during cleanup: {e}'))
