# Beryl user stories

# Main / Common

- [x] [d528fd4](https://github.com/mdubiel/beryl3/commit/d528fd4677330c54c51ae8e3431e658b4f995845) As a user, I want to be able to log in so that I can securely store and manage my items.
- [x] [882c03d](https://github.com/mdubiel/beryl3/commit/882c03d2f2b5c3b75dfc620a7f94781ac7849762) As a user, I want to organize my items into lists so that I can track them easily.
- [x] [086a086](https://github.com/mdubiel/beryl3/commit/086a086275e068f1b76f59c74583cabdb66a087a) As a user, I want to share my lists using a short link so that external users can view them.

# List - The Collection

- [x] [882c03d](https://github.com/mdubiel/beryl3/commit/882c03d2f2b5c3b75dfc620a7f94781ac7849762) As a user, I want to create lists of items so that I can group related things together.
- [x] [086a086](https://github.com/mdubiel/beryl3/commit/086a086275e068f1b76f59c74583cabdb66a087a) As a user, I want to set my lists as either private or public so that I can control who sees them.
- [x] [086a086](https://github.com/mdubiel/beryl3/commit/086a086275e068f1b76f59c74583cabdb66a087a) As a user, I want my public lists to have an aesthetically pleasing view so that they are enjoyable for others to browse.
- [ ] (commit: ________) As a user, I want to add a header image to my lists, either by uploading one or generating one via AI, so that I can personalize their appearance.

# Item - The Thing

- [x] [dd516c0](https://github.com/mdubiel/beryl3/commit/dd516c0d4670d767976e18beefb0c4e5094f8a5b) As a user, I want others (both registered and external) to be able to reserve items on my public lists (e.g., for gifts) so that duplicates are avoided.
- [x] [dd516c0](https://github.com/mdubiel/beryl3/commit/dd516c0d4670d767976e18beefb0c4e5094f8a5b) As the list owner, I want to see that an item is reserved, but not *who* reserved it, so that the gift remains a surprise.
- [x] [dd516c0](https://github.com/mdubiel/beryl3/commit/dd516c0d4670d767976e18beefb0c4e5094f8a5b) As a user, I want to set properties for each item, such as visibility, shareability, and marking it as a favorite, so that I can manage individual items effectively.
- [x] [882c03d](https://github.com/mdubiel/beryl3/commit/882c03d2f2b5c3b75dfc620a7f94781ac7849762) As a user, I want to assign a status to each item (e.g., 'In Collection', 'Wanted', 'Reserved', 'Purchased') so that I can track its lifecycle.
- [ ] (commit: ________) As a user, I want to upload one or more images for each item so that I can visually identify them.
- [x] [dd516c0](https://github.com/mdubiel/beryl3/commit/dd516c0d4670d767976e18beefb0c4e5094f8a5b) As a user, I want to categorize items by type (e.g., Book, Music Record, LEGO Set, TCG Card) so that I can manage different kinds of collectibles appropriately.
- [x] [dd516c0](https://github.com/mdubiel/beryl3/commit/dd516c0d4670d767976e18beefb0c4e5094f8a5b) As a user, I want item types to have specific, relevant attributes (e.g., Author for Books, Set Number for LEGO) so that I can record detailed information.
- [x] [dd516c0](https://github.com/mdubiel/beryl3/commit/dd516c0d4670d767976e18beefb0c4e5094f8a5b) As a user, I want each item to have common fields like name/title, description, and images, as well as type-specific attributes (e.g., 'Series' for comics, 'Author' for books), so that I can capture all necessary details.
- [ ] (commit: ________) As a user, when entering attribute values (like an author's name), I want to select from previously used values *or* enter a new one within the same input field (like a ComboBox) so that data entry is faster and more consistent.
- [ ] (commit: ________) As a user, I want to move or copy items between my lists so that I can reorganize my collections easily.
- [ ] (commit: ________) As a user, I want reserved items to automatically become unreserved after a configurable period (with a default setting) so that items don't stay reserved indefinitely if someone forgets.
- [ ] (commit: ________) As a user who has reserved an item on someone else's list, I want to see a list of my reservations so that I can keep track of them.
- [ ] (commit: ________) As a user, I want to add external links (e.g., to a shop or information page) to each item so that I can easily reference related web resources.
- [x] [dd516c0](https://github.com/mdubiel/beryl3/commit/dd516c0d4670d767976e18beefb0c4e5094f8a5b) As an external visitor viewing a public list, I want to be able to reserve an available item by providing my email address, so that I can indicate my intention to gift it without needing to register.

# Application Owner

- [ ] (commit: ________) As the application owner, I want to offer a premium subscription tier so that I can monetize the application and provide enhanced features.
- [ ] (commit: ________) As the application owner, I want the free tier to have configurable limits on the number of lists and items per list so that I can encourage users to upgrade to the premium tier.
- [ ] (commit: xxx) As the application owner, I want to view overall application usage statistics so that I can understand growth trends and feature popularity.
- [ ] (commit: ________) As the application owner, I want a dedicated financial dashboard showing key metrics like Ok, so that I can track the financial health and growth of the subscription business.

# Application Administration

- [ ] (commit: ________) As an application administrator, I want a dedicated view to see a list of all users, including their list/item usage (used vs. permitted), list privacy status (public/private), links to public lists, and last login date, so that I can monitor user activity and platform usage.
- [ ] (commit: xxx) As an application administrator, I want to be able to search and filter the user list view so that I can quickly find specific users or groups of users.
- [ ] (commit: ________) As an application administrator, I want to access searchable activity logs for all users so that I can troubleshoot issues and monitor security.
- [ ] (commit: ________) As an application administrator, I want the ability to adjust the free tier limits (number of lists and items) for individual users so that I can grant exceptions or reward specific users.
- [ ] (commit: xxx) As an application administrator, I want the ability to manage user credentials (e.g., reset passwords) so that I can provide support when users are locked out or need assistance.
- [ ] (commit: ________) As an application administrator, I want a dashboard displaying key system health metrics (e.g., server load, database response time, error rates) so that I can proactively monitor application stability and performance.
- [ ] (commit: ________) As an application administrator, I want tools to manage application backups and initiate restores so that I can ensure data integrity and recovery in case of failures.
- [ ] (commit: ) As an application administrator, I want to have possibility to define ItemTypes and it's attributes.
- [ ] (commit: ) As an application administrator, I want to have an option to define shortnames to links used in the system (to make them look nicelly when user adds link). I should be able to define its name ane url pattern (regexp with verification), It also should provide a list of applied shortcuts from already defined links by users.

# Marketing

- [ ] (commit: ________) As a marketer, I want the application's main landing page (root `/`) to prominently feature calls-to-action for user registration and upgrading to premium, so that I can maximize lead generation and conversion rates.
- [ ] (commit: ________) As a marketer, I want the ability to feature or highlight selected public user lists (e.g., on the landing page or a dedicated section), so that I can showcase the application's value and encourage new user sign-ups by demonstrating active use.
- [ ] (commit: ________) As a marketer, I want the system to suggest potentially interesting public lists for highlighting, so that I can efficiently discover content to feature.
- [ ] (commit: ________) As a marketer, I want clear opportunities for users and visitors to subscribe to a marketing mailing list (e.g., via a dedicated form or an option during registration), so that I can build an engaged audience for newsletters, updates, and promotional campaigns.
- [ ] (commit: ________) As a marketer, I want users to be able to easily share their public lists directly to social media platforms (like Facebook, Twitter, Pinterest) with pre-populated text, so that they can organically promote the application and attract new users through their networks.
- [ ] (commit: ________) As a marketer, I want to implement a referral program where existing users receive a benefit (e.g., temporary premium access, increased free tier limits) for successfully referring new registered users, so that I can incentivize word-of-mouth growth and user acquisition.
- [ ] (commit: ________) As a marketer, I want to integrate web analytics tools (like Google Analytics or Plausible) into the application, particularly on the landing page, public list views, and registration/upgrade funnels, so that I can track marketing campaign effectiveness, understand user acquisition sources, and measure key conversion rates.

# Functional

- [ ] RecentActivity should be as real application log that users and admins can review. Each entry should be marked "is user visible" if it is related to user action. Also, this functionallity should have some static methods as I can call RecentActivity.log(...) to have an atomic call in the functions instead of creating objects manually every time. It also should contain "user visible text" with possible links in markdown. User visible text, should be JSON with appropiate object type, its hash (or more objects if it refers to more than one), activity text.
- [ ] Attributes can be linkable eg. https://www.lego.com/en-de/product/10357 where `10357` is a set ID. Needs to have a good verification, and be optional.
- [ ] Tasks controls (like celery reservetions release) should be visible in Sys Panel
- [ ] Each reservation should have a datetime of expiry, this informations shold be send in reservation email and celery task to remove reservation scheduled at this time.
- [ ] Branding - made by nerd for nerds
- [ ] Colleciton can be also a story, with some text and pictures in between and ordered item list