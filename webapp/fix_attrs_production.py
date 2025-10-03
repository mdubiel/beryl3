#!/usr/bin/env python3
"""
Direct script to fix production attributes
Run this on Django Europe production server
"""

import os
import sys
import django
import re

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'production_settings')
django.setup()

from web.models import Collection, CollectionItem, ItemType, ItemAttribute
from django.contrib.auth import get_user_model

def main():
    User = get_user_model()
    user = User.objects.get(username="mdubiel")
    print(f"Found user: {user.username}")

    # Polish to English mapping
    polish_to_english = {
        "Seria": "series",
        "Autor": "author", 
        "Wydawca": "publisher",
        "Wolumen": "volume",
        "Przeczytane": "read_status",
        "Numer zestawu": "set_number",
        "Ilość części": "piece_count"
    }

    # Get item types
    book_type = ItemType.objects.filter(name="book").first()
    lego_type = ItemType.objects.filter(name="lego_set").first()
    comic_type = ItemType.objects.filter(name="comic").first()

    print(f"Item types: book={book_type is not None}, lego={lego_type is not None}, comic={comic_type is not None}")

    # Create missing attributes for book type
    if book_type:
        for english_name in ["series", "volume", "read_status"]:
            attr, created = ItemAttribute.objects.get_or_create(
                name=english_name,
                item_type=book_type,
                defaults={
                    "display_name": english_name.replace("_", " ").title(),
                    "attribute_type": "BOOLEAN" if english_name == "read_status" else "TEXT",
                    "required": False,
                    "order": 10
                }
            )
            print(f"Attribute {english_name}: {'created' if created else 'exists'}")

    # Process items
    items = CollectionItem.objects.filter(created_by=user)
    print(f"Processing {items.count()} items...")

    sample_item = items.first()
    if sample_item:
        print(f"Sample item: {sample_item.name}")
        print(f"Description preview: {sample_item.description[:200]}...")
        print(f"Current attributes: {sample_item.attributes}")

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
            pattern = rf"{re.escape(polish_name)}:\s*([^\n]+)"
            match = re.search(pattern, item.description)
            if match:
                value = match.group(1).strip()
                parsed_attrs[english_name] = value
                remaining_description = re.sub(pattern + r"\n?", "", remaining_description)
        
        if parsed_attrs:
            # Determine correct item type
            if "set_number" in parsed_attrs or "piece_count" in parsed_attrs:
                new_item_type = lego_type or item.item_type
            elif "series" in parsed_attrs and "volume" in parsed_attrs:
                new_item_type = comic_type or book_type or item.item_type
            else:
                new_item_type = book_type or item.item_type
            
            # Update item
            item.attributes = parsed_attrs
            item.item_type = new_item_type
            item.description = remaining_description.strip()
            item.save()
            
            fixed_count += 1
            if fixed_count <= 10:
                attrs_str = ', '.join([f"{k}={v}" for k, v in parsed_attrs.items()])
                print(f"Fixed: {item.name} -> {attrs_str}")

    print(f"✅ Fixed {fixed_count} items total")

if __name__ == "__main__":
    main()