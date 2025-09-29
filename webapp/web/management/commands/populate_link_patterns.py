"""
Django management command to populate link patterns for collection item URLs
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from web.models import LinkPattern

logger = logging.getLogger("webapp")


class Command(BaseCommand):
    help = "Populate comprehensive link patterns for popular internet platforms"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without making changes'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip patterns that already exist (by display name)'
        )
        parser.add_argument(
            '--category',
            choices=['ecommerce', 'gaming', 'entertainment', 'books', 'music', 
                    'collectibles', 'fashion', 'art', 'sports', 'technology', 'all'],
            default='all',
            help='Only create patterns for specific category'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']
        category = options['category']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        try:
            with transaction.atomic():
                # Get current state
                current_patterns = set(LinkPattern.objects.values_list('display_name', flat=True))
                self.stdout.write(f'Current link patterns: {len(current_patterns)}')
                
                # Create new link patterns
                created_count = self._create_link_patterns(dry_run, skip_existing, current_patterns, category)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully {"would create" if dry_run else "created"} {created_count} new link patterns'
                    )
                )
                
                # Show final summary
                if not dry_run:
                    total_patterns = LinkPattern.objects.count()
                    self.stdout.write(
                        self.style.SUCCESS(f'Final total: {total_patterns} link patterns')
                    )
                
                if dry_run:
                    # Rollback transaction in dry run mode
                    transaction.set_rollback(True)
                    
        except Exception as e:
            logger.error(f"Error populating link patterns: {str(e)}")
            raise CommandError(f"Failed to populate link patterns: {str(e)}")

    def _create_link_patterns(self, dry_run, skip_existing, current_patterns, category_filter):
        """Create all new link patterns"""
        link_patterns_data = self._get_link_patterns_data()
        created_count = 0
        
        for pattern_data in link_patterns_data:
            # Filter by category if specified
            if category_filter != 'all' and pattern_data['category'] != category_filter:
                continue
                
            display_name = pattern_data['display_name']
            
            if display_name in current_patterns:
                if skip_existing:
                    self.stdout.write(f'Skipping existing: {display_name}')
                    continue
                else:
                    self.stdout.write(self.style.WARNING(f'Updating existing: {display_name}'))
            
            # Create or update link pattern
            if not dry_run:
                pattern, created = LinkPattern.objects.get_or_create(
                    display_name=display_name,
                    defaults={
                        'name': display_name.lower().replace(' ', '_').replace('/', '_'),
                        'url_pattern': pattern_data['url_pattern'],
                        'description': pattern_data['description'],
                        'icon': pattern_data['icon'],
                        'is_active': True
                    }
                )
                
                if not created:
                    # Update existing
                    pattern.url_pattern = pattern_data['url_pattern']
                    pattern.description = pattern_data['description'] 
                    pattern.icon = pattern_data['icon']
                    pattern.save()
            
            self.stdout.write(f'{"Would create" if dry_run else "Created"}: {display_name} ({pattern_data["category"]})')
            created_count += 1
        
        return created_count

    def _get_link_patterns_data(self):
        """Return comprehensive link patterns data structure"""
        return [
            # E-commerce & Shopping Platforms
            {
                'display_name': 'Amazon Product',
                'url_pattern': 'https://amazon.com/dp/{asin}',
                'description': 'Amazon product pages using ASIN identifier',
                'icon': 'shopping-cart',
                'category': 'ecommerce'
            },
            {
                'display_name': 'Amazon UK',
                'url_pattern': 'https://amazon.co.uk/dp/{asin}',
                'description': 'Amazon UK product pages',
                'icon': 'shopping-cart',
                'category': 'ecommerce'
            },
            {
                'display_name': 'eBay Listing',
                'url_pattern': 'https://ebay.com/itm/{item_id}',
                'description': 'eBay auction and buy-it-now listings',
                'icon': 'gavel',
                'category': 'ecommerce'
            },
            {
                'display_name': 'eBay UK',
                'url_pattern': 'https://ebay.co.uk/itm/{item_id}',
                'description': 'eBay UK listings',
                'icon': 'gavel',
                'category': 'ecommerce'
            },
            {
                'display_name': 'Walmart',
                'url_pattern': 'https://walmart.com/ip/{product_id}',
                'description': 'Walmart product pages',
                'icon': 'store',
                'category': 'ecommerce'
            },
            {
                'display_name': 'Target',
                'url_pattern': 'https://target.com/p/{product_id}',
                'description': 'Target retail product pages',
                'icon': 'target',
                'category': 'ecommerce'
            },
            {
                'display_name': 'Best Buy',
                'url_pattern': 'https://bestbuy.com/site/{product_id}',
                'description': 'Best Buy electronics and appliances',
                'icon': 'zap',
                'category': 'ecommerce'
            },
            {
                'display_name': 'Newegg',
                'url_pattern': 'https://newegg.com/p/{product_id}',
                'description': 'Newegg computer and electronics store',
                'icon': 'pc-case',
                'category': 'ecommerce'
            },
            {
                'display_name': 'Etsy Shop',
                'url_pattern': 'https://etsy.com/listing/{listing_id}',
                'description': 'Etsy handmade and vintage items',
                'icon': 'heart',
                'category': 'ecommerce'
            },
            {
                'display_name': 'AliExpress',
                'url_pattern': 'https://aliexpress.com/item/{item_id}',
                'description': 'AliExpress global marketplace',
                'icon': 'globe',
                'category': 'ecommerce'
            },

            # Entertainment - Gaming
            {
                'display_name': 'Steam Game',
                'url_pattern': 'https://store.steampowered.com/app/{app_id}',
                'description': 'Steam digital game store',
                'icon': 'gamepad-2',
                'category': 'gaming'
            },
            {
                'display_name': 'PlayStation Store',
                'url_pattern': 'https://store.playstation.com/product/{product_id}',
                'description': 'PlayStation digital store',
                'icon': 'gamepad-2',
                'category': 'gaming'
            },
            {
                'display_name': 'Xbox Store',
                'url_pattern': 'https://microsoft.com/store/p/{product_id}',
                'description': 'Xbox and Microsoft Store',
                'icon': 'gamepad-2',
                'category': 'gaming'
            },
            {
                'display_name': 'Nintendo eShop',
                'url_pattern': 'https://nintendo.com/games/detail/{game_id}',
                'description': 'Nintendo Switch and 3DS games',
                'icon': 'gamepad-2',
                'category': 'gaming'
            },
            {
                'display_name': 'Epic Games Store',
                'url_pattern': 'https://store.epicgames.com/p/{game_slug}',
                'description': 'Epic Games digital store',
                'icon': 'gamepad-2',
                'category': 'gaming'
            },
            {
                'display_name': 'GOG Game',
                'url_pattern': 'https://gog.com/game/{game_slug}',
                'description': 'Good Old Games DRM-free store',
                'icon': 'gamepad-2',
                'category': 'gaming'
            },
            {
                'display_name': 'BoardGameGeek',
                'url_pattern': 'https://boardgamegeek.com/boardgame/{game_id}',
                'description': 'Board game database and community',
                'icon': 'dices',
                'category': 'gaming'
            },
            {
                'display_name': 'Metacritic Game',
                'url_pattern': 'https://metacritic.com/game/{platform}/{game_slug}',
                'description': 'Game reviews and scores',
                'icon': 'star',
                'category': 'gaming'
            },
            {
                'display_name': 'IGN Game Review',
                'url_pattern': 'https://ign.com/games/{game_slug}',
                'description': 'IGN game reviews and news',
                'icon': 'newspaper',
                'category': 'gaming'
            },
            {
                'display_name': 'GameSpot',
                'url_pattern': 'https://gamespot.com/games/{game_slug}',
                'description': 'GameSpot reviews and previews',
                'icon': 'monitor',
                'category': 'gaming'
            },

            # Entertainment - Movies & TV
            {
                'display_name': 'IMDb Movie',
                'url_pattern': 'https://imdb.com/title/{title_id}',
                'description': 'Internet Movie Database',
                'icon': 'film',
                'category': 'entertainment'
            },
            {
                'display_name': 'Rotten Tomatoes',
                'url_pattern': 'https://rottentomatoes.com/m/{movie_slug}',
                'description': 'Movie and TV show reviews',
                'icon': 'star',
                'category': 'entertainment'
            },
            {
                'display_name': 'TMDb Movie',
                'url_pattern': 'https://themoviedb.org/movie/{movie_id}',
                'description': 'The Movie Database',
                'icon': 'database',
                'category': 'entertainment'
            },
            {
                'display_name': 'Netflix',
                'url_pattern': 'https://netflix.com/title/{title_id}',
                'description': 'Netflix streaming service',
                'icon': 'play',
                'category': 'entertainment'
            },
            {
                'display_name': 'Hulu',
                'url_pattern': 'https://hulu.com/movie/{movie_slug}',
                'description': 'Hulu streaming platform',
                'icon': 'play',
                'category': 'entertainment'
            },
            {
                'display_name': 'Amazon Prime Video',
                'url_pattern': 'https://primevideo.com/detail/{title_id}',
                'description': 'Amazon Prime Video streaming',
                'icon': 'play',
                'category': 'entertainment'
            },
            {
                'display_name': 'Disney Plus',
                'url_pattern': 'https://disneyplus.com/movies/{movie_slug}',
                'description': 'Disney+ streaming service',
                'icon': 'play',
                'category': 'entertainment'
            },
            {
                'display_name': 'HBO Max',
                'url_pattern': 'https://hbomax.com/feature/{feature_id}',
                'description': 'HBO Max streaming platform',
                'icon': 'play',
                'category': 'entertainment'
            },
            {
                'display_name': 'Apple TV',
                'url_pattern': 'https://tv.apple.com/movie/{movie_slug}',
                'description': 'Apple TV+ streaming service',
                'icon': 'apple',
                'category': 'entertainment'
            },
            {
                'display_name': 'Vudu',
                'url_pattern': 'https://vudu.com/content/movies/details/{movie_id}',
                'description': 'Vudu digital movie service',
                'icon': 'film',
                'category': 'entertainment'
            },

            # Books & Literature
            {
                'display_name': 'Goodreads Book',
                'url_pattern': 'https://goodreads.com/book/show/{book_id}',
                'description': 'Goodreads book community and reviews',
                'icon': 'book',
                'category': 'books'
            },
            {
                'display_name': 'Amazon Books',
                'url_pattern': 'https://amazon.com/dp/{isbn}',
                'description': 'Amazon book store using ISBN',
                'icon': 'book',
                'category': 'books'
            },
            {
                'display_name': 'Barnes & Noble',
                'url_pattern': 'https://barnesandnoble.com/w/{book_slug}',
                'description': 'Barnes & Noble bookstore',
                'icon': 'book',
                'category': 'books'
            },
            {
                'display_name': 'Google Books',
                'url_pattern': 'https://books.google.com/books?id={book_id}',
                'description': 'Google Books digital library',
                'icon': 'search',
                'category': 'books'
            },
            {
                'display_name': 'WorldCat',
                'url_pattern': 'https://worldcat.org/oclc/{oclc_number}',
                'description': 'WorldCat library catalog',
                'icon': 'globe',
                'category': 'books'
            },
            {
                'display_name': 'LibraryThing',
                'url_pattern': 'https://librarything.com/work/{work_id}',
                'description': 'LibraryThing book cataloging',
                'icon': 'library',
                'category': 'books'
            },
            {
                'display_name': 'Open Library',
                'url_pattern': 'https://openlibrary.org/books/{book_id}',
                'description': 'Internet Archive Open Library',
                'icon': 'book-open',
                'category': 'books'
            },
            {
                'display_name': 'ISBN DB',
                'url_pattern': 'https://isbndb.com/book/{isbn}',
                'description': 'ISBN database lookup',
                'icon': 'hash',
                'category': 'books'
            },
            {
                'display_name': 'Book Depository',
                'url_pattern': 'https://bookdepository.com/book/{book_id}',
                'description': 'Book Depository online bookstore',
                'icon': 'package',
                'category': 'books'
            },
            {
                'display_name': 'Audible',
                'url_pattern': 'https://audible.com/pd/{product_id}',
                'description': 'Audible audiobook store',
                'icon': 'headphones',
                'category': 'books'
            },

            # Music
            {
                'display_name': 'Spotify Album',
                'url_pattern': 'https://open.spotify.com/album/{album_id}',
                'description': 'Spotify music streaming',
                'icon': 'music',
                'category': 'music'
            },
            {
                'display_name': 'Apple Music',
                'url_pattern': 'https://music.apple.com/album/{album_id}',
                'description': 'Apple Music streaming service',
                'icon': 'apple',
                'category': 'music'
            },
            {
                'display_name': 'YouTube Music',
                'url_pattern': 'https://music.youtube.com/playlist?list={playlist_id}',
                'description': 'YouTube Music streaming',
                'icon': 'youtube',
                'category': 'music'
            },
            {
                'display_name': 'SoundCloud',
                'url_pattern': 'https://soundcloud.com/{artist}/{track}',
                'description': 'SoundCloud audio platform',
                'icon': 'cloud',
                'category': 'music'
            },
            {
                'display_name': 'Bandcamp',
                'url_pattern': 'https://{artist}.bandcamp.com/album/{album_slug}',
                'description': 'Bandcamp independent music',
                'icon': 'music',
                'category': 'music'
            },
            {
                'display_name': 'Last.fm Album',
                'url_pattern': 'https://last.fm/music/{artist}/{album}',
                'description': 'Last.fm music database and scrobbling',
                'icon': 'radio',
                'category': 'music'
            },
            {
                'display_name': 'AllMusic',
                'url_pattern': 'https://allmusic.com/album/{album_id}',
                'description': 'AllMusic comprehensive database',
                'icon': 'database',
                'category': 'music'
            },
            {
                'display_name': 'Discogs Release',
                'url_pattern': 'https://discogs.com/release/{release_id}',
                'description': 'Discogs music marketplace and database',
                'icon': 'disc',
                'category': 'music'
            },
            {
                'display_name': 'MusicBrainz',
                'url_pattern': 'https://musicbrainz.org/release/{release_id}',
                'description': 'MusicBrainz open music encyclopedia',
                'icon': 'database',
                'category': 'music'
            },
            {
                'display_name': 'Deezer',
                'url_pattern': 'https://deezer.com/album/{album_id}',
                'description': 'Deezer music streaming service',
                'icon': 'headphones',
                'category': 'music'
            },

            # Collectibles & Hobbies
            {
                'display_name': 'eBay Category',
                'url_pattern': 'https://ebay.com/sch/i.html?_nkw={search_term}',
                'description': 'eBay search and category browsing',
                'icon': 'search',
                'category': 'collectibles'
            },
            {
                'display_name': 'Worthpoint',
                'url_pattern': 'https://worthpoint.com/worthopedia/{item_slug}',
                'description': 'Worthpoint price guide and auction results',
                'icon': 'trending-up',
                'category': 'collectibles'
            },
            {
                'display_name': 'LiveAuctioneers',
                'url_pattern': 'https://liveauctioneers.com/item/{item_id}',
                'description': 'Live auction platform',
                'icon': 'gavel',
                'category': 'collectibles'
            },
            {
                'display_name': 'Heritage Auctions',
                'url_pattern': 'https://ha.com/itm/{lot_number}',
                'description': 'Heritage Auctions collectibles',
                'icon': 'landmark',
                'category': 'collectibles'
            },
            {
                'display_name': 'COMC Cards',
                'url_pattern': 'https://comc.com/Cards/{card_slug}',
                'description': 'Check Out My Cards trading card marketplace',
                'icon': 'credit-card',
                'category': 'collectibles'
            },
            {
                'display_name': 'PSA Card',
                'url_pattern': 'https://psacard.com/cert/{cert_number}',
                'description': 'PSA graded card certification',
                'icon': 'shield',
                'category': 'collectibles'
            },
            {
                'display_name': 'Beckett Grading',
                'url_pattern': 'https://beckett.com/grading/card/{card_id}',
                'description': 'Beckett card grading service',
                'icon': 'award',
                'category': 'collectibles'
            },
            {
                'display_name': 'Coin World',
                'url_pattern': 'https://coinworld.com/news/{coin_slug}',
                'description': 'Coin World numismatic news and pricing',
                'icon': 'circle',
                'category': 'collectibles'
            },
            {
                'display_name': 'NGC Coin',
                'url_pattern': 'https://ngccoin.com/coin-explorer/{coin_id}',
                'description': 'NGC coin grading and population reports',
                'icon': 'coins',
                'category': 'collectibles'
            },
            {
                'display_name': 'PCGS Coin',
                'url_pattern': 'https://pcgs.com/coinfacts/{coin_id}',
                'description': 'PCGS coin grading and CoinFacts database',
                'icon': 'coins',
                'category': 'collectibles'
            },

            # Fashion & Lifestyle
            {
                'display_name': 'StockX',
                'url_pattern': 'https://stockx.com/{product_slug}',
                'description': 'StockX sneaker and streetwear marketplace',
                'icon': 'trending-up',
                'category': 'fashion'
            },
            {
                'display_name': 'GOAT Sneakers',
                'url_pattern': 'https://goat.com/sneakers/{sneaker_slug}',
                'description': 'GOAT authentic sneaker marketplace',
                'icon': 'footprints',
                'category': 'fashion'
            },
            {
                'display_name': 'Grailed',
                'url_pattern': 'https://grailed.com/listings/{listing_id}',
                'description': 'Grailed menswear marketplace',
                'icon': 'shirt',
                'category': 'fashion'
            },
            {
                'display_name': 'Vestiaire Collective',
                'url_pattern': 'https://vestiairecollective.com/men/{item_slug}',
                'description': 'Vestiaire Collective luxury consignment',
                'icon': 'shopping-bag',
                'category': 'fashion'
            },
            {
                'display_name': 'The RealReal',
                'url_pattern': 'https://therealreal.com/products/{product_slug}',
                'description': 'The RealReal luxury consignment',
                'icon': 'gem',
                'category': 'fashion'
            },
            {
                'display_name': 'Chrono24 Watches',
                'url_pattern': 'https://chrono24.com/watch/{watch_id}',
                'description': 'Chrono24 luxury watch marketplace',
                'icon': 'watch',
                'category': 'fashion'
            },
            {
                'display_name': 'Hodinkee Shop',
                'url_pattern': 'https://shop.hodinkee.com/products/{product_slug}',
                'description': 'Hodinkee watch shop and magazine',
                'icon': 'watch',
                'category': 'fashion'
            },
            {
                'display_name': 'WatchStation',
                'url_pattern': 'https://watchstation.com/products/{product_id}',
                'description': 'Fossil WatchStation store',
                'icon': 'clock',
                'category': 'fashion'
            },
            {
                'display_name': 'Tourneau',
                'url_pattern': 'https://tourneau.com/watches/{watch_slug}',
                'description': 'Tourneau luxury watch retailer',
                'icon': 'watch',
                'category': 'fashion'
            },
            {
                'display_name': 'Crown & Caliber',
                'url_pattern': 'https://crownandcaliber.com/products/{product_slug}',
                'description': 'Crown & Caliber pre-owned luxury watches',
                'icon': 'crown',
                'category': 'fashion'
            },

            # Art & Crafts
            {
                'display_name': 'Artsy',
                'url_pattern': 'https://artsy.net/artwork/{artwork_slug}',
                'description': 'Artsy contemporary art marketplace',
                'icon': 'palette',
                'category': 'art'
            },
            {
                'display_name': 'Saatchi Art',
                'url_pattern': 'https://saatchiart.com/art/{artwork_slug}',
                'description': 'Saatchi Art online gallery',
                'icon': 'image',
                'category': 'art'
            },
            {
                'display_name': 'Artnet',
                'url_pattern': 'https://artnet.com/artists/{artist_slug}',
                'description': 'Artnet auction results and artist database',
                'icon': 'paintbrush',
                'category': 'art'
            },
            {
                'display_name': '1stDibs',
                'url_pattern': 'https://1stdibs.com/furniture/{item_slug}',
                'description': '1stDibs luxury antiques and design',
                'icon': 'house',
                'category': 'art'
            },
            {
                'display_name': 'Live Auctioneers Art',
                'url_pattern': 'https://liveauctioneers.com/item/{artwork_id}',
                'description': 'LiveAuctioneers fine art auctions',
                'icon': 'hammer',
                'category': 'art'
            },
            {
                'display_name': 'Ravelry Yarn',
                'url_pattern': 'https://ravelry.com/yarns/library/{yarn_slug}',
                'description': 'Ravelry knitting and crochet community',
                'icon': 'scissors',
                'category': 'art'
            },
            {
                'display_name': 'Joann Fabrics',
                'url_pattern': 'https://joann.com/product/{product_id}',
                'description': 'Joann Fabrics craft supplies',
                'icon': 'scissors',
                'category': 'art'
            },
            {
                'display_name': 'Michaels Crafts',
                'url_pattern': 'https://michaels.com/product/{product_id}',
                'description': 'Michaels craft and hobby store',
                'icon': 'paintbrush',
                'category': 'art'
            },
            {
                'display_name': 'Hobby Lobby',
                'url_pattern': 'https://hobbylobby.com/product/{product_id}',
                'description': 'Hobby Lobby arts and crafts',
                'icon': 'heart',
                'category': 'art'
            },
            {
                'display_name': 'Blick Art Materials',
                'url_pattern': 'https://dickblick.com/products/{product_slug}',
                'description': 'Blick Art Materials art supplies',
                'icon': 'brush',
                'category': 'art'
            },

            # Sports & Fitness
            {
                'display_name': 'Dick\'s Sporting Goods',
                'url_pattern': 'https://dickssportinggoods.com/p/{product_slug}',
                'description': 'Dick\'s Sporting Goods athletic equipment',
                'icon': 'dumbbell',
                'category': 'sports'
            },
            {
                'display_name': 'REI',
                'url_pattern': 'https://rei.com/product/{product_id}',
                'description': 'REI outdoor gear and equipment',
                'icon': 'mountain',
                'category': 'sports'
            },
            {
                'display_name': 'Nike',
                'url_pattern': 'https://nike.com/t/{product_slug}',
                'description': 'Nike athletic apparel and footwear',
                'icon': 'zap',
                'category': 'sports'
            },
            {
                'display_name': 'Adidas',
                'url_pattern': 'https://adidas.com/us/{product_slug}',
                'description': 'Adidas sportswear and equipment',
                'icon': 'activity',
                'category': 'sports'
            },
            {
                'display_name': 'Under Armour',
                'url_pattern': 'https://underarmour.com/en-us/p/{product_id}',
                'description': 'Under Armour athletic performance gear',
                'icon': 'shield',
                'category': 'sports'
            },
            {
                'display_name': 'Patagonia',
                'url_pattern': 'https://patagonia.com/product/{product_slug}',
                'description': 'Patagonia outdoor clothing and gear',
                'icon': 'mountain',
                'category': 'sports'
            },
            {
                'display_name': 'Decathlon',
                'url_pattern': 'https://decathlon.com/products/{product_slug}',
                'description': 'Decathlon sports equipment and apparel',
                'icon': 'bike',
                'category': 'sports'
            },
            {
                'display_name': 'Sports Direct',
                'url_pattern': 'https://sportsdirect.com/product/{product_id}',
                'description': 'Sports Direct UK sporting goods',
                'icon': 'target',
                'category': 'sports'
            },
            {
                'display_name': 'Fitness Depot',
                'url_pattern': 'https://fitnessdepot.ca/product/{product_slug}',
                'description': 'Fitness Depot home gym equipment',
                'icon': 'dumbbell',
                'category': 'sports'
            },
            {
                'display_name': 'Rogue Fitness',
                'url_pattern': 'https://roguefitness.com/{product_slug}',
                'description': 'Rogue Fitness gym equipment and accessories',
                'icon': 'dumbbell',
                'category': 'sports'
            },

            # Technology & Electronics
            {
                'display_name': 'Newegg Tech',
                'url_pattern': 'https://newegg.com/p/{product_id}',
                'description': 'Newegg computer hardware and electronics',
                'icon': 'cpu',
                'category': 'technology'
            },
            {
                'display_name': 'B&H Photo',
                'url_pattern': 'https://bhphotovideo.com/c/product/{product_id}',
                'description': 'B&H Photo camera and electronics store',
                'icon': 'camera',
                'category': 'technology'
            },
            {
                'display_name': 'Adorama',
                'url_pattern': 'https://adorama.com/product/{product_slug}',
                'description': 'Adorama photography and electronics',
                'icon': 'aperture',
                'category': 'technology'
            },
            {
                'display_name': 'Micro Center',
                'url_pattern': 'https://microcenter.com/product/{product_id}',
                'description': 'Micro Center computer and electronics store',
                'icon': 'monitor',
                'category': 'technology'
            },
            {
                'display_name': 'Fry\'s Electronics',
                'url_pattern': 'https://frys.com/product/{product_id}',
                'description': 'Fry\'s Electronics consumer electronics',
                'icon': 'zap',
                'category': 'technology'
            },
            {
                'display_name': 'TigerDirect',
                'url_pattern': 'https://tigerdirect.com/product/{product_id}',
                'description': 'TigerDirect computer hardware store',
                'icon': 'pc-case',
                'category': 'technology'
            },
            {
                'display_name': 'PC Part Picker',
                'url_pattern': 'https://pcpartpicker.com/product/{product_id}',
                'description': 'PCPartPicker computer build planning',
                'icon': 'settings',
                'category': 'technology'
            },
            {
                'display_name': 'Tom\'s Hardware',
                'url_pattern': 'https://tomshardware.com/reviews/{review_slug}',
                'description': 'Tom\'s Hardware reviews and benchmarks',
                'icon': 'chart-bar',
                'category': 'technology'
            },
            {
                'display_name': 'AnandTech',
                'url_pattern': 'https://anandtech.com/show/{article_id}',
                'description': 'AnandTech in-depth hardware analysis',
                'icon': 'trending-up',
                'category': 'technology'
            },
            {
                'display_name': 'TechSpot',
                'url_pattern': 'https://techspot.com/products/{product_slug}',
                'description': 'TechSpot technology news and reviews',
                'icon': 'monitor',
                'category': 'technology'
            }
        ]