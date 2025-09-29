"""
Django management command to populate item types and their attributes
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from web.models import ItemType, ItemAttribute

logger = logging.getLogger("webapp")


class Command(BaseCommand):
    help = "Populate comprehensive item types and attributes for collection management"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip item types that already exist (by display name)'
        )
        parser.add_argument(
            '--clean-test-data',
            action='store_true',
            help='Remove test item types like "aaa"'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']
        clean_test = options['clean_test_data']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            with transaction.atomic():
                # Clean test data if requested
                if clean_test:
                    self._clean_test_data(dry_run)
                
                # Get current state
                current_types = set(ItemType.objects.values_list('display_name', flat=True))
                self.stdout.write(f'Current item types: {len(current_types)}')
                
                # Create new item types
                created_count = self._create_item_types(dry_run, skip_existing, current_types)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully {"would create" if dry_run else "created"} {created_count} new item types'
                    )
                )
                
                # Show final summary
                if not dry_run:
                    total_types = ItemType.objects.count()
                    total_attributes = ItemAttribute.objects.count()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Final totals: {total_types} item types, {total_attributes} attributes'
                        )
                    )
                
                if dry_run:
                    # Rollback transaction in dry run mode
                    transaction.set_rollback(True)
                    
        except Exception as e:
            logger.error(f"Error populating item types: {str(e)}")
            raise CommandError(f"Failed to populate item types: {str(e)}")

    def _clean_test_data(self, dry_run):
        """Remove test data like 'aaa' item type"""
        test_types = ItemType.objects.filter(display_name__in=['aaa', 'test', 'Test'])
        
        if test_types.exists():
            self.stdout.write(f'{"Would remove" if dry_run else "Removing"} {test_types.count()} test item types')
            if not dry_run:
                for item_type in test_types:
                    item_type.delete()  # Soft delete

    def _create_item_types(self, dry_run, skip_existing, current_types):
        """Create all new item types with their attributes"""
        new_item_types = self._get_new_item_types_data()
        created_count = 0
        
        for item_type_data in new_item_types:
            display_name = item_type_data['display_name']
            
            if display_name in current_types:
                if skip_existing:
                    self.stdout.write(f'Skipping existing: {display_name}')
                    continue
                else:
                    self.stdout.write(self.style.WARNING(f'Updating existing: {display_name}'))
            
            # Create or update item type
            if not dry_run:
                item_type, created = ItemType.objects.get_or_create(
                    display_name=display_name,
                    defaults={
                        'name': display_name.lower().replace(' ', '_').replace('/', '_'),
                        'description': item_type_data['description'],
                        'icon': item_type_data['icon']
                    }
                )
                
                if not created:
                    # Update existing
                    item_type.description = item_type_data['description']
                    item_type.icon = item_type_data['icon']
                    item_type.save()
                
                # Create attributes
                self._create_attributes(item_type, item_type_data['attributes'])
            
            self.stdout.write(f'{"Would create" if dry_run else "Created"}: {display_name} ({len(item_type_data["attributes"])} attributes)')
            created_count += 1
        
        return created_count

    def _create_attributes(self, item_type, attributes_data):
        """Create attributes for an item type"""
        # Remove existing attributes if updating
        item_type.attributes.all().delete()
        
        for order, attr_data in enumerate(attributes_data, 1):
            ItemAttribute.objects.create(
                item_type=item_type,
                name=attr_data['name'].lower().replace(' ', '_'),
                display_name=attr_data['name'],
                attribute_type=attr_data['type'],
                required=attr_data.get('required', False),
                order=order,
                choices=attr_data.get('choices', None)
            )

    def _get_new_item_types_data(self):
        """Return comprehensive item types data structure"""
        return [
            # Entertainment & Media
            {
                'display_name': 'Video Game',
                'description': 'Digital and physical video games across all platforms',
                'icon': 'gamepad-2',
                'attributes': [
                    {'name': 'Platform', 'type': 'CHOICE', 'choices': ['PC', 'PlayStation', 'Xbox', 'Nintendo Switch', 'Mobile']},
                    {'name': 'Genre', 'type': 'TEXT'},
                    {'name': 'Developer', 'type': 'TEXT'},
                    {'name': 'Publisher', 'type': 'TEXT'},
                    {'name': 'Release Year', 'type': 'NUMBER'},
                    {'name': 'ESRB Rating', 'type': 'CHOICE', 'choices': ['E', 'T', 'M', 'AO', 'RP']},
                    {'name': 'Metacritic Score', 'type': 'NUMBER'}
                ]
            },
            {
                'display_name': 'Movie/DVD',
                'description': 'Movies, DVDs, Blu-rays and digital films',
                'icon': 'film',
                'attributes': [
                    {'name': 'Director', 'type': 'TEXT'},
                    {'name': 'Genre', 'type': 'TEXT'},
                    {'name': 'Release Year', 'type': 'NUMBER'},
                    {'name': 'Runtime', 'type': 'NUMBER'},
                    {'name': 'Rating', 'type': 'CHOICE', 'choices': ['G', 'PG', 'PG-13', 'R', 'NC-17']},
                    {'name': 'Studio', 'type': 'TEXT'},
                    {'name': 'Format', 'type': 'CHOICE', 'choices': ['DVD', 'Blu-ray', '4K UHD', 'Digital']}
                ]
            },
            {
                'display_name': 'TV Series',
                'description': 'Television series and shows across all formats',
                'icon': 'tv',
                'attributes': [
                    {'name': 'Creator', 'type': 'TEXT'},
                    {'name': 'Genre', 'type': 'TEXT'},
                    {'name': 'Seasons', 'type': 'NUMBER'},
                    {'name': 'Episodes', 'type': 'NUMBER'},
                    {'name': 'Network', 'type': 'TEXT'},
                    {'name': 'Years Aired', 'type': 'TEXT'},
                    {'name': 'Status', 'type': 'CHOICE', 'choices': ['Ongoing', 'Completed', 'Cancelled']}
                ]
            },
            {
                'display_name': 'Music CD',
                'description': 'Music albums and singles in physical and digital formats',
                'icon': 'disc',
                'attributes': [
                    {'name': 'Artist', 'type': 'TEXT'},
                    {'name': 'Album', 'type': 'TEXT'},
                    {'name': 'Genre', 'type': 'TEXT'},
                    {'name': 'Release Year', 'type': 'NUMBER'},
                    {'name': 'Label', 'type': 'TEXT'},
                    {'name': 'Track Count', 'type': 'NUMBER'},
                    {'name': 'Format', 'type': 'CHOICE', 'choices': ['CD', 'Digital', 'Cassette']}
                ]
            },
            
            # Collectibles & Toys
            {
                'display_name': 'Action Figure',
                'description': 'Action figures, collectible figures and character models',
                'icon': 'user',
                'attributes': [
                    {'name': 'Character', 'type': 'TEXT'},
                    {'name': 'Series', 'type': 'TEXT'},
                    {'name': 'Manufacturer', 'type': 'TEXT'},
                    {'name': 'Scale', 'type': 'TEXT'},
                    {'name': 'Release Year', 'type': 'NUMBER'},
                    {'name': 'Articulation', 'type': 'NUMBER'},
                    {'name': 'Accessories', 'type': 'TEXT'}
                ]
            },
            {
                'display_name': 'Trading Card',
                'description': 'Trading cards including sports, gaming and collectible cards',
                'icon': 'credit-card',
                'attributes': [
                    {'name': 'Game/Set', 'type': 'TEXT'},
                    {'name': 'Card Name', 'type': 'TEXT'},
                    {'name': 'Rarity', 'type': 'CHOICE', 'choices': ['Common', 'Uncommon', 'Rare', 'Ultra Rare']},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['Mint', 'Near Mint', 'Played', 'Poor']},
                    {'name': 'Set Number', 'type': 'TEXT'},
                    {'name': 'Release Year', 'type': 'NUMBER'},
                    {'name': 'Graded', 'type': 'BOOLEAN'}
                ]
            },
            {
                'display_name': 'Coin',
                'description': 'Collectible coins including historical and commemorative pieces',
                'icon': 'circle',
                'attributes': [
                    {'name': 'Country', 'type': 'TEXT'},
                    {'name': 'Denomination', 'type': 'TEXT'},
                    {'name': 'Year', 'type': 'NUMBER'},
                    {'name': 'Composition', 'type': 'TEXT'},
                    {'name': 'Mint Mark', 'type': 'TEXT'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['Uncirculated', 'Fine', 'Good', 'Poor']},
                    {'name': 'Certified', 'type': 'BOOLEAN'}
                ]
            },
            {
                'display_name': 'Stamp',
                'description': 'Postage stamps and philatelic collectibles',
                'icon': 'mail',
                'attributes': [
                    {'name': 'Country', 'type': 'TEXT'},
                    {'name': 'Denomination', 'type': 'TEXT'},
                    {'name': 'Issue Date', 'type': 'DATE'},
                    {'name': 'Topic/Theme', 'type': 'TEXT'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['Mint', 'Used', 'Damaged']},
                    {'name': 'Perforated', 'type': 'BOOLEAN'},
                    {'name': 'Commemorative', 'type': 'BOOLEAN'}
                ]
            },
            
            # Tools & Equipment
            {
                'display_name': 'Tool',
                'description': 'Hand tools, power tools and workshop equipment',
                'icon': 'wrench',
                'attributes': [
                    {'name': 'Tool Type', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Size', 'type': 'TEXT'},
                    {'name': 'Material', 'type': 'TEXT'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['New', 'Good', 'Fair', 'Poor']},
                    {'name': 'Electric', 'type': 'BOOLEAN'}
                ]
            },
            {
                'display_name': 'Kitchen Appliance',
                'description': 'Kitchen appliances and cooking equipment',
                'icon': 'chef-hat',
                'attributes': [
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Capacity', 'type': 'TEXT'},
                    {'name': 'Power', 'type': 'NUMBER'},
                    {'name': 'Year Purchased', 'type': 'NUMBER'},
                    {'name': 'Warranty', 'type': 'BOOLEAN'}
                ]
            },
            
            # Fashion & Accessories
            {
                'display_name': 'Watch',
                'description': 'Wristwatches, pocket watches and timepieces',
                'icon': 'watch',
                'attributes': [
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Movement', 'type': 'CHOICE', 'choices': ['Automatic', 'Quartz', 'Manual']},
                    {'name': 'Case Material', 'type': 'TEXT'},
                    {'name': 'Water Resistance', 'type': 'NUMBER'},
                    {'name': 'Purchase Year', 'type': 'NUMBER'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['Excellent', 'Good', 'Fair', 'Poor']}
                ]
            },
            {
                'display_name': 'Sneaker/Shoe',
                'description': 'Sneakers, shoes and footwear collectibles',
                'icon': 'footprints',
                'attributes': [
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Size', 'type': 'TEXT'},
                    {'name': 'Colorway', 'type': 'TEXT'},
                    {'name': 'Release Year', 'type': 'NUMBER'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['Deadstock', 'Worn', 'Beaters']},
                    {'name': 'Retail Price', 'type': 'NUMBER'}
                ]
            },
            
            # Art & Crafts
            {
                'display_name': 'Artwork',
                'description': 'Original artwork, prints and artistic creations',
                'icon': 'palette',
                'attributes': [
                    {'name': 'Artist', 'type': 'TEXT'},
                    {'name': 'Title', 'type': 'TEXT'},
                    {'name': 'Medium', 'type': 'TEXT'},
                    {'name': 'Dimensions', 'type': 'TEXT'},
                    {'name': 'Year Created', 'type': 'NUMBER'},
                    {'name': 'Style', 'type': 'TEXT'},
                    {'name': 'Signed', 'type': 'BOOLEAN'}
                ]
            },
            {
                'display_name': 'Craft Supply',
                'description': 'Crafting materials, supplies and tools',
                'icon': 'scissors',
                'attributes': [
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Color', 'type': 'TEXT'},
                    {'name': 'Quantity', 'type': 'TEXT'},
                    {'name': 'Material', 'type': 'TEXT'},
                    {'name': 'Purchase Date', 'type': 'DATE'},
                    {'name': 'Project', 'type': 'TEXT'}
                ]
            },
            
            # Sports & Outdoor
            {
                'display_name': 'Sports Equipment',
                'description': 'Sports gear, equipment and athletic accessories',
                'icon': 'dumbbell',
                'attributes': [
                    {'name': 'Sport', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Size', 'type': 'TEXT'},
                    {'name': 'Material', 'type': 'TEXT'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['New', 'Good', 'Fair', 'Poor']},
                    {'name': 'Year Purchased', 'type': 'NUMBER'}
                ]
            },
            
            # Home & Garden
            {
                'display_name': 'Plant',
                'description': 'House plants, garden plants and botanical specimens',
                'icon': 'leaf',
                'attributes': [
                    {'name': 'Scientific Name', 'type': 'TEXT'},
                    {'name': 'Common Name', 'type': 'TEXT'},
                    {'name': 'Plant Type', 'type': 'CHOICE', 'choices': ['Succulent', 'Flower', 'Tree', 'Herb', 'Vegetable']},
                    {'name': 'Light Requirements', 'type': 'CHOICE', 'choices': ['Full Sun', 'Partial Sun', 'Shade']},
                    {'name': 'Water Needs', 'type': 'CHOICE', 'choices': ['Low', 'Medium', 'High']},
                    {'name': 'Growth Size', 'type': 'TEXT'},
                    {'name': 'Bloom Time', 'type': 'TEXT'}
                ]
            },
            {
                'display_name': 'Garden Tool',
                'description': 'Gardening tools and outdoor equipment',
                'icon': 'shovel',
                'attributes': [
                    {'name': 'Tool Type', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Handle Material', 'type': 'TEXT'},
                    {'name': 'Head Material', 'type': 'TEXT'},
                    {'name': 'Length', 'type': 'NUMBER'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['New', 'Good', 'Fair', 'Poor']},
                    {'name': 'Purchase Year', 'type': 'NUMBER'}
                ]
            },
            {
                'display_name': 'Furniture',
                'description': 'Furniture pieces and home furnishings',
                'icon': 'house',
                'attributes': [
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Style', 'type': 'TEXT'},
                    {'name': 'Material', 'type': 'TEXT'},
                    {'name': 'Designer/Brand', 'type': 'TEXT'},
                    {'name': 'Dimensions', 'type': 'TEXT'},
                    {'name': 'Year Made', 'type': 'NUMBER'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['Excellent', 'Good', 'Fair', 'Poor']}
                ]
            },
            
            # Technology & Electronics
            {
                'display_name': 'Computer',
                'description': 'Computers, laptops and computing devices',
                'icon': 'monitor',
                'attributes': [
                    {'name': 'Type', 'type': 'CHOICE', 'choices': ['Desktop', 'Laptop', 'Tablet', 'Server']},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Processor', 'type': 'TEXT'},
                    {'name': 'RAM', 'type': 'NUMBER'},
                    {'name': 'Storage', 'type': 'TEXT'},
                    {'name': 'Operating System', 'type': 'TEXT'}
                ]
            },
            {
                'display_name': 'Camera',
                'description': 'Cameras, lenses and photography equipment',
                'icon': 'camera',
                'attributes': [
                    {'name': 'Type', 'type': 'CHOICE', 'choices': ['DSLR', 'Mirrorless', 'Point-and-Shoot', 'Film']},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Megapixels', 'type': 'NUMBER'},
                    {'name': 'Lens Mount', 'type': 'TEXT'},
                    {'name': 'Purchase Year', 'type': 'NUMBER'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['Excellent', 'Good', 'Fair', 'Poor']}
                ]
            },
            {
                'display_name': 'Audio Equipment',
                'description': 'Headphones, speakers and audio gear',
                'icon': 'headphones',
                'attributes': [
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Impedance', 'type': 'NUMBER'},
                    {'name': 'Frequency Response', 'type': 'TEXT'},
                    {'name': 'Wireless', 'type': 'BOOLEAN'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['New', 'Good', 'Fair', 'Poor']}
                ]
            },
            
            # Vehicles & Transportation
            {
                'display_name': 'Car',
                'description': 'Automobiles and motor vehicles',
                'icon': 'car',
                'attributes': [
                    {'name': 'Make', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Year', 'type': 'NUMBER'},
                    {'name': 'Color', 'type': 'TEXT'},
                    {'name': 'Mileage', 'type': 'NUMBER'},
                    {'name': 'Engine', 'type': 'TEXT'},
                    {'name': 'Transmission', 'type': 'CHOICE', 'choices': ['Manual', 'Automatic', 'CVT']}
                ]
            },
            {
                'display_name': 'Motorcycle',
                'description': 'Motorcycles and motor bikes',
                'icon': 'bike',
                'attributes': [
                    {'name': 'Make', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Year', 'type': 'NUMBER'},
                    {'name': 'Engine Size', 'type': 'NUMBER'},
                    {'name': 'Type', 'type': 'CHOICE', 'choices': ['Cruiser', 'Sport', 'Touring', 'Dirt']},
                    {'name': 'Color', 'type': 'TEXT'},
                    {'name': 'Mileage', 'type': 'NUMBER'}
                ]
            },
            {
                'display_name': 'Bicycle',
                'description': 'Bicycles and cycling equipment',
                'icon': 'bike',
                'attributes': [
                    {'name': 'Type', 'type': 'CHOICE', 'choices': ['Road', 'Mountain', 'Hybrid', 'BMX', 'Electric']},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Frame Size', 'type': 'TEXT'},
                    {'name': 'Frame Material', 'type': 'TEXT'},
                    {'name': 'Gear Count', 'type': 'NUMBER'},
                    {'name': 'Year', 'type': 'NUMBER'}
                ]
            },
            
            # Personal Items
            {
                'display_name': 'Jewelry',
                'description': 'Jewelry, precious metals and gemstones',
                'icon': 'gem',
                'attributes': [
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Material', 'type': 'TEXT'},
                    {'name': 'Gemstone', 'type': 'TEXT'},
                    {'name': 'Carat Weight', 'type': 'NUMBER'},
                    {'name': 'Style', 'type': 'TEXT'},
                    {'name': 'Appraised Value', 'type': 'NUMBER'},
                    {'name': 'Certification', 'type': 'TEXT'}
                ]
            },
            {
                'display_name': 'Perfume/Cologne',
                'description': 'Fragrances and scents',
                'icon': 'spray-can',
                'attributes': [
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Fragrance Name', 'type': 'TEXT'},
                    {'name': 'Type', 'type': 'CHOICE', 'choices': ['Eau de Parfum', 'Eau de Toilette', 'Cologne']},
                    {'name': 'Size', 'type': 'TEXT'},
                    {'name': 'Notes', 'type': 'TEXT'},
                    {'name': 'Release Year', 'type': 'NUMBER'},
                    {'name': 'Bottle Type', 'type': 'TEXT'}
                ]
            },
            {
                'display_name': 'Bag/Purse',
                'description': 'Handbags, backpacks and carrying accessories',
                'icon': 'shopping-bag',
                'attributes': [
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Material', 'type': 'TEXT'},
                    {'name': 'Color', 'type': 'TEXT'},
                    {'name': 'Size', 'type': 'TEXT'},
                    {'name': 'Style/Collection', 'type': 'TEXT'},
                    {'name': 'Authentication', 'type': 'BOOLEAN'}
                ]
            },
            
            # Professional & Education
            {
                'display_name': 'Musical Instrument',
                'description': 'Musical instruments and accessories',
                'icon': 'music',
                'attributes': [
                    {'name': 'Instrument Type', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Material', 'type': 'TEXT'},
                    {'name': 'Year Made', 'type': 'NUMBER'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['Excellent', 'Good', 'Fair', 'Poor']},
                    {'name': 'Serial Number', 'type': 'TEXT'}
                ]
            },
            {
                'display_name': 'Educational Material',
                'description': 'Textbooks, educational resources and learning materials',
                'icon': 'book-open',
                'attributes': [
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Subject', 'type': 'TEXT'},
                    {'name': 'Grade Level', 'type': 'TEXT'},
                    {'name': 'Edition', 'type': 'TEXT'},
                    {'name': 'Publisher', 'type': 'TEXT'},
                    {'name': 'ISBN', 'type': 'TEXT'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['New', 'Good', 'Fair', 'Poor']}
                ]
            },
            {
                'display_name': 'Professional Tool',
                'description': 'Specialized professional and trade tools',
                'icon': 'briefcase',
                'attributes': [
                    {'name': 'Profession', 'type': 'TEXT'},
                    {'name': 'Tool Type', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Certification', 'type': 'TEXT'},
                    {'name': 'Purchase Date', 'type': 'DATE'},
                    {'name': 'Warranty', 'type': 'BOOLEAN'}
                ]
            },
            
            # Outdoor & Recreation
            {
                'display_name': 'Camping Gear',
                'description': 'Camping equipment and outdoor gear',
                'icon': 'tent',
                'attributes': [
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Capacity', 'type': 'TEXT'},
                    {'name': 'Season Rating', 'type': 'CHOICE', 'choices': ['3-Season', '4-Season', 'Summer']},
                    {'name': 'Weight', 'type': 'NUMBER'},
                    {'name': 'Material', 'type': 'TEXT'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['New', 'Good', 'Fair', 'Poor']}
                ]
            },
            {
                'display_name': 'Fishing Equipment',
                'description': 'Fishing rods, reels and tackle',
                'icon': 'fish',
                'attributes': [
                    {'name': 'Type', 'type': 'TEXT'},
                    {'name': 'Brand', 'type': 'TEXT'},
                    {'name': 'Model', 'type': 'TEXT'},
                    {'name': 'Length', 'type': 'NUMBER'},
                    {'name': 'Action', 'type': 'CHOICE', 'choices': ['Fast', 'Medium', 'Slow']},
                    {'name': 'Line Weight', 'type': 'TEXT'},
                    {'name': 'Condition', 'type': 'CHOICE', 'choices': ['New', 'Good', 'Fair', 'Poor']}
                ]
            }
        ]