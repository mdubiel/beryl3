"""
Management command to set up initial users for QA environment.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from allauth.account.models import EmailAddress

User = get_user_model()


class Command(BaseCommand):
    help = 'Create initial users for QA environment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Delete and recreate users if they already exist',
        )

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial users for QA environment...')
        
        # Create or get admin group with all permissions
        admin_group = self.get_or_create_admin_group()
        
        # User 1: Super admin
        admin_user = self.create_user(
            user_id=1,
            email='admin@mdubiel.org',
            password='Admin123!',
            is_superuser=True,
            is_staff=True,
            recreate=options['recreate']
        )
        
        if admin_user:
            self.stdout.write(f'  Created superuser: {admin_user.email} (ID: {admin_user.id})')
            self.verify_email(admin_user)
        
        # User 2: System panel access user
        sys_user = self.create_user(
            user_id=2,
            email='mdubiel@gmail.com',
            password='Admin123!',
            is_superuser=False,
            is_staff=True,
            recreate=options['recreate']
        )
        
        if sys_user:
            # Add to admin group for system panel access
            sys_user.groups.add(admin_group)
            self.stdout.write(f'  Created system user: {sys_user.email} (ID: {sys_user.id})')
            self.verify_email(sys_user)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created initial users!')
        )

    def get_or_create_admin_group(self):
        """Create or get admin group with system panel permissions."""
        group, created = Group.objects.get_or_create(name='System Administrators')
        
        if created:
            self.stdout.write('  Created System Administrators group')
            
            # Add permissions for accessing admin/system panel
            # You can customize these permissions based on your needs
            permissions = [
                'auth.view_user',
                'auth.add_user', 
                'auth.change_user',
                'auth.delete_user',
                'auth.view_group',
                'auth.add_group',
                'auth.change_group',
                'auth.delete_group',
            ]
            
            for perm_code in permissions:
                try:
                    app_label, codename = perm_code.split('.')
                    permission = Permission.objects.get(
                        content_type__app_label=app_label,
                        codename=codename
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'    Permission {perm_code} not found, skipping')
                    )
        
        return group

    def create_user(self, user_id, email, password, is_superuser=False, is_staff=False, recreate=False):
        """Create a user with specific ID."""
        try:
            # Check if user exists
            user = User.objects.get(id=user_id)
            if recreate:
                user.delete()
                self.stdout.write(f'  Deleted existing user with ID {user_id}')
            else:
                self.stdout.write(f'  User with ID {user_id} already exists, skipping')
                return user
        except User.DoesNotExist:
            pass
        
        # Also check by email
        try:
            existing_user = User.objects.get(email=email)
            if recreate:
                existing_user.delete()
                self.stdout.write(f'  Deleted existing user with email {email}')
            else:
                self.stdout.write(f'  User with email {email} already exists, skipping')
                return existing_user
        except User.DoesNotExist:
            pass
        
        # Create the user with specific ID
        user = User(
            id=user_id,
            email=email,
            username=email,  # Use email as username
            is_superuser=is_superuser,
            is_staff=is_staff,
            is_active=True
        )
        user.set_password(password)
        user.save()
        
        return user

    def verify_email(self, user):
        """Mark email as verified for django-allauth."""
        email_address, created = EmailAddress.objects.get_or_create(
            user=user,
            email=user.email,
            defaults={
                'verified': True,
                'primary': True
            }
        )
        
        if not created and not email_address.verified:
            email_address.verified = True
            email_address.primary = True
            email_address.save()
        
        self.stdout.write(f'    Email {user.email} marked as verified')