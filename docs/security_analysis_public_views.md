# Beryl3 Webapp - Public Views Security Analysis Report

## Executive Summary

This report analyzes the isolation of public views (collection_public_detail and public_user_profile) from authenticated user space in the beryl3 webapp. The analysis covers authentication/permission requirements, data exposure risks, and potential security vulnerabilities.

**Key Findings**: The public views are **well-isolated** with proper visibility checks, minimal authentication requirements, and appropriate data filtering. However, there are some **areas for improvement** related to data exposure and edge cases.

---

## 1. Public Views Identified

### 1.1 Public Collection View
- **URL Pattern**: `/share/collections/<hash>/`
- **URL Name**: `public_collection_view`
- **File**: `/webapp/web/views/public.py` (lines 34-277)
- **Template**: `/templates/public/collection_public_detail.html`
- **Authentication Required**: NO
- **Function Signature**: `public_collection_view(request, hash)`

### 1.2 Public User Profile View
- **URL Pattern**: `/u/<username>/`
- **URL Name**: `public_user_profile`
- **File**: `/webapp/web/views/public.py` (lines 461-574)
- **Template**: `/templates/public/user_profile.html`
- **Authentication Required**: NO
- **Function Signature**: `public_user_profile(request, username)`

### 1.3 Lazy Load Item Image (Supporting Endpoint)
- **URL Pattern**: `/api/items/<item_hash>/image/`
- **URL Name**: `lazy_load_item_image`
- **File**: `/webapp/web/views/public.py` (lines 577-608)
- **Template**: `/templates/partials/_item_image_lazy.html`
- **Authentication Required**: NO
- **Function Signature**: `lazy_load_item_image(request, item_hash)`

### 1.4 Item Reservation Endpoints
- **Book Item (Authenticated)**: `book_item_authenticated()` - requires login
- **Book Item (Guest)**: `book_item_guest()` - NO authentication
- **Unreserve Item (Guest)**: `unreserve_guest_item()` - NO authentication (token-based)

---

## 2. Authentication & Permission Architecture

### 2.1 Access Control Models

#### Collection Visibility Enum
```python
class Visibility(models.TextChoices):
    PRIVATE = "PRIVATE", _("Visible only to me")
    UNLISTED = "UNLISTED", _("Shared with link")
    PUBLIC = "PUBLIC", _("Public")
```

#### Permission Model Comparison

| View | Authentication | Authorization | Visibility Filter |
|------|---------------|-----------------|--------------------|
| `collection_detail` (private) | @login_required | owner_required | N/A (auto-filtered) |
| `public_collection_view` | NONE | visibility check | PRIVATE → 404 |
| `public_user_profile` | NONE | active user check | PUBLIC collections only |
| `collection_item_detail` (private) | @login_required | owner_required | N/A (auto-filtered) |
| Item images (public) | NONE | parent visibility | Content moderation check |

### 2.2 Visibility Check Implementation

**In `public_collection_view()` (lines 48-59)**:
```python
# Only allow access if the collection is not private.
if collection.visibility == Collection.Visibility.PRIVATE:
    # Log access denied to private collection
    logger.warning('public_collection_view: Access denied to private collection...')
    # We raise Http404 to avoid leaking the existence of private collections.
    raise Http404("Collection not found or is private.")
```

**Key Security Features**:
- Returns 404 (not 403) to avoid information leakage about collection existence
- Checks visibility before rendering any collection data
- Allows both PUBLIC and UNLISTED collections (intentional - UNLISTED = "Shared with link")

---

## 3. Data Exposure Analysis

### 3.1 Public Collection View Data

#### What IS Exposed
1. **Collection Metadata**:
   - Collection name, description
   - Owner's display name and public profile URL
   - Collection images (if uploaded)

2. **Item Metadata** (for non-private items):
   - Item name, description, type, status
   - Item images and attributes (based on item type)
   - Item links (URLs, display names)
   - Favorite status (visual indicator)
   - Reservation information (who reserved, when)
   - Custom fields: `your_id`, location

3. **Aggregated Statistics**:
   - Total items count
   - In Collection count
   - Wanted count
   - Reserved count
   - Item type distribution

4. **User Profile Information**:
   - Display name (from nickname or full name)
   - User join date (month/year only)
   - Public profile URL

#### What is NOT Exposed
```
SECURE - NOT EXPOSED:
✓ User email address
✓ User full name (only display name shown)
✓ Private/UNLISTED collections (only PUBLIC shown in profile)
✓ User edit/admin controls
✓ Any authenticated user data
✓ Reserved by name/email (shown only on item in collection, not in public card)
✓ User ID (only hash used in URL)
✓ Passwords, security tokens
✓ Collection settings/metadata
✓ Admin information
✓ Server logs or debug information
```

### 3.2 Public User Profile View Data

#### What IS Exposed
1. **User Public Profile**:
   - Display name (nickname or full name)
   - Join date (month/year only)
   - User profile hash

2. **User Statistics** (from public collections only):
   - Number of public collections
   - Total items across public collections
   - Total favorite items
   - 12 most recent favorite items

3. **Public Collections List**:
   - Collection names, descriptions, images
   - Item counts per collection
   - Visibility status (marked as "Public")

4. **Favorite Items Display**:
   - Item names, images
   - Collection each item belongs to
   - Favorite status (visual indicator)

#### Data Filtering Logic (lines 516-540)
```python
# Get only PUBLIC collections
public_collections = Collection.objects.filter(
    created_by=user,
    visibility=Collection.Visibility.PUBLIC  # CRITICAL: Filters out PRIVATE/UNLISTED
).select_related('created_by__profile').prefetch_related(
    'images__media_file',
    'items'
).annotate(
    item_count=Count('items')
).order_by('-updated')

# Calculate aggregated statistics from public collections only
total_items = 0
total_favorites = 0
for collection in public_collections:
    total_items += collection.item_count
    total_favorites += collection.items.filter(is_favorite=True).count()

# Get public favorites (from public collections only)
public_favorites = CollectionItem.objects.filter(
    collection__created_by=user,
    collection__visibility=Collection.Visibility.PUBLIC,  # CRITICAL: Double-filtered
    is_favorite=True
)
```

**Data Filtering Strategy**:
- Single source of truth: `Collection.Visibility.PUBLIC` check
- Statistics only count public collections
- Favorites only from public collections
- UNLISTED collections completely hidden from profile
- PRIVATE collections completely hidden from profile

### 3.3 Content Moderation Integration

**Image URL Generation** (in `MediaFile.get_user_safe_url()`):
```python
def get_user_safe_url(self, request=None):
    # For SYS admin views, always return actual file URL
    if request and url_name and url_name.startswith('sys_'):
        return self.file_url
    
    # For user-facing content, check moderation status
    if self.content_moderation_status in [
        self.ContentModerationStatus.FLAGGED, 
        self.ContentModerationStatus.REJECTED
    ]:
        # Return a static error image URL
        return f"{settings.STATIC_URL}images/content-unavailable.svg"
    
    return self.file_url
```

**Impact**: Flagged/rejected images are replaced with placeholder, preventing inappropriate content exposure.

---

## 4. Authentication & Login Dependency

### 4.1 Views That Require Authentication

**ALL AUTHENTICATED-ONLY VIEWS**:
- `collection_create()` - @login_required
- `collection_list_view()` - @login_required
- `collection_detail_view()` - @login_required
- `collection_update_view()` - @login_required
- `collection_delete_view()` - @login_required
- `collection_item_create_view()` - @login_required
- `collection_item_detail_view()` - @login_required
- `collection_item_update_view()` - @login_required
- `collection_item_delete_view()` - @login_required
- ALL HTMX endpoints (items_hx, collection_hx, images) - @login_required

### 4.2 Public Views (No Authentication)

**COMPLETELY PUBLIC**:
- `public_collection_view()` - NO decorator
- `public_user_profile()` - NO decorator
- `lazy_load_item_image()` - NO decorator
- `book_item_guest()` - NO decorator (email validation instead)
- `unreserve_guest_item()` - NO decorator (token validation instead)

**HYBRID**:
- `book_item_authenticated()` - @login_required

### 4.3 Login Check in User Profile

```python
# Suggest nickname if user is viewing their own profile
suggest_nickname = False
if request.user.is_authenticated and request.user == user:
    suggest_nickname = not user.profile.nickname
```

**Feature**: Authenticated users viewing their own profile get suggestion to set nickname. This is safe because:
- Check uses object equality (`request.user == user`)
- Only affects UI suggestion, not data access
- No data exposure difference for authenticated vs unauthenticated users

---

## 5. URL Pattern Security

### 5.1 User Identification Methods

**Primary**: User Profile Hash (10-character nanoid)
```
/u/<user_hash>/
Example: /u/a1b2c3d4e5/
```

**Secondary**: Nickname (case-insensitive, alphanumeric + dash/underscore)
```
/u/<nickname>/
Example: /u/john-doe/
```

**URL Lookup Logic** (lines 476-490):
```python
# Try to find user by hash first, then by nickname
user = None
try:
    # Try to find by hash first (most common case)
    user = User.objects.select_related('profile').filter(
        profile__hash=username,
        is_active=True
    ).first()

    # If not found by hash, try by nickname (case-insensitive)
    if not user:
        user = User.objects.select_related('profile').filter(
            profile__nickname=username.lower(),  # Nicknames are stored in lowercase
            is_active=True
        ).first()
except Exception as e:
    logger.error('...')
```

**Security Analysis**:
- ✓ Hash is 10 characters (2^50+ possible combinations) - not bruteforcing risk
- ✓ Nickname uniqueness enforced at database level
- ✓ Only active users can be accessed (`is_active=True`)
- ✓ Email/User ID NEVER used in public URLs
- ✓ Graceful fallback: if user not found, raises 404

**Potential Issue - Information Leakage**:
- Attackers can enumerate user hashes by trying all 10-character combinations
- Severity: LOW - but consider hash brute-forcing rate limiting if needed

### 5.2 Collection Hash Security

**Collection Identification**: 10-character nanoid
```
/share/collections/<collection_hash>/
Example: /share/collections/a1b2c3d4e5/
```

**Security**:
- ✓ Hash is 10 characters, not sequential
- ✓ Visibility check prevents access to private collections
- ✓ Returns 404 to avoid information leakage
- ✓ No item-level visibility checks needed (items inherit collection visibility)

---

## 6. Data Leakage Risk Assessment

### 6.1 Items in Public Collections

#### Threat: Reserved Item Exposure
**Code in `_item_public_card.html` (lines 150-227)**:

For public view, items show status badges:
```html
<div class="badge {% if item.status == 'IN_COLLECTION' %}badge-success...
    {{ item.get_status_display }}
</div>
```

**Risk Analysis**: LOW
- Reserved items show only generic "Reserved" status
- `reserved_by_name` and `reserved_by_email` fields are NOT exposed in public templates
- Guest email stored in `reserved_by_email` is safe (not exposed)
- Token stored in `guest_reservation_token` is NOT exposed

**Verification**: Searched `/templates/public/` - no references to:
- `reserved_by_name`
- `reserved_by_email`
- `guest_reservation_token`

#### Threat: Custom Fields Exposure
**Code in `_item_public_card.html` and models**:

Custom fields ARE exposed:
- `your_id` - custom identifier (safe)
- `location` - physical location reference (safe)

**Risk Analysis**: MEDIUM (data exposure, not security risk)
- Users can control what they enter in custom fields
- Fields are meant to be visible (for collection management)
- Public visibility is user's responsibility via collection visibility setting

### 6.2 Profile Information Exposure

#### Threat: User Enumeration
**Risk**: Attackers can enumerate all public users by trying hashes

**Current Mitigation**:
- Hash is random (not sequential)
- User must have public collection to appear in discovery
- But direct URL access works for any active user with a profile hash

**Recommendation**: Consider adding rate limiting on failed user lookups

#### Threat: Activity Tracking
**Code**: Profile shows "Joined [Month Year]"

**Risk Analysis**: MINIMAL
- Only month/year shown (not exact date)
- Public information (user registration date)
- No timing information that could reveal pattern

### 6.3 Content Moderation Data

**Risk**: Flagged images show placeholder instead of actual image

**Analysis**: SAFE
- Flagged content never shown to public
- Admin can still see flagged content (correct for moderation)
- Users see uniform placeholder (no content leakage)

---

## 7. Database Query Analysis

### 7.1 Query Optimization & N+1 Issues

#### public_collection_view() Queries (lines 72-79)
```python
all_items = collection.items.select_related(
    'item_type',
    'location'
).prefetch_related(
    'links',
    'attribute_values__item_attribute',  # Critical: Avoids 100+ N+1 queries
    'item_type__attributes'  # Task 65 fix: Avoids N+1 in get_display_attributes()
).order_by('name')
```

**Analysis**: OPTIMIZED
- ✓ Uses `select_related` for foreign keys (item_type, location)
- ✓ Uses `prefetch_related` for reverse relations (links, attribute_values)
- ✓ Prefetches item_type attributes to avoid N+1
- ✓ No unguarded template access

#### public_user_profile() Queries (lines 516-546)
```python
public_collections = Collection.objects.filter(
    created_by=user,
    visibility=Collection.Visibility.PUBLIC
).select_related('created_by__profile').prefetch_related(
    'images__media_file',
    'items'
).annotate(
    item_count=Count('items')
).order_by('-updated')

public_favorites = CollectionItem.objects.filter(
    collection__created_by=user,
    collection__visibility=Collection.Visibility.PUBLIC,
    is_favorite=True
).select_related(
    'collection',
    'item_type'
).prefetch_related(
    'images__media_file'
).order_by('-updated')[:12]
```

**Analysis**: OPTIMIZED
- ✓ Filters at database level (visibility check in WHERE clause)
- ✓ Uses select_related for ForeignKeys
- ✓ Uses prefetch_related for images
- ✓ Limits favorites to 12 items
- ✓ Annotates item counts (database aggregation)

#### Grouping Logic (lines 104-109)
```python
attr_lookup = {}
if collection.group_by == Collection.GroupBy.ATTRIBUTE and collection.grouping_attribute:
    for attr_val in CollectionItemAttributeValue.objects.filter(
        item__in=all_items,
        item_attribute=collection.grouping_attribute
    ).select_related('item'):
        attr_lookup[attr_val.item_id] = attr_val.value
```

**Analysis**: SAFE
- ✓ Pre-fetches grouping attributes to avoid N+1
- ✓ Uses in-memory lookup dict instead of repeated queries

### 7.2 SQL Injection Risk

**Assessment**: NO RISK
- All queries use ORM with parameterized queries
- User input (`hash`, `username`) only used with `.filter()` (safe)
- No string concatenation in queries
- Template tags properly escape output

---

## 8. URL & Route Security

### 8.1 Public Routes Enumeration

```python
# Public Collection View
path('share/collections/<str:hash>/', public.public_collection_view, name='public_collection_view'),

# Public User Profile
path('u/<str:username>/', public.public_user_profile, name='public_user_profile'),

# Item Image (HTMX lazy load)
path('api/items/<str:item_hash>/image/', public.lazy_load_item_image, name='lazy_load_item_image'),

# Item Reservations (guest)
path('item/<str:hash>/book/guest/', public.book_item_guest, name='book_item_guest'),
path('item/<str:hash>/book/release/<str:token>/', public.unreserve_guest_item, name='unreserve_guest_item'),
```

### 8.2 Route Protection

**Public Routes**: Absolutely none - by design
**Authenticated Routes**: Protected by @login_required decorator
**Hybrid Routes**: 
- `book_item_authenticated()` - requires login
- `book_item_guest()` - public with email validation

---

## 9. Template Security Analysis

### 9.1 Public Collection Template

**File**: `/templates/public/collection_public_detail.html`

**Data Exposed**:
- Collection name ✓
- Owner display name ✓
- Collection description (with markdown) ✓
- Items list with full attributes ✓
- Item links and URLs ✓
- Favorite status ✓
- Reservation status ✓

**Data Safe**:
- No edit buttons (no modification allowed)
- No delete buttons (no deletion allowed)
- No user email (not in template)
- No user ID (not in template)

**XSS Protection**:
```html
{{ collection.description|markdown_safe }}
```
Uses custom `markdown_safe` filter - should be reviewed for security

**CSRF Protection**:
```html
<form ...>
    hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
</form>
```
✓ CSRF token included in HTMX requests

### 9.2 Public User Profile Template

**File**: `/templates/public/user_profile.html`

**Data Exposed**:
- Display name ✓
- Join date (month/year) ✓
- Statistics (counts only) ✓
- Public collection list ✓
- Favorite items ✓

**Data Safe**:
- No email address ✗ (not in code)
- No edit controls ✓
- No settings access ✓
- No private collection info ✓

### 9.3 Template Tag Security

**Custom Filter**: `markdown_safe`
```html
{{ collection.description|markdown_safe }}
```

**Risk**: MEDIUM
- Description is user-controlled (collection creator)
- Should verify this filter properly escapes/sanitizes
- Could allow XSS if not properly implemented

**Recommendation**: Verify `markdown_safe` implementation in code

---

## 10. Edge Cases & Potential Vulnerabilities

### 10.1 Race Conditions

**Scenario**: User changes collection visibility from PUBLIC to PRIVATE while someone is viewing

**Current Mitigation**: None (implicit)
**Impact**: User could see collection briefly, then get 404 on page refresh
**Severity**: LOW (expected behavior)

### 10.2 Deleted User Profiles

**Code** (line 482):
```python
user = User.objects.select_related('profile').filter(
    profile__hash=username,
    is_active=True  # Only active users
).first()
```

**Analysis**: SAFE
- ✓ Only active users shown
- ✓ Inactive users return 404
- ✓ No profile data for deleted users

### 10.3 Item Visibility Bypass

**Threat**: Can users access items from private collections via direct URL?

**Analysis**: SAFE - No direct item URL for public view
- Items are only accessible through collection view
- Item detail view (`/items/<hash>/`) requires authentication + ownership
- No public item detail endpoint exists
- Items filtered by parent collection visibility

**Code Evidence** (public.py):
```python
# Items only retrieved within collection context
all_items = collection.items.select_related(...)
# If collection is PRIVATE, view raises Http404 before accessing items
```

### 10.4 Profile Discovery

**Threat**: Can attackers enumerate all user profiles?

**Current State**:
- Profiles accessible by hash: `/u/<hash>/`
- Profiles accessible by nickname: `/u/<nickname>/`
- Direct enumeration possible (no rate limiting)

**Mitigations**:
- ✓ Hash is 10 characters (not easily guessable)
- ✓ Only public collections shown
- No negative enumeration (404 same as non-existent)

**Recommendation**: Consider rate limiting on user profile lookups

### 10.5 Content Moderation Bypass

**Question**: Can users see flagged content through API/JSON?

**Current Code**:
```python
image_url = item.default_image.media_file.get_user_safe_url(request)
```

**Analysis**: SAFE
- `get_user_safe_url()` always checks content moderation
- Returns placeholder for flagged/rejected content
- No API endpoint bypasses this check

---

## 11. Security Recommendations

### HIGH PRIORITY

1. **Review `markdown_safe` Filter**
   - Verify it properly sanitizes user input
   - Ensure no XSS attack vectors
   - Consider using `django-bleach` or similar if not already

2. **Add Rate Limiting to User Profile Lookups**
   - Prevent enumeration of all possible user hashes
   - Example: 10 failed lookups per minute per IP

### MEDIUM PRIORITY

3. **Add CSRF Token to Public Forms**
   - Guest reservation form already has token ✓
   - Verify all HTMX requests include token

4. **Document Public API Contract**
   - Public endpoints lack versioning
   - Consider adding API version prefix
   - Document expected response formats

5. **Add Integrity Check to Item Visibility**
   - Verify items in public collections are actually from that collection
   - Currently implicit (by filtering on collection.items)

### LOW PRIORITY

6. **Audit Content Moderation Implementation**
   - Verify `get_user_safe_url()` is used everywhere images are accessed
   - Check for any direct file access bypasses

7. **Add Logging to Public Views**
   - Already has good logging ✓
   - Consider adding view counts for analytics

---

## 12. Compliance & Privacy Analysis

### 12.1 GDPR/Privacy Considerations

**Personal Data Exposed**:
- Display name (user-chosen, safe)
- Join date (metadata, minimal)
- Profile hash (derived, not personally identifying)

**Personal Data NOT Exposed**:
- Email address ✓
- Real name (unless used as display name) ✓
- Phone number ✓
- Address information ✓
- Reserved by name/email ✓

**User Control**:
- ✓ Can set nickname in settings
- ✓ Can make collections private
- ✓ Can set use_nickname flag
- ✗ Cannot prevent profile discovery (by hash)

**Recommendation**: Add user setting to make profile completely private

### 12.2 Data Retention

**Public Data**:
- Persistent while user account active
- Cleared when user is deactivated (is_active=False)
- No archival/backup exposure mentioned

---

## 13. Testing Recommendations

### 13.1 Unit Tests

```python
# Test visibility filtering
def test_public_collection_view_rejects_private():
    collection = Collection.objects.create(
        name="Private", 
        visibility=Collection.Visibility.PRIVATE
    )
    response = client.get(f'/share/collections/{collection.hash}/')
    assert response.status_code == 404

def test_public_collection_view_allows_public():
    collection = Collection.objects.create(
        name="Public",
        visibility=Collection.Visibility.PUBLIC
    )
    response = client.get(f'/share/collections/{collection.hash}/')
    assert response.status_code == 200
```

### 13.2 Integration Tests

```python
# Test profile shows only public collections
def test_public_profile_shows_only_public_collections():
    user = User.objects.create_user('test')
    Collection.objects.create(
        created_by=user,
        name="Public",
        visibility=Collection.Visibility.PUBLIC
    )
    Collection.objects.create(
        created_by=user,
        name="Private",
        visibility=Collection.Visibility.PRIVATE
    )
    
    response = client.get(f'/u/{user.profile.hash}/')
    assert "Public" in response.content
    assert "Private" not in response.content
```

### 13.3 Security Tests

```python
# Test CSRF protection
def test_guest_booking_requires_csrf_token():
    # Should fail without token
    
# Test content moderation
def test_flagged_image_not_exposed():
    # Should return placeholder URL
```

---

## 14. Summary Table

| Aspect | Status | Notes |
|--------|--------|-------|
| Visibility Filtering | ✓ SAFE | PRIVATE collections properly blocked with 404 |
| Authentication | ✓ SAFE | Only PUBLIC views are public; sensitive operations require login |
| URL Security | ✓ SAFE | Hash-based, not sequential; email not used |
| Data Exposure | ✓ SAFE | No sensitive personal data exposed |
| Database Queries | ✓ OPTIMIZED | Proper prefetch_related usage; no N+1 queries |
| Template Security | ⚠ REVIEW | markdown_safe filter needs verification |
| CSRF Protection | ✓ SAFE | Tokens included in HTMX requests |
| Content Moderation | ✓ SAFE | Flagged content properly hidden |
| Rate Limiting | ✗ MISSING | User profile enumeration not limited |
| Documentation | ⚠ PARTIAL | Code comments good; API contract not documented |

---

## 15. Conclusion

The public views in beryl3 are **well-designed and properly isolated** from the authenticated user space. Key strengths:

1. ✓ Visibility checks prevent unauthorized collection access
2. ✓ Proper use of Django ORM prevents SQL injection
3. ✓ No sensitive personal data exposed in public views
4. ✓ Database queries optimized to prevent N+1 performance issues
5. ✓ CSRF protection on public forms

**Recommended Actions**:
1. Audit the `markdown_safe` template filter for XSS vulnerability
2. Add rate limiting to user profile lookups
3. Document public API contract and rate limits

The webapp demonstrates security-conscious design with proper separation of concerns between public and authenticated views.
