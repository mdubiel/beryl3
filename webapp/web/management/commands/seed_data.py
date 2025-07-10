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

User = get_user_model()


class Command(BaseCommand):

    help = "Generates test data for collections and items for a specific user."

    def add_arguments(self, parser):
        # We add a command-line argument to specify the user ID.
        parser.add_argument(
            '--user-id',
            type=int,
            help='The ID of the user to create data for.',
            required=True
        )

    @transaction.atomic
    def handle(self, *args, **options):
        user_id = options['user_id']
        self.stdout.write(f"Starting to seed data for user with ID: {user_id}...")

        # Get the User
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"User with ID {user_id} not found. Aborting.")) # pylint: disable=no-member
            return

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
