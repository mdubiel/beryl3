# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import random
from faker import Faker

from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from django.test import Client
from allauth.account.models import EmailAddress
from web.models import Collection, CollectionItem, RecentActivity

User = get_user_model()

class Command(BaseCommand):
    help = "Generates a fully activated test user and verifies the RecentActivity logging system."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("--- Starting Activity Log Verification Script ---"))
        faker = Faker()

        # Step 1: Generate and Register a new user
        password = faker.password(length=12, special_chars=True, digits=True, upper_case=True, lower_case=True)
        username = f"testuser_{faker.user_name().lower().replace(' ', '')}_{random.randint(100, 999)}"
        email = f"{username}@example.com"
        
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.ERROR(f"Generated user '{username}' already exists. Please run the command again."))
            return

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f"Step 1: Successfully registered new user '{user.username}'"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create user: {e}"))
            return

        # Step 2: Manually Create and Verify the allauth EmailAddress object
        try:
            EmailAddress.objects.create(
                user=user,
                email=email,
                primary=True,
                verified=True
            )
            self.stdout.write(self.style.NOTICE(f"   - Created and verified EmailAddress '{email}' for allauth."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to create EmailAddress object: {e}"))
            return


        # Step 3: Log the user in to trigger the signal
        client = Client()
        login_successful = client.login(username=username, password=password)
        if login_successful:
            self.stdout.write(self.style.SUCCESS(f"Step 3: Successfully logged in as '{user.username}' to trigger signal."))
        else:
            self.stdout.write(self.style.ERROR("Failed to log in the new user. Check password or if account is active."))
            return
            
        # Step 4: Create a new Collection
        collection = Collection.objects.create(
            created_by=user,
            name=f"{faker.bs().title()} Collection",
            description=faker.sentence()
        )
        self.stdout.write(self.style.SUCCESS(f"Step 4: Created collection '{collection.name}'"))
        
        # Step 5 & 6: Create and Reserve Items
        self.stdout.write(self.style.NOTICE(f"Step 5: Creating 3 'Wanted' items..."))
        item_to_reserve = None
        for i in range(3):
            item = CollectionItem.objects.create(
                collection=collection,
                created_by=user,
                name=f"Wanted Item #{i+1}",
                status=CollectionItem.Status.WANTED
            )
            item_to_reserve = item
        
        if item_to_reserve:
            item_to_reserve.status = CollectionItem.Status.RESERVED
            item_to_reserve.save(update_fields=['status'])
            self.stdout.write(self.style.SUCCESS(f"Step 6: Reserved item '{item_to_reserve.name}'"))
        else:
            self.stdout.write(self.style.ERROR("Could not reserve an item."))
            return

        # Final Verification
        self.stdout.write(self.style.NOTICE("\n--- Verifying Created Activity Logs ---"))
        activities = RecentActivity.objects.filter(created_by=user).order_by('created')
        
        expected_log_count = 4 
        if activities.count() == expected_log_count:
            self.stdout.write(self.style.SUCCESS(f"SUCCESS: Found {activities.count()} activity logs as expected."))
        else:
            self.stdout.write(self.style.WARNING(f"WARNING: Found {activities.count()} logs, but expected {expected_log_count}."))

        for activity in activities:
            self.stdout.write(f"  - [{activity.created.strftime('%Y-%m-%d %H:%M')}] {activity}")

        # Final Credentials Output
        self.stdout.write(self.style.SUCCESS("\n" + ("-"*50)))
        self.stdout.write(self.style.SUCCESS("  Test User Ready for Manual Login"))
        self.stdout.write(self.style.SUCCESS(f"  Email:    {email}"))
        self.stdout.write(self.style.SUCCESS(f"  Password: {password}"))
        self.stdout.write(self.style.SUCCESS( ("-"*50)))