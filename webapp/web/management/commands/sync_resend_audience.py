"""
Django management command to synchronize user marketing preferences with Resend audience
"""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction, models
from django.utils import timezone
from web.services.resend_service import sync_user_marketing_subscription, resend_service

logger = logging.getLogger("webapp")
User = get_user_model()


class Command(BaseCommand):
    help = 'Synchronize user marketing email preferences with Resend audience'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Sync only a specific user by ID',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Sync only a specific user by email',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of users to process in each batch (default: 50)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force sync even if recently checked',
        )

    def handle(self, *args, **options):
        """
        Main command handler
        """
        dry_run = options['dry_run']
        user_id = options['user_id']
        email = options['email']
        batch_size = options['batch_size']
        force = options['force']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Check Resend configuration
        if not resend_service.api_key or not resend_service.audience_id:
            self.stdout.write(
                self.style.ERROR('Resend API not configured. Check RESEND_API_KEY and RESEND_MARKETING_AUDIENCE_ID')
            )
            return
        
        # Get users to sync
        users_queryset = User.objects.select_related('profile')
        
        if user_id:
            users_queryset = users_queryset.filter(id=user_id)
        elif email:
            users_queryset = users_queryset.filter(email=email)
        else:
            # Filter users that need syncing
            if not force:
                from datetime import timedelta
                cutoff_time = timezone.now() - timedelta(hours=1)  # Only sync if not checked in last hour
                users_queryset = users_queryset.filter(
                    models.Q(profile__resend_last_checked_at__isnull=True) |
                    models.Q(profile__resend_last_checked_at__lt=cutoff_time) |
                    models.Q(profile__resend_sync_status__in=['unknown', 'out_of_sync', 'error'])
                )
        
        users_count = users_queryset.count()
        
        if users_count == 0:
            self.stdout.write(
                self.style.SUCCESS('No users need syncing.')
            )
            return
        
        self.stdout.write(f'Found {users_count} users to sync.')
        
        # Process users in batches
        processed = 0
        errors = 0
        synced = 0
        
        for i in range(0, users_count, batch_size):
            batch = users_queryset[i:i + batch_size]
            
            for user in batch:
                try:
                    if not hasattr(user, 'profile'):
                        self.stdout.write(
                            self.style.WARNING(f'User {user.email} has no profile, skipping')
                        )
                        continue
                    
                    old_status = user.profile.resend_sync_status
                    
                    if not dry_run:
                        with transaction.atomic():
                            sync_user_marketing_subscription(user)
                    
                    new_status = user.profile.resend_sync_status if not dry_run else 'would_sync'
                    
                    if old_status != new_status or dry_run:
                        self.stdout.write(
                            f'  {user.email}: {old_status} -> {new_status}'
                        )
                        synced += 1
                    
                    processed += 1
                    
                except Exception as e:
                    errors += 1
                    self.stdout.write(
                        self.style.ERROR(f'Error syncing {user.email}: {str(e)}')
                    )
                    logger.error(f'Error syncing user {user.email}: {str(e)}')
            
            # Progress update
            if processed % 100 == 0:
                self.stdout.write(f'Processed {processed}/{users_count} users...')
        
        # Final summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSync completed:\n'
                f'  Processed: {processed} users\n'
                f'  Synced: {synced} users\n'
                f'  Errors: {errors} users'
            )
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('This was a dry run - no changes were made')
            )