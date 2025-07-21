# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from web.models import Collection, CollectionItem, RecentActivity


class Command(BaseCommand):
    help = 'Create Application admin group with appropriate permissions'

    def handle(self, *args, **options):
        # Create the Application admin group
        admin_group, created = Group.objects.get_or_create(name='Application admin')
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created "Application admin" group')
            )
        else:
            self.stdout.write(
                self.style.WARNING('"Application admin" group already exists')
            )

        # Define permissions for the admin group
        permissions_to_add = [
            # User management
            'auth.view_user',
            'auth.change_user',
            'auth.delete_user',
            
            # Group management
            'auth.view_group',
            'auth.change_group',
            
            # Collection management
            'web.view_collection',
            'web.change_collection',
            'web.delete_collection',
            
            # Collection item management
            'web.view_collectionitem',
            'web.change_collectionitem',
            'web.delete_collectionitem',
            
            # Activity logs
            'web.view_recentactivity',
            'web.delete_recentactivity',
            
            # Item types and attributes
            'web.view_itemtype',
            'web.change_itemtype',
            'web.delete_itemtype',
            'web.view_itemattribute',
            'web.change_itemattribute',
            'web.delete_itemattribute',
        ]

        added_permissions = []
        for perm_codename in permissions_to_add:
            try:
                app_label, codename = perm_codename.split('.')
                permission = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                admin_group.permissions.add(permission)
                added_permissions.append(perm_codename)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'Permission {perm_codename} not found')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Added {len(added_permissions)} permissions to Application admin group')
        )
        
        # List current members
        members = admin_group.user_set.all()
        if members:
            self.stdout.write('Current group members:')
            for user in members:
                self.stdout.write(f'  - {user.username} ({user.email})')
        else:
            self.stdout.write(
                self.style.WARNING('No users in Application admin group yet')
            )
            self.stdout.write(
                'To add users to this group, use: python manage.py shell'
            )
            self.stdout.write(
                'Then: from django.contrib.auth import get_user_model; '
                'from django.contrib.auth.models import Group; '
                'user = get_user_model().objects.get(email="your@email.com"); '
                'group = Group.objects.get(name="Application admin"); '
                'user.groups.add(group)'
            )