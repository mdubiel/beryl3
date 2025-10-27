# Testing Checklist - Session Tasks (48-62)

**Version:** 0.2.73
**Session Date:** 2025-10-27
**Tasks Implemented:** 12 tasks

---

## ✅ Task 48: Hidden Attributes Hint

**What to Test:**
1. Create an item with type "Book" and add attributes (Author, ISBN, etc.)
2. Change item type to "Movie"
3. Verify alert appears showing "X hidden attributes not part of Movie type"
4. Click "Show Hidden" button
5. Verify hidden attributes table appears with warning styling
6. Verify you can edit/delete hidden attributes
7. Click "Hide Hidden" to collapse section
8. Verify works with items that have no type (no alert)

**Expected Behavior:**
- Alert badge shows count of hidden attributes
- Toggle button shows/hides hidden attributes
- Hidden section has warning background (bg-warning/20)
- Each hidden attribute has edit/delete actions

**Files to Check:**
- `/items/<hash>/` - Item detail page

---

## ✅ Task 49: Sorting and Grouping

**What to Test:**
1. Go to collection edit page `/collections/<hash>/edit/`
2. Find "Group By" dropdown (None, Item Type, Status, Attribute)
3. Select "Group By: Item Type"
4. Verify collection items are grouped by type with headers
5. Change "Sort By" to different options (Name, Created, Updated, Attribute)
6. Select "Group By: Attribute" and choose an attribute
7. Verify items are grouped by that attribute value
8. Test with "Sort By: Attribute" and select attribute

**Expected Behavior:**
- Collection shows grouped headers with item counts
- Items within groups are sorted correctly
- Group headers are collapsible
- Sorting works within each group

**Files to Check:**
- `/collections/<hash>/` - Collection detail view
- `/collections/<hash>/edit/` - Collection settings

---

## ✅ Task 50: Location and Your ID Fields

### Your ID Field
**What to Test:**
1. Create new item in a collection
2. Look for "Your ID" field in Personal Information section
3. Enter "BOOK-001" and save
4. Create another item
5. Verify suggestion shows "BOOK-002" as placeholder
6. Test with different patterns: numeric (001), prefix+separator (ID_42)
7. Edit existing item - verify Your ID appears in inline edit

**Expected Behavior:**
- Smart suggestions based on last used ID
- Works with: numeric, prefix-separator, letters+numbers
- Preserves leading zeros
- Owner-only visibility (not in public views)

### Location Field
**What to Test:**
1. Go to `/locations/` from user menu "My Locations"
2. Create new location: "Office Shelf A"
3. Verify location appears in list with 0 items
4. Edit an item and assign this location
5. Verify location shows in item detail (owner only)
6. Click location link - should show items in that location
7. Test location autocomplete when editing item
8. Try creating duplicate location name (should fail)
9. Delete location - items should show location cleared

**Expected Behavior:**
- Location CRUD works correctly
- Autocomplete shows existing locations
- Item count updates automatically
- Location links to filtered view
- Owner-only visibility

**Files to Check:**
- `/locations/` - Location list
- `/locations/<hash>/` - Items in location
- `/items/<hash>/` - Item detail shows Your ID and Location
- `/items/add/` - Create form shows suggestions
- `/items/<hash>/edit/` - Edit form shows suggestions

---

## ✅ Task 51: Improved Move Item Dialog

**What to Test:**
1. From any item, click "Move/Copy" dropdown
2. Select "Move to another collection"
3. Verify modal opens with improved UI:
   - Title has icon
   - Close button (X) in header
   - Loading spinner with text
4. Wait for collections to load
5. If >5 collections, verify search box appears
6. Type in search box - verify filtering works
7. Hover over a collection - verify border turns primary
8. Verify collection shows: avatar, name, item count, visibility icon
9. Click a collection to move item
10. Verify success modal with "Go to Collection" and "View Item" buttons

**Expected Behavior:**
- Modal is wider (max-w-2xl) for better display
- Search appears for >5 collections
- Live filtering by collection name
- Visual feedback on hover
- Clear visibility status (🌐 PUBLIC, 🔗 LINK, 🔒 PRIVATE)
- Error states show appropriate messages

**Files to Check:**
- Any item detail or collection list view

---

## ✅ Task 52: Smart Filter Statistics

**What to Test:**
1. Go to a collection with items that have attributes
2. Look for "Quick Filters" section above items
3. Verify badges show "Attribute Name: Value <count>"
4. Click a badge to filter by that attribute value
5. Verify URL updates with attribute filter
6. Verify items are filtered correctly
7. Click "Clear Attribute Filter" to remove
8. Test combining with other filters (search, status, type)

**Expected Behavior:**
- Badges show attribute name, value, and count
- Badge format: "Author: Terry Pratchett 12"
- Clickable badges filter collection
- Active filter highlighted in primary color
- Works with existing search/status filters

**Files to Check:**
- `/collections/<hash>/` - Collection detail view

---

## ✅ Task 53: Clickable Thumbnails

**What to Test:**
1. Go to any collection list view
2. Hover over item thumbnail images
3. Verify cursor changes to pointer
4. Verify slight opacity change on hover (opacity-90)
5. Click thumbnail
6. Verify it navigates to item detail page
7. Test with items that have no image (icon placeholder)
8. Verify placeholder is also clickable

**Expected Behavior:**
- All thumbnails clickable
- Hover shows visual feedback
- Links to correct item detail page
- Works for both images and placeholders

**Files to Check:**
- `/collections/<hash>/` - Collection list view

---

## ✅ Task 56: Error Pages

**What to Test:**
1. Visit non-existent page: `/this-does-not-exist/`
2. Verify custom 404 page appears with:
   - Large "404" text
   - Search-x icon
   - "Go Back" and "Go to Dashboard" buttons
   - Helpful links at bottom
3. Try to access another user's private collection
4. Verify 403 page appears with shield-alert icon
5. To test 500 error (in dev):
   - Temporarily break a view
   - Verify 500 page shows with server-crash icon
   - Check it doesn't extend base (standalone HTML)
6. For 400 error, submit malformed request
7. Verify all error pages match app styling

**Expected Behavior:**
- Custom pages for: 400, 403, 404, 500, 503
- DaisyUI styling matches application
- Icons: search-x (404), shield-alert (403), server-crash (500), triangle-alert (400), construction (503)
- 503 auto-refreshes every 30 seconds
- All have "Go Back" and "Go Home" buttons

**Files to Check:**
- Any invalid URL for 404
- Private resources for 403
- (500/503 require specific scenarios)

---

## ✅ Task 58: Enhanced Attribute Display

**What to Test:**
1. Go to collection with items having attributes
2. Look at "Quick Filters" badges
3. Verify format is "Attribute Name: Value <count>"
4. Example: "Author: Terry Pratchett 12" (not just "Terry Pratchett 12")
5. Verify font is smaller (text-xs)
6. Verify gap between elements is tighter (gap-1)

**Expected Behavior:**
- Attribute name always shown before value
- Smaller, more compact display
- Clear attribution of which attribute each value belongs to

**Files to Check:**
- `/collections/<hash>/` - Quick Filters section

---

## ✅ Task 59: Boolean Toggle

**What to Test:**
1. Create item with type that has boolean attribute (e.g., Book → "Read")
2. Add boolean attribute with value True
3. In item detail view, find the attribute
4. Verify there's an arrow-left-right icon button next to it
5. Click the toggle button
6. Verify value switches from Yes to No (or vice versa) instantly
7. Verify page doesn't reload (HTMX)
8. Check browser console for toggle logging

**Expected Behavior:**
- Quick toggle with single click
- Visual update without page reload
- Icon shows circle-check (Yes) or circle-x (No)
- Toggle button has arrow-left-right icon

**Files to Check:**
- `/items/<hash>/` - Item detail page with boolean attributes

---

## ✅ Task 60: Item Type Popup Layout

**What to Test:**
1. Go to any item (detail or list view)
2. Click item type button (package icon)
3. Verify dropdown opens with improved layout:
   - Grid layout (2/3/4 columns depending on screen)
   - Items sorted alphabetically
   - Items flow top-to-bottom (not left-to-right)
   - Fits within viewport (no horizontal overflow)
   - Has scrollbar if many types (max-h-96)
4. Verify current type is highlighted with primary border
5. Hover over other types - border changes to primary
6. Verify header shows package icon + "Select Item Type"
7. Resize window - verify responsive grid
8. Click a type to change item type

**Expected Behavior:**
- No horizontal overflow beyond viewport
- Alphabetically sorted
- Grid adapts: 2 cols (mobile), 3 (tablet), 4 (desktop)
- Vertical scrolling for many items
- Current type clearly highlighted
- Smooth hover effects

**Files to Check:**
- `/items/<hash>/` - Item detail page
- `/collections/<hash>/` - Item list view (any item)

---

## ✅ Task 62: Dynamic Background Images

**What to Test:**
1. Create public collection with items that have images
2. Visit public collection URL: `/c/<hash>/`
3. Verify random image from collection/items used as background
4. Verify background is fixed (doesn't scroll)
5. Verify semi-transparent overlay for text readability
6. Scroll page - verify background stays fixed
7. Refresh page - verify different random image may appear
8. Test with collection that has no images (fallback)

**Expected Behavior:**
- Random image selected from collection or item images
- Background: fixed, full viewport coverage
- Overlay makes text readable
- Performance optimized
- Graceful fallback when no images

**Files to Check:**
- `/c/<hash>/` - Public collection view

---

## 🔧 General Testing

### Icon Validation
**Critical:** All Lucide icons must be valid
- Check browser console for "IconNotFound" errors
- All icons in this session have been validated
- Fixed: alert-circle → triangle-alert

### Responsive Design
Test on different screen sizes:
- Mobile (320px, 375px, 414px)
- Tablet (768px, 1024px)
- Desktop (1280px, 1920px)

### Browser Compatibility
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

### Performance
- Page load times
- HTMX requests complete quickly
- No console errors
- Smooth animations

### Accessibility
- Keyboard navigation works
- Screen reader friendly (alt text, labels)
- Focus indicators visible
- Color contrast sufficient

---

## 📝 Known Issues / Limitations

None currently identified for implemented tasks.

---

## 🚀 Deployment Checklist

Before deploying to production:

1. ✅ All icons validated (no IconNotFound errors)
2. ✅ All migrations applied
3. ✅ Error handlers configured in urls.py
4. ✅ Static files collected
5. ✅ Templates cached properly
6. ✅ HTMX endpoints tested
7. ✅ Database indexes for filtering (if needed)
8. ✅ Responsive design verified
9. ✅ Browser compatibility tested
10. ✅ Performance acceptable

---

## 📊 Session Summary

**Tasks Completed:** 12
**Version:** 0.2.73
**Commits:** 14
**Files Modified:** 30+
**Files Created:** 20+

**Completed Tasks:**
- Task 48: Hidden attributes hint
- Task 49: Sorting and grouping (verified)
- Task 50: Location and Your ID
- Task 51: Improved move dialog
- Task 52: Smart filters (verified)
- Task 53: Clickable thumbnails
- Task 56: Error pages
- Task 58: Enhanced attribute display
- Task 59: Boolean toggle (verified)
- Task 60: Item type popup layout
- Task 62: Background images (verified)

**Next Priority Tasks:**
- Task 45: Complete attribute filtering
- Task 57: Attribute autocompletion
- Task 54: Mobile UI improvements
- Task 55: Consolidate JavaScript

---

**Testing Completed By:** ___________
**Date:** ___________
**Issues Found:** ___________
**Notes:** ___________
