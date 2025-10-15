# Task 47: Collection Attribute Grouping

## Task Description
When a collection has items sharing common attribute values (e.g., book series, manufacturer, etc.), allow grouping them by those shared attributes. This feature helps organize large collections into logical groups.

Initial requirement: "When collection has a 'series' of some attribute, eg. there is 'series of Discworld novels' (items sharing the same attribute key and value), they could be grouped. It can be enabled per collection via checkbox 'enable grouping'. It can be seen only by owners, and all list displays need to respect that."

## Final Implementation

After iterative refinement based on user feedback, the implementation evolved to provide flexible grouping and sorting options.

### Backend Changes

**File: `web/models.py` (lines 630-677)**

Added new fields to Collection model:

```python
class GroupBy(models.TextChoices):
    NONE = "NONE", _("No Grouping")
    ITEM_TYPE = "ITEM_TYPE", _("Item Type")
    STATUS = "STATUS", _("Status")
    ATTRIBUTE = "ATTRIBUTE", _("Attribute")

class SortBy(models.TextChoices):
    NAME = "NAME", _("Name")
    CREATED = "CREATED", _("Date Created")
    UPDATED = "UPDATED", _("Date Updated")
    ATTRIBUTE = "ATTRIBUTE", _("Attribute Value")

group_by = models.CharField(max_length=20, choices=GroupBy.choices, default=GroupBy.NONE)
grouping_attribute = models.ForeignKey('ItemAttribute', null=True, blank=True, related_name='grouped_collections')
sort_by = models.CharField(max_length=20, choices=SortBy.choices, default=SortBy.NAME)
sort_attribute = models.ForeignKey('ItemAttribute', null=True, blank=True, related_name='sorted_collections')
```

**File: `web/forms.py` (lines 19-60)**

Dynamic form that filters attributes based on collection usage:

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)

    # Filter attributes to only those used in the collection
    if self.instance and self.instance.pk:
        used_attribute_ids = CollectionItemAttributeValue.objects.filter(
            item__collection=self.instance
        ).values_list('item_attribute_id', flat=True).distinct()

        if used_attribute_ids:
            used_attributes = ItemAttribute.objects.filter(id__in=used_attribute_ids)
            self.fields['grouping_attribute'].queryset = used_attributes
            self.fields['sort_attribute'].queryset = used_attributes
        else:
            self.fields['grouping_attribute'].queryset = ItemAttribute.objects.none()
            self.fields['sort_attribute'].queryset = ItemAttribute.objects.none()
```

**File: `web/views/collection.py` (lines 176-261)**

Comprehensive grouping logic:

1. **Group by Item Type**: Groups items by their item_type field
2. **Group by Status**: Groups items by status (In Collection, Wanted, Reserved)
3. **Group by Attribute**: Groups items by a selected attribute value

Sorting within groups:
- **By Name**: Case-insensitive alphabetical
- **By Created/Updated**: Reverse chronological
- **By Attribute**: Smart numeric/string sorting with proper type handling

**File: `web/views/public.py` (lines 81-160)**

Same grouping and sorting logic applied to public view for consistency.

### Frontend Changes

**File: `templates/collection/collection_form.html` (lines 64-92)**

Grouping options only shown when editing (not creating):
- Info alert explaining grouping disables pagination
- Group By dropdown (None, Item Type, Status, Attribute)
- Group By Attribute selector (filtered to used attributes)
- Sort By dropdown (Name, Created, Updated, Attribute)
- Sort By Attribute selector (filtered to used attributes)

**File: `templates/collection/collection_detail.html` (lines 234-270)**

Clean display layout:
- Group headers with icon, name, and item count badge
- Items listed under each header
- No grey container boxes (clean, minimal design)
- Falls back to ungrouped display when grouping disabled

**File: `templates/public/collection_public_detail.html` (lines 137-164)**

Same grouping display for public view.

### Key Features

1. **Flexible Grouping Options**
   - No Grouping (default)
   - Group by Item Type
   - Group by Status
   - Group by Attribute (user-selected)

2. **Smart Attribute Filtering**
   - Only shows attributes actually used in collection items
   - Prevents selecting attributes that aren't present
   - Updates dynamically as items are added/removed

3. **Advanced Sorting**
   - Sort by Name (alphabetical)
   - Sort by Date Created (newest first)
   - Sort by Date Updated (most recently updated first)
   - Sort by Attribute value with smart type handling

4. **Smart Numeric Sorting**
   - Numbers sorted numerically: 1, 2, 5, 10 (not "1", "10", "2", "5")
   - Numeric strings converted to numbers
   - Mixed types handled gracefully
   - Items without attribute appear last

5. **User Experience**
   - Grouping options only available when editing (not creating)
   - Info alert explains pagination is disabled when grouping
   - Clean header-based layout without containers
   - Applied to both private and public views

6. **Integration with Other Features**
   - Grouping disables pagination (shows all items)
   - Works with filtering (Task 45)
   - Public view respects grouping settings

## Files Modified

- `web/models.py` - Added grouping and sorting fields
- `web/forms.py` - Dynamic attribute filtering
- `web/views/collection.py` - Grouping and sorting logic
- `web/views/public.py` - Same logic for public view
- `templates/collection/collection_form.html` - Grouping UI
- `templates/collection/collection_detail.html` - Grouped display
- `templates/public/collection_public_detail.html` - Public grouped display

## Migrations

- `0029_collection_enable_grouping.py` - Initial enable_grouping field
- `0030_collection_grouping_attribute.py` - Added grouping_attribute FK
- `0031_remove_collection_enable_grouping_and_more.py` - Replaced with group_by/sort_by system

## Demo Collection

**File: `web/management/commands/create_grouping_demo.py`**

Creates a demo "Discworld Novels Collection" with:
- 17 books across 4 series (Rincewind, Death, Witches, City Watch)
- 2 standalone books
- Grouped by "Series" attribute
- Sorted by "Name" within groups
- Volume numbers for testing numeric sorting

Run with: `python manage.py create_grouping_demo`

## Testing

### Test Cases

1. **Group by Item Type**
   - Collection with mixed item types (Books, DVDs, Games)
   - Enable "Group by Item Type"
   - Verify items grouped correctly
   - Verify items without type in "Other Items"

2. **Group by Status**
   - Collection with mixed statuses
   - Enable "Group by Status"
   - Verify groups: In Collection, Wanted, Reserved

3. **Group by Attribute**
   - Collection with series attribute
   - Select "Series" as grouping attribute
   - Verify books grouped by series
   - Verify books without series in "Other Items"

4. **Numeric Sorting**
   - Add "Volume" attribute (NUMBER type)
   - Set volumes: 1, 2, 5, 10, 20
   - Enable "Sort by Attribute" → Volume
   - Verify numeric order (not alphabetical)

5. **Attribute Filtering**
   - Edit collection
   - Verify only used attributes appear in dropdowns
   - Add new item with new attribute
   - Verify new attribute appears in dropdown

6. **Public View**
   - Set collection to PUBLIC
   - Verify grouping displayed on public page
   - Verify sorting applied correctly
   - Verify same layout as private view

7. **Pagination Integration**
   - Enable grouping
   - Verify pagination controls hidden
   - Disable grouping
   - Verify pagination controls return

## Grouping Algorithm

### Step 1: Initialize Groups
```python
groups = defaultdict(list)
ungrouped_items = []
```

### Step 2: Iterate Items and Group
For each item in collection:
- If Group by Item Type: Add to item_type group
- If Group by Status: Add to status group
- If Group by Attribute: Get attribute value, add to that group
- If item lacks the grouping criterion: Add to ungrouped_items

### Step 3: Create Grouped Structure
```python
grouped_items = [
    {
        'attribute_name': 'Series',
        'attribute_value': 'Rincewind',
        'items': [item1, item2, item3]
    },
    ...
]
```

### Step 4: Sort Groups
Sort groups alphabetically by attribute_value

### Step 5: Sort Items Within Groups
Based on sort_by setting:
- Name: Alphabetical (case-insensitive)
- Created: Newest first
- Updated: Most recent first
- Attribute: Smart type-aware sorting (numeric or alphabetic)

### Step 6: Append Ungrouped Items
Add "Other Items" group if any items lack the grouping attribute

## Sorting Algorithm (Attribute)

Smart type-aware sorting with priority levels:

```python
def get_attr_value(item):
    value = get_attribute_value(item)

    if isinstance(value, (int, float)):
        return (0, value)  # Numbers first, numeric sort
    elif isinstance(value, str):
        try:
            return (0, float(value))  # Numeric strings as numbers
        except ValueError:
            return (1, value.lower())  # Text strings, alphabetical
    else:
        return (2, str(value))  # Other types
    # Items without attribute: (3, '')
```

Priority levels:
0. Numbers (sorted numerically)
1. Text strings (sorted alphabetically)
2. Other types
3. Missing attribute

## Example Output

**Discworld Collection (Grouped by Series, Sorted by Volume)**

```
Series: City Watch (3 items)
├─ Guards! Guards!
├─ Men at Arms
└─ Feet of Clay

Series: Death (4 items)
├─ Mort (Volume 4)
├─ Reaper Man (Volume 11)
├─ Soul Music (Volume 16)
└─ Hogfather (Volume 20)

Series: Rincewind (4 items)
├─ The Colour of Magic (Volume 1)
├─ The Light Fantastic (Volume 2)
├─ Sourcery (Volume 5)
└─ Eric (Volume 9)

Other Items (2 items)
├─ Pyramids
└─ Small Gods
```

## Design Decisions

1. **Grouping only when editing**: Can't group during creation because no items exist yet
2. **Attribute filtering**: Only show attributes actually used to avoid confusion
3. **Disable pagination when grouped**: Cleaner UX to show all groups at once
4. **Smart numeric sorting**: Handles common case of volume/chapter numbers
5. **Same logic for public view**: Consistency between owner and visitor experience
6. **Info alert on form**: Users informed that grouping disables pagination
7. **Clean header layout**: No grey boxes, just headers and items for minimal design

## Outcome

✅ Flexible grouping by Item Type, Status, or Attribute
✅ Smart attribute filtering (only shows used attributes)
✅ Advanced sorting with smart numeric handling
✅ Clean, minimal header-based layout
✅ Applied to both private and public views
✅ Grouping disables pagination (better UX)
✅ Info alert explains behavior
✅ Demo collection for testing
✅ Comprehensive documentation
