"""
Management command for batch content analysis of uploaded images
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from web.models import MediaFile
from web.services.content_moderation import content_moderation_service
import logging

logger = logging.getLogger("webapp")


class Command(BaseCommand):
    help = 'Batch analyze images for inappropriate content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of files to process in each batch (default: 50)'
        )
        
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-analyze files that have already been checked'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it'
        )
        
        parser.add_argument(
            '--file-id',
            type=int,
            help='Analyze a specific file by ID'
        )

    def handle(self, *args, **options):
        if not content_moderation_service.is_enabled():
            raise CommandError("Content moderation is not enabled. Set CONTENT_MODERATION_ENABLED=True")

        batch_size = options['batch_size']
        force = options['force']
        dry_run = options['dry_run']
        file_id = options['file_id']

        # Handle specific file analysis
        if file_id:
            return self._analyze_specific_file(file_id, force, dry_run)

        # Handle batch analysis
        return self._analyze_batch(batch_size, force, dry_run, options)

    def _analyze_specific_file(self, file_id, force, dry_run):
        """Analyze a specific file"""
        try:
            media_file = MediaFile.objects.get(id=file_id)
        except MediaFile.DoesNotExist:
            raise CommandError(f"MediaFile with ID {file_id} does not exist")

        self.stdout.write(f"Analyzing file: {media_file.original_filename}")

        if not media_file.content_type or not media_file.content_type.startswith('image/'):
            self.stdout.write(
                self.style.WARNING(f"Skipping non-image file: {media_file.content_type}")
            )
            return

        if not force and media_file.content_moderation_checked_at:
            self.stdout.write(
                self.style.WARNING(
                    f"File already analyzed at {media_file.content_moderation_checked_at}. "
                    "Use --force to re-analyze."
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"Would analyze: {media_file.original_filename}")
            )
            return

        # Perform analysis
        result = media_file.analyze_content(force=force)
        
        if result.get('status') == 'error':
            self.stdout.write(
                self.style.ERROR(f"Analysis failed: {result.get('error')}")
            )
        elif result.get('is_inappropriate'):
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  FLAGGED: {media_file.original_filename} "
                    f"(confidence: {result.get('confidence_score', 0):.2f})"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ APPROVED: {media_file.original_filename} "
                    f"(confidence: {result.get('confidence_score', 0):.2f})"
                )
            )

    def _analyze_batch(self, batch_size, force, dry_run, options):
        """Analyze a batch of files"""
        
        # Build query for files to analyze
        query = MediaFile.objects.filter(
            content_type__startswith='image/',
            file_exists=True
        ).order_by('created')

        if not force:
            # Exclude already checked files and approved files
            query = query.filter(
                content_moderation_checked_at__isnull=True
            ).exclude(
                content_moderation_status=MediaFile.ContentModerationStatus.APPROVED
            )

        total_count = query.count()
        
        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS("No files need analysis")
            )
            return

        self.stdout.write(f"Found {total_count} files to analyze")

        if dry_run:
            files_to_show = query[:10]  # Show first 10 files
            for media_file in files_to_show:
                self.stdout.write(f"  - {media_file.original_filename}")
            
            if total_count > 10:
                self.stdout.write(f"  ... and {total_count - 10} more files")
            
            self.stdout.write(
                self.style.SUCCESS(f"Would analyze {total_count} files in batches of {batch_size}")
            )
            return

        # Process in batches
        processed = 0
        approved = 0
        flagged = 0
        errors = 0

        while processed < total_count:
            # Get current batch
            batch = list(query[processed:processed + batch_size])
            
            if not batch:
                break

            self.stdout.write(f"Processing batch {processed + 1}-{processed + len(batch)} of {total_count}")

            for media_file in batch:
                try:
                    with transaction.atomic():
                        result = media_file.analyze_content(force=force)
                        processed += 1

                        if result.get('status') == 'error':
                            errors += 1
                            self.stdout.write(
                                self.style.ERROR(
                                    f"  Error analyzing {media_file.original_filename}: "
                                    f"{result.get('error')}"
                                )
                            )
                        elif result.get('is_inappropriate'):
                            flagged += 1
                            action = result.get('action', 'none')
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ⚠️  FLAGGED: {media_file.original_filename} "
                                    f"(confidence: {result.get('confidence_score', 0):.2f}, "
                                    f"action: {action})"
                                )
                            )
                        else:
                            approved += 1
                            if options['verbosity'] >= 2:
                                self.stdout.write(
                                    f"  ✓ APPROVED: {media_file.original_filename}"
                                )

                except Exception as e:
                    errors += 1
                    logger.error(f"Error processing file {media_file.id}: {e}")
                    self.stdout.write(
                        self.style.ERROR(f"  Error processing {media_file.original_filename}: {e}")
                    )

        # Print summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"Batch analysis completed!"))
        self.stdout.write(f"Total processed: {processed}")
        self.stdout.write(self.style.SUCCESS(f"Approved: {approved}"))
        
        if flagged > 0:
            self.stdout.write(self.style.WARNING(f"Flagged: {flagged}"))
        
        if errors > 0:
            self.stdout.write(self.style.ERROR(f"Errors: {errors}"))

        # Show flagged files summary
        if flagged > 0:
            self.stdout.write("\nFiles flagged for review:")
            flagged_files = MediaFile.objects.filter(
                content_moderation_status=MediaFile.ContentModerationStatus.FLAGGED
            ).order_by('-content_moderation_checked_at')[:10]
            
            for media_file in flagged_files:
                user_info = ""
                if hasattr(media_file, 'created_by') and media_file.created_by:
                    user_info = f" (user: {media_file.created_by.email})"
                
                self.stdout.write(
                    f"  - {media_file.original_filename}{user_info} "
                    f"(score: {media_file.content_moderation_score:.2f})"
                )