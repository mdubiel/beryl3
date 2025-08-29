"""
Management command to create a sample collection with items, descriptions, images, and attributes.
This command is useful for testing, demos, and populating the system with sample data.
"""

import random
import requests
from io import BytesIO
from django.core.management.base import BaseCommand, CommandError
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
from django.db import transaction
from faker import Faker
from web.models import (
    Collection, CollectionItem, ItemType, ItemAttribute, 
    CollectionImage, CollectionItemImage, MediaFile, CollectionItemLink
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates a sample collection with items, descriptions, images, and attributes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of the user who will own the collection',
            required=True
        )
        parser.add_argument(
            '--collection-name',
            type=str,
            help='Name of the collection to create (if not provided, will generate random name)'
        )
        parser.add_argument(
            '--item-count',
            type=int,
            default=15,
            help='Number of items to create (default: 15)'
        )
        parser.add_argument(
            '--images-per-item',
            type=int,
            default=3,
            help='Average number of images per item (default: 3)'
        )

    def handle(self, *args, **options):
        user_email = options['user_email']
        collection_name = options.get('collection_name')
        item_count = options['item_count']
        images_per_item = options['images_per_item']

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            raise CommandError(f'User with email "{user_email}" does not exist')

        # Generate collection name if not provided
        if not collection_name:
            fake = Faker()
            collection_name = f"[test] {fake.catch_phrase()} Collection"

        self.stdout.write(f'Creating sample collection for user: {user.email}')
        self.stdout.write(f'Collection name: {collection_name}')

        with transaction.atomic():
            # Create collection
            collection = self.create_collection(user, collection_name)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created collection: {collection.name}')
            )

            # Add collection images
            self.add_collection_images(collection)
            self.stdout.write('✓ Added collection images')

            # Create items
            self.create_items(collection, item_count, images_per_item)
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created {item_count} items with images and attributes')
            )

        # Verify collection was created correctly
        collection.refresh_from_db()
        if collection.created_by != user:
            raise CommandError(f'Collection was not properly bound to user {user.email}')
            
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSample collection created successfully!\n'
                f'Collection: {collection.name} ({collection.hash})\n'
                f'Items: {item_count}\n'
                f'Owner: {collection.created_by.email if collection.created_by else "None"}\n'
                f'Visibility: {collection.visibility}'
            )
        )

    def create_collection(self, user, name):
        """Create a collection with random description and visibility."""
        description = self.generate_description(
            "collection", 
            name, 
            random.randint(100, 1000)
        )
        
        visibility_choices = ['PUBLIC', 'UNLISTED', 'PRIVATE']
        visibility = random.choice(visibility_choices)
        
        collection = Collection.objects.create(
            name=name,
            description=description,
            visibility=visibility,
            created_by=user
        )
        
        return collection

    def add_collection_images(self, collection):
        """Add random images to the collection from free image sources."""
        num_images = random.randint(2, 4)
        
        for i in range(num_images):
            try:
                media_file = self.download_random_image(
                    f"collection-{collection.hash}-{i+1}",
                    category="landscape"
                )
                
                if media_file:
                    CollectionImage.objects.create(
                        collection=collection,
                        media_file=media_file,
                        is_default=(i == 0)  # First image is default
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Warning: Could not add collection image {i+1}: {e}')
                )

    def create_items(self, collection, count, avg_images_per_item):
        """Create items with descriptions, attributes, links, and images."""
        # Get or create item types
        item_types = self.get_or_create_item_types()
        
        item_names = [
            "Vintage Camera", "Classic Lens", "Photography Book", "Tripod Stand",
            "Flash Equipment", "Film Roll", "Light Meter", "Camera Bag",
            "Photography Print", "Darkroom Timer", "Enlarger", "Photo Album",
            "Studio Light", "Reflector", "Memory Card", "Camera Filter",
            "Photo Frame", "Slide Projector", "Contact Sheet", "Developer Chemical"
        ]
        
        for i in range(count):
            try:
                # Pick random item type and name
                item_type = random.choice(item_types)
                base_name = random.choice(item_names)
                item_name = f"{base_name} #{i+1:03d}"
                
                # Create item
                item = CollectionItem.objects.create(
                    collection=collection,
                    name=item_name,
                    description=self.generate_description("item", item_name, random.randint(100, 1000)),
                    status=random.choice(['IN_COLLECTION', 'WANTED', 'LENT_OUT']),
                    item_type=item_type,
                    created_by=collection.created_by,
                    is_favorite=random.choice([True, False, False])  # 33% chance of favorite
                )
                
                # Add attributes
                self.add_item_attributes(item, item_type)
                
                # Add links
                self.add_item_links(item)
                
                # Add images
                self.add_item_images(item, avg_images_per_item)
                
                if (i + 1) % 5 == 0:
                    self.stdout.write(f'  Created {i + 1}/{count} items...')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Warning: Could not create item {i+1}: {e}')
                )

    def get_or_create_item_types(self):
        """Get existing item types or create sample ones."""
        # Try to get existing item types first
        existing_types = list(ItemType.objects.all()[:10])
        if existing_types:
            return existing_types
        
        # Create sample item types if none exist
        sample_types = [
            {"name": "camera", "display_name": "Camera", "icon": "camera"},
            {"name": "book", "display_name": "Book", "icon": "book"},
            {"name": "equipment", "display_name": "Equipment", "icon": "tool"},
            {"name": "print", "display_name": "Print", "icon": "image"},
            {"name": "accessory", "display_name": "Accessory", "icon": "package"},
        ]
        
        created_types = []
        for type_data in sample_types:
            item_type, created = ItemType.objects.get_or_create(
                name=type_data["name"],
                defaults={
                    "display_name": type_data["display_name"],
                    "icon": type_data["icon"]
                }
            )
            created_types.append(item_type)
            
        return created_types

    def add_item_attributes(self, item, item_type):
        """Add random attributes to an item based on its type."""
        if not item_type:
            return
            
        # Get or create sample attributes for this item type
        attributes = self.get_or_create_sample_attributes(item_type)
        
        # Add random values for some attributes
        num_attributes = random.randint(2, min(5, len(attributes)))
        selected_attributes = random.sample(attributes, num_attributes)
        
        item_attributes = {}
        for attr in selected_attributes:
            value = self.generate_attribute_value(attr)
            if value:
                item_attributes[attr.name] = value
                
        if item_attributes:
            item.attributes = item_attributes
            item.save()

    def get_or_create_sample_attributes(self, item_type):
        """Get or create sample attributes for an item type."""
        existing_attrs = list(item_type.attributes.all())
        if existing_attrs:
            return existing_attrs[:8]  # Limit to reasonable number
            
        # Create sample attributes if none exist
        sample_attrs = [
            {"name": "brand", "display_name": "Brand", "attribute_type": "TEXT"},
            {"name": "model", "display_name": "Model", "attribute_type": "TEXT"},
            {"name": "year", "display_name": "Year", "attribute_type": "NUMBER"},
            {"name": "condition", "display_name": "Condition", "attribute_type": "CHOICE", 
             "choices": ["Mint", "Excellent", "Good", "Fair", "Poor"]},
            {"name": "color", "display_name": "Color", "attribute_type": "TEXT"},
            {"name": "weight", "display_name": "Weight (g)", "attribute_type": "NUMBER"},
            {"name": "purchased", "display_name": "Date Purchased", "attribute_type": "DATE"},
            {"name": "working", "display_name": "Working Condition", "attribute_type": "BOOLEAN"},
        ]
        
        created_attrs = []
        for attr_data in sample_attrs:
            choices_data = attr_data.get("choices")
            choices_json = {}
            if choices_data:
                choices_json = {"choices": choices_data}
                
            attr, created = ItemAttribute.objects.get_or_create(
                item_type=item_type,
                name=attr_data["name"],
                defaults={
                    "display_name": attr_data["display_name"],
                    "attribute_type": attr_data["attribute_type"],
                    "choices": choices_json,
                    "required": False
                }
            )
            created_attrs.append(attr)
            
        return created_attrs

    def generate_attribute_value(self, attribute):
        """Generate a random value for an attribute based on its type."""
        attr_type = attribute.attribute_type
        
        if attr_type == "TEXT":
            if "brand" in attribute.name.lower():
                return random.choice(["Canon", "Nikon", "Sony", "Fuji", "Leica", "Pentax"])
            elif "model" in attribute.name.lower():
                return f"Model {random.randint(100, 999)}{random.choice(['A', 'B', 'X', 'Pro'])}"
            elif "color" in attribute.name.lower():
                return random.choice(["Black", "Silver", "White", "Brown", "Red", "Blue"])
            else:
                return f"Sample {random.choice(['Value', 'Text', 'Data'])}"
                
        elif attr_type == "NUMBER":
            if "year" in attribute.name.lower():
                return random.randint(1950, 2024)
            elif "weight" in attribute.name.lower():
                return random.randint(50, 2000)
            else:
                return random.randint(1, 100)
                
        elif attr_type == "CHOICE":
            if hasattr(attribute, 'choices') and attribute.choices:
                if isinstance(attribute.choices, dict):
                    choices = attribute.choices.get("choices", [])
                else:
                    choices = attribute.choices
                return random.choice(choices) if choices else None
            return None
            
        elif attr_type == "BOOLEAN":
            return random.choice([True, False])
            
        elif attr_type == "DATE":
            from datetime import date, timedelta
            start_date = date(2020, 1, 1)
            end_date = date.today()
            random_days = random.randint(0, (end_date - start_date).days)
            return (start_date + timedelta(days=random_days)).isoformat()
            
        return None

    def add_item_links(self, item):
        """Add random links to an item."""
        num_links = random.randint(0, 3)
        
        sample_links = [
            {"url": "https://example.com/manual", "description": "User Manual"},
            {"url": "https://example.com/reviews", "description": "Reviews"},
            {"url": "https://example.com/specs", "description": "Technical Specs"},
            {"url": "https://example.com/gallery", "description": "Photo Gallery"},
            {"url": "https://example.com/forum", "description": "Discussion Forum"},
        ]
        
        for i in range(num_links):
            link_data = random.choice(sample_links)
            CollectionItemLink.objects.create(
                item=item,
                url=link_data["url"],
                display_name=link_data["description"]
            )

    def add_item_images(self, item, avg_count):
        """Add random images to an item."""
        num_images = max(1, random.randint(1, avg_count * 2))  # At least 1 image
        
        for i in range(num_images):
            try:
                media_file = self.download_random_image(
                    f"item-{item.hash}-{i+1}",
                    category=random.choice(["object", "technology", "vintage"])
                )
                
                if media_file:
                    CollectionItemImage.objects.create(
                        item=item,
                        media_file=media_file,
                        is_default=(i == 0)  # First image is default
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Warning: Could not add image {i+1} to item {item.name}: {e}')
                )

    def download_random_image(self, filename, category="nature", width=800, height=600):
        """Download a random image from Picsum (Lorem Ipsum for photos)."""
        try:
            from django.core.files.storage import default_storage
            
            # Use Picsum for free random images
            url = f"https://picsum.photos/{width}/{height}?random={hash(filename)}"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Save file to storage
            file_path = f"sample_images/{filename}.jpg"
            saved_path = default_storage.save(file_path, ContentFile(response.content))
            
            # Create MediaFile record
            media_file = MediaFile.objects.create(
                original_filename=f"{filename}.jpg",
                file_size=len(response.content),
                content_type="image/jpeg",
                file_path=saved_path,
                storage_backend=MediaFile.StorageBackend.LOCAL,
                media_type=MediaFile.MediaType.COLLECTION_ITEM,
                file_exists=True
            )
            
            return media_file
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not download image {filename}: {e}')
            )
            return None

    def generate_description(self, content_type, name, length):
        """Generate a random description of specified length."""
        base_texts = {
            "collection": [
                f"Welcome to {name}, a carefully curated collection that showcases",
                "This collection represents years of passionate collecting and research.",
                f"Each item in {name} has been selected for its historical significance",
                "This comprehensive collection features items spanning multiple decades",
                f"The {name} collection documents the evolution of photography through"
            ],
            "item": [
                f"This {name} is a remarkable example of vintage photography equipment.",
                f"The {name} represents a significant piece of photographic history.",
                f"This particular {name} showcases the craftsmanship of its era.",
                f"Found in excellent condition, this {name} tells a story of dedication",
                f"The {name} is a testament to the quality and durability of classic"
            ]
        }
        
        filler_sentences = [
            "Its pristine condition reflects the care it has received over the years.",
            "The attention to detail in its construction is immediately apparent.",
            "This piece has been professionally maintained and stored in optimal conditions.",
            "The patina and wear patterns tell the story of its authentic use.",
            "Documentation and provenance add significant value to this acquisition.",
            "It represents the pinnacle of manufacturing quality from its time period.",
            "The mechanical precision and smooth operation demonstrate superior engineering.",
            "This example showcases features that were innovative for its time.",
            "The aesthetic design reflects the artistic sensibilities of the era.",
            "Its functional capabilities remain impressive by today's standards.",
            "The materials used in its construction were selected for durability.",
            "Every component shows the meticulous attention to quality control.",
            "The finish and surface treatments have aged gracefully over time.",
            "This piece would be equally at home in a museum or private collection.",
            "The historical context surrounding its development is fascinating.",
            "It represents a significant investment in preserving photographic heritage.",
            "The craftsmanship evident in every detail is truly remarkable.",
            "This example demonstrates the evolution of design and technology.",
            "The functionality and form combine to create something truly special.",
            "Its place in the broader context of collecting cannot be overstated."
        ]
        
        # Start with a base sentence
        base = random.choice(base_texts[content_type])
        text = base
        
        # Add filler sentences until we reach desired length
        while len(text) < length:
            remaining_length = length - len(text) - 1  # Account for space
            
            if remaining_length < 50:  # If very little space left
                text += " A truly exceptional piece."
                break
                
            sentence = random.choice(filler_sentences)
            if len(text) + len(sentence) + 1 <= length:
                text += " " + sentence
            else:
                # Truncate the last sentence to fit
                available_space = remaining_length - 1
                if available_space > 20:
                    text += " " + sentence[:available_space-3] + "..."
                break
        
        return text.strip()