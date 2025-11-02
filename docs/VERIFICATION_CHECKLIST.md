# Verification Checklist

**Current Version:** 0.2.98
**Last Updated:** 2025-11-02
**Tasks Covered:** Task 45, Task 54, Task 57, Task 64

---

## 📋 How to Use This Checklist

This document groups **similar testing scenarios** into logical buckets for efficient testing.

**Instructions:**
1. Pick a bucket to test (Filtering, Mobile UI, Public Profiles)
2. Follow verification steps in order
3. Mark checkboxes `[ ]` → `[x]` as you complete each step
4. Write any issues in the "Issues Found" section
5. I will read your feedback and fix reported issues

---

## 🆕 Recent Updates

### ⚠️ MIGRATION REQUIRED - November 2, 2025
**Before testing v0.2.96**, run:
```bash
DJANGO_SETTINGS_MODULE=webapp.settings python manage.py makemigrations
DJANGO_SETTINGS_MODULE=webapp.settings python manage.py migrate
```

### Latest Fixes - v0.2.98 (November 2, 2025)

**NEW FIXES (v0.2.98):**
- **Icons**: Fixed invalid 'home' icon - changed to 'house' (all templates)
- **Breadcrumbs**: Added user breadcrumb to public profiles (Home > User > Collection)
- **Placeholder Images**: Removed ALL placeholder generation from Collection.save()
- **Placeholder Cleanup**: Removed 26 placeholder URLs from database
- **Stats Colors**: Yellow (warning) for favorites, green (success) for total items
- **User Card**: Removed border and shadow from public profile header
- **User Menu**: Made dropdown consistent between public and regular pages

**PREVIOUS FIXES (v0.2.97):**
- **Public Profiles**: Hash-based URLs - default `/u/<hash>/`, optional `/u/<nickname>/`
- **Hash Field**: Auto-generated 10-char nanoID for each user profile
- **URL Logic**: Both hash and nickname URLs work if nickname set
- **Dashboard**: Added "Public Profile" button in top section
- **Migration**: Auto-populates hash for existing users

**PREVIOUS FIXES (v0.2.96):**
- **Move Confirmation**: Fixed "copied" message when item was moved
- **Move/Copy Modal**: Added 3rd "Stay Here" button, refreshes on click
- **Move Icon**: Changed from 'move' to 'folder-sync'
- **Modal Buttons**: Styled with primary/secondary colors (was ghost)
- **Copy Item**: Fixed attributes error, now properly copies attribute values
- **Copy Button**: Fixed Share URL copy button
- **Public Stats**: Fixed stats cards not wrapping
- **Nickname Validation**: Form validation added (was only in model)

**PREVIOUS FIXES:**
- **v0.2.95** - Move/Copy buttons consolidated
- **v0.2.94** - Item Type modal for 100+ types
- **v0.2.93** - Mobile dropdown scrolling removed
- **v0.2.92** - Attribute value clearing fixed
- **v0.2.91** - Status filter fixed (shows all statuses)
- **v0.2.90** - Remove placeholder images command
- **v0.2.84** - Public user profiles (Task 64)

---

## 📑 Test Buckets

Jump to the section you want to test:

1. [🔍 BUCKET: Collection Filtering (Task 45)](#bucket-collection-filtering)
2. [📱 BUCKET: Mobile UI & Desktop Actions (Task 54)](#bucket-mobile-ui--desktop-actions)
3. [👤 BUCKET: Public User Profiles (Task 64)](#bucket-public-user-profiles)
4. [⚠️ Known Issue: Autocomplete (Task 57)](#known-issue-autocomplete)

# 🔍 BUCKET: Collection Filtering

**Task 45** | **Version:** 0.2.91-0.2.96 | **Status:** ✅ Fixed (re-test required)

## What Was Fixed
- **v0.2.96** - Filter panel no longer disappears when no results found
- **v0.2.92** - Attribute value clears when changing attribute
- **v0.2.91** - Status filter now shows available statuses correctly

## Test Setup
Go to a collection with diverse items:
- [x] Multiple item types (Books, Movies, etc.)
- [x] Multiple statuses (In Collection, Wanted, Reserved, etc.)
- [x] Items with attributes (e.g., Books with "Author", "Publisher")
- [x] Some items without type or attributes

---

## Part A: Individual Filters

### Status Filter
- [x] Open **Status** dropdown in filter form
- [x] ✅ **VERIFY:** Shows actual statuses ("In Collection", "Wanted", etc.) - not just "All Statuses"
- [x] Select a specific status and click **Filter**
- [x] ✅ **VERIFY:** Only items with that status displayed

### Item Type Filter
- [x] Open **Item Type** dropdown
- [x] ✅ **VERIFY:** Only types present in collection shown
- [x] ✅ **VERIFY:** "No Type" option appears if applicable
- [x] Select a type and click **Filter**
- [x] ✅ **VERIFY:** Only items of that type displayed

### Attribute Filter
- [x] Open **Filter by Attribute** dropdown
- [x] ✅ **VERIFY:** Only attributes used in collection shown
- [x] Select an attribute (e.g., "Author")
- [x] ✅ **VERIFY:** "Attribute Value" dropdown appears with all values
- [x] Select a value and click **Filter**
- [x] ✅ **VERIFY:** Only matching items shown
- [x] **Change** to different attribute
- [x] ✅ **VERIFY:** Attribute Value field clears (v0.2.92 fix)

### Search Filter
- [x] Enter text in **Search** field and click **Filter**
- [x] ✅ **VERIFY:** Results match search term

---

## Part B: Combined Filters & Persistence

- [ ] Apply ALL filters: Search + Status + Item Type + Attribute
- [ ] ✅ **VERIFY:** Items match ALL criteria (AND logic)
- [ ] Navigate to page 2 (if available)
- [ ] ✅ **VERIFY:** Filters persist in URL
- [ ] ✅ **VERIFY:** Page 2 respects all filters
- [ ] Refresh the page
- [ ] ✅ **VERIFY:** Filters still applied
- [ ] Click **Clear** button
- [ ] ✅ **VERIFY:** All filters reset, showing all items

---

## Part C: No Results Scenario (v0.2.96 FIX)

- [x] Apply filter that returns **zero results** (e.g., status that doesn't exist)
- [x] ✅ **VERIFY:** "No items match your filters" message appears
- [x] ✅ **VERIFY:** Filter panel is STILL VISIBLE (v0.2.96 fix)
- [x] ✅ **VERIFY:** Can click "Clear" to reset filters
- [x] Click **Clear**
- [x] ✅ **VERIFY:** All items shown again

---

## Seed Data for Testing
To generate test data with multiple collections and items for pagination testing:
```bash
DJANGO_SETTINGS_MODULE=webapp.settings python manage.py seed_data
```

---

## Issues Found:
```
(Write any new issues here)



```

# 📱 BUCKET: Mobile UI & Desktop Actions

**Task 54** | **Version:** 0.2.93-0.2.96 | **Status:** ✅ Fixed (re-test required)

## What Was Fixed
- **v0.2.96** - Move/Copy redesigned: single menu item, modal with 2 buttons per collection
- **v0.2.96** - Item Type modal buttons now borderless/subtle
- **v0.2.96** - Delete modal now works on mobile
- **v0.2.96** - Desktop Item Type now uses modal (consistent with mobile)
- **v0.2.96** - Copy button in Share URL section now works
- **v0.2.96** - Stats cards use flex-wrap, no rounded borders
- **v0.2.94** - Item Type uses searchable modal (not submenu)
- **v0.2.93** - Removed scrolling from mobile dropdown (opens upward)

---

## Part A: Mobile Item Actions (< 768px)

### Setup
- [x] Resize browser to mobile width (< 768px) or use device emulator
- [x] Go to any collection with items

### Dropdown Structure & Basic Actions
- [x] ✅ **VERIFY:** Only 2 visible buttons: Edit (pencil) + More (three dots)
- [x] Click **More Actions** button (three dots)
- [x] ✅ **VERIFY:** Dropdown opens **upward** (v0.2.93)
- [x] ✅ **VERIFY:** No scrolling required (v0.2.93)
- [x] ✅ **VERIFY:** Three sections: Change / Actions / Delete

### Status Submenu
- [x] Click **Status** submenu
- [x] ✅ **VERIFY:** All statuses shown, current is disabled/bold
- [x] Select different status
- [x] ✅ **VERIFY:** Item updates via HTMX

### Item Type Modal (v0.2.94/v0.2.96)
- [x] Click **Change Type**
- [x] ✅ **VERIFY:** Modal opens (not submenu)
- [x] ✅ **VERIFY:** Search box at top
- [x] ✅ **VERIFY:** Grid layout (2-4 columns), current type highlighted
- [x] ✅ **VERIFY:** Buttons are borderless/ghost style (v0.2.96 fix)
- [x] ✅ **VERIFY:** Current type has primary color
- [x] Type in search box
- [x] ✅ **VERIFY:** Instant filtering works
- [x] Click a type
- [x] ✅ **VERIFY:** Modal closes, item updates

### Move/Copy to Collection (v0.2.96 REDESIGN)
- [x] Find Actions section in dropdown
- [x] ✅ **VERIFY:** Single menu item "Move or Copy to Collection" (not two separate items)
- [x] Click **Move or Copy to Collection**
- [x] ✅ **VERIFY:** Modal opens with title "Move or Copy Item"
- [x] ✅ **VERIFY:** Each collection has TWO icon-only buttons side-by-side
- [x] Hover over first button (arrow icon)
- [x] ✅ **VERIFY:** Tooltip shows "Move here"
- [x] Hover over second button (copy icon)
- [x] ✅ **VERIFY:** Tooltip shows "Copy here"
- [x] Click **Move** button on a collection
- [x] ✅ **VERIFY:** Item moves, confirmation appears
- [x] Try **Copy** button on another collection
- [ ] ✅ **VERIFY:** Item copies, confirmation appears

### Delete Item (v0.2.96 FIX)
- [x] Click **Delete Item** from dropdown
- [x] ✅ **VERIFY:** Modal opens with "Delete Item?" title (v0.2.96 fix)
- [x] ✅ **VERIFY:** Shows item name and "cannot be undone" warning
- [x] ✅ **VERIFY:** Has Cancel and Delete buttons
- [x] Click **Cancel**
- [x] ✅ **VERIFY:** Modal closes, item not deleted

### Other Mobile Actions
- [x] Test **Manage Images** → ✅ Navigates correctly
- [x] Test **Add Attribute** → ✅ HTMX modal opens
- [x] Test **Add Link** → ✅ HTMX modal opens

---

## Part B: Desktop Actions (>= 768px)

### Layout & Functionality
- [x] Resize browser to desktop width (>= 768px)
- [x] ✅ **VERIFY:** All action buttons in horizontal row
- [x] ✅ **VERIFY:** Buttons properly grouped (btn-group)
- [x] ✅ **VERIFY:** "More Actions" dropdown is HIDDEN

### Item Type Modal (v0.2.96 FIX - Consistent with Mobile)
- [x] Click **Item Type** button (package icon)
- [x] ✅ **VERIFY:** Modal opens (v0.2.96 fix - NOT dropdown)
- [x] ✅ **VERIFY:** Same modal as mobile: search box + grid
- [x] ✅ **VERIFY:** Buttons are borderless/ghost style
- [x] Test search and selection
- [x] ✅ **VERIFY:** Works same as mobile

### Move/Copy Dropdown (v0.2.96 REDESIGN)
- [x] Click **Move** button (move icon)
- [x] ✅ **VERIFY:** Dropdown shows single "Move or Copy to Collection" item
- [x] Click the menu item
- [x] ✅ **VERIFY:** Same modal as mobile with two buttons per collection
- [x] Test Move and Copy buttons
- [x] ✅ **VERIFY:** Works same as mobile

### Other Desktop Buttons
- [x] Test **Add Attribute** → ✅ HTMX modal opens
- [x] Test **Add Link** → ✅ HTMX modal opens
- [x] Test **Status** dropdown → ✅ Shows all statuses
- [x] Test **Manage Images** → ✅ Navigates correctly
- [x] Test **Edit Item** → ✅ Navigates correctly
- [x] Test **Delete** dropdown → ✅ Shows confirmation

---

## Part C: Share URL Controls

### Copy Button (v0.2.96 FIX)
- [x] Go to PUBLIC or UNLISTED collection
- [x] Resize to mobile width (< 768px)
- [x] Find share URL section below collection name
- [x] ✅ **VERIFY:** Share URL input full width on mobile
- [x] ✅ **VERIFY:** Buttons are larger (not tiny)
- [x] ✅ **VERIFY:** Visibility badge shows icon only (text hidden)
- [x] Click **Copy** button
- [x] ✅ **VERIFY:** URL copied to clipboard (v0.2.96 fix)
- [x] ✅ **VERIFY:** Button shows checkmark briefly
- [x] Click **Open** button
- [x] ✅ **VERIFY:** Public view opens in new tab

---

## Part D: Stats Cards (v0.2.96 FIX)

### Collection Stats (Private View)
- [x] Go to any collection
- [x] Scroll to stats section (below description)
- [x] ✅ **VERIFY:** Stats cards use flex-wrap layout (v0.2.96 fix)
- [x] ✅ **VERIFY:** No rounded borders/shadow (v0.2.96 fix)
- [x] Resize browser from wide to narrow
- [x] ✅ **VERIFY:** Cards wrap as needed based on screen size

### Collection Stats (Public View)
- [x] Visit a public collection
- [x] Check stats cards
- [x] ✅ **VERIFY:** Same flex-wrap behavior
- [x] ✅ **VERIFY:** No rounded borders

---

## Issues Found:
```
### Move/Copy to Collection (v0.2.96 REDESIGN)
 - after move there is this dialog: "✅ Success!

Item successfully copied to "Smile Hear Collection"."
Few items to fix here: Make all 3 buttons in the row: [ go to new collection ] [ item details ] [ go to originall collection ]. When user decides to see originall collection, this view should be refreshed (so load paga again instead of closing the dialog). Also, when user moves object the text should be "moved" not "copied".

 - Also I do not like move item icon, find somethign else
 - I do not like how the icons are styled. Use the same styling as action buttons.

 - copy erroring with "Failed to copy item" 📱 ERROR | items.copy_item_to_collection | Error copying item 'Darkblue Modern' [12eelozfai]: 'CollectionItem' object has no attribute 'attributes'

## Part C: Share URL Controls
- public URL do not work, there is an error "Failed to copy. Please try again or copy manually."

## Part D
### Collection Stats (Public View) - stats still do not wrap

```

# 👤 BUCKET: Public User Profiles

**Task 64** | **Version:** 0.2.84-0.2.97 | **Status:** ✅ Completed (NEW URL LOGIC v0.2.97)

## What Was Implemented
- **v0.2.97** - Hash-based URLs (default `/u/<hash>/`, optional `/u/<nickname>/`)
- **v0.2.97** - Auto-generated nanoID hash for each user (10 characters)
- **v0.2.97** - Dashboard "Public Profile" button added
- **v0.2.97** - Migration to populate hash for existing users
- **v0.2.96** - Nickname validation, case-insensitive matching, lowercase storage
- **v0.2.96** - Stats cards flex-wrap layout
- **v0.2.84-0.2.90** - Public profile pages, PUBLIC-only collections, responsive design

---

## Part A: Profile URLs & Access (v0.2.97 UPDATED)

### Hash-Based URL (Always Works)
- [x] Visit your dashboard
- [x] ✅ **VERIFY:** "Public Profile" button visible in top right section (v0.2.97 NEW)
- [x] Click "Public Profile" button
- [x] ✅ **VERIFY:** Opens in new tab
- [x] Check the URL format
- [x] ✅ **VERIFY:** URL is `/u/<10-char-hash>/` (NOT numeric user ID) (v0.2.97 FIX)
- [x] Example: `/u/x9k2mP4aB1/` (10 random characters)
- [x] ✅ **VERIFY:** Profile loads correctly
- [x] Copy hash from URL
- [x] Log out
- [x] Visit same hash URL as guest
- [x] ✅ **VERIFY:** Profile still loads (hash is permanent)

### Nickname URL (Optional, Works Alongside Hash)
- [x] Set a valid nickname in account settings (e.g., "john-doe")
- [x] Save and return to dashboard
- [x] Click "Public Profile" button
- [x] ✅ **VERIFY:** URL still uses hash (primary URL)
- [x] Manually visit `/u/john-doe/`
- [x] ✅ **VERIFY:** Works! Same profile loads (v0.2.97 NEW)
- [x] Try mixed case: `/u/John-Doe/`
- [x] ✅ **VERIFY:** Works (case-insensitive)
- [x] ✅ **VERIFY:** Both URLs work simultaneously:
  - `/u/<hash>/` - Always works
  - `/u/john-doe/` - Works when nickname is set

### Nickname Validation
- [x] Go to Account Settings
- [x] Try setting nickname with **spaces** (e.g., "My Name")
- [x] ✅ **VERIFY:** Validation error shown
- [x] Try setting nickname with **special chars** (e.g., "user@123" or "user!")
- [x] ✅ **VERIFY:** Validation error shown
- [x] Set valid nickname with **mixed case** (e.g., "JohnDoe123")
- [x] Save and check
- [x] ✅ **VERIFY:** Nickname stored as lowercase "johndoe123"
- [x] Try setting duplicate nickname (use another user's nickname)
- [x] ✅ **VERIFY:** Unique constraint error

### Nickname Suggestion Banner
- [x] Clear your nickname in account settings (leave it empty)
- [x] Visit your public profile via hash URL
- [x] ✅ **VERIFY:** Banner suggests setting nickname (v0.2.97 UPDATED)
- [x] ✅ **VERIFY:** Banner includes link to account settings
- [x] Log out and visit same profile
- [x] ✅ **VERIFY:** Banner does NOT appear (only for owner)
- [x] Set a valid nickname
- [x] Visit your profile again
- [x] ✅ **VERIFY:** Banner no longer appears

### Invalid URLs
- [x] Visit `/u/nonexistent/`
- [x] ✅ **VERIFY:** 404 error page
- [x] Visit `/u/12345/` (numeric, old-style ID)
- [x] ✅ **VERIFY:** 404 error (IDs no longer used) (v0.2.97 CHANGE)
- [x] ✅ **VERIFY:** URLs never expose email addresses

---

## Part B: Profile Content & Display

### Basic Information
- [x] Visit your public profile
- [x] ✅ **VERIFY:** Display name shows correctly
- [x] ✅ **VERIFY:** Join date displays (Month Year format)
- [ ] ✅ **VERIFY:** Three statistics cards:
  - Public Collections count
  - Total Items (from public collections only)
  - Favorites (from public collections only)
- [x] ✅ **VERIFY:** Statistics are accurate

### Stats Cards (v0.2.96 FIX)
- [x] Check stats cards layout
- [x] ✅ **VERIFY:** Cards use flex-wrap (v0.2.96 fix)
- [x] ✅ **VERIFY:** No rounded borders/shadow (v0.2.96 fix)
- [x] Resize browser from wide to narrow
- [x] ✅ **VERIFY:** Cards wrap as needed

### No Placeholders
- [x] ✅ **VERIFY:** No avatar placeholder (removed v0.2.86)
- [failed] ✅ **VERIFY:** Collections without images show no placeholder
- [x] ✅ **VERIFY:** Items without images show no placeholder
- [failed] ✅ **VERIFY:** No picsum.photos or placehold.co URLs

---

## Part C: Privacy & Visibility

### Privacy Controls
- [x] Create collections with different visibility:
  - At least 2 PUBLIC
  - At least 1 UNLISTED
  - At least 1 PRIVATE
- [x] Visit your public profile
- [x] ✅ **VERIFY:** Only PUBLIC collections shown (UNLISTED/PRIVATE hidden)
- [x] Mark items as favorites in PRIVATE collections
- [x] ✅ **VERIFY:** Private favorites NOT shown on profile
- [x] Log out and visit another user's profile
- [x] ✅ **VERIFY:** Can only see their PUBLIC collections
- [x] ✅ **VERIFY:** Statistics only count PUBLIC data

---

## Part D: Navigation & Links

### Username Linking
- [x] Visit a PUBLIC collection (not your own)
- [x] Find "Owned by [username]" text
- [x] ✅ **VERIFY:** Username is clickable link with hover effect
- [x] Click username
- [x] ✅ **VERIFY:** Navigates to that user's public profile

### User Dropdown Link
- [x] Click your user avatar/menu in top navigation
- [x] ✅ **VERIFY:** "Public Profile" option with external-link icon
- [x] Click **Public Profile**
- [x] ✅ **VERIFY:** Opens in new tab showing your public profile

---

## New Tests for v0.2.98

### Breadcrumbs
- [ ] Visit a public user profile
- [ ] ✅ **VERIFY:** Breadcrumb shows "Home > {{ display_name }}"
- [ ] Visit a public collection
- [ ] ✅ **VERIFY:** Breadcrumb shows "Home > {{ owner_name }} > {{ collection_name }}"
- [ ] Click on owner name in breadcrumb
- [ ] ✅ **VERIFY:** Navigates to owner's public profile

### Placeholder Images (v0.2.98 FIX)
- [ ] Create a new collection without adding an image
- [ ] Save the collection
- [ ] ✅ **VERIFY:** No placeholder image is generated (image_url is empty)
- [ ] ✅ **VERIFY:** Collection shows without any image (no placehold.co URLs)
- [ ] Visit public collections
- [ ] ✅ **VERIFY:** No placehold.co, picsum.photos, or any placeholder URLs anywhere

### Stats Colors (v0.2.98 FIX)
- [ ] Visit your public profile
- [ ] Check stats card colors
- [ ] ✅ **VERIFY:** "Total Items" uses green (text-success)
- [ ] ✅ **VERIFY:** "Favorites" uses yellow (text-warning)
- [ ] ✅ **VERIFY:** "Public Collections" uses primary color

### User Card Styling (v0.2.98 FIX)
- [ ] Visit your public profile
- [ ] Check the main user info card
- [ ] ✅ **VERIFY:** No border around the card
- [ ] ✅ **VERIFY:** No shadow (shadow-lg removed)
- [ ] ✅ **VERIFY:** Clean, flat appearance

### User Dropdown Consistency (v0.2.98 FIX)
- [ ] Log in and visit a public collection page
- [ ] Click user avatar dropdown
- [ ] ✅ **VERIFY:** Menu includes:
  - Dashboard
  - Your Collections
  - My Locations (v0.2.98 NEW)
  - Public Profile (v0.2.98 NEW)
  - Account Settings
  - Manage Emails
  - Change Password
  - Logout
- [ ] Now visit your regular dashboard
- [ ] Click user avatar dropdown
- [ ] ✅ **VERIFY:** Same menu items appear (consistency)

## Issues Found:
```
(Write any new issues here)
```

---

# ⚠️ Known Issue: Autocomplete

**Task 57** | **Version:** 0.2.77 | **Status:** ⚠️ Needs Reimplementation

## Known Issue

**The current autocomplete implementation does not work.**

**Requested Solution:** Reimplement using Location field technique (Task 50):
- Combobox pattern with hidden inputs
- Visible search field
- HTMX endpoint
- JavaScript handlers

**Impact:** Users cannot autocomplete attribute values when adding/editing attributes.

**Skip testing this until reimplemented.**

---

# 📋 Cross-Cutting Tests

## Responsive Testing
Test each bucket at multiple widths to ensure layouts adapt correctly:

- [x] **320px** (small phone) - Mobile layouts, no horizontal scrolling
- [x] **375px** (iPhone SE) - Standard mobile experience
- [x] **768px** (tablet) - Breakpoint where mobile/desktop switch occurs
- [x] **1024px** (desktop) - Standard desktop layout
- [x] **1920px** (large desktop) - Wide screen layouts

## Browser Testing
Test core functionality in each browser:

- [x] **Chrome/Edge** (latest) - Primary browser
- [x] **Firefox** (latest) - Gecko engine
- [x] **Safari** (latest) - WebKit engine

---

## 📊 Testing Summary

**Tester:** ___________
**Date:** ___________

### Results by Bucket

| Bucket | Status | Issues Count |
|--------|--------|--------------|
| 🔍 Collection Filtering | ⬜ Pass / ⬜ Fail / ⬜ Pass with Issues | ___ |
| 📱 Mobile UI & Desktop | ⬜ Pass / ⬜ Fail / ⬜ Pass with Issues | ___ |
| 👤 Public User Profiles | ⬜ Pass / ⬜ Fail / ⬜ Pass with Issues | ___ |

**Overall Status:** ⬜ Pass / ⬜ Fail / ⬜ Pass with Issues

---

## 🔄 Workflow

1. **Pick a bucket** to test (Filtering, Mobile UI, or Public Profiles)
2. **Follow steps** in order, mark checkboxes as you go
3. **Document issues** in "Issues Found" sections
4. **Submit feedback** - I will read this file and fix reported issues
5. **Re-test** after fixes are deployed
6. **Repeat** until all buckets pass

**Note:** Test one bucket at a time for better focus and faster feedback cycles.
