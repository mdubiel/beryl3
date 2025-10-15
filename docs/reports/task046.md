# Task 46: Collection Pagination

## Task Description
Add pagination to collection detail view to handle large collections efficiently. Users should be able to:
- Navigate through pages of items
- Select items per page (10/25/50/100)
- See current page and total pages
- Filters should be preserved across page changes

## Implementation

### Backend Changes

**File: `web/views/collection.py` (lines 228-247)**
- Added Django Paginator import
- Implemented pagination with configurable items per page
- Default: 25 items per page
- Supported options: 10, 25, 50, 100
- Error handling for invalid page numbers (PageNotAnInteger, EmptyPage)
- Filters preserved in pagination links

**File: `web/views/public.py` (lines 161-183)**
- Same pagination implementation for public view
- Smart handling: pagination disabled when grouping is enabled
- When grouped, all items shown without pagination

### Frontend Changes

**File: `templates/collection/collection_detail.html` (lines 272-300)**
- Navigation controls with first/previous/next/last buttons (« ‹ › »)
- Page counter showing current page and total pages
- Items per page dropdown selector
- Filter parameters preserved in all pagination links
- White background styling (`bg-base-100`) for consistency

**File: `templates/public/collection_public_detail.html` (lines 167-194)**
- Same pagination UI as private view
- Responsive layout (flex-col on mobile, flex-row on desktop)
- Only shows when `page_obj` exists and has multiple pages

### Key Features

1. **Configurable Page Size**
   - 10, 25, 50, or 100 items per page
   - Defaults to 25 items
   - Selection persists across page navigation

2. **Navigation Controls**
   - First page (««)
   - Previous page (‹)
   - Current page indicator
   - Next page (›)
   - Last page (»)

3. **Filter Preservation**
   - Search query preserved
   - Status filter preserved
   - Item type filter preserved
   - Items per page setting preserved

4. **Error Handling**
   - Invalid page numbers default to page 1
   - Empty pages default to last page
   - Invalid items-per-page values default to 25

5. **Smart Integration**
   - Pagination disabled when grouping is enabled (Task 47)
   - Works seamlessly with filtering (Task 45)
   - Applied to both private and public views

## Files Modified

- `web/views/collection.py` - Pagination logic for private view
- `web/views/public.py` - Pagination logic for public view
- `templates/collection/collection_detail.html` - Pagination UI for private view
- `templates/public/collection_public_detail.html` - Pagination UI for public view

## Testing

### Test Cases

1. **Basic Pagination**
   - Create collection with 30+ items
   - Verify pagination controls appear
   - Navigate through pages
   - Verify correct items shown on each page

2. **Items Per Page**
   - Change items per page to 10
   - Verify page count updates
   - Change to 100
   - Verify single page for small collections

3. **Filter Preservation**
   - Apply status filter
   - Navigate to page 2
   - Verify filter still applied
   - Change items per page
   - Verify filter still applied

4. **Edge Cases**
   - Navigate to invalid page number (should default to page 1)
   - Navigate to page beyond last (should default to last page)
   - Set invalid items per page (should default to 25)

5. **Grouping Integration**
   - Enable grouping on collection
   - Verify pagination controls hidden
   - Verify all items shown in groups
   - Disable grouping
   - Verify pagination returns

## URL Parameters

- `page` - Current page number (default: 1)
- `per_page` - Items per page (10/25/50/100, default: 25)
- Additional filter parameters from Task 45

## Example URLs

- `/collections/abc123/?page=1&per_page=25`
- `/collections/abc123/?page=2&per_page=50&status=IN_COLLECTION`
- `/share/collections/abc123/?page=1&per_page=10`

## Notes

- Pagination is disabled when grouping is enabled (Task 47)
- When grouping is active, all items are shown organized in groups
- Pagination UI matches DaisyUI design system
- All buttons use white background (`bg-base-100`) for consistency
- Same implementation for both private and public views

## Outcome

✅ Collection pagination implemented successfully
✅ Works with filtering (Task 45)
✅ Works with grouping (Task 47)
✅ Applied to both private and public views
✅ User-friendly navigation controls
✅ Configurable page size
✅ Filter preservation across pages
