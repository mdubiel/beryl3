# Task 33: Implement Content Moderation with Nudity Detection

**Status:** ✅ Completed (Additional requirements pending)
**Verified:** Yes
**Commit ID:** 3ea305a

## Task Description

Implement nudity detection in the images. Implement feature flag how to handle this detection. This flag should have the following levels: "flag only", "delete", "soft ban", "hard ban".

## Implementation Summary

### Core Features Implemented

1. **Content Moderation System**
   - Nudity detection using AI/ML service
   - Automatic image scanning on upload
   - Configurable moderation actions via feature flags

2. **Feature Flag Levels**
   - **Flag Only:** Image flagged, reported in SYS dashboard, user not affected
   - **Delete:** Image removed, user notified, logged
   - **Soft Ban:** Delete + increment misuse counter, ban at threshold
   - **Hard Ban:** Immediate permanent ban on first violation

3. **Database Models Enhanced**
   - Added `content_moderation_status` field to MediaFile model
   - Added `misuse_counter` field to User model
   - Added `is_banned` status integration with django-allauth

4. **SYS Dashboard Features**
   - `/sys/content-moderation/` - Main moderation dashboard
   - Batch processing capability for existing images
   - User, item, image, findings table display
   - Last check timestamp tracking

5. **User Notifications**
   - Upload forms show validation notices
   - Point to terms of service (regulamin aplikacji)
   - Clear messaging about content policies

### Technical Implementation

**MediaFile Model Enhancement:**
```python
# Fields added:
- content_moderation_status (choices: PENDING, APPROVED, FLAGGED, REJECTED)
- moderation_score (decimal)
- moderation_findings (JSON)
- last_moderation_check (datetime)
```

**User Model Enhancement:**
```python
# Fields added:
- misuse_counter (integer, default=0)
- is_banned (boolean, default=False)
- ban_reason (text)
- banned_at (datetime)
```

**Feature Flags:**
```python
CONTENT_MODERATION_ACTION = [
    'flag_only',
    'delete',
    'soft_ban',
    'hard_ban'
]
SOFT_BAN_THRESHOLD = 3  # Configurable
```

### Moderation Workflow

1. **On Upload:**
   - Image uploaded by user
   - Automatic moderation scan triggered
   - Results stored in MediaFile model
   - Action taken based on feature flag

2. **Flag Only Mode:**
   - Image marked as FLAGGED
   - Admin notified in SYS dashboard
   - User can continue using app
   - Image remains visible to user

3. **Delete Mode:**
   - Image immediately removed
   - User receives notification
   - Activity logged
   - No ban applied

4. **Soft Ban Mode:**
   - Image deleted
   - User notified
   - Misuse counter incremented
   - If counter >= threshold: permanent ban
   - Activity logged with structured logging

5. **Hard Ban Mode:**
   - Image deleted
   - User immediately banned
   - Ban integrated with django-allauth
   - Cannot login
   - Activity logged

### Batch Processing

**Location:** `/sys/content-moderation/batch/`

**Features:**
- Process all existing images
- Batch size configurable
- Progress tracking
- Skip already checked images (optional)
- Results summary

**Table Display:**
- User (owner of image)
- Item (collection item)
- Image (thumbnail with blur)
- Findings (moderation results)
- Last check (timestamp)
- Actions (approve/delete/ban user)

### Django-Allauth Integration

**Banning Implementation:**
```python
# User model
user.is_active = False  # Prevents login
user.is_banned = True
user.ban_reason = "Content policy violation"
user.banned_at = timezone.now()
user.save()
```

**Login Prevention:**
- Custom adapter checks `is_banned` flag
- Banned users cannot login
- Clear error message displayed
- Admin intervention required to unban

### Files Modified
- `web/models.py` - MediaFile and User model enhancements
- `web/views/sys.py` - Moderation dashboard views
- `web/views/items.py` - Image upload handling
- `templates/sys/content_moderation.html` - Dashboard template
- `templates/sys/content_moderation_batch.html` - Batch processing
- `templates/partials/_image_upload_notice.html` - User notices
- `web/adapters.py` - django-allauth custom adapter

### Big Model Approach

All image verification logic placed in MediaFile model (following "big models, small views" concept):
- `check_content_moderation()` - Scan image
- `apply_moderation_action()` - Take action based on flag
- `get_moderation_display()` - Format findings
- `is_safe_for_display()` - Check if image can be shown

## Testing Checklist
- ✅ Image upload triggers moderation
- ✅ Flag only mode works correctly
- ✅ Delete mode removes images
- ✅ Soft ban increments counter
- ✅ Soft ban triggers at threshold
- ✅ Hard ban works immediately
- ✅ Batch processing functional
- ✅ SYS dashboard displays correctly
- ✅ User notifications sent
- ✅ Django-allauth integration works
- ✅ Banned users cannot login
- ✅ Misuse counter visible in /sys/users

## Additional Requirements (Pending Implementation)

The following enhancements are documented in TODO.md under "Task 33 Additional Requirements":

1. **Approved Images:** Never re-validate approved images
2. **Image URL Logic:** Return error image for flagged content (except SYS views)
3. **Thumbnail Handling:** Apply same logic to thumbnails
4. **SYS Moderation View Updates:** Simplified interface with approve/delete actions
5. **Flagged Content View:** Table format with detailed findings
6. **Media Browser Enhancements:** Add thumbnails, improve column layout

See TODO.md lines 1176-1217 for detailed specifications.

## Related Tasks
- Task 35: System administration interface
- Task 36: Daily metrics (includes moderation metrics)

## Commit Reference
```
3ea305a - feat: Add content moderation status migration
```

## Migration Files
- `web/migrations/0025_mediafile_content_moderation.py`
- `web/migrations/0026_user_moderation_fields.py`
