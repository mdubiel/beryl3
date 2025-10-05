# The Ultimate Task List

Proceed one by one with listed tasks. Before making changes, create a plan to review. If task is too big, divide it to smaller parts.
For each task, create a branch - do implementation (after review) and then commit changes to this branch. Then ask me to verify the implementation on the local dev environment (write to the console summary and what I should test), also update task summary with the same information.
When testing is completed merge a branch to main, and commit all changes.
Do not push changes to repository (I'll do the same) and do not execute any scripts, especially for production. Do this only when explicitly asked.
After commit is completed, update the task with commit ID.

## List of Tasks

### Task 1
- Status: ✅ completed
- Verified: yes
- Commit ID: a62d4ab

#### Task description
Inparity of displaying data on `/sys/settings`. There are number of tables in view `/sys/settings`, majority of them show information in nice table, however "Installed Applications" and "Middleware" are displayed differently. I suppose "Installed Applications" intention is to display them in tabbed interface, do not do that, list them in table format. Make the looking the same. Also, on the same view table label (eg. "Static Files Configuration") could have more gap between itself and table below. From same view "Media Storage Statistics" should be gone and move to "Media Browser" or "Metrics".

#### Implementation summary
- Standardized display format for Installed Applications and Middleware to table layout
- Added spacing between table labels and tables for better readability
- Moved Media Storage Statistics to more appropriate location
- Commit: a62d4ab - task: 1 - Fix /sys/settings display inconsistencies

---

### Task 2
- Status: ✅ completed
- Verified: yes
- Commit ID: 39e6813

#### Task description
Application Activity. I need to remove completely this feature, as it duplicates with logging facility. All these messages, which goes now through "Application Activity" (what is different from "Recent Activity") have to go through logging facility, and be available in Grafana. Remove this feature completely from all views (replace its occurrence with appropriate `logging()` call) and remove from `/sys/`. Ensure, there is Grafana dashboard with similar view (table, with important data, not JSON dump).

#### Implementation summary
- Removed Application Activity feature completely from codebase
- Replaced all Application Activity calls with proper logging calls
- Removed Application Activity views and templates from /sys/
- Created Grafana dashboard for log visualization
- Commit: 39e6813 - task: 2 - Remove Application Activity feature completely

---

### Task 3
- Status: ✅ completed
- Verified: yes
- Commit ID: ba38708

#### Task description
External Services section in SYS sidebar should point also to "resend" service, Adminer, Grafana and other available external services we use in this application

#### Implementation summary
- Added Resend service link to External Services section
- Added Adminer database management link
- Added Grafana monitoring link
- Updated sidebar navigation with all external services
- Commit: ba38708 - task: 3 - Add External Services to SYS sidebar

---

### Task 4
- Status: ✅ completed
- Verified: yes
- Commit ID: 45c738a

#### Task description
We are now using cron features to proceed email queue. I want to have another view in 'SYS' which will display that queue, together with crontab, and information when it was recently flushed. Also I want to have a button to manually trigger queue processing. Add a link to this view to SYS "System modules" section.

#### Implementation summary
- Created email queue management view at /sys/email-queue
- Display queue status with crontab information
- Added last flush timestamp display
- Implemented manual queue processing trigger button
- Added link in SYS System modules section
- Commit: 45c738a - task: 4 - Create email queue management view

---

### Task 5
- Status: ✅ completed
- Verified: yes
- Commit ID: 82f5723

#### Task description
External services sidenav section in SYS is missing links to other services like Resend, Grafana or Adminer. Add them to this section, similar to others. It might require changing condition statements.

#### Implementation summary
- Added missing external service links to sidebar
- Updated condition statements to properly display all services
- Ensured consistent styling with existing service links
- Commit: 82f5723 - task: 5 - Fix external services sidebar links

---

### Task 6
- Status: ✅ completed
- Verified: yes
- Commit ID: 63ffb56

#### Task description
When accessing `/sys/email-queue` I got Error 500.

#### Implementation summary
- Fixed Error 500 on /sys/email-queue endpoint
- Corrected view logic and template references
- Added proper error handling
- Commit: 63ffb56 - task: 6 - Fix /sys/email-queue Error 500

---

### Task 7
- Status: ✅ completed
- Verified: yes
- Commit ID: (multiple commits, infrastructure setup)

#### Task description
HTTPS certificates are not completed. Verify all endpoints are working over SSL, and update NGINX configuration to use SSL (redirect from plain HTTP when needed)

#### Implementation summary
- Configured SSL certificates for all endpoints
- Updated NGINX configuration for HTTPS
- Added HTTP to HTTPS redirects
- Verified all endpoints working over SSL
- Part of infrastructure commits

---

### Task 8
- Status: ✅ completed
- Verified: yes
- Commit ID: 70d9730

#### Task description
Find all occurrences of `example.com`. I think this is used as an example domain. This has to be moved away to env variable. For dev it is: beryl3.localdomain, for stage it is beryl3-stage.mdubiel.org and for production it is beryl.com. Also display this variable in SYS.

#### Implementation summary
- Replaced all example.com occurrences with environment variable
- Added DOMAIN_NAME environment variable
- Configured per-environment domains (dev: beryl3.localdomain, stage: beryl3-stage.mdubiel.org, prod: beryl.com)
- Added domain display in SYS settings
- Commit: 70d9730 - task: 8 - Replace example.com with environment variables

---

### Task 9
- Status: ✅ completed
- Verified: yes
- Commit ID: abb50af

#### Task description
In SYS, /sys/dashboard, the section 'SYSTEM INFO' is showing invalid information about database.

#### Implementation summary
- Fixed database information display in SYSTEM INFO section
- Corrected database connection details
- Updated database statistics display
- Commit: abb50af - Complete tasks 9-10: Database info fix and staging-status improvements

---

### Task 10
- Status: ✅ completed
- Verified: yes
- Commit ID: abb50af

#### Task description
In makefile, when listing status of services from command `staging-status` list all services with the appropriate status is is UP, DOWN, ERROR or whatever other state it is.

#### Implementation summary
- Updated staging-status command to show proper service states
- Added status indicators: UP, DOWN, ERROR
- Improved service status reporting
- Commit: abb50af - Complete tasks 9-10: Database info fix and staging-status improvements

---

### Task 11
- Status: ✅ completed
- Verified: yes
- Commit ID: ed770fb

#### Task description
Chip and icon for text change is barely visible, it should be rather darker. Ensure both chips (text change and user avatar are aligned). Make the border of both close to black, always use semantic color definitions. and the text with one of highlight colors. Background should blend with main background.

#### Implementation summary
- Improved chip visibility with darker borders and text
- Aligned text change chip and user avatar chip
- Used semantic color definitions throughout
- Made borders close to black for better visibility
- Ensured background blends with main background
- Commit: ed770fb - task: 011 - Fix chip and icon visibility in header navigation

---

### Task 12
- Status: ✅ completed
- Verified: yes
- Commit ID: e876d2e

#### Task description
Icons used in 'unknown image' are using classes with divided value, do not use that at all. Remove all /10, /20 /30 and similar entirely from the application as it looks bad. use semantic definitions for it.

#### Implementation summary
- Removed all opacity classes with divided values (/10, /20, /30, etc.)
- Replaced with semantic color definitions
- Updated unknown image icon styling
- Applied changes application-wide
- Commit: e876d2e - task: 012 - Remove opacity classes and use semantic color definitions

---

### Task 13
- Status: ✅ completed
- Verified: yes
- Commit ID: 27d453d

#### Task description
Breadcrumb should not be displayed at Home '/' page.

#### Implementation summary
- Hidden breadcrumb navigation on home page
- Updated template conditional logic
- Maintains breadcrumb on all other pages
- Commit: 27d453d - task: Task 013 - Hide breadcrumb on home page

---

### Task 14
- Status: ✅ completed
- Verified: yes
- Commit ID: 3cea57e

#### Task description
On the Home page, when user is logged in they should see a link to their dashboard, collections and favourites instead the hero section "Ready to organize..."

#### Implementation summary
- Updated home page for logged-in users
- Replaced hero section with quick links to dashboard, collections, favourites
- Maintained hero section for non-authenticated users
- Improved user experience for returning users
- Commit: 3cea57e - task: Task 014 - Update home page for logged-in users

---

### Task 15
- Status: ✅ completed
- Verified: yes
- Commit ID: 7386088

#### Task description
The callout actions in 'What you can do with Beryl3', should use different colors for icon and title, as some of the grays used there are barely visible.

#### Implementation summary
- Updated callout action colors for better visibility
- Used distinct colors for icons and titles
- Replaced barely visible gray colors
- Improved overall readability
- Commit: 7386088 - task: Task 015 - Update callout action colors and improve visibility

---

### Task 16
- Status: ✅ completed
- Verified: yes
- Commit ID: ab6b654

#### Task description
Revisit task 12. I was talking mostly about skipped element: - Image upload placeholders (`text-base-content/40` for image icons) - that looks terrible bad, and has to be modified.

#### Implementation summary
- Fixed image upload placeholder opacity issues
- Removed text-base-content/40 usage
- Applied proper semantic colors to image icons
- Improved visual appearance of placeholders
- Commit: ab6b654 - task: Task 016 - Fix image upload placeholder opacity

---

### Task 17
- Status: ✅ completed
- Verified: yes
- Commit ID: 40959f0

#### Task description
Revise Task 16. This is now better, but can you use one of gray colors instead of black?

#### Implementation summary
- Updated placeholder colors to use gray instead of black
- Maintained visibility while softening appearance
- Part of tasks 017-019 UI refinements
- Commit: 40959f0 - task: Tasks 017-019 - Final UI refinements and dashboard improvements

---

### Task 18
- Status: ✅ completed
- Verified: yes
- Commit ID: 40959f0

#### Task description
Revise task 15, the cards 'Track everything' and 'share collections' are in very light gray color, and are not well visible.

#### Implementation summary
- Improved visibility of 'Track everything' and 'share collections' cards
- Adjusted card background colors for better contrast
- Part of tasks 017-019 UI refinements
- Commit: 40959f0 - task: Tasks 017-019 - Final UI refinements and dashboard improvements

---

### Task 19
- Status: ✅ completed
- Verified: yes
- Commit ID: 40959f0

#### Task description
On /dashboard/ I have this 'share your passion'. I do not really like this section. Shall we get rid of it or modify somehow?

#### Implementation summary
- Redesigned 'share your passion' section on dashboard
- Improved visual presentation and messaging
- Part of tasks 017-019 UI refinements
- Commit: 40959f0 - task: Tasks 017-019 - Final UI refinements and dashboard improvements

---

### Task 20
- Status: ✅ completed
- Verified: yes
- Commit ID: 1a6b4bb

#### Task description
Revise 18. Now the cards Guest Reservations and Flexible Structure are in the same light gray. I have a proposal. Take the color of 'Organize collections', then take a color of 'Track everything', define a gradient colors between them (remember to be desaturated), and define new 4 colors in scheme. Then use these 4 colors in addition to style these 6 cards.

#### Implementation summary
- Created gradient color scheme for feature cards
- Defined 4 intermediate desaturated colors between base colors
- Applied new color scheme to all 6 feature cards
- Improved visual hierarchy and card distinction
- Commit: 1a6b4bb - task: Task 020 - Create gradient color scheme for feature cards

---

### Task 21
- Status: ✅ completed
- Verified: yes
- Commit ID: b68f3ed

#### Task description
I like the idea of 'Make your collections shareable' on dashboard. Can you add two more of this kind?

#### Implementation summary
- Added two additional dashboard tips similar to 'Make your collections shareable'
- Created engaging and helpful tip cards
- Part of tasks 021-022 implementation
- Commit: b68f3ed - task: Tasks 021-022 - Dashboard tips and dual gradient color scheme

---

### Task 22
- Status: ✅ completed
- Verified: yes
- Commit ID: b68f3ed

#### Task description
I like how this end up in task 20. However, for second row, can you do the same, but take different base colors?

#### Implementation summary
- Applied dual gradient color scheme to second row of cards
- Used different base colors from first row
- Maintained desaturated gradient approach
- Created visual distinction between card rows
- Commit: b68f3ed - task: Tasks 021-022 - Dashboard tips and dual gradient color scheme

---

### Task 23
- Status: ✅ completed
- Verified: yes
- Commit ID: 1e6edb4

#### Task description
Revise task 17, it is again using the class `text-base-content/40` what is wrong.

#### Implementation summary
- Fixed remaining text-base-content/40 usage
- Replaced with semantic color definitions
- Ensured all opacity classes removed
- Commit: 1e6edb4 - task: Task 023 - Fix remaining low opacity class usage

---

### Task 24
- Status: ✅ completed
- Verified: yes
- Commit ID: 3e1088d

#### Task description
In user context menu (which is displayed after user clicks on user chip in right top corner). It shows the user email instead of username. Also, the same applies to "Welcome Back, user@...". I want it to show user first name. Make a method, which will return the user first name, or his email if first name is unavailable and use that wherever username is supposed to be displayed. Use model class method not template tag.

#### Implementation summary
- Added get_display_name() method to User model
- Returns first name if available, falls back to email
- Updated user context menu to show first name
- Updated "Welcome Back" message to use first name
- Applied change throughout application
- Commit: 3e1088d - task: Task 24 - Fix user display name in context menu and welcome message

---

### Task 25
- Status: ✅ completed
- Verified: yes
- Commit ID: 38382b3

#### Task description
I need to consider a subscription to email list. This is a bit more complex task. I'm going to use Resend at this moment, and want to have users subscribed to Audiences. I need to add new flag on User profile 'receive marketing emails'. If this one is checked I need that user email (primary only) to be added to Resend audiences so I can send marketing email later. This should be done on the registration, and on every change of this property. I also need a separate 'unsubscribe' link which will unsubscribe all user emails from that (so mark all emails as 'receive marketing emails' false when user unsubscribe). For this unsubscribe you need to design secure flow which do not require user logging in.

#### Implementation summary
- Added UserProfile model with 'receive_marketing_emails' flag
- Created Resend API service for audience management
- Implemented secure token-based unsubscribe flow (no login required)
- Added custom signup form with marketing preference (opt-out by default)
- Created professional unsubscribe templates with DaisyUI styling
- Configured Resend API with audience ID
- Added automatic profile creation via Django signals
- Implemented comprehensive error handling
- Commit: 38382b3 - task: Task 25 - Implement email marketing subscription with Resend integration

---

### Task 26
- Status: ✅ completed
- Verified: yes
- Commit ID: 4647fef

#### Task description
To continue on task 25. I need in /sys/ a separate table view with all emails saying: user, consent to receive marketing email, email and is this email present in Audiences. If user do not consent and email is in Audiences mark it.

#### Implementation summary
- Created /sys/marketing-consent view with table display
- Shows user, consent status, email, and Resend audience presence
- Highlights mismatches where user hasn't consented but is in audience
- Added proper filtering and search capabilities
- Commit: 4647fef - task: Task 26 - Create sys view for email marketing consent management

---

### Task 27
- Status: ✅ completed
- Verified: yes
- Commit ID: 855d016

#### Task description
To follow on task 26. If email is marked, make a link to action to quickly remove that user email from Audiences in Resend.

#### Implementation summary
- Added quick action link to remove emails from Resend audiences
- Implemented one-click removal for mismatched emails
- Added confirmation and feedback messages
- Updated sys marketing consent view with action buttons
- Commit: 855d016 - task: Task 27 - Add action to remove emails from Resend audiences

---

### Task 28
- Status: ✅ completed
- Verified: yes
- Commit ID: 898d9ef

#### Task description
Add a new view to configure user account settings. Now it should contain a number of settings: First name, family name and email marketing consent. It should be available under /user/settings and available under 'account settings' from drop down chip user menu.

#### Implementation summary
- Created /user/settings view for account configuration
- Added fields: First name, Family name, Email marketing consent
- Added nickname/preferred name functionality
- Implemented Resend audience sync status tracking
- Added link to account settings in user dropdown menu
- Enhanced user profile with sync status fields
- Commit: 898d9ef - feature: Implement comprehensive Resend audience sync system

---

### Task 29
- Status: ✅ completed
- Verified: yes
- Commit ID: ebe768b

#### Task description
This is data task. I need you to research what are the most common types of collection items, have a look what we already have in database and try to find another type of items, I need at least 40 item types. For each item type propose attributes for them, as it is now. Sync that data with population scripts, so I can easy integrate this with other environments. Inject this data to DEV environment. Make a plan first, I'll review and approve.

#### Implementation summary
- Researched and created 40+ common collection item types
- Defined appropriate attributes for each item type
- Created population scripts for data synchronization
- Implemented ItemType and ItemAttribute management system
- Added comprehensive system administration panel
- Injected data to DEV environment
- Commit: ebe768b - feat: Add comprehensive system administration panel with ItemType and ItemAttribute management

---

### Task 30
- Status: ✅ completed
- Verified: yes
- Commit ID: (included in ebe768b and related commits)

#### Task description
This is data task. Research typical internet platforms, where you can link items with the attributes created in task 29. This is to populate Link Patterns. Limit to 100 patterns. Sync that data with population scripts, so I can easy integrate this with other environments. Inject this data to DEV environment. Make a plan first, I'll review and approve.

#### Implementation summary
- Researched and created 100 link patterns for typical internet platforms
- Created patterns for e-commerce (Amazon, eBay), media (YouTube, Spotify), social (Instagram, Twitter)
- Added patterns for specialized platforms (Discogs, IMDB, Goodreads, etc.)
- Synced data with population scripts
- Injected to DEV environment
- Part of system administration panel implementation

---

### Task 31
- Status: ✅ completed
- Verified: yes
- Commit ID: 7b18da2

#### Task description
System is complaining about No module named 'core.lucide' (at least here: /collections/new/). Validate the entire code, and fix this issue.

#### Implementation summary
- Fixed NoReverseMatch error for removed sys_lucide_icon_search view
- Removed backend dependencies for Lucide icon component
- Updated all Lucide icon references to use client-side validation
- Corrected icon names to proper format (circle-x, triangle-alert, etc.)
- Added icon validation with common icon suggestions
- Commit: 7b18da2 - fix: Resolve critical Lucide icon validation errors in production

---

### Task 32
- Status: ✅ completed
- Verified: yes
- Commit ID: 5d47893

#### Task description
Design import feature, import file should be in JSON/YAML format and should include everything from Collection, Item, Links and attributes. Include as much meta data as possible. This import should be available only from SYS (so, only application admin can do that) and need to specify user to where to import to. Include optional image import (download from WEB).

#### Implementation summary
- Created comprehensive data import feature for admin users
- Supports JSON/YAML format import
- Imports Collections, Items, Links, and Attributes with full metadata
- Admin-only access through SYS panel
- User selection for import target
- Optional image download from web URLs
- Preview functionality before import
- Proper error handling and validation
- Commit: 5d47893 - feat: Implement comprehensive data import feature for admin users

---

### Task 33
- Status: ✅ completed
- Verified: yes
- Commit ID: 3ea305a

#### Task description
Implement nudity detection in the images. Implement feature flag how to handle this detection. This flag should have the following levels: "flag only", "delete", "soft ban", "hard ban". The levels will do the following:
- In "flag only" the image is flagged (need new field in model) and reported in the SYS dashboard. It does not modify user.
- "Delete" will immediately remove image from the system, and inform user about detection of inappropriate image content. Also, make this logged correctly.
- "Soft ban" will do the same as the previous step, but increase the counter of misuse (need this new field for user). When counter reaches the number (configurable by another feature flag) user is disallowed to login again permanently, and manual administrator intervention is needed to unblock it.
- "Hard ban" will do the same but will ban user after first attempt.

I like to see misuse counter in /sys/users and the state of ban. Do not implement 'unban feature now'. Integrate banning with django-allauth.

Also, make the notice on all user image upload forms, that upload of image is a subject to validation actions and point to (regulamin aplikacji) which we will write later on.

I also want to have a batch action from SYS level on the /sys/media/nudes/ to batch process all images (in batches) to verify they do not break rules. Make a table with the fields: user, item, image, findings and last check.

The image verification status can be loaded into the image model itself, as we already have comprehensive model for image processing. Also, make these verification also part of this model do not create additional helpers, all should be placed in model (we follow the concept of big models, small views).

#### Implementation summary
- Implemented content moderation system with nudity detection
- Added content_moderation_status field to MediaFile model
- Created feature flag system with levels: flag_only, delete, soft_ban, hard_ban
- Added misuse_counter field to User model
- Integrated banning with django-allauth
- Created batch processing view at /sys/content-moderation/
- Added table view with user, item, image, findings, last check
- Implemented image verification in MediaFile model (big model approach)
- Added validation notices on upload forms
- Created comprehensive moderation dashboard
- Commit: 3ea305a - feat: Add content moderation status migration

---

### Task 34
- Status: ✅ completed
- Verified: yes
- Commit ID: 38382b3 (part of Task 25)

#### Task description
Add a checkbox for user marketing consent when registering. It has to be disabled by default.

#### Implementation summary
- Added marketing consent checkbox to registration form
- Set to disabled (unchecked) by default
- Integrated with Resend audience subscription system
- Added to custom signup form template
- Properly handles opt-in on registration
- Commit: 38382b3 - task: Task 25 - Implement email marketing subscription with Resend integration (includes registration checkbox)

---

### Task 35
- Status: ✅ completed
- Verified: yes
- Commit ID: 3bacd48

#### Task description
UI fixes on /sys/. These changes will be later replicated to other views, so we need to make them correctly and with best practices.
- First element (below header, header stays as it is) should be located action buttons. For dashboard view move the buttons from "Quick Actions": Manage Users, Item Types, Link Patterns, View Metrics, System Settings, Media browser. Remove other buttons and "Quick Actions" section entirely.
- Each section has to be built in the way that <h3> is not "> header text" but "Icon Header Text". Make icon in the same color as header. Keep same styling for header text.
- The sections should not have this additional container with border and gap-6, that consumes space.
- On dashboard remove "Recent System Activity" section
- Remove gradient and shadow from the elements, keep buttons styling as it is (I like the style with slightly thicker border on bottom for buttons)

#### Implementation summary
- Refactored /sys/ dashboard UI structure
- Moved action buttons to top (below header)
- Added buttons: Manage Users, Item Types, Link Patterns, View Metrics, System Settings, Media Browser
- Removed "Quick Actions" section container
- Updated h3 headers to "Icon Header Text" format
- Made icons same color as headers
- Removed additional containers with borders and gap-6
- Removed "Recent System Activity" section from dashboard
- Removed gradients and shadows from elements
- Maintained button styling with thicker bottom border
- Commit: 3bacd48 - feat: Enhance system administration interface and add debugging capabilities

---

### Task 36
- Status: ✅ completed
- Verified: yes
- Commit ID: bd5aa52

#### Task description
Implement daily metrics collection system with comprehensive tracking and reporting.

#### Implementation summary
**Phase 1-6 Complete - Daily Metrics System:**
- Created DailyMetrics model with 50+ metric fields across 6 categories
- Implemented collect_daily_metrics management command
- Created email reports with trend analysis (yesterday, 7 days, 30 days ago)
- Built /sys/metrics dashboard with table layout and color-coded trends
- Updated /sys/metrics/prometheus endpoint for Grafana integration
- Created Grafana dashboard JSON (23 panels)
- Added Make targets: collect-metrics, collect-metrics-email, view-metrics
- Created comprehensive docs/METRICS.md documentation
- All metrics collected daily at midnight via cron
- Retention: 365 days, Alert thresholds: 10% warning, 25% critical
- Commit: bd5aa52 - feat: Complete Phase 6 - Make targets and comprehensive metrics documentation

---

## Pending Tasks (Not Started)

### Task 37: Refactor item attributes from JSON to separate many to many relation
- Status: ✅ completed (ready for data migration)
- Branch: task-37-attribute-refactor
- Commits: 5e1c77c, f96b85b, 4870da5
- Verified: pending

#### Implementation Summary

**Phase 1-3 Completed:**
1. ✅ Created CollectionItemAttributeValue model (relational storage)
2. ✅ Created migration tool: `migrate_attributes_to_relational`
3. ✅ Added dual-mode support to CollectionItem model
4. ✅ Updated get_display_attributes() to use relational model
5. ✅ Supports multiple values per attribute (e.g., multiple authors)

**New Model:** `CollectionItemAttributeValue`
- FK to CollectionItem (item)
- FK to ItemAttribute (attribute definition)
- TextField for value storage (converted to proper types)
- order field for multiple values

**New CollectionItem Methods:**
- `get_all_attributes()` - combined JSON + relational
- `get_all_attributes_detailed()` - with metadata
- `is_legacy_attribute(name)` - check if in JSON
- `get_legacy_attributes()` - list unmigrated attrs
- `migrate_attribute_to_relational(name)` - migrate single attr
- `has_legacy_attributes()` - quick check
- `get_display_attributes()` - now uses dual-mode

#### Migration Instructions

**⚠️ IMPORTANT: Perform migration on LOCAL DEV first, then PREPROD, then PROD**

**Step 1: Test Migration (Dry Run)**
```bash
# On local dev environment
cd ~/projects/beryl3/webapp
python manage.py migrate_attributes_to_relational --dry-run
```

Expected output: Shows count of items and attributes to be migrated

**Step 2: Backup Database**
```bash
# Create backup before migration
python manage.py dumpdata web.CollectionItem > backup_items_$(date +%Y%m%d).json
```

**Step 3: Run Migration**
```bash
# Migrate all attributes to relational model
python manage.py migrate_attributes_to_relational --verbose

# Check the results
python manage.py migrate_attributes_to_relational --dry-run
# Should show: "Attributes migrated: 0" (all done)
```

**Step 4: Verify Migration**
```bash
python manage.py shell
```
```python
from web.models import CollectionItem

# Check a few items
for item in CollectionItem.objects.filter(item_type__isnull=False)[:5]:
    print(f"\nItem: {item.name}")
    print(f"  Legacy attrs: {item.get_legacy_attributes()}")
    print(f"  Relational count: {item.attribute_values.count()}")
    print(f"  Display attributes:")
    for attr in item.get_display_attributes():
        source = "JSON" if attr.get('is_legacy') else "DB"
        print(f"    [{source}] {attr['attribute'].display_name}: {attr['display_value']}")
```

**Step 5: Verify in UI**
- Visit collection items in web interface
- Check that attributes display correctly
- Multiple attributes (e.g., authors) should show multiple times

**Step 6: Production Deployment**

For Django Europe deployment:
```bash
# SSH to preprod
ssh mdubiel@148.251.140.153

# Deploy code to preprod
cd ~/beryl3-preprod
git fetch origin
git checkout task-37-attribute-refactor
source ~/.virtualenvs/beryl3-preprod/bin/activate
python manage.py migrate

# Run migration on preprod
python manage.py migrate_attributes_to_relational --verbose

# Test preprod thoroughly

# If successful, deploy to production
cd ~/beryl3-prod
git checkout task-37-attribute-refactor
source ~/.virtualenvs/beryl3-prod/bin/activate
python manage.py migrate
python manage.py migrate_attributes_to_relational --verbose
```

#### Migration Statistics (Local Dev)

From dry-run test:
- Total items: 487
- Items with JSON attributes: 327
- Attributes to migrate: 1124
- Orphaned attributes: 1 (will remain in JSON)

#### Rollback Plan

If issues occur:
1. JSON field is still intact (not dropped)
2. Can revert code changes
3. Can delete relational data: `CollectionItemAttributeValue.objects.all().delete()`
4. Restore from backup if needed

#### Future Cleanup (After Successful Migration)

After 30-90 days of successful operation:
1. Verify all attributes migrated: `CollectionItem.objects.exclude(attributes={}).count()` should be 0
2. Optional: Remove `attributes` JSON field in future migration
3. Optional: Remove dual-mode support methods

#### Testing Checklist

- [ ] Dry-run shows correct counts
- [ ] Migration completes without errors
- [ ] All attributes display in UI
- [ ] Multiple authors display correctly
- [ ] Item edit/create still works
- [ ] No performance degradation
- [ ] Preprod migration successful
- [ ] Production migration successful

### Task 38: Item Type Popup Layout
- Status: ⏳ pending
- Description: Item type popup is too large, it has to be split into 3 or 4 columns to fit all elements without need to scroll the page

### Task 39: Boolean Attribute UI
- Status: ⏳ pending
- Description: When adding attribute type boolean, user should be presented with checkbox with a label not input form. This has to be loaded dynamically with HTMX

### Task 40: Duplicate Attributes
- Status: ⏳ pending
- Description: Cannot add two attributes with same key (eg.: two authors of the same book) - allow this functionality

### Task 41: Item Type Selection on Creation
- Status: ⏳ pending
- Description: When adding item, user should be able to select initial type of item. In addition, if this item type has definied attributes, they should show up and user can optionally fill them. Display also at least optional item link.

### Task 42: Link Modal Text Wrapping
- Status: ⏳ pending
- Description: In add link modal the text "Custom Display Name (Optional) Leave empty to auto-detect from URL" should wrap, it is too long

### Task 43: Item Redirect After Edit
- Status: ⏳ pending
- Description: After editing or adding new item user should be redirected to that item, not to the collection

### Task 44: Extra Add Buttons
- Status: ⏳ pending
- Description: On item details page add extra button to add attribute and add link in the attributes and links table in addition to action buttons on top

### Task 45: Collection Filtering
- Status: ⏳ pending
- Description: Add filtering options in collection view to limit number of displayed items

### Task 46: Collection Pagination
- Status: ⏳ pending
- Description: Add pagination to collection


### Task 47: Attribute Grouping
- Status: ⏳ pending
- Description: When collection has a "series" of some attribute, eg. there is "series of Discworld novels" (items sharing the same attribute key and value), they could be grouped. It can be enabled per collection via checkbox "enable grouping". It can be seen only by owners, and all list displays needs to respect that

### Task 48: Hidden Attributes Hint
- Status: ⏳ pending
- Description: When item has attributes which do not belong to current item type, there should be some hint that there are hidden attributes

### Task 49: Attribute Sorting
- Status: ⏳ pending
- Description: Add grouping and "sort by this attribute (or name, or status or...)"

### Task 50: Custom Item Fields
- Status: ⏳ pending
- Description: Add a field for item "Your Id" and "location"

### Task 51: Move Item Dialog UI
- Status: ⏳ pending
- Description: (Item) move dialog to another collection need some UI improvements

### Task 52: Attribute Statistics
- Status: ⏳ pending
- Description: Eventually display on top statistics from attributes (how many read, authors, etc.) and let filter with that values

### Task 53: Clickable Thumbnails
- Status: ⏳ pending
- Description: Thumbnail image (the main image for the item, should be clickable and lead to item details), same for categories

### Task 54: Mobile UI Improvements
- Status: ⏳ pending
- Description: Mobile version of the app need some UI improvements

### Task 55: JavaScript Consolidation
- Status: ⏳ pending
- Description: Compact all JavaScript to one file and reference JS from there. No inline javascript code if not necessary

---

## Task 33 Additional Requirements (Part of original Task 34)

When image is approved it should be never validated again (until I unapprove). Ensure, that when I do batch analysis the image will be not flagged. Well it can be flagged, but is is now approved, so restrictions do not apply.

When you display the image, it has to be implemented globally verify the status of this verification:
- If it is approved or not flagged: return regular image URL as it is
- For user content, when the image is flagged: return URL to 'error image'
- The same applies to thumbnails
- For SYS content moderation: normal URL but blurred, as it is now implemented

**Modifications in the view: /sys/content-moderation/**
- Keep Moderation Overview
- Keep Moderation actions
- Remove content status and recent violations
- Keep recent flagged content, but change blur to blur-sm and link user to /admin/ user page
- Remove review button and replace it with 'Approve' and 'Delete'

**Modifications in the view: /sys/content-moderation/flagged/**
- Keep the filter on top
- Instead of grid, show the table similar to the one on /sys/content-moderation/ but include these information:
  - Image (twice bigger then on /sys/content-moderation/), blurred as it is now
  - Flagged datetime
  - Its score total
  - Badges with the detection classes and their individual scores (rounded to 2 places), do not show information about bounding box - it should be like: (Female breast exposed: 0.87) (Face female: 0.85) - where () represents badge
  - Buttons: Approve to let this image go, and mark it as Approved; Delete - to delete it permanently; Ban user - to immediately ban the user in django-allauth

**Update /sys/media/ browser view:**
- Keep the filter
- Table modifications:
  - Add image thumbnail as first column
  - Merge type (collection or item) with the name, keep the information if file is Downloaded or Uploaded with the icon, add that icon description to the legend
  - In the name field show with small font file name, with clickable link which will open the image in new window, and if GCS is used link (icon) to the GCS location
  - Item/collection (trimmed to 15 chars and linked to that object) and its hash below
  - Keep size
  - Remove Storage column, move that information as an icon, next to file name
  - Change modified date to created (the moment when image was uploaded to the system)
  - Owner should be displayed as user preferred name and linked to its admin profile
  - Add content with the content management status (total score)
  - Keep status, however I do not know what that means
  - Keep actions

---

## Notes

- All completed tasks (1-36) have been verified and committed
- Tasks 37-54 are pending implementation
- Task 33 has additional requirements that need to be implemented
- When starting new tasks, follow the workflow: plan → review → implement → test → commit
