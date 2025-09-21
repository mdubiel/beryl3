# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

import random
from web.models import Collection, CollectionItem
from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()


class Command(BaseCommand):

    help = "Creates a regular user and generates test data for collections and items."

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate',
            action='store_true',
            help='Delete and recreate user if they already exist',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Creating regular user and seeding test data...")

        # Create or get the regular user
        user = self.create_user(
            email='user@mdubiel.org',
            password='User123!',
            recreate=options['recreate']
        )
        
        if not user:
            self.stdout.write(self.style.ERROR("Failed to create user. Aborting."))
            return

        self.stdout.write(f"Created/found user: {user.email} (ID: {user.id})")
        self.verify_email(user)

        # Initialize Faker
        faker = Faker()

        # Create Collections and Items
        for _ in range(5):
            collection_name = f"{faker.word().capitalize()} {faker.word().capitalize()} Collection"
            collection = Collection.objects.create(
                created_by=user,
                name=collection_name,
                description=faker.sentence(nb_words=10),
                image_url=f"https://picsum.photos/seed/{faker.slug()}/800/600"
            )
            self.stdout.write(f"  Created Collection: '{collection.name}'")

            # Create a random number of items for this collection ---
            num_items = random.randint(10, 20)
            for _ in range(num_items):
                item_name = f"{faker.color_name().capitalize()} {faker.word().capitalize()}"
                CollectionItem.objects.create(
                    collection=collection,
                    created_by=user,
                    name=item_name,
                    description=faker.bs(),
                    status=random.choice(CollectionItem.Status.values),
                    image_url=f"https://picsum.photos/seed/{faker.slug()}/400/300"
                )

            self.stdout.write(f"    - Added {num_items} items to '{collection.name}'")

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded data for user '{user.username}'.")
            ) # pylint: disable=no-member

    def create_user(self, email, password, recreate=False):
        """Create a regular user."""
        try:
            # Check if user exists by email
            existing_user = User.objects.get(email=email)
            if recreate:
                existing_user.delete()
                self.stdout.write(f'  Deleted existing user: {email}')
            else:
                self.stdout.write(f'  User {email} already exists, using existing user')
                return existing_user
        except User.DoesNotExist:
            pass
        
        # Create the user
        user = User(
            email=email,
            username=email,  # Use email as username
            is_superuser=False,
            is_staff=False,
            is_active=True
        )
        user.set_password(password)
        user.save()
        
        self.stdout.write(f'  Created regular user: {email} (ID: {user.id})')
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
