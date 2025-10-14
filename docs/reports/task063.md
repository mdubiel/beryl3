# Task 63: Fix Dropdown Z-Index Issue on Public Collection Pages

**Status:** ✅ Completed

**Description:**
Fixed z-index stacking issues where dropdown menus (font selector and user menu) were appearing behind the breadcrumb navigation on public collection pages with background images.

## Problem

On `/share/collections/<hash>` pages with background images, the dropdown menus in the header were being rendered behind the breadcrumb navigation, making them unusable.

**Root Cause:**
The issue was caused by complex stacking context interactions:
1. Template blocks were injecting classes that created stacking contexts on parent elements
2. The header had `z-10 relative` which created a stacking context that trapped dropdowns
3. The main container had `relative z-1` which further complicated z-index hierarchy
4. Breadcrumbs and header were in different stacking contexts

## Solution

### Key Changes

1. **Removed z-index and positioning from header element** (`base.html:129`)
   - Changed from: `<header class="flex items-center justify-between py-4 px-2 z-10 relative {% block header_classes %}{% endblock %}">`
   - Changed to: `<header class="flex items-center justify-between py-4 px-2">`
   - This prevents the header from creating its own stacking context

2. **Simplified breadcrumbs styling** (`base.html:215`)
   - Changed from: `<div class="text-sm breadcrumbs px-4 py-4 z-10 relative {% block breadcrumbs_classes %}{% endblock %}">`
   - Changed to: `<div class="text-sm breadcrumbs px-4 pt-4 {% block breadcrumbs_classes %}{% endblock %}">`
   - Removed z-index and relative positioning, kept conditional styling via blocks

3. **Moved breadcrumbs inside main container** (`base.html:212-234`)
   - Moved breadcrumbs from outside the navbar wrapper to inside the main content area wrapper
   - This ensures both header and breadcrumbs are in the same stacking context hierarchy

4. **Kept dropdown z-index at default DaisyUI value** (`base.html:147,182,203`)
   - Dropdowns use `z-[1]` which works with DaisyUI's default `z-index: 999` on `.dropdown-content`
   - DaisyUI's `position: absolute` on dropdowns allows them to float above other elements

5. **Removed container z-index override** (`collection_public_detail.html:16`)
   - Removed `{% block container_classes %}relative z-1{% endblock %}`
   - Container only uses conditional `relative` positioning when needed

6. **Created dedicated CSS class for header wrapper** (`input.css:195-197`)
   - Added `.public-collection-header-wrapper` class with background styling
   - Migrated inline classes to proper CSS class
   - Applied to header wrapper div via template block

7. **Simplified header wrapper spacing** (`base.html:128`)
   - Changed from: `<div class="space-y-4 mt-4 mb-8{% block header_wrapper_classes %}{% endblock %}">`
   - Changed to: `<div class="mt-4 mb-8 {% block header_wrapper_classes %}{% endblock %}">`
   - Removed `space-y-4` which was interfering with background coverage

## Technical Details

### Template Structure (base.html)

```django
<div class="w-11/12 md:w-5/6 lg:w-4/5 mx-auto {% block container_classes %}{% endblock %}">

    {# Navbar - outside frame #}
    <div class="mt-4 mb-8 {% block header_wrapper_classes %}{% endblock %}">
    <header class="flex items-center justify-between py-4 px-2">
        <!-- Header content with dropdowns -->
        <div class="dropdown dropdown-end">
            <ul tabindex="0" class="dropdown-content menu bg-base-100 rounded-box z-[1] w-52 p-2 shadow">
                <!-- Dropdown items -->
            </ul>
        </div>
    </header>

    {# Main content area #}
    <div class="bg-base-100 relative {% block content_wrapper_classes %}{% endblock %}">
        {% if request.resolver_match.url_name != 'index' %}
        <div class="text-sm breadcrumbs px-4 pt-4 {% block breadcrumbs_classes %}{% endblock %}">
            <!-- Breadcrumbs -->
        </div>
        {% endif %}

        <main>
            {% block content %}{% endblock %}
        </main>
    </div>

    </div> {# End of navbar #}
</div>
```

### CSS Classes (input.css)

```css
.public-collection-header-wrapper {
  @apply bg-white/50 backdrop-blur-lg shadow-sm;
}

.public-collection-breadcrumbs {
  @apply bg-white/50 backdrop-blur-lg shadow-sm;
}

.public-collection-breadcrumbs ul {
  @apply items-center;
}

.public-collection-breadcrumbs a,
.public-collection-breadcrumbs span {
  @apply text-gray-800;
}
```

### Public Collection Template (collection_public_detail.html)

```django
{% if background_image_url %}
{% block body_classes %}public-collection-bg public-collection-overlay{% endblock %}
{% block body_style %}style="background-image: url('{{ background_image_url }}');"{% endblock %}
{% block header_wrapper_classes %}public-collection-header-wrapper{% endblock %}
{% block breadcrumbs_classes %}public-collection-breadcrumbs{% endblock %}
{% block content_wrapper_classes %}public-collection-transparent-bg{% endblock %}
{% endif %}
```

## Z-Index Hierarchy

Final stacking order (from bottom to top):
1. Background overlay: `z-index: -1` (fixed position, behind everything)
2. Regular content: `z-index: auto` (normal flow)
3. Header wrapper background: No z-index, uses template blocks for conditional styling
4. Breadcrumbs: No z-index, styled via CSS class
5. Dropdowns: `z-index: 999` (DaisyUI default from `.dropdown-content` class)

## Key Principles Applied

1. **Avoid creating stacking contexts unnecessarily** - Removed `position: relative` and `z-index` from elements that don't need them
2. **Use DaisyUI defaults** - Leveraged DaisyUI's built-in dropdown positioning rather than fighting it
3. **Separation of concerns** - Styling in CSS classes, structure in templates, conditional logic in Django template blocks
4. **Django template inheritance** - Used template blocks for conditional class injection (correct Django pattern)

## Files Modified

1. `/home/mdubiel/projects/beryl3/webapp/templates/base.html`
   - Removed z-index from header
   - Simplified breadcrumbs positioning
   - Moved breadcrumbs structure
   - Added header wrapper class block
   - Simplified header wrapper spacing

2. `/home/mdubiel/projects/beryl3/webapp/templates/public/collection_public_detail.html`
   - Removed container z-index override
   - Changed to use CSS class for header wrapper

3. `/home/mdubiel/projects/beryl3/webapp/src/input.css`
   - Added `.public-collection-header-wrapper` class

## Testing

Test on pages:
- `/share/collections/<hash>` with background image
- `/share/collections/<hash>` without background image
- Regular user pages (should be unaffected)

Verify:
1. Font selector dropdown appears above breadcrumbs
2. User menu dropdown appears above breadcrumbs
3. Header has proper background styling with backdrop blur
4. Breadcrumbs have proper background styling
5. Dropdowns close properly on click outside
6. All navigation works correctly

## Notes

- The use of Django template blocks (`{% block header_wrapper_classes %}`) is intentional and follows Django best practices
- These blocks allow child templates to conditionally inject CSS classes into parent template elements
- The alternative (separate templates or view-level logic) would be more complex and less maintainable
- All styling classes are now properly defined in `input.css` for centralized CSS management
- DaisyUI's dropdown component handles positioning automatically via `position: absolute` on `.dropdown-content`
