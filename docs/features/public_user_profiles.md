# Public User Profiles

## Overview

Each user has a public profile page that displays their public collections, statistics, and favorite items. The profile is accessible via a unique URL that uses either the user's profile hash or optional nickname.

## URL Structure

### Default URL (Always Available)
- Format: `/u/<hash>/`
- Example: `/u/x9k2mP4aB1/`
- The hash is a unique 10-character nanoID automatically generated for each user profile
- This URL is always available for all users

### Nickname URL (Optional)
- Format: `/u/<nickname>/`
- Example: `/u/john-doe/`
- Only available if user has set a nickname in account settings
- Nickname is case-insensitive (stored as lowercase, lookup is case-insensitive)
- Nickname can only contain: letters, digits, dash (-), and underscore (_)
- Nickname must be unique across all users

## URL Access Logic

When accessing `/u/<username>/`:
1. System first tries to find user by profile hash (exact match)
2. If not found, tries to find user by nickname (case-insensitive match)
3. If neither found, returns 404

Both URLs work simultaneously if user has a nickname set:
- `/u/<hash>/` - Always works
- `/u/<nickname>/` - Works if nickname is set

## Accessing Public Profile

### From User Dropdown Menu
- Visible when logged in
- Link labeled "Public Profile" with external link icon
- Opens in new tab

### From Dashboard
- Button in top right section: "Public Profile"
- Opens in new tab

### From Public Collections
- Username links on public collection pages
- Clicking username takes you to their public profile

## What's Displayed

### User Information
- Display name (nickname if set, otherwise full name or email prefix)
- Join date (month and year only)

### Statistics
- Number of public collections
- Total items across public collections
- Number of favorite items (from public collections only)

### Collections List
- Only PUBLIC collections are shown
- UNLISTED and PRIVATE collections are hidden
- Each collection shows:
  - Collection name
  - Description (truncated)
  - Item count
  - Collection image (if available)
  - Link to public collection view

### Favorite Items
- Items marked as favorite from public collections
- Displayed as image grid
- Links to the collection containing the item

## Setting Up Nickname

### Via Account Settings
1. Navigate to Account Settings from user dropdown
2. Find "Nickname" field
3. Enter desired nickname (letters, digits, dash, underscore only)
4. Check "Use Nickname for Display" to use nickname as display name
5. Save settings

### Validation Rules
- Required format: letters, digits, dash (-), underscore (_) only
- Case-insensitive uniqueness check
- Automatically converted to lowercase on save
- Shows error if nickname is already taken
- Shows error if invalid characters are used

### Suggestion Banner
- If user views their own profile and has no nickname set
- Banner suggests setting up custom URL via account settings
- Only shown to the profile owner, not other visitors

## Privacy Considerations

### What's Public
- User's display name
- Join date (month and year)
- PUBLIC collections and their contents
- Favorite items from PUBLIC collections
- Statistics based on PUBLIC collections only

### What's Private
- User's email address (never shown)
- User's numeric ID (never used in URLs)
- PRIVATE and UNLISTED collections
- Items from private/unlisted collections
- Statistics from private/unlisted collections
- Personal settings and preferences

## Implementation Details

### Model: UserProfile
- `hash` field: CharField(max_length=10, unique=True, blank=True)
  - Auto-generated using nanoID (size=10)
  - Generated on save if not present
  - Used for default public URL

- `nickname` field: CharField(max_length=50, unique=True, blank=True, null=True)
  - Optional user-defined nickname
  - Validated for allowed characters
  - Converted to lowercase on save
  - Used for optional pretty URL

- `use_nickname` field: BooleanField(default=False)
  - Controls whether nickname is used as display name
  - Independent of whether nickname URL works

### View: public_user_profile
- URL pattern: `/u/<str:username>/`
- Tries hash match first (faster, most common)
- Falls back to nickname match (case-insensitive)
- Returns 404 if no match found
- Only shows PUBLIC collections and related data

### Method: get_public_profile_url()
- Always returns URL using hash
- Ensures consistent, stable URLs
- Nickname URL works as alternative if set

## Migration Process

1. **0034_add_user_profile_hash.py**
   - Adds `hash` field to UserProfile
   - Field is blank=True to allow gradual population

2. **0035_populate_user_profile_hashes.py**
   - Data migration to populate hash for existing users
   - Generates unique 10-character nanoIDs
   - Ensures no duplicate hashes

## Testing Checklist

- [ ] User without nickname can access profile via hash URL
- [ ] User with nickname can access profile via both hash and nickname URLs
- [ ] Nickname URLs are case-insensitive (/u/John/ and /u/john/ both work)
- [ ] Invalid nicknames are rejected in account settings
- [ ] Duplicate nicknames are rejected
- [ ] Public profile link appears in user dropdown
- [ ] Public profile link appears on dashboard
- [ ] Only PUBLIC collections are shown on profile
- [ ] Statistics reflect only PUBLIC collections
- [ ] Favorite items from private collections are hidden
- [ ] Suggestion banner shows when user has no nickname (viewing own profile)
- [ ] Suggestion banner doesn't show to other visitors
- [ ] Email and user ID are never exposed in URLs or UI
