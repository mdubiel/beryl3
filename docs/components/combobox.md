# Combobox Component Documentation

## Overview

The **Combobox** is a reusable HTMX-powered autocomplete component that provides:
- Real-time autocomplete as user types
- Selection from dropdown results
- Manual entry of new values
- Auto-submission of forms (optional)
- Query highlighting in results
- Keyboard and mouse interaction

## When to Use

Use the combobox when:
- User needs to select from existing options OR enter a new value
- List of options is too long for a simple dropdown
- Real-time filtering/search is beneficial
- You want consistent autocomplete behavior across the application

**Keywords**: When documentation or requirements mention "combobox", this component should be implemented.

## Architecture

### Files
- **`/static/js/combobox.js`** - Core JavaScript component (auto-loaded in base.html)
- **Templates** - Use combobox naming convention for HTML elements

### How It Works
1. User types in text input with `data-combobox="unique-id"`
2. HTMX sends request to autocomplete endpoint with query parameter `q`
3. Server returns HTML fragment with results
4. Results call `window.comboboxSelect(id, itemId, itemName)` when clicked
5. Component updates hidden fields and optionally submits form

## Implementation Guide

### Step 1: HTML Structure

```html
<!-- Hidden fields to store selected value -->
<input type="hidden" name="field_id" id="combobox-{UNIQUE_ID}-value" value="">
<input type="hidden" name="field_name" id="combobox-{UNIQUE_ID}-name" value="">

<!-- Text input for typing/display -->
<input type="text"
       id="combobox-{UNIQUE_ID}-search"
       name="q"
       class="input input-bordered w-full"
       placeholder="Type to search..."
       autocomplete="off"
       data-combobox="{UNIQUE_ID}"
       data-combobox-submit="true"
       hx-get="{% url 'your_autocomplete_endpoint' %}"
       hx-trigger="keyup changed delay:300ms, input changed delay:300ms"
       hx-target="#combobox-{UNIQUE_ID}-results"
       hx-swap="innerHTML"
       hx-include="this">

<!-- Results container -->
<div id="combobox-{UNIQUE_ID}-results"
     class="absolute w-full bg-base-100 shadow-lg rounded-box mt-1 max-h-60 overflow-y-auto border border-base-300 hidden"
     style="z-index: 9999;">
    <!-- Autocomplete results will appear here -->
</div>
```

### Step 2: Backend Autocomplete Endpoint

```python
@login_required
def your_autocomplete_view(request):
    query = request.GET.get('q', '').strip()

    # Only return results if query is not empty
    if query:
        items = YourModel.objects.filter(
            name__icontains=query,
            created_by=request.user
        ).order_by('name')[:10]
    else:
        items = YourModel.objects.none()

    return render(request, 'partials/_your_autocomplete_results.html', {
        'items': items,
        'query': query
    })
```

### Step 3: Autocomplete Results Template

```django
{% load lucide %}

{% if items %}
    {% for item in items %}
    <button type="button"
            class="w-full px-3 py-2 hover:bg-base-200 cursor-pointer flex items-center gap-2 text-left text-sm"
            onmousedown="window.comboboxSelect('{UNIQUE_ID}', '{{ item.id }}', '{{ item.name|escapejs }}'); return false;">
        {% lucide 'icon-name' size=12 %}
        <span data-combobox-item-name="{{ item.name }}"></span>
    </button>
    {% endfor %}
    <script>
        // Show dropdown and highlight query
        var container = document.getElementById('combobox-{UNIQUE_ID}-results');
        if (container) {
            container.classList.remove('hidden');
            window.comboboxHighlightQuery('combobox-{UNIQUE_ID}-results', '{{ query }}');
        }
    </script>
{% else %}
    <script>
        // Hide dropdown when no results
        var el = document.getElementById('combobox-{UNIQUE_ID}-results');
        if (el) el.classList.add('hidden');
    </script>
{% endif %}
```

### Step 4: Form Handling

The backend receives:
- `{field_id}` - ID of selected item (empty if manually typed)
- `{field_name}` - Name/text value (always populated)

```python
# In your form handler
item_id = request.POST.get('field_id', '').strip()
item_name = request.POST.get('field_name', '').strip()

if item_id:
    # User selected from autocomplete
    selected_item = YourModel.objects.get(id=item_id, created_by=request.user)
    obj.field = selected_item
elif item_name:
    # User typed a new name - check if exists or create new
    existing_item = YourModel.objects.filter(
        created_by=request.user,
        name=item_name
    ).first()

    if existing_item:
        obj.field = existing_item
    else:
        # Create new item
        new_item = YourModel.objects.create(
            name=item_name,
            created_by=request.user
        )
        obj.field = new_item
else:
    # Both empty - clear the field
    obj.field = None
```

## Configuration Options

### `data-combobox` (required)
Unique ID for this combobox instance. Must match the ID used in all element IDs.

**Example**: `data-combobox="location"`

### `data-combobox-submit` (optional)
Set to `"true"` to auto-submit form when user selects from autocomplete.

**Example**: `data-combobox-submit="true"`

**Use cases**:
- Modal forms where selection should immediately save
- Filters that should apply on selection

**Don't use**:
- Main create/edit forms where user may select multiple fields

## JavaScript API

### `window.comboboxSelect(comboboxId, itemId, itemName)`
Programmatically select an item.

**Parameters**:
- `comboboxId` (string) - The unique ID of the combobox
- `itemId` (string|number) - The ID of the selected item
- `itemName` (string) - The display name of the selected item

**Example**:
```javascript
window.comboboxSelect('location', '123', 'New York Office');
```

### `window.comboboxClear(comboboxId)`
Clear all combobox values.

**Parameters**:
- `comboboxId` (string) - The unique ID of the combobox

**Example**:
```javascript
window.comboboxClear('location');
```

### `window.comboboxHighlightQuery(containerId, query)`
Highlight search query in results (called automatically by results template).

**Parameters**:
- `containerId` (string) - The ID of the results container
- `query` (string) - The search query to highlight

## Styling Guide

### Text Size
- Input field: `input input-bordered w-full` (default Daisy UI sizing)
- Results items: `text-sm` (smaller, more compact)
- Icon size: `size=12` (smaller to match text)
- Padding: `px-3 py-2` (compact spacing)

### Z-Index
Results dropdown uses `style="z-index: 9999;"` to appear above modals.

### Colors
- Default: Uses Daisy UI theme colors
- Hover: `hover:bg-base-200`
- Highlighted query: `<strong>` tags (browser default bold)

## Complete Example: Location Combobox

See implementation in:
- **Form**: `webapp/templates/partials/_item_edit_location.html`
- **Results**: `webapp/templates/partials/_location_autocomplete_results.html`
- **Backend**: `webapp/web/views/location.py::location_autocomplete_view`
- **Handler**: `webapp/web/views/items_hx.py::item_save_personal_info` (location field handling)

## Debugging

### Enable Debug Mode
Debug logging is controlled by Django's DEBUG setting:

```html
<!-- In base.html -->
<script>
    window.DJANGO_DEBUG = {% if debug %}true{% else %}false{% endif %};
</script>
```

When `DEBUG=True`, combobox logs to browser console:
- `[Combobox] Initializing combobox: {id}`
- `[Combobox] Select called: {id} {itemId} {itemName}`
- `[Combobox] Clear called: {id}`
- `[Combobox] Auto-submitting form for: {id}`

### Common Issues

**Issue**: Autocomplete not showing
- Check: HTMX endpoint returns data (`network tab`)
- Check: Container ID matches (`combobox-{id}-results`)
- Check: Backend returns results for query

**Issue**: Selection not working
- Check: `window.comboboxSelect` is called with correct ID
- Check: Hidden field IDs match pattern (`combobox-{id}-value`, `combobox-{id}-name`)

**Issue**: Form not submitting
- Check: `data-combobox-submit="true"` is set
- Check: Input is inside a `<form>` element

**Issue**: Query not highlighted
- Check: Results template calls `window.comboboxHighlightQuery()`
- Check: Items have `data-combobox-item-name` attribute

## Migration Guide

### Converting Existing Autocomplete

1. **Rename IDs** to follow combobox convention:
   ```html
   <!-- Before -->
   <input id="location_search" name="location_name">
   <div id="location_results">

   <!-- After -->
   <input id="combobox-location-search" name="q" data-combobox="location">
   <div id="combobox-location-results">
   ```

2. **Add hidden fields**:
   ```html
   <input type="hidden" id="combobox-location-value" name="location">
   <input type="hidden" id="combobox-location-name" name="location_name">
   ```

3. **Remove inline JavaScript** - combobox.js handles everything

4. **Update result items**:
   ```html
   <!-- Before -->
   onclick="selectLocation('{{ item.id }}', '{{ item.name }}')"

   <!-- After -->
   onmousedown="window.comboboxSelect('location', '{{ item.id }}', '{{ item.name }}'); return false;"
   ```

5. **Update clear buttons**:
   ```html
   <!-- Before -->
   onclick="clearLocation()"

   <!-- After -->
   onclick="window.comboboxClear('location')"
   ```

## Best Practices

1. **Unique IDs**: Always use unique combobox IDs per page
2. **Consistent naming**: Use semantic names (e.g., "location", "category", "tag")
3. **Empty query handling**: Return empty results when query is blank
4. **Limit results**: Cap at 10-20 items for performance
5. **Mobile-friendly**: Ensure touch targets are 44x44px minimum
6. **Accessibility**: Use semantic HTML (`<button>` for items)
7. **Loading states**: Consider adding HTMX indicators for slow networks

## Future Enhancements

Potential improvements (not yet implemented):
- Keyboard navigation (arrow keys)
- Multi-select combobox
- Async loading indicator
- Pagination for large result sets
- Configurable debounce delay
- Clear button in input field
