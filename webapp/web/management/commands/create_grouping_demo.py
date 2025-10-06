# -*- coding: utf-8 -*-

"""
Management command to create a demo collection showcasing the grouping feature (Task 47).
Creates a collection of Discworld novels grouped by series.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from web.models import Collection, CollectionItem, ItemType, ItemAttribute, CollectionItemAttributeValue

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a demo collection to showcase attribute grouping (Task 47)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            help='Username of the collection owner (defaults to first superuser)',
        )

    def handle(self, *args, **options):
        # Get user
        username = options.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{username}" not found'))
                return
        else:
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                self.stdout.write(self.style.ERROR('No superuser found. Please create one first.'))
                return

        self.stdout.write(f'Creating demo collection for user: {user.username}')

        # Get or create "Book" item type
        book_type, created = ItemType.objects.get_or_create(
            name='book',
            defaults={
                'display_name': 'Book',
                'description': 'A physical or digital book',
                'created_by': user
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created item type: {book_type.display_name}'))

        # Get or create "Series" attribute
        series_attr, created = ItemAttribute.objects.get_or_create(
            item_type=book_type,
            name='series',
            defaults={
                'display_name': 'Series',
                'attribute_type': 'TEXT',
                'created_by': user
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created attribute: {series_attr.display_name}'))

        # Get or create "Author" attribute
        author_attr, created = ItemAttribute.objects.get_or_create(
            item_type=book_type,
            name='author',
            defaults={
                'display_name': 'Author',
                'attribute_type': 'TEXT',
                'created_by': user
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created attribute: {author_attr.display_name}'))

        # Create collection with grouping enabled
        collection = Collection.objects.create(
            name='Discworld Novels Collection',
            description='A collection of Terry Pratchett\'s Discworld novels, grouped by series',
            group_by=Collection.GroupBy.ATTRIBUTE,
            grouping_attribute=series_attr,
            sort_by=Collection.SortBy.NAME,
            created_by=user
        )
        self.stdout.write(self.style.SUCCESS(f'Created collection: {collection.name}'))

        # Define books with their series
        books = [
            # Rincewind series
            {'name': 'The Colour of Magic', 'series': 'Rincewind'},
            {'name': 'The Light Fantastic', 'series': 'Rincewind'},
            {'name': 'Sourcery', 'series': 'Rincewind'},
            {'name': 'Eric', 'series': 'Rincewind'},

            # Death series
            {'name': 'Mort', 'series': 'Death'},
            {'name': 'Reaper Man', 'series': 'Death'},
            {'name': 'Soul Music', 'series': 'Death'},
            {'name': 'Hogfather', 'series': 'Death'},

            # Witches series
            {'name': 'Equal Rites', 'series': 'Witches'},
            {'name': 'Wyrd Sisters', 'series': 'Witches'},
            {'name': 'Witches Abroad', 'series': 'Witches'},
            {'name': 'Lords and Ladies', 'series': 'Witches'},

            # City Watch series
            {'name': 'Guards! Guards!', 'series': 'City Watch'},
            {'name': 'Men at Arms', 'series': 'City Watch'},
            {'name': 'Feet of Clay', 'series': 'City Watch'},

            # Standalone
            {'name': 'Small Gods', 'series': None},
            {'name': 'Pyramids', 'series': None},
        ]

        # Create items with attributes
        for book_data in books:
            item = CollectionItem.objects.create(
                collection=collection,
                name=book_data['name'],
                item_type=book_type,
                status=CollectionItem.Status.IN_COLLECTION,
                created_by=user
            )

            # Add author attribute
            author_value = CollectionItemAttributeValue.objects.create(
                item=item,
                item_attribute=author_attr,
                created_by=user
            )
            author_value.set_typed_value('Terry Pratchett')
            author_value.save()

            # Add series attribute if book has a series
            if book_data['series']:
                series_value = CollectionItemAttributeValue.objects.create(
                    item=item,
                    item_attribute=series_attr,
                    created_by=user
                )
                series_value.set_typed_value(book_data['series'])
                series_value.save()

            self.stdout.write(f'  Created: {item.name}')

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Demo collection created successfully!\n'
            f'Collection: {collection.name} ({collection.hash})\n'
            f'Items: {collection.items.count()}\n'
            f'Group By: {collection.get_group_by_display()}\n'
            f'Sort By: {collection.get_sort_by_display()}\n'
            f'\nView at: /collections/{collection.hash}/'
        ))
