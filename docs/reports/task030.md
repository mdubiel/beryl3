# Task 30: Internet Platform Link Patterns Population

## Overview
Research and implement 100 link patterns for popular internet platforms to enable users to easily link their collection items to relevant online resources.

## Analysis of Current System

### Current Link Patterns
Need to check existing patterns in database:

```python
from web.models import LinkPattern
for pattern in LinkPattern.objects.filter(is_deleted=False):
    print(f"- {pattern.display_name}: {pattern.url_pattern}")
```

## Proposed Link Patterns (100 total)

### E-commerce & Shopping Platforms
1. **Amazon Product** - `https://amazon.com/dp/{asin}`
2. **Amazon UK** - `https://amazon.co.uk/dp/{asin}`
3. **eBay Listing** - `https://ebay.com/itm/{item_id}`
4. **eBay UK** - `https://ebay.co.uk/itm/{item_id}`
5. **Walmart** - `https://walmart.com/ip/{product_id}`
6. **Target** - `https://target.com/p/{product_id}`
7. **Best Buy** - `https://bestbuy.com/site/{product_id}`
8. **Newegg** - `https://newegg.com/p/{product_id}`
9. **Etsy Shop** - `https://etsy.com/listing/{listing_id}`
10. **AliExpress** - `https://aliexpress.com/item/{item_id}`

### Entertainment - Gaming
11. **Steam Game** - `https://store.steampowered.com/app/{app_id}`
12. **PlayStation Store** - `https://store.playstation.com/product/{product_id}`
13. **Xbox Store** - `https://microsoft.com/store/p/{product_id}`
14. **Nintendo eShop** - `https://nintendo.com/games/detail/{game_id}`
15. **Epic Games Store** - `https://store.epicgames.com/p/{game_slug}`
16. **GOG Game** - `https://gog.com/game/{game_slug}`
17. **BoardGameGeek** - `https://boardgamegeek.com/boardgame/{game_id}`
18. **Metacritic Game** - `https://metacritic.com/game/{platform}/{game_slug}`
19. **IGN Game Review** - `https://ign.com/games/{game_slug}`
20. **GameSpot** - `https://gamespot.com/games/{game_slug}`

### Entertainment - Movies & TV
21. **IMDb Movie** - `https://imdb.com/title/{title_id}`
22. **Rotten Tomatoes** - `https://rottentomatoes.com/m/{movie_slug}`
23. **TMDb Movie** - `https://themoviedb.org/movie/{movie_id}`
24. **Netflix** - `https://netflix.com/title/{title_id}`
25. **Hulu** - `https://hulu.com/movie/{movie_slug}`
26. **Amazon Prime Video** - `https://primevideo.com/detail/{title_id}`
27. **Disney Plus** - `https://disneyplus.com/movies/{movie_slug}`
28. **HBO Max** - `https://hbomax.com/feature/{feature_id}`
29. **Apple TV** - `https://tv.apple.com/movie/{movie_slug}`
30. **Vudu** - `https://vudu.com/content/movies/details/{movie_id}`

### Books & Literature
31. **Goodreads Book** - `https://goodreads.com/book/show/{book_id}`
32. **Amazon Books** - `https://amazon.com/dp/{isbn}`
33. **Barnes & Noble** - `https://barnesandnoble.com/w/{book_slug}`
34. **Google Books** - `https://books.google.com/books?id={book_id}`
35. **WorldCat** - `https://worldcat.org/oclc/{oclc_number}`
36. **LibraryThing** - `https://librarything.com/work/{work_id}`
37. **Open Library** - `https://openlibrary.org/books/{book_id}`
38. **ISBN DB** - `https://isbndb.com/book/{isbn}`
39. **Book Depository** - `https://bookdepository.com/book/{book_id}`
40. **Audible** - `https://audible.com/pd/{product_id}`

### Music
41. **Spotify Album** - `https://open.spotify.com/album/{album_id}`
42. **Apple Music** - `https://music.apple.com/album/{album_id}`
43. **YouTube Music** - `https://music.youtube.com/playlist?list={playlist_id}`
44. **SoundCloud** - `https://soundcloud.com/{artist}/{track}`
45. **Bandcamp** - `https://{artist}.bandcamp.com/album/{album_slug}`
46. **Last.fm Album** - `https://last.fm/music/{artist}/{album}`
47. **AllMusic** - `https://allmusic.com/album/{album_id}`
48. **Discogs Release** - `https://discogs.com/release/{release_id}`
49. **MusicBrainz** - `https://musicbrainz.org/release/{release_id}`
50. **Deezer** - `https://deezer.com/album/{album_id}`

### Collectibles & Hobbies
51. **eBay Category** - `https://ebay.com/sch/i.html?_nkw={search_term}`
52. **Worthpoint** - `https://worthpoint.com/worthopedia/{item_slug}`
53. **LiveAuctioneers** - `https://liveauctioneers.com/item/{item_id}`
54. **Heritage Auctions** - `https://ha.com/itm/{lot_number}`
55. **COMC (Cards)** - `https://comc.com/Cards/{card_slug}`
56. **PSA Card** - `https://psacard.com/cert/{cert_number}`
57. **Beckett Grading** - `https://beckett.com/grading/card/{card_id}`
58. **Coin World** - `https://coinworld.com/news/{coin_slug}`
59. **NGC Coin** - `https://ngccoin.com/coin-explorer/{coin_id}`
60. **PCGS Coin** - `https://pcgs.com/coinfacts/{coin_id}`

### Fashion & Lifestyle
61. **StockX** - `https://stockx.com/{product_slug}`
62. **GOAT Sneakers** - `https://goat.com/sneakers/{sneaker_slug}`
63. **Grailed** - `https://grailed.com/listings/{listing_id}`
64. **Vestiaire Collective** - `https://vestiairecollective.com/men/{item_slug}`
65. **The RealReal** - `https://therealreal.com/products/{product_slug}`
66. **Chrono24 Watches** - `https://chrono24.com/watch/{watch_id}`
67. **Hodinkee Shop** - `https://shop.hodinkee.com/products/{product_slug}`
68. **WatchStation** - `https://watchstation.com/products/{product_id}`
69. **Tourneau** - `https://tourneau.com/watches/{watch_slug}`
70. **Crown & Caliber** - `https://crownandcaliber.com/products/{product_slug}`

### Art & Crafts
71. **Artsy** - `https://artsy.net/artwork/{artwork_slug}`
72. **Saatchi Art** - `https://saatchiart.com/art/{artwork_slug}`
73. **Artnet** - `https://artnet.com/artists/{artist_slug}`
74. **1stDibs** - `https://1stdibs.com/furniture/{item_slug}`
75. **Live Auctioneers Art** - `https://liveauctioneers.com/item/{artwork_id}`
76. **Ravelry (Yarn)** - `https://ravelry.com/yarns/library/{yarn_slug}`
77. **Joann Fabrics** - `https://joann.com/product/{product_id}`
78. **Michaels Crafts** - `https://michaels.com/product/{product_id}`
79. **Hobby Lobby** - `https://hobbylobby.com/product/{product_id}`
80. **Blick Art Materials** - `https://dickblick.com/products/{product_slug}`

### Sports & Fitness
81. **Dick's Sporting Goods** - `https://dickssportinggoods.com/p/{product_slug}`
82. **REI** - `https://rei.com/product/{product_id}`
83. **Nike** - `https://nike.com/t/{product_slug}`
84. **Adidas** - `https://adidas.com/us/{product_slug}`
85. **Under Armour** - `https://underarmour.com/en-us/p/{product_id}`
86. **Patagonia** - `https://patagonia.com/product/{product_slug}`
87. **Decathlon** - `https://decathlon.com/products/{product_slug}`
88. **Sports Direct** - `https://sportsdirect.com/product/{product_id}`
89. **Fitness Depot** - `https://fitnessdepot.ca/product/{product_slug}`
90. **Rogue Fitness** - `https://roguefitness.com/{product_slug}`

### Technology & Electronics
91. **Newegg Tech** - `https://newegg.com/p/{product_id}`
92. **B&H Photo** - `https://bhphotovideo.com/c/product/{product_id}`
93. **Adorama** - `https://adorama.com/product/{product_slug}`
94. **Micro Center** - `https://microcenter.com/product/{product_id}`
95. **Fry's Electronics** - `https://frys.com/product/{product_id}`
96. **TigerDirect** - `https://tigerdirect.com/product/{product_id}`
97. **PC Part Picker** - `https://pcpartpicker.com/product/{product_id}`
98. **Tom's Hardware** - `https://tomshardware.com/reviews/{review_slug}`
99. **AnandTech** - `https://anandtech.com/show/{article_id}`
100. **TechSpot** - `https://techspot.com/products/{product_slug}`

## Implementation Plan

### Phase 1: Current State Analysis
1. **Audit existing patterns** in database
2. **Identify gaps** in coverage
3. **Prioritize by user value** and popularity

### Phase 2: Data Structure Design
1. **Create management command** `populate_link_patterns.py`
2. **Define URL pattern validation** rules
3. **Organize by category** for better management

### Phase 3: Pattern Development
1. **Research URL structures** for each platform
2. **Validate URL patterns** work correctly
3. **Test parameter substitution** functionality
4. **Create descriptive names** and help text

### Phase 4: Implementation
1. **Create population script** with dry-run mode
2. **Handle existing patterns** (update vs skip)
3. **Add proper categorization** and icons
4. **Implement error handling** and validation

### Phase 5: Testing & Validation
1. **Test URL generation** with real data
2. **Verify links work** correctly
3. **Check admin interface** displays properly
4. **Validate user experience** in item creation

## Pattern Categories
- **E-commerce** (10): Shopping platforms
- **Gaming** (10): Game stores and review sites  
- **Movies/TV** (10): Streaming and review platforms
- **Books** (10): Reading and book review platforms
- **Music** (10): Streaming and music databases
- **Collectibles** (10): Auction and grading sites
- **Fashion** (10): Clothing and accessory platforms
- **Art/Crafts** (10): Art sales and craft supplies
- **Sports** (10): Sporting goods retailers
- **Technology** (10): Electronics and tech reviews

## URL Pattern Format
```
https://{domain}/{path_structure}/{parameter}
```

Examples:
- `https://amazon.com/dp/{asin}`
- `https://imdb.com/title/{title_id}`
- `https://spotify.com/album/{album_id}`

## Success Criteria
- ✅ 100 unique link patterns across diverse platforms
- ✅ Proper URL parameter validation
- ✅ Categorized for easy management
- ✅ Icons assigned to each pattern
- ✅ Population script works in all environments
- ✅ Links generate correctly with real data

## Risk Mitigation
- **URL validation** to ensure patterns work
- **Platform research** to verify URL structures
- **Dry-run testing** before deployment
- **Rollback capability** if issues occur
- **Documentation** for pattern usage

This comprehensive link pattern system will significantly enhance the utility of Beryl3 collections by connecting items to relevant online resources and marketplaces.