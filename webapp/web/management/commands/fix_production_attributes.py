"""
Management command to fix production attributes stored in descriptions
and move them to proper JSON attributes field
"""

import json
import re
import logging
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction

from web.models import Collection, CollectionItem, ItemType, ItemAttribute

User = get_user_model()
logger = logging.getLogger("webapp")


class Command(BaseCommand):
    help = 'Fix production attributes from descriptions to JSON field'

    def add_arguments(self, parser):
        parser.add_argument('--user', type=str, required=True, help='Username to fix data for')
        parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without making changes')

    def handle(self, *args, **options):
        username = options['user']
        dry_run = options['dry_run']

        # Get target user
        try:
            target_user = User.objects.get(username=username)
            self.stdout.write(f"Target user: {target_user.username} (ID: {target_user.id})")
        except User.DoesNotExist:
            raise CommandError(f"User '{username}' not found")

        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")

        # Polish to English attribute mapping
        polish_to_english = {
            'Seria': 'series',
            'Autor': 'author', 
            'Wydawca': 'publisher',
            'Wolumen': 'volume',
            'Przeczytane': 'read_status',
            'Numer zestawu': 'set_number',
            'Ilość części': 'piece_count'
        }

        # Get existing item types and their attributes
        book_type = ItemType.objects.filter(name='book').first()
        lego_type = ItemType.objects.filter(name='lego_set').first()
        comic_type = ItemType.objects.filter(name='comic').first()
        
        # Create missing attributes for book type
        if book_type:
            for polish_name, english_name in polish_to_english.items():
                if english_name not in ['set_number', 'piece_count']:  # These are for LEGO
                    attr, created = ItemAttribute.objects.get_or_create(
                        name=english_name,
                        item_type=book_type,
                        defaults={
                            'display_name': english_name.replace('_', ' ').title(),
                            'attribute_type': 'BOOLEAN' if english_name == 'read_status' else 'TEXT',
                            'required': False,
                            'order': 10,
                            'help_text': f'Imported from {polish_name}'
                        }
                    )
                    if created:
                        self.stdout.write(f"Created attribute: {english_name} for book type")

        # Process items
        items = CollectionItem.objects.filter(created_by=target_user)
        self.stdout.write(f"Processing {items.count()} items...")
        
        fixed_count = 0
        for item in items:
            if not item.description:
                continue
                
            # Check if description contains Polish attributes
            has_polish_attrs = any(polish_name in item.description for polish_name in polish_to_english.keys())
            if not has_polish_attrs:
                continue
                
            # Parse attributes from description
            parsed_attrs = {}
            remaining_description = item.description
            
            for polish_name, english_name in polish_to_english.items():
                # Look for pattern: "Polish_name: value"
                pattern = rf"{re.escape(polish_name)}:\s*([^\n]+)"
                match = re.search(pattern, item.description)
                if match:
                    value = match.group(1).strip()
                    parsed_attrs[english_name] = value
                    # Remove this attribute from description
                    remaining_description = re.sub(pattern + r'\n?', '', remaining_description)
            
            if parsed_attrs:
                if not dry_run:
                    # Determine correct item type
                    new_item_type = item.item_type
                    if 'set_number' in parsed_attrs or 'piece_count' in parsed_attrs:
                        new_item_type = lego_type or item.item_type
                    elif 'series' in parsed_attrs and 'volume' in parsed_attrs:
                        new_item_type = comic_type or book_type or item.item_type
                    else:
                        new_item_type = book_type or item.item_type
                    
                    # Update item
                    item.attributes = parsed_attrs
                    item.item_type = new_item_type
                    item.description = remaining_description.strip()
                    item.save()
                
                fixed_count += 1
                if fixed_count <= 10:  # Show first 10
                    attrs_str = ', '.join([f"{k}={v}" for k, v in parsed_attrs.items()])
                    self.stdout.write(f"Fixed: {item.name} -> {attrs_str}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Fixed {fixed_count} items with Polish attributes for user {target_user.username}"
            )
        )