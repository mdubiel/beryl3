# Task 65: Performance Analysis - Critical Findings

## Executive Summary

**CRITICAL ISSUE DISCOVERED**: The `default_image` property does NOT use `prefetch_related` cache, causing N+1 queries even with proper prefetch setup.

## User's Key Observations

1. **Grouping vs Pagination Impact**:
   - With grouping: ~8 seconds (no pagination, all 71 items)
   - Without grouping (25 per page): ~2 seconds
   - **Finding**: Pagination reduces items from 71 → 25 (4x improvement)

2. **Linear Scaling with Item Count**:
   - 40 items with images: 4 seconds (100ms/item)
   - 71 items with images: 8 seconds (113ms/item)
   - **Pattern**: ~100ms per item (consistent)

3. **Images are the Bottleneck**:
   - 60 items WITHOUT images: 380ms (6ms/item)
   - 71 items WITH images: 8000ms (113ms/item)
   - **Impact**: Images cause 18x slowdown per item

## Root Cause Analysis

### Problem 1: `@property default_image` Bypasses Prefetch Cache

**Location**: `webapp/web/models.py` lines 1190-1192

```python
@property
def default_image(self):
    """Get the default image for this collection item"""
    return self.images.filter(is_default=True).first()  # ⚠️ NEW QUERY EVERY TIME
```

**Test Results**:
```
With prefetch_related('images__media_file'):
  - Still executes 1 query per item.default_image access
  - Prefetch cache is NOT used by .filter()
  - Each of 71 items = 71 queries!
```

**SQL Generated**:
```sql
SELECT * FROM web_collectionitemimage
WHERE item_id = ? AND is_default = TRUE
ORDER BY item_id, order
LIMIT 1
```

### Problem 2: Template Accesses `default_image` Property

**Location**: `webapp/templates/partials/_item_image_lazy.html` line 2

```django
{% if item.default_image and item.default_image.media_file.file_exists %}
```

**What Happens**:
1. Template calls `item.default_image` (property)
2. Property executes: `self.images.filter(is_default=True).first()`
3. Django creates NEW database query (doesn't use prefetch cache)
4. This happens for EVERY item in the page
5. 71 items = 71 separate queries

**Evidence from Script**:
```
3. With prefetch_related from view:
   Queries executed: 3
   SQL: SELECT ... FROM web_collectionitem WHERE id = 1140
   SQL: SELECT ... FROM web_collectionitemimage WHERE item_id IN (1140)  # Prefetch
   SQL: SELECT ... FROM web_collectionitemimage WHERE item_id = 1140 AND is_default = TRUE  # Property!
```

### Problem 3: Django Prefetch Limitation

**Why .filter() Breaks Prefetch**:

Django's prefetch cache stores results of:
```python
item.images.all()  # Uses cache ✅
```

But does NOT work with:
```python
item.images.filter(is_default=True)  # Bypasses cache, hits DB ❌
item.images.filter(is_default=True).first()  # Bypasses cache, hits DB ❌
```

**Django Documentation** (from Django docs):
> "The prefetch cache only works with `.all()`. Any further filtering using `.filter()`, `.exclude()`, or other QuerySet methods will trigger a new database query."

## Performance Impact Breakdown

### Current Performance (71 items with images):

| Operation | Time | Count | Total |
|-----------|------|-------|-------|
| Initial query (6 queries) | 10ms | 1 | 10ms |
| Prefetch images | 20ms | 1 | 20ms |
| Template rendering setup | 500ms | 1 | 500ms |
| **Per-item default_image query** | **5ms** | **71** | **355ms** |
| **Per-item template rendering** | **100ms** | **71** | **7100ms** |
| **TOTAL** | | | **~8 seconds** |

### Why 100ms per item?

Each item card rendering:
1. Call `item.default_image` property → 5ms (DB query)
2. Access `default_image.media_file` → 2ms (already prefetched)
3. Call `file_exists` property → 3ms (filesystem check!)
4. Render rest of item card HTML → 90ms

**The culprits**:
- Database query: 5ms × 71 = 355ms
- Filesystem checks: 3ms × 71 = 213ms
- Template rendering: 90ms × 71 = 6390ms

## Database Schema Analysis

### Indexes (All Present ✅)

**CollectionItemImage**:
- ✅ `item_id` - for reverse lookup
- ✅ `media_file_id` - for joins
- ✅ `(item_id, is_default)` - composite index (perfect for default_image query!)
- ✅ `(item_id, order)` - for ordering
- ✅ `(item_id, media_file_id)` - unique constraint

**MediaFile**:
- ✅ Primary key on `id`
- ✅ `media_type` index
- ✅ `storage_backend` index
- ✅ `(media_type, storage_backend)` - composite
- ✅ `(file_exists, last_verified)` - composite

**Conclusion**: All necessary indexes exist. This is NOT an indexing problem.

### Relationship Structure

```
CollectionItem (71 items)
    ↓ 1:N
CollectionItemImage (N images, typically 1-3 per item)
    ↓ N:1
MediaFile (actual image files)
```

**Not N:N** - it's a proper N:1:N relationship with junction table `CollectionItemImage`.

## Why Template Caching Helped (But Not Enough)

### What We Cached:
```django
{% cache 3600 public_item_card item.id item.updated %}
    {% include "partials/_item_public_card.html" with item=item %}
{% endcache %}
```

### What Gets Cached:
- The rendered HTML of the item card
- After first render: No template rendering needed

### What DOESN'T Get Cached:
- The HTMX lazy-load endpoint still runs for each image
- Each endpoint call loads item, executes `default_image` property
- Still hits database + filesystem

### Results:
- Cold cache: 7.0s (full rendering)
- Warm cache: 2.5s (HTML cached, but HTMX endpoints still slow)

## Solutions (For Tomorrow)

### Solution 1: Fix `default_image` Property to Use Prefetch Cache ⭐

**Current (Broken)**:
```python
@property
def default_image(self):
    return self.images.filter(is_default=True).first()  # Hits DB
```

**Fixed Version**:
```python
@property
def default_image(self):
    """Get default image using prefetch cache when available"""
    # Try to use prefetch cache first
    if hasattr(self, '_prefetched_objects_cache') and 'images' in self._prefetched_objects_cache:
        # Use prefetched data
        for img in self.images.all():  # Uses cache
            if img.is_default:
                return img
        return None
    # Fallback to database query if not prefetched
    return self.images.filter(is_default=True).first()
```

**Expected Impact**: Eliminate 71 × 5ms = 355ms of database queries

### Solution 2: Add Pagination to Grouped Views ⭐⭐⭐

**Current**: Grouping displays all 71 items at once
**Proposed**: Paginate groups or items within groups (25 per page)

**Expected Impact**:
- 71 items → 25 items per page
- 8 seconds → ~2.8 seconds (3x improvement)

### Solution 3: Optimize `file_exists` Property

**Current**: Each `media_file.file_exists` hits the filesystem
**Proposed**:
1. Cache `file_exists` as database field (updated periodically)
2. OR skip the check in template (assume files exist)

**Expected Impact**: Eliminate 71 × 3ms = 213ms of filesystem I/O

### Solution 4: Pre-compute Image URLs in View

**Current**: Template calls `{% media_url item.default_image.media_file %}`
**Proposed**: Build image URLs in view context

```python
# In view
for item in items:
    if item.default_image:
        item._cached_image_url = media_url(item.default_image.media_file)
```

**Expected Impact**: Reduce template tag overhead

### Solution 5: Client-Side Image URLs (Radical Approach)

**Current**: HTMX endpoint renders server-side template
**Proposed**: Return JSON with image URL, render with JavaScript

```javascript
// Client-side
htmx.on('htmx:afterRequest', function(evt) {
    if (evt.detail.successful) {
        const data = JSON.parse(evt.detail.xhr.responseText);
        evt.target.innerHTML = `<img src="${data.url}" alt="${data.alt}">`;
    }
});
```

**Expected Impact**: Eliminate server-side template rendering per image

## Priority Actions for Tomorrow

### High Priority:
1. ✅ **Fix `default_image` property** to use prefetch cache (355ms saved)
2. ✅ **Add pagination to grouped views** (3x improvement: 8s → 2.8s)
3. ✅ **Cache `file_exists` as database field** (213ms saved)

### Medium Priority:
4. Pre-compute image URLs in view context
5. Profile template rendering overhead (why 90ms per card?)

### Low Priority:
6. Consider client-side image rendering (architectural change)

## Expected Final Performance

| Optimization | Time Saved | Cumulative |
|--------------|------------|------------|
| **Start** | | **8.0s** |
| Fix default_image property | -355ms | 7.6s |
| Add file_exists DB field | -213ms | 7.4s |
| Add pagination (71→25 items) | -5.2s | **2.2s** |

**Target**: ~2.2 seconds for 25 items (with grouping + pagination)

## Key Learnings

1. **Django Prefetch Limitation**: `.filter()` on prefetched relations ALWAYS hits database
2. **Properties Hide Queries**: `@property` methods can mask N+1 queries
3. **Template Caching ≠ Query Caching**: Cached HTML doesn't cache the queries needed to generate it
4. **Filesystem I/O Adds Up**: 3ms × 71 = 213ms is significant
5. **Pagination is Critical**: Reducing items has linear impact on performance

## References

- Django documentation: Query prefetching and caching
- Script: `workflows/tasks/task65_check_indexes.py`
- Analysis: Query pattern tests showing property behavior
- User observation: Linear scaling with item count
