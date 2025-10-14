# Task 58: Group Display of Multiple Same Attributes

**Status:** ✅ Completed

**Description:**
When displaying multiple values of the same attribute (like multiple authors), group them together. Display the attribute name once on the left side (aligned top-left), and list all values one per row on the right side.

## Requirements

### Before (ungrouped display):
```
Author: Terry Pratchett
Author: Neil Gaiman
Genre: Fantasy
Genre: Humor
```

### After (grouped display with pluralization):
```
Authors:
  - Terry Pratchett
  - Neil Gaiman
Genres:
  - Fantasy
  - Humor
```

**Note:** Attribute names are automatically pluralized when there are multiple values (e.g., "Author" becomes "Authors").

## Implementation

### 1. Created Template Filter for Grouping (`attribute_tags.py`)

**File:** `/home/mdubiel/projects/beryl3/webapp/core/templatetags/attribute_tags.py`

Created a new template filter `group_attributes` that:
- Takes the flat list of attributes from `get_display_attributes()`
- Groups attributes by attribute ID
- Preserves order of first appearance
- Combines multiple values of the same attribute into a single group
- **Automatically pluralizes attribute names** when there are multiple values

**Key Features:**
- Input: List of individual attribute dictionaries (one per value)
- Output: List of grouped dictionaries with attribute name, plural display name, and array of values
- Maintains all necessary data (attribute, value, display_value, attr_value_hash)
- Preserves order using OrderedDict
- Adds `display_name` field with smart pluralization

**Pluralization:**
- Uses Django's built-in `pluralize` template filter
- Single value: "Author"
- Multiple values: "Authors" (adds 's' by default)
- Simple and maintainable using Django's standard functionality

**Layout:**
- **Grid display** with two columns:
  - Column 1: Attribute names (right-aligned, fixed 8rem width)
  - Column 2: Attribute values (left-aligned with 1rem padding, fills remaining space)
- CSS Grid with `grid-cols-[8rem_1fr]` for consistent alignment
- No horizontal gap between columns for continuous borders
- Left padding on values column (`pl-4`) for spacing
- Vertical gap of 0.5rem (`gap-y-2`) between rows
- Borders span both columns continuously

### 2. Updated Templates

#### Public View Templates

**File:** `/home/mdubiel/projects/beryl3/webapp/templates/partials/_item_public_card.html`

Changes:
- Added `{% load attribute_tags %}`
- Applied `|group_attributes` filter to attribute list
- **Changed to grid layout** with `grid-cols-[auto_1fr]`
- **Attribute names**: Right-aligned, bold, auto-width column
- **Attribute values**: Left-aligned, fills remaining space
- **Pluralization**: Uses Django's `pluralize` filter (e.g., "Authors:" for multiple)
- Values displayed:
  - Multiple values: Each on separate row
  - Single value: Displayed inline
- Preserved all attribute type handling (URL, BOOLEAN, DATE)

#### User Collection View Templates

**File:** `/home/mdubiel/projects/beryl3/webapp/templates/partials/_item_attributes.html`

Changes:
- Added `{% load attribute_tags %}`
- Applied `|group_attributes` filter
- **Changed to grid layout** with `grid-cols-[auto_1fr]`
- **Attribute names**: Right-aligned, bold, auto-width column
- **Attribute values**: Left-aligned, fills remaining space
- **Pluralization**: Uses Django's `pluralize` filter (e.g., "Authors:" for multiple)
- Multiple values displayed as list with individual action buttons
- Single values displayed inline with action buttons
- Preserved all HTMX interactions (edit, delete, toggle boolean)

#### Item Detail View Template

**File:** `/home/mdubiel/projects/beryl3/webapp/templates/partials/_item_attributes_detail.html`

Changes:
- Added `{% load attribute_tags %}`
- Applied `|group_attributes` filter
- Updated table layout to support grouped display
- **Attribute names**: Right-aligned with `text-right` class
- **Attribute values**: Left-aligned (default)
- Added `align-top` class to table cells for proper vertical alignment
- **Pluralization**: Uses Django's `pluralize` filter (e.g., "Authors:" for multiple)
- Multiple values displayed with spacing (space-y-2)
- Each value has its own action buttons (edit/delete/toggle)
- Preserved table structure and all HTMX functionality

## Technical Details

### Template Filter Logic

```python
@register.filter
def group_attributes(attributes):
    """Groups attributes by attribute name."""
    if not attributes:
        return []

    grouped = OrderedDict()

    for attr_data in attributes:
        attr = attr_data['attribute']
        attr_id = attr.id

        if attr_id not in grouped:
            grouped[attr_id] = {
                'attribute': attr,
                'values': [],
                'is_multiple': attr_data.get('is_multiple', False),
            }

        grouped[attr_id]['values'].append({
            'value': attr_data['value'],
            'display_value': attr_data.get('display_value', attr_data['value']),
            'attr_value_hash': attr_data.get('attr_value_hash'),
        })

        if attr_data.get('is_multiple', False):
            grouped[attr_id]['is_multiple'] = True

    return list(grouped.values())
```

**Pluralization in Templates:**
Uses Django's built-in `pluralize` filter directly in templates:
```django
{{ group.attribute.display_name }}{{ group.values|length|pluralize }}
```

### Layout Structure

**Grid Layout (Public and Collection List Views):**
```html
<div class="grid grid-cols-[8rem_1fr] gap-y-2">
    {% for group in attributes %}
    <!-- Attribute name - right-aligned, fixed width -->
    <div class="text-xs font-bold text-right {% if not forloop.last %}border-b border-base-300 pb-2{% endif %}">
        {{ group.attribute.display_name }}{{ group.values|length|pluralize }}:
    </div>

    <!-- Values - left-aligned with padding -->
    <div class="pl-4 {% if not forloop.last %}border-b border-base-300 pb-2{% endif %}">
        <!-- Multiple values or single value -->
    </div>
    {% endfor %}
</div>
```

**Key Layout Features:**
- Fixed 8rem width for attribute names ensures perfect right-alignment
- No horizontal gap (`gap-x-3` removed) for continuous borders
- Left padding (`pl-4`) on values column for spacing
- Borders span both columns continuously
- Vertical gap (`gap-y-2`) between rows

**Table Layout (Detail View):**
```html
<tr class="align-top">
    <td class="font-medium w-1/3 align-top text-right">
        {{ group.attribute.display_name }}{{ group.values|length|pluralize }}:
    </td>
    <td class="align-top">
        <!-- Multiple values with individual actions -->
    </td>
</tr>
```

## Views Affected

1. **Public Collection View** (`/share/collections/<hash>`)
   - Item cards display grouped attributes
   - Read-only display (no actions)

2. **User Collection View** (`/collections/<hash>`)
   - Item list displays grouped attributes
   - Full HTMX actions preserved (edit, delete, toggle)

3. **Item Detail View** (`/items/<hash>`)
   - Table displays grouped attributes
   - Full HTMX actions preserved
   - Better vertical alignment for multiple values

## Benefits

1. **Improved Readability**
   - Attribute names not repeated for each value
   - Clear visual grouping of related values
   - Easier to scan and understand item attributes

2. **Better Use of Space**
   - Attribute name shown once instead of repeated
   - More compact display for items with many attributes
   - Cleaner layout overall

3. **Maintained Functionality**
   - All HTMX interactions preserved
   - Individual edit/delete for each value
   - Boolean toggle functionality intact
   - All attribute types handled correctly (URL, BOOLEAN, DATE, TEXT)

4. **Consistent Display**
   - Same grouping logic applied across all views
   - Consistent user experience
   - Single source of truth for grouping logic

## Testing Recommendations

1. **Test with items having:**
   - Multiple authors (2-5 authors)
   - Multiple genres
   - Mix of single and multiple attributes
   - Boolean attributes (should display individually)
   - URL attributes (should be clickable links)
   - Long attribute values (test text wrapping)

2. **Test HTMX interactions:**
   - Edit individual attribute values
   - Delete individual values from grouped attributes
   - Toggle boolean attributes
   - Add new attribute values
   - Verify page updates correctly after actions

3. **Test responsive behavior:**
   - Mobile view (stacked layout)
   - Tablet view
   - Desktop view
   - Long attribute names
   - Many values (10+ authors)

4. **Test all views:**
   - Public collection view (read-only)
   - User collection list view (with actions)
   - Item detail view (table layout)
   - Verify consistent behavior across all views

## Files Modified

1. `/home/mdubiel/projects/beryl3/webapp/core/templatetags/attribute_tags.py` (NEW)
   - Created template filter for grouping attributes

2. `/home/mdubiel/projects/beryl3/webapp/templates/partials/_item_public_card.html`
   - Updated to use grouped attribute display

3. `/home/mdubiel/projects/beryl3/webapp/templates/partials/_item_attributes.html`
   - Updated to use grouped attribute display with actions

4. `/home/mdubiel/projects/beryl3/webapp/templates/partials/_item_attributes_detail.html`
   - Updated table layout to support grouped attributes

## Important: Server Restart Required

After adding a new templatetags module (`attribute_tags.py`), **Django must be restarted** to recognize the new template library.

**Steps:**
1. Stop the current development server (if running)
2. Restart the development server:
   ```bash
   make run-dev-server
   ```

## Verification Steps

1. Ensure the development server has been restarted (see above)

2. Navigate to the application

2. Navigate to a collection with items that have multiple same attributes

3. Verify in collection list view:
   - Attributes are grouped correctly
   - Attribute name appears once on the left
   - Values appear one per line on the right
   - Actions work for each individual value

4. Navigate to item detail view:
   - Verify table layout displays grouped attributes
   - Test edit/delete actions for individual values
   - Test toggle for boolean attributes

5. View public collection (if available):
   - Verify read-only grouped display works correctly
   - No action buttons should be visible

## Future Enhancements

Possible future improvements:
- Add visual bullet points or numbers for multiple values
- Collapsible groups for attributes with many values (10+)
- Inline editing for attribute values
- Drag-and-drop reordering of multiple values
- Batch operations on grouped attributes

## Notes

- The grouping is done at the template level using a template filter
- No changes to models or views were required
- The existing `get_display_attributes()` method provides all necessary data
- All HTMX functionality is preserved
- The implementation is backwards compatible with items having single attributes
