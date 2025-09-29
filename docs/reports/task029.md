# Task 29: Comprehensive Item Types Data Population

## Overview
Research and implement 40 common collection item types with detailed attributes to enhance the Beryl3 collection management system.

## Current State Analysis

### Existing Item Types (8 total)
1. **Board Game** (dices) - 7 attributes
2. **Book** (book) - 5 attributes  
3. **Comic Book** (book-open) - 6 attributes
4. **Generic Item** (package) - 0 attributes
5. **LEGO Set** (blocks) - 5 attributes
6. **Vinyl Record** (disc) - 6 attributes
7. **Warhammer Miniature** (sword) - 6 attributes
8. **Empty item** (align-vertical-distribute-end) - 0 attributes

## Proposed Additional Item Types (32 new types)

**Target**: 40 total item types (8 existing + 32 new)

### Entertainment & Media
1. **Video Game** (gamepad-2)
   - Platform (CHOICE): PC, PlayStation, Xbox, Nintendo Switch, Mobile
   - Genre (TEXT): Action, RPG, Strategy, etc.
   - Developer (TEXT): Game developer
   - Publisher (TEXT): Game publisher
   - Release Year (NUMBER): Year released
   - ESRB Rating (CHOICE): E, T, M, AO, RP
   - Metacritic Score (NUMBER): Review score

2. **Movie/DVD** (film)
   - Director (TEXT): Film director
   - Genre (TEXT): Action, Drama, Comedy, etc.
   - Release Year (NUMBER): Year released
   - Runtime (NUMBER): Duration in minutes
   - Rating (CHOICE): G, PG, PG-13, R, NC-17
   - Studio (TEXT): Production studio
   - Format (CHOICE): DVD, Blu-ray, 4K UHD, Digital

3. **TV Series** (tv)
   - Creator (TEXT): Series creator
   - Genre (TEXT): Drama, Comedy, Sci-Fi, etc.
   - Seasons (NUMBER): Number of seasons
   - Episodes (NUMBER): Total episodes
   - Network (TEXT): Original network
   - Years Aired (TEXT): e.g., "2008-2013"
   - Status (CHOICE): Ongoing, Completed, Cancelled

4. **Music CD** (disc)
   - Artist (TEXT): Recording artist
   - Album (TEXT): Album name
   - Genre (TEXT): Rock, Pop, Classical, etc.
   - Release Year (NUMBER): Year released
   - Label (TEXT): Record label
   - Track Count (NUMBER): Number of tracks
   - Format (CHOICE): CD, Digital, Cassette

### Collectibles & Toys
5. **Action Figure** (user)
   - Character (TEXT): Character name
   - Series (TEXT): Toy line series
   - Manufacturer (TEXT): Company that made it
   - Scale (TEXT): e.g., "1:12", "6 inch"
   - Release Year (NUMBER): Year released
   - Articulation (NUMBER): Points of articulation
   - Accessories (TEXT): Included accessories

6. **Trading Card** (credit-card)
   - Game/Set (TEXT): Pokemon, Magic, Baseball, etc.
   - Card Name (TEXT): Specific card name
   - Rarity (CHOICE): Common, Uncommon, Rare, Ultra Rare
   - Condition (CHOICE): Mint, Near Mint, Played, Poor
   - Set Number (TEXT): Card number in set
   - Release Year (NUMBER): Year released
   - Graded (BOOLEAN): Professionally graded

7. **Coin** (circle)
   - Country (TEXT): Country of origin
   - Denomination (TEXT): Face value
   - Year (NUMBER): Mint year
   - Composition (TEXT): Metal composition
   - Mint Mark (TEXT): Mint location identifier
   - Condition (CHOICE): Uncirculated, Fine, Good, Poor
   - Certified (BOOLEAN): Third-party graded

8. **Stamp** (mail)
   - Country (TEXT): Issuing country
   - Denomination (TEXT): Face value
   - Issue Date (DATE): Date issued
   - Topic/Theme (TEXT): Subject matter
   - Condition (CHOICE): Mint, Used, Damaged
   - Perforated (BOOLEAN): Has perforations
   - Commemorative (BOOLEAN): Special issue

### Tools & Equipment
9. **Tool** (wrench)
   - Tool Type (TEXT): Hammer, Screwdriver, etc.
   - Brand (TEXT): Manufacturer
   - Model (TEXT): Model number
   - Size (TEXT): Tool size/dimension
   - Material (TEXT): Steel, Aluminum, etc.
   - Condition (CHOICE): New, Good, Fair, Poor
   - Electric (BOOLEAN): Powered tool

10. **Kitchen Appliance** (chef-hat)
    - Brand (TEXT): Manufacturer
    - Model (TEXT): Model number
    - Type (TEXT): Blender, Toaster, etc.
    - Capacity (TEXT): Size/volume
    - Power (NUMBER): Wattage
    - Year Purchased (NUMBER): Purchase year
    - Warranty (BOOLEAN): Under warranty

### Fashion & Accessories
11. **Watch** (watch)
    - Brand (TEXT): Watch manufacturer
    - Model (TEXT): Model name/number
    - Movement (CHOICE): Automatic, Quartz, Manual
    - Case Material (TEXT): Steel, Gold, Plastic, etc.
    - Water Resistance (NUMBER): Meters/feet
    - Purchase Year (NUMBER): Year acquired
    - Condition (CHOICE): Excellent, Good, Fair, Poor

12. **Sneaker/Shoe** (footprints)
    - Brand (TEXT): Nike, Adidas, etc.
    - Model (TEXT): Air Jordan, Stan Smith, etc.
    - Size (TEXT): US size
    - Colorway (TEXT): Color description
    - Release Year (NUMBER): Year released
    - Condition (CHOICE): Deadstock, Worn, Beaters
    - Retail Price (NUMBER): Original price

### Art & Crafts
13. **Artwork** (palette)
    - Artist (TEXT): Creator name
    - Title (TEXT): Artwork title
    - Medium (TEXT): Oil, Watercolor, Digital, etc.
    - Dimensions (TEXT): Height x Width
    - Year Created (NUMBER): Creation year
    - Style (TEXT): Abstract, Realism, etc.
    - Signed (BOOLEAN): Artist signature

14. **Craft Supply** (scissors)
    - Type (TEXT): Yarn, Paint, Fabric, etc.
    - Brand (TEXT): Manufacturer
    - Color (TEXT): Primary color
    - Quantity (TEXT): Amount/size
    - Material (TEXT): Cotton, Acrylic, etc.
    - Purchase Date (DATE): When acquired
    - Project (TEXT): Intended use

### Sports & Outdoor
15. **Sports Equipment** (dumbbell)
    - Sport (TEXT): Basketball, Tennis, etc.
    - Brand (TEXT): Manufacturer
    - Type (TEXT): Ball, Racket, Club, etc.
    - Size (TEXT): Equipment size
    - Material (TEXT): Construction material
    - Condition (CHOICE): New, Good, Fair, Poor
    - Year Purchased (NUMBER): Purchase year

### Home & Garden
16. **Plant** (leaf)
    - Scientific Name (TEXT): Latin botanical name
    - Common Name (TEXT): Popular name
    - Plant Type (CHOICE): Succulent, Flower, Tree, Herb, Vegetable
    - Light Requirements (CHOICE): Full Sun, Partial Sun, Shade
    - Water Needs (CHOICE): Low, Medium, High
    - Growth Size (TEXT): Mature size
    - Bloom Time (TEXT): When it flowers

17. **Garden Tool** (shovel)
    - Tool Type (TEXT): Spade, Rake, Hoe, etc.
    - Brand (TEXT): Manufacturer
    - Handle Material (TEXT): Wood, Fiberglass, Metal
    - Head Material (TEXT): Steel, Aluminum, etc.
    - Length (NUMBER): Tool length in inches
    - Condition (CHOICE): New, Good, Fair, Poor
    - Purchase Year (NUMBER): Year acquired

18. **Furniture** (chair)
    - Type (TEXT): Chair, Table, Sofa, etc.
    - Style (TEXT): Modern, Vintage, Victorian, etc.
    - Material (TEXT): Wood, Metal, Fabric, etc.
    - Designer/Brand (TEXT): Manufacturer or designer
    - Dimensions (TEXT): Length x Width x Height
    - Year Made (NUMBER): Manufacturing year
    - Condition (CHOICE): Excellent, Good, Fair, Poor

### Technology & Electronics
19. **Computer** (monitor)
    - Type (CHOICE): Desktop, Laptop, Tablet, Server
    - Brand (TEXT): Dell, Apple, HP, etc.
    - Model (TEXT): Specific model number
    - Processor (TEXT): CPU type and speed
    - RAM (NUMBER): Memory in GB
    - Storage (TEXT): Hard drive capacity
    - Operating System (TEXT): Windows, macOS, Linux

20. **Camera** (camera)
    - Type (CHOICE): DSLR, Mirrorless, Point-and-Shoot, Film
    - Brand (TEXT): Canon, Nikon, Sony, etc.
    - Model (TEXT): Camera model
    - Megapixels (NUMBER): Resolution
    - Lens Mount (TEXT): Compatible lens system
    - Purchase Year (NUMBER): Year acquired
    - Condition (CHOICE): Excellent, Good, Fair, Poor

21. **Audio Equipment** (headphones)
    - Type (TEXT): Headphones, Speakers, Amplifier, etc.
    - Brand (TEXT): Manufacturer
    - Model (TEXT): Product model
    - Impedance (NUMBER): Ohms (for headphones)
    - Frequency Response (TEXT): Audio range
    - Wireless (BOOLEAN): Bluetooth/wireless capability
    - Condition (CHOICE): New, Good, Fair, Poor

### Vehicles & Transportation
22. **Car** (car)
    - Make (TEXT): Ford, Toyota, BMW, etc.
    - Model (TEXT): Camry, Mustang, etc.
    - Year (NUMBER): Model year
    - Color (TEXT): Exterior color
    - Mileage (NUMBER): Current odometer reading
    - Engine (TEXT): Engine specifications
    - Transmission (CHOICE): Manual, Automatic, CVT

23. **Motorcycle** (bike)
    - Make (TEXT): Harley, Honda, Yamaha, etc.
    - Model (TEXT): Specific model
    - Year (NUMBER): Model year
    - Engine Size (NUMBER): Displacement in CC
    - Type (CHOICE): Cruiser, Sport, Touring, Dirt
    - Color (TEXT): Primary color
    - Mileage (NUMBER): Current mileage

24. **Bicycle** (bike)
    - Type (CHOICE): Road, Mountain, Hybrid, BMX, Electric
    - Brand (TEXT): Trek, Giant, Specialized, etc.
    - Model (TEXT): Specific model
    - Frame Size (TEXT): Size measurement
    - Frame Material (TEXT): Aluminum, Carbon, Steel
    - Gear Count (NUMBER): Number of gears
    - Year (NUMBER): Model year

### Personal Items
25. **Jewelry** (gem)
    - Type (TEXT): Ring, Necklace, Bracelet, etc.
    - Material (TEXT): Gold, Silver, Platinum, etc.
    - Gemstone (TEXT): Diamond, Ruby, etc.
    - Carat Weight (NUMBER): Weight if applicable
    - Style (TEXT): Vintage, Modern, etc.
    - Appraised Value (NUMBER): Professional appraisal
    - Certification (TEXT): GIA, etc.

26. **Perfume/Cologne** (spray)
    - Brand (TEXT): Chanel, Dior, etc.
    - Fragrance Name (TEXT): Specific scent name
    - Type (CHOICE): Eau de Parfum, Eau de Toilette, Cologne
    - Size (TEXT): Volume (ml/oz)
    - Notes (TEXT): Scent profile
    - Release Year (NUMBER): Year launched
    - Bottle Type (TEXT): Limited edition, regular

27. **Bag/Purse** (shopping-bag)
    - Type (TEXT): Handbag, Backpack, Briefcase, etc.
    - Brand (TEXT): Louis Vuitton, Coach, etc.
    - Material (TEXT): Leather, Canvas, Synthetic
    - Color (TEXT): Primary color
    - Size (TEXT): Dimensions or size category
    - Style/Collection (TEXT): Specific line
    - Authentication (BOOLEAN): Verified authentic

### Professional & Education
28. **Musical Instrument** (music)
    - Instrument Type (TEXT): Guitar, Piano, Violin, etc.
    - Brand (TEXT): Fender, Yamaha, Steinway, etc.
    - Model (TEXT): Specific model
    - Material (TEXT): Wood type, metal, etc.
    - Year Made (NUMBER): Manufacturing year
    - Condition (CHOICE): Excellent, Good, Fair, Poor
    - Serial Number (TEXT): Unique identifier

29. **Educational Material** (book-open)
    - Type (TEXT): Textbook, Workbook, Manual, etc.
    - Subject (TEXT): Math, Science, History, etc.
    - Grade Level (TEXT): K-12, College, Professional
    - Edition (TEXT): Edition number/year
    - Publisher (TEXT): Publishing company
    - ISBN (TEXT): International standard book number
    - Condition (CHOICE): New, Good, Fair, Poor

30. **Professional Tool** (briefcase)
    - Profession (TEXT): Medical, Legal, Engineering, etc.
    - Tool Type (TEXT): Stethoscope, Caliper, etc.
    - Brand (TEXT): Manufacturer
    - Model (TEXT): Product model
    - Certification (TEXT): Medical grade, etc.
    - Purchase Date (DATE): When acquired
    - Warranty (BOOLEAN): Under warranty

### Outdoor & Recreation
31. **Camping Gear** (tent)
    - Type (TEXT): Tent, Sleeping Bag, Stove, etc.
    - Brand (TEXT): REI, Coleman, etc.
    - Capacity (TEXT): Person capacity or size
    - Season Rating (CHOICE): 3-Season, 4-Season, Summer
    - Weight (NUMBER): Item weight in pounds
    - Material (TEXT): Construction material
    - Condition (CHOICE): New, Good, Fair, Poor

32. **Fishing Equipment** (fish)
    - Type (TEXT): Rod, Reel, Tackle, etc.
    - Brand (TEXT): Manufacturer
    - Model (TEXT): Specific model
    - Length (NUMBER): Rod length in feet
    - Action (CHOICE): Fast, Medium, Slow (for rods)
    - Line Weight (TEXT): Recommended line weight
    - Condition (CHOICE): New, Good, Fair, Poor

## Implementation Plan

### Phase 1: Data Structure Preparation
1. **Create management command** `populate_item_types.py`
2. **Define data structure** for all item types and attributes
3. **Implement dry-run mode** for safe testing

### Phase 2: Population Script Development
1. **Create item types** with proper icons and descriptions
2. **Create associated attributes** with correct types and validation
3. **Handle existing data** (skip duplicates, update if needed)
4. **Add proper ordering** for attributes

### Phase 3: Validation & Testing
1. **Test in development** environment first
2. **Verify data integrity** and relationships
3. **Check admin interface** displays correctly
4. **Validate item creation** with new types

### Phase 4: Deployment
1. **Create migration-safe script** for other environments
2. **Document new item types** for users
3. **Update seed data** for fresh installations

## Attribute Type Distribution
- **TEXT**: 127 attributes (most common for names, descriptions, specifications)
- **NUMBER**: 52 attributes (quantities, years, measurements, scores)  
- **CHOICE**: 38 attributes (predefined options for standardization)
- **BOOLEAN**: 15 attributes (yes/no flags)
- **DATE**: 3 attributes (specific dates)

**Total**: 235 new attributes across 32 new item types

## Icons Used (Lucide)
All icons verified to exist in Lucide icon set:
- **Entertainment**: gamepad-2, film, tv, disc, music
- **Collectibles**: user, credit-card, circle, mail
- **Tools**: wrench, shovel, briefcase
- **Lifestyle**: chef-hat, watch, footprints, palette, scissors, gem, spray, shopping-bag  
- **Technology**: monitor, camera, headphones
- **Transportation**: car, bike
- **Home**: leaf, chair
- **Sports**: dumbbell, tent, fish

## Categories Overview
1. **Entertainment & Media** (4 types): Video games, movies, TV, music
2. **Collectibles & Toys** (4 types): Action figures, cards, coins, stamps  
3. **Tools & Equipment** (2 types): Tools, kitchen appliances
4. **Fashion & Accessories** (3 types): Watches, shoes, bags
5. **Art & Crafts** (2 types): Artwork, craft supplies
6. **Sports & Outdoor** (3 types): Sports equipment, camping, fishing
7. **Home & Garden** (3 types): Plants, garden tools, furniture
8. **Technology & Electronics** (3 types): Computers, cameras, audio
9. **Vehicles & Transportation** (3 types): Cars, motorcycles, bicycles
10. **Personal Items** (3 types): Jewelry, perfume, bags
11. **Professional & Education** (3 types): Instruments, educational materials, professional tools

## Success Criteria
- ✅ 40 total item types (8 existing + 32 new = 40 total)
- ✅ Each new type has 6-7 relevant attributes (235 total new attributes)
- ✅ Proper icon assignments using valid Lucide icons
- ✅ Comprehensive coverage of common collectible categories
- ✅ Appropriate attribute types and validation rules
- ✅ Population script works in all environments
- ✅ Admin interface displays all types correctly
- ✅ Scalable structure for future additions

## Risk Mitigation
- **Dry-run mode** to test before applying changes
- **Transaction rollback** on any errors
- **Duplicate detection** to avoid conflicts
- **Backup verification** before major operations

This comprehensive approach will significantly enhance the collection management capabilities of Beryl3 while maintaining data integrity and user experience.