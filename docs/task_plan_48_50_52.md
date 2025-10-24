# Implementation Plan for Tasks 48, 50, and 52

## Task 49: Attribute Sorting and Grouping - ✅ VERIFIED COMPLETE

**Status:** Already implemented in tasks 46 and 47

**Current Implementation:**
- Collection model has `group_by`, `grouping_attribute`, `sort_by`, `sort_attribute` fields
- UI in collection edit form (collection_form.html:64-92)
- Backend logic in collection_detail_view handles:
  - Grouping by: None, Item Type, Status, Attribute
  - Sorting by: Name, Created, Updated, Attribute
  - Smart sorting with numeric vs. string handling
- Template displays grouped items with headers and counts
- Attribute dropdowns filtered to only show attributes used in collection

**No further work needed.**

---

## Task 48: Add Hidden Attributes Hint

**Description:** When an item has attributes that don't belong to its current item type, show a hint that there are hidden attributes.

### Analysis

**Current Behavior:**
- CollectionItem has optional `item_type` field
- Items can have attributes via CollectionItemAttributeValue
- Attributes are linked to ItemAttribute which belongs to an ItemType
- Template `_item_attributes.html` displays all attributes
- No filtering based on item_type currently

**Problem:**
- If an item's type changes, old attributes remain but may not be relevant
- User doesn't know there are "hidden" attributes not in current type schema

### Implementation Plan

#### 1. Model Method: `CollectionItem.get_hidden_attributes()`
**File:** `webapp/web/models.py`

Add method to CollectionItem class to identify attributes not belonging to current item type:

```python
def get_hidden_attributes(self):
    """
    Returns list of attribute values that don't belong to the current item type.
    Returns empty list if item has no type set.
    """
    if not self.item_type:
        return []

    # Get all attribute IDs for this item type
    type_attribute_ids = set(
        self.item_type.attributes.values_list('id', flat=True)
    )

    # Get all attribute values for this item
    all_attribute_values = self.attribute_values.select_related('item_attribute')

    # Filter to those not in the type's schema
    hidden = [
        av for av in all_attribute_values
        if av.item_attribute_id not in type_attribute_ids
    ]

    return hidden

def get_hidden_attributes_count(self):
    """Returns count of hidden attributes."""
    return len(self.get_hidden_attributes())
```

#### 2. Template Updates
**Files:**
- `webapp/templates/partials/_item_attributes.html`
- `webapp/templates/item/item_detail.html`

Add visual indicator when hidden attributes exist:

```html
{% if item.get_hidden_attributes_count > 0 %}
<div class="alert alert-info mt-2">
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" class="stroke-current shrink-0 w-5 h-5">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>
    <span>
        This item has {{ item.get_hidden_attributes_count }} hidden attribute{{ item.get_hidden_attributes_count|pluralize }}
        not part of the "{{ item.item_type.display_name }}" type.
        <button class="btn btn-xs btn-ghost ml-2" onclick="toggleHiddenAttributes()">
            Show Hidden
        </button>
    </span>
</div>

<div id="hidden-attributes" class="hidden mt-4">
    <h4 class="font-semibold mb-2">Hidden Attributes:</h4>
    {% for attr_value in item.get_hidden_attributes %}
    <div class="grid grid-cols-3 gap-4 py-2 border-b border-base-300">
        <div class="text-right text-neutral">{{ attr_value.item_attribute.display_name }}</div>
        <div class="col-span-2">{{ attr_value.get_display_value }}</div>
    </div>
    {% endfor %}
</div>
```

#### 3. JavaScript for Toggle
Add to item detail template:

```javascript
function toggleHiddenAttributes() {
    const hiddenDiv = document.getElementById('hidden-attributes');
    hiddenDiv.classList.toggle('hidden');
}
```

### Files to Modify
1. `webapp/web/models.py` - Add methods to CollectionItem
2. `webapp/templates/item/item_detail.html` - Add hidden attributes hint
3. `webapp/templates/partials/_item_attributes.html` - Optionally filter displayed attributes

---

## Task 50: Add Custom Item Fields (Your ID and Location)

**Description:** Add two new fields to CollectionItem:
- `your_id`: Custom user-defined identifier
- `location`: Physical location with autocomplete and management

### Analysis

**Requirements:**
1. **Your ID Field:**
   - Simple text field
   - User-defined identifier for personal cataloging
   - Visible only to owner (not in public views)
   - Searchable and filterable

2. **Location Field:**
   - New `Location` model with autocomplete
   - ForeignKey from CollectionItem to Location
   - Location belongs to user (one user's locations)
   - Autocomplete/combo box during item edit
   - Location management view at `/locations/`
   - Shows location list with item counts
   - Click location → virtual collection of items in that location

### Implementation Plan

#### 1. Create Location Model
**File:** `webapp/web/models.py`

```python
class Location(BaseModel):
    """Physical location where collection items are stored."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="locations"
    )

    class Meta:
        ordering = ['name']
        unique_together = [['created_by', 'name']]

    def __str__(self):
        return self.name

    def get_item_count(self):
        """Return count of items in this location."""
        return self.items.count()

    def get_absolute_url(self):
        """URL to view items in this location."""
        return reverse('location_items', kwargs={'hash': self.hash})
```

#### 2. Update CollectionItem Model
**File:** `webapp/web/models.py`

Add fields to CollectionItem:

```python
class CollectionItem(BaseModel):
    # ... existing fields ...

    # Task 50: Custom fields
    your_id = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Your personal identifier for this item"
    )
    location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items',
        help_text="Physical location where this item is stored"
    )
```

#### 3. Create Migration
```bash
python manage.py makemigrations -n add_your_id_and_location
```

#### 4. Update Forms
**File:** `webapp/web/forms.py`

Add to CollectionItemForm:

```python
class CollectionItemForm(forms.ModelForm):
    class Meta:
        model = CollectionItem
        fields = [
            'name', 'description', 'status', 'item_type',
            'your_id', 'location', 'is_favorite'
        ]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Filter locations to only user's own
        if user:
            self.fields['location'].queryset = Location.objects.filter(
                created_by=user
            ).order_by('name')

        # Make location widget an autocomplete (using datalist)
        self.fields['location'].widget.attrs.update({
            'class': 'select select-bordered w-full',
            'x-data': 'locationAutocomplete',
        })
```

#### 5. Location Management Views
**File:** `webapp/web/views/location.py` (new file)

```python
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from webapp.web.models import Location, CollectionItem

@login_required
def location_list_view(request):
    """List all user's locations."""
    locations = Location.objects.filter(
        created_by=request.user
    ).annotate(
        item_count=models.Count('items')
    ).order_by('name')

    return render(request, 'location/location_list.html', {
        'locations': locations
    })

@login_required
def location_items_view(request, hash):
    """View all items in a specific location."""
    location = get_object_or_404(
        Location,
        hash=hash,
        created_by=request.user
    )

    items = CollectionItem.objects.filter(
        location=location,
        collection__created_by=request.user
    ).select_related('collection', 'item_type')

    return render(request, 'location/location_items.html', {
        'location': location,
        'items': items
    })

@login_required
def location_create_view(request):
    """Create a new location."""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')

        location = Location.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )

        return redirect('location_list')

    return render(request, 'location/location_form.html')

@login_required
def location_delete_view(request, hash):
    """Delete a location."""
    location = get_object_or_404(
        Location,
        hash=hash,
        created_by=request.user
    )

    if request.method == 'POST':
        location.delete()
        return redirect('location_list')

    return render(request, 'location/location_confirm_delete.html', {
        'location': location
    })
```

#### 6. HTMX Autocomplete Endpoint
**File:** `webapp/web/views/location.py`

```python
@login_required
def location_autocomplete_view(request):
    """HTMX endpoint for location autocomplete."""
    query = request.GET.get('q', '').strip()

    if len(query) < 1:
        locations = Location.objects.filter(
            created_by=request.user
        ).order_by('name')[:10]
    else:
        locations = Location.objects.filter(
            created_by=request.user,
            name__icontains=query
        ).order_by('name')[:10]

    return render(request, 'partials/_location_autocomplete.html', {
        'locations': locations,
        'query': query
    })
```

#### 7. Update Item Edit Template
**File:** `webapp/templates/item/item_edit.html`

Add fields to form with autocomplete:

```html
<label class="label mt-4">Your ID</label>
<input type="text" name="your_id" value="{{ form.your_id.value|default:'' }}"
       class="input input-bordered w-full"
       placeholder="Your personal ID or reference">
<p class="text-xs text-neutral mt-1">A custom identifier for your personal use</p>

<label class="label mt-4">Location</label>
<div x-data="{ showCreateLocation: false }">
    <div class="flex gap-2">
        <select name="location" class="select select-bordered flex-1"
                hx-get="{% url 'location_autocomplete' %}"
                hx-trigger="keyup changed delay:300ms"
                hx-target="#location-suggestions">
            <option value="">-- No Location --</option>
            {% for location in user_locations %}
            <option value="{{ location.id }}"
                    {% if form.location.value == location.id %}selected{% endif %}>
                {{ location.name }}
            </option>
            {% endfor %}
        </select>
        <button type="button" @click="showCreateLocation = !showCreateLocation"
                class="btn btn-outline btn-sm">
            {% lucide 'plus' size=14 %} New
        </button>
    </div>

    <div x-show="showCreateLocation" class="mt-2 p-3 bg-base-200 rounded">
        <input type="text" id="new-location-name" placeholder="New location name"
               class="input input-bordered input-sm w-full mb-2">
        <button type="button" @click="createLocation()" class="btn btn-primary btn-sm">
            Create Location
        </button>
    </div>
</div>
```

#### 8. Display in Item Detail
**File:** `webapp/templates/item/item_detail.html`

Show your_id and location (owner only):

```html
{% if request.user == item.collection.created_by %}
<div class="grid grid-cols-3 gap-4 py-2 border-b border-base-300 bg-base-100/50">
    <div class="text-right text-neutral font-semibold">Your ID:</div>
    <div class="col-span-2">
        {{ item.your_id|default:"<span class='text-neutral'>Not set</span>" }}
    </div>
</div>
<div class="grid grid-cols-3 gap-4 py-2 border-b border-base-300 bg-base-100/50">
    <div class="text-right text-neutral font-semibold">Location:</div>
    <div class="col-span-2">
        {% if item.location %}
        <a href="{{ item.location.get_absolute_url }}" class="link link-primary">
            {% lucide 'map-pin' size=14 class='inline' %}
            {{ item.location.name }}
        </a>
        {% else %}
        <span class="text-neutral">Not set</span>
        {% endif %}
    </div>
</div>
{% endif %}
```

#### 9. Location List Template
**File:** `webapp/templates/location/location_list.html`

```html
{% extends "base.html" %}
{% load lucide %}

{% block title %}My Locations{% endblock %}

{% block content %}
<div class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold">My Locations</h1>
    <a href="{% url 'location_create' %}" class="btn btn-primary">
        {% lucide 'plus' size=16 class='mr-2' %} New Location
    </a>
</div>

<div class="grid gap-4">
    {% for location in locations %}
    <div class="card bg-base-100 shadow-sm">
        <div class="card-body">
            <div class="flex justify-between items-start">
                <div class="flex-1">
                    <h3 class="card-title">
                        {% lucide 'map-pin' size=20 class='mr-2' %}
                        {{ location.name }}
                    </h3>
                    {% if location.description %}
                    <p class="text-sm text-neutral mt-2">{{ location.description }}</p>
                    {% endif %}
                    <div class="mt-3">
                        <a href="{{ location.get_absolute_url }}" class="link link-primary text-sm">
                            View {{ location.item_count }} item{{ location.item_count|pluralize }}
                        </a>
                    </div>
                </div>
                <div class="dropdown dropdown-end">
                    <button class="btn btn-ghost btn-sm btn-square">
                        {% lucide 'more-vertical' size=16 %}
                    </button>
                    <ul class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52">
                        <li><a href="{% url 'location_delete' location.hash %}">Delete</a></li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
    {% empty %}
    <p class="text-neutral text-center py-8">No locations yet. Create one to organize your items.</p>
    {% endfor %}
</div>
{% endblock %}
```

#### 10. URL Configuration
**File:** `webapp/web/urls.py`

```python
# Location management
path('locations/', views.location_list_view, name='location_list'),
path('locations/create/', views.location_create_view, name='location_create'),
path('locations/<str:hash>/', views.location_items_view, name='location_items'),
path('locations/<str:hash>/delete/', views.location_delete_view, name='location_delete'),
path('api/locations/autocomplete/', views.location_autocomplete_view, name='location_autocomplete'),
```

#### 11. Add to User Menu
**File:** `webapp/templates/partials/_user_menu.html`

Add link to locations:

```html
<li>
    <a href="{% url 'location_list' %}">
        {% lucide 'map-pin' size=16 %}
        My Locations
    </a>
</li>
```

### Files to Create/Modify
1. **Models:** `webapp/web/models.py` - Add Location model, update CollectionItem
2. **Views:** `webapp/web/views/location.py` (new) - Location CRUD views
3. **Forms:** `webapp/web/forms.py` - Update CollectionItemForm
4. **Templates (new):**
   - `webapp/templates/location/location_list.html`
   - `webapp/templates/location/location_items.html`
   - `webapp/templates/location/location_form.html`
   - `webapp/templates/location/location_confirm_delete.html`
   - `webapp/templates/partials/_location_autocomplete.html`
5. **Templates (update):**
   - `webapp/templates/item/item_edit.html`
   - `webapp/templates/item/item_detail.html`
   - `webapp/templates/partials/_user_menu.html`
6. **URLs:** `webapp/web/urls.py`
7. **Migration:** Django migration for new fields

---

## Task 52: Display Attribute Statistics and Filtering

**Description:** Display smart filter badges above items showing aggregate statistics from attributes (e.g., "Terry Pratchett | 12"), clickable to filter collection.

### Analysis

**Requirements:**
1. Display above items in collection view
2. Show attribute value counts (e.g., "Terry Pratchett | 12")
3. Clickable badges to filter collection
4. Borderless DaisyUI badges
5. Aggregate by attribute type and value
6. Works with existing filter system

### Implementation Plan

#### 1. Update Collection View
**File:** `webapp/web/views/collection.py`

Add attribute statistics to context:

```python
def collection_detail_view(request, hash):
    # ... existing code ...

    # Task 52: Calculate attribute statistics
    attribute_stats = get_attribute_statistics(items_queryset, collection)

    context = {
        # ... existing context ...
        'attribute_stats': attribute_stats,
    }

    return render(request, 'collection/collection_detail.html', context)


def get_attribute_statistics(items_queryset, collection):
    """
    Calculate aggregate statistics for attributes in the collection.
    Returns list of dicts with attribute name, value, count.
    """
    from collections import defaultdict

    # Get all attribute values for items in queryset
    attribute_values = CollectionItemAttributeValue.objects.filter(
        item__in=items_queryset
    ).select_related('item_attribute').values(
        'item_attribute__display_name',
        'item_attribute__id',
        'value'
    )

    # Aggregate by attribute and value
    stats = defaultdict(lambda: defaultdict(int))

    for av in attribute_values:
        attr_name = av['item_attribute__display_name']
        attr_id = av['item_attribute__id']
        value = av['value']

        # Create display value
        display_value = value

        # Truncate long values
        if len(display_value) > 30:
            display_value = display_value[:27] + '...'

        stats[(attr_name, attr_id)][display_value] += 1

    # Convert to list format for template
    result = []
    for (attr_name, attr_id), values in stats.items():
        for value, count in sorted(values.items(), key=lambda x: -x[1]):
            result.append({
                'attribute_name': attr_name,
                'attribute_id': attr_id,
                'value': value,
                'count': count
            })

    # Sort by count descending, limit to top 20
    result.sort(key=lambda x: -x['count'])
    return result[:20]
```

#### 2. Add Attribute Filter to View
**File:** `webapp/web/views/collection.py`

Extend filtering logic:

```python
# Existing filters
filter_search = request.GET.get('search', '').strip()
filter_status = request.GET.get('status', '').strip()
filter_item_type = request.GET.get('item_type', '').strip()

# Task 52: Add attribute value filter
filter_attribute = request.GET.get('attribute', '').strip()
filter_attribute_value = request.GET.get('attribute_value', '').strip()

# Apply attribute filter
if filter_attribute and filter_attribute_value:
    items_queryset = items_queryset.filter(
        attribute_values__item_attribute_id=filter_attribute,
        attribute_values__value=filter_attribute_value
    )
```

#### 3. Update Template - Add Smart Filter Badges
**File:** `webapp/templates/collection/collection_detail.html`

Add after filters, before item list:

```html
{# Task 52: Smart attribute filter badges #}
{% if attribute_stats and stats.total_items > 0 %}
<div class="mb-6">
    <h3 class="text-sm font-semibold mb-3 text-neutral">Quick Filters</h3>
    <div class="flex flex-wrap gap-2">
        {% for stat in attribute_stats %}
        <a href="?attribute={{ stat.attribute_id }}&attribute_value={{ stat.value|urlencode }}{% if filter_search %}&search={{ filter_search }}{% endif %}{% if filter_status %}&status={{ filter_status }}{% endif %}{% if filter_item_type %}&item_type={{ filter_item_type }}{% endif %}"
           class="badge badge-lg gap-2 cursor-pointer hover:badge-primary transition-colors
                  {% if filter_attribute == stat.attribute_id|stringformat:'s' and filter_attribute_value == stat.value %}badge-primary{% else %}badge-ghost{% endif %}">
            <span class="font-medium">{{ stat.value }}</span>
            <span class="badge badge-sm badge-neutral">{{ stat.count }}</span>
        </a>
        {% endfor %}
    </div>
    {% if filter_attribute %}
    <div class="mt-2">
        <a href="?{% if filter_search %}search={{ filter_search }}&{% endif %}{% if filter_status %}status={{ filter_status }}&{% endif %}{% if filter_item_type %}item_type={{ filter_item_type }}{% endif %}"
           class="btn btn-ghost btn-xs">
            {% lucide 'x' size=12 %} Clear Attribute Filter
        </a>
    </div>
    {% endif %}
</div>
{% endif %}
```

#### 4. Update Filter Form - Add Attribute Filter Display
**File:** `webapp/templates/collection/collection_detail.html`

Show active attribute filter in main filter form:

```html
{# Show active filters summary #}
{% if filter_search or filter_status or filter_item_type or filter_attribute %}
<div class="mb-4">
    <div class="flex flex-wrap gap-2 items-center">
        <span class="text-sm text-neutral">Active filters:</span>
        {% if filter_search %}
        <span class="badge badge-primary">Search: {{ filter_search }}</span>
        {% endif %}
        {% if filter_status %}
        <span class="badge badge-primary">Status: {{ filter_status }}</span>
        {% endif %}
        {% if filter_item_type %}
        <span class="badge badge-primary">Type: {{ filter_item_type }}</span>
        {% endif %}
        {% if filter_attribute %}
        <span class="badge badge-primary">Attribute: {{ filter_attribute_value }}</span>
        {% endif %}
        <a href="?" class="btn btn-ghost btn-xs">Clear All</a>
    </div>
</div>
{% endif %}
```

#### 5. Performance Optimization
Add database index for attribute filtering:

**Migration:**
```python
class Migration(migrations.Migration):
    dependencies = [
        ('web', 'XXXX_previous_migration'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='collectionitemattributevalue',
            index=models.Index(
                fields=['item_attribute', 'value'],
                name='web_colle_item_at_idx'
            ),
        ),
    ]
```

### Files to Modify
1. `webapp/web/views/collection.py` - Add attribute statistics and filtering
2. `webapp/templates/collection/collection_detail.html` - Add smart filter badges UI
3. New migration for performance index

---

## Testing Plan

### Task 48
1. Create item with item type and attributes
2. Change item type
3. Verify hidden attributes indicator appears
4. Click "Show Hidden" and verify attributes display
5. Test with item without type (no indicator)

### Task 50
1. Create new location
2. Assign location to item
3. View locations list
4. Click location to see items
5. Test autocomplete when editing item
6. Test "Your ID" field saves and displays
7. Verify fields hidden in public view
8. Test location deletion

### Task 52
1. Add items with various attribute values
2. View collection and verify smart filter badges
3. Click badge to filter by attribute value
4. Verify count accuracy
5. Test with multiple filters combined
6. Test performance with large collections

---

## Summary

**Task 48:** 2 file modifications (models, templates)
**Task 50:** ~10 files (1 model, 5 new templates, 4 updated files, URLs, migration)
**Task 52:** 2 file modifications (view, template), 1 migration

Total estimated time: 4-6 hours of development + testing
