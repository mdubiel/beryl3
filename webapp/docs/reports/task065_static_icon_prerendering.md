# Task 65: Static Icon Pre-rendering Plan

## Concept

Replace runtime `{% lucide_cached %}` template tag processing with **build-time icon pre-rendering**. Icons are rendered once during deployment and embedded directly as static HTML/SVG in templates.

## Benefits

### Performance
- **Zero runtime overhead** - no template tag processing at all
- **Faster than lucide_cached** - no LRU cache lookup needed
- **Smallest possible overhead** - direct HTML output

### Expected Improvement
```
Current (lucide_cached): 50ms per item → 5-10ms per item
After (static icons):    50ms per item → 0-1ms per item

Total page load:
- Current: 1.5s (cold), 0.5s (warm)
- After:   1.0s (cold), 0.3s (warm)
```

## Implementation Approaches

### Approach 1: Template Pre-processor (Recommended)

**Concept**: During deployment, scan templates and replace `{% lucide %}` tags with rendered SVG HTML.

**Workflow**:
```
1. Pre-deployment: Templates contain {% lucide 'star' size=20 %}
2. Build step: Script scans and replaces with actual SVG
3. Post-deployment: Templates contain <svg>...</svg>
4. Runtime: Django just outputs static HTML
```

**Pros**:
- ✅ Zero runtime overhead
- ✅ No code changes to templates (automated)
- ✅ Can be rolled back easily
- ✅ Works with existing caching

**Cons**:
- ⚠️ Build step complexity
- ⚠️ Larger template files
- ⚠️ Need to track original vs compiled templates

### Approach 2: Template Compilation to Python

**Concept**: Compile templates to Python code with embedded SVG strings.

**Similar to**: Django's cached template loader, but with icon pre-rendering.

**Pros**:
- ✅ Maximum performance
- ✅ Native Python execution
- ✅ Can optimize entire template

**Cons**:
- ❌ High complexity
- ❌ Harder to debug
- ❌ Major architectural change

### Approach 3: Django Template Fragment Pre-rendering

**Concept**: Create a management command that pre-renders template fragments with icons and stores them.

**Workflow**:
```python
# During deployment
python manage.py prerender_icons

# Creates static HTML fragments
icons/star-20-primary.html
icons/tag-12-neutral.html
...

# Templates include these
{% include "icons/star-20-primary.html" %}
```

**Pros**:
- ✅ Simple implementation
- ✅ Reusable across templates
- ✅ Easy to manage and cache

**Cons**:
- ⚠️ Manual template updates needed
- ⚠️ More files to manage

### Approach 4: Build-time Template Macro Expansion

**Concept**: Create a custom template preprocessor that expands macros at build time.

**Example**:
```django
{# Before build #}
{% icon 'star' 20 'text-primary' %}

{# After build - expanded to: #}
<svg width="20" height="20" class="text-primary">
  <path d="M12 2l3.09..."/>
</svg>
```

**Pros**:
- ✅ Clean syntax
- ✅ Type-safe (validates at build time)
- ✅ Can expand other macros too

**Cons**:
- ⚠️ Custom preprocessor maintenance
- ⚠️ Need build pipeline

## Recommended Implementation: Approach 1 (Template Pre-processor)

### Phase 1: Create Pre-rendering Script

**File**: `workflows/bin/prerender_lucide_icons.py`

```python
#!/usr/bin/env python
"""
Pre-render lucide icons in Django templates.

Scans templates for {% lucide %} tags, renders them to SVG,
and creates optimized templates with inline SVG.

Usage:
    python workflows/bin/prerender_lucide_icons.py --env production
    python workflows/bin/prerender_lucide_icons.py --dry-run
"""
import os
import re
import sys
from pathlib import Path
from typing import Dict, Tuple

# Setup Django
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'webapp'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')

import django
django.setup()

from lucide.templatetags.lucide import lucide as original_lucide


class IconPrerenderer:
    """Pre-renders lucide icons in Django templates"""

    # Regex to match {% lucide 'name' size=X class='...' %}
    LUCIDE_PATTERN = re.compile(
        r"{%\s*lucide(?:_cached)?\s+"
        r"'(?P<name>[^']+)'|\"(?P<name2>[^\"]+)\""
        r"(?:\s+size=(?P<size>\d+))?"
        r"(?P<kwargs>(?:\s+\w+=(?:'[^']*'|\"[^\"]*\"))*)"
        r"\s*%}"
    )

    def __init__(self, template_dir: Path, output_dir: Path = None):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir) if output_dir else template_dir / 'compiled'
        self.icon_cache: Dict[str, str] = {}

    def parse_kwargs(self, kwargs_str: str) -> dict:
        """Parse kwargs from template tag string"""
        kwargs = {}
        if not kwargs_str:
            return kwargs

        # Match key='value' or key="value"
        pattern = r"(\w+)=(?:'([^']*)'|\"([^\"]*)\")"
        for match in re.finditer(pattern, kwargs_str):
            key = match.group(1)
            value = match.group(2) or match.group(3)
            kwargs[key] = value

        return kwargs

    def render_icon(self, name: str, size: int = 24, **kwargs) -> str:
        """Render a lucide icon to SVG string"""
        cache_key = f"{name}:{size}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"

        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        # Use original lucide function
        svg = original_lucide(name, size=size, **kwargs)

        self.icon_cache[cache_key] = svg
        return svg

    def prerender_template(self, template_path: Path) -> Tuple[str, int]:
        """
        Pre-render lucide icons in a template.
        Returns: (rendered_content, replacement_count)
        """
        with open(template_path, 'r') as f:
            content = f.read()

        replacement_count = 0

        def replace_icon(match):
            nonlocal replacement_count

            # Extract parameters
            name = match.group('name') or match.group('name2')
            size = int(match.group('size')) if match.group('size') else 24
            kwargs_str = match.group('kwargs') or ''
            kwargs = self.parse_kwargs(kwargs_str)

            # Render icon
            svg = self.render_icon(name, size, **kwargs)

            replacement_count += 1

            # Add comment for debugging
            return f"{{# lucide '{name}' size={size} - pre-rendered #}}\n{svg}"

        # Replace all lucide tags
        rendered_content = self.LUCIDE_PATTERN.sub(replace_icon, content)

        return rendered_content, replacement_count

    def process_template_file(self, template_path: Path, dry_run: bool = False):
        """Process a single template file"""
        print(f"Processing: {template_path.relative_to(self.template_dir)}")

        rendered_content, count = self.prerender_template(template_path)

        if count == 0:
            print(f"  └─ No lucide icons found")
            return

        print(f"  └─ Pre-rendered {count} icon(s)")

        if not dry_run:
            # Create output directory
            output_path = self.output_dir / template_path.relative_to(self.template_dir)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write rendered template
            with open(output_path, 'w') as f:
                f.write(rendered_content)

            print(f"  └─ Saved to: {output_path.relative_to(self.template_dir.parent)}")

    def process_all_templates(self, dry_run: bool = False):
        """Process all templates in template directory"""
        template_files = list(self.template_dir.rglob('*.html'))

        print(f"Found {len(template_files)} template files")
        print()

        total_icons = 0

        for template_path in template_files:
            try:
                _, count = self.prerender_template(template_path)
                total_icons += count

                if count > 0:
                    self.process_template_file(template_path, dry_run)

            except Exception as e:
                print(f"ERROR processing {template_path}: {e}")

        print()
        print(f"Total icons pre-rendered: {total_icons}")
        print(f"Unique icons cached: {len(self.icon_cache)}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Pre-render lucide icons in templates')
    parser.add_argument('--template-dir', default='webapp/templates',
                       help='Template directory to process')
    parser.add_argument('--output-dir',
                       help='Output directory (default: template-dir/compiled)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be done without writing files')
    parser.add_argument('--env', choices=['local', 'qa', 'production'],
                       default='local', help='Target environment')

    args = parser.parse_args()

    template_dir = Path(args.template_dir)
    output_dir = Path(args.output_dir) if args.output_dir else None

    if not template_dir.exists():
        print(f"ERROR: Template directory not found: {template_dir}")
        sys.exit(1)

    print("="*80)
    print("LUCIDE ICON PRE-RENDERING")
    print("="*80)
    print(f"Environment: {args.env}")
    print(f"Template dir: {template_dir}")
    print(f"Output dir: {output_dir or template_dir / 'compiled'}")
    print(f"Dry run: {args.dry_run}")
    print()

    prerenderer = IconPrerenderer(template_dir, output_dir)
    prerenderer.process_all_templates(dry_run=args.dry_run)

    if args.dry_run:
        print()
        print("DRY RUN - No files were modified")
    else:
        print()
        print("Pre-rendering complete!")


if __name__ == '__main__':
    main()
```

### Phase 2: Deployment Integration

**Update deployment scripts to run pre-rendering**:

#### For Django Europe Production

Add to deployment workflow:

```bash
# In workflows/bin/dje-deploy-project.py or Makefile

# Step 1: Pre-render icons
echo "Pre-rendering lucide icons..."
python workflows/bin/prerender_lucide_icons.py \
    --template-dir webapp/templates \
    --output-dir webapp/templates/compiled \
    --env production

# Step 2: Update settings to use compiled templates
export DJANGO_TEMPLATE_DIRS="webapp/templates/compiled,webapp/templates"

# Step 3: Deploy as normal
rsync -av webapp/templates/compiled/ mdubiel@s30:~/beryl3-prod/templates/

# Step 4: Restart service
ssh mdubiel@s30 "cd ~/beryl3-prod && sudo systemctl restart beryl3-prod-service"
```

#### Settings Configuration

Update `webapp/settings.py`:

```python
# Template configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # Compiled templates (with pre-rendered icons) take precedence
            BASE_DIR / 'templates' / 'compiled',
            # Fallback to source templates
            BASE_DIR / 'templates',
        ],
        # ...
    },
]
```

### Phase 3: Rollback Strategy

**Preserve original templates**:

```bash
# Keep original templates in git
git add webapp/templates/*.html

# Compiled templates are generated (in .gitignore)
echo "webapp/templates/compiled/" >> .gitignore

# To rollback: Just remove compiled directory
rm -rf webapp/templates/compiled/
# Django falls back to original templates
```

### Phase 4: CI/CD Integration

**Add to GitHub Actions / CI pipeline**:

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Pre-render icons
        run: |
          python workflows/bin/prerender_lucide_icons.py \
            --env production

      - name: Deploy to production
        run: |
          # Your deployment script
          ./deploy.sh
```

## Alternative: Inline During Collectstatic

**Integrate with Django's collectstatic**:

```python
# Create custom storage backend

from django.contrib.staticfiles.storage import StaticFilesStorage

class IconPrerenderedStorage(StaticFilesStorage):
    """Storage that pre-renders icons during collectstatic"""

    def post_process(self, paths, dry_run=False, **options):
        # Pre-render icons in templates
        prerenderer = IconPrerenderer(settings.TEMPLATE_DIRS[0])
        prerenderer.process_all_templates(dry_run=dry_run)

        # Continue with normal static file processing
        return super().post_process(paths, dry_run, **options)
```

```python
# settings.py
STATICFILES_STORAGE = 'myapp.storage.IconPrerenderedStorage'
```

**Usage**:
```bash
python manage.py collectstatic
# Automatically pre-renders icons as part of static collection
```

## Testing Strategy

### Test 1: Verify Rendering Correctness

```python
def test_prerendering():
    """Ensure pre-rendered icons match runtime rendering"""
    from lucide.templatetags.lucide import lucide

    # Render at runtime
    runtime_svg = lucide('star', size=20, class_='text-primary')

    # Pre-render
    prerenderer = IconPrerenderer(...)
    prerendered_svg = prerenderer.render_icon('star', 20, class_='text-primary')

    assert runtime_svg == prerendered_svg
```

### Test 2: Performance Comparison

```python
def test_performance():
    """Measure performance improvement"""
    import time

    # Template with {% lucide %} tags
    template_runtime = Template("{% load lucide %}{% lucide 'star' %}")

    # Pre-rendered template
    template_static = Template("<svg>...</svg>")

    # Benchmark
    start = time.time()
    for _ in range(1000):
        template_runtime.render(Context())
    runtime_time = time.time() - start

    start = time.time()
    for _ in range(1000):
        template_static.render(Context())
    static_time = time.time() - start

    improvement = (runtime_time - static_time) / runtime_time * 100
    print(f"Improvement: {improvement:.1f}%")
```

## Monitoring

### Track Pre-rendering in Logs

```python
# Add to pre-rendering script
import logging

logger = logging.getLogger('deployment')

logger.info(f"Pre-rendered {count} icons in {elapsed:.2f}s")
logger.info(f"Cache size: {len(prerenderer.icon_cache)} unique icons")
logger.info(f"Templates processed: {len(template_files)}")
```

### Verify in Production

```bash
# Check that compiled templates exist
ssh mdubiel@s30 "ls -la ~/beryl3-prod/templates/compiled/partials/"

# Verify icons are pre-rendered (should see <svg> not {% lucide %})
ssh mdubiel@s30 "grep -c '<svg' ~/beryl3-prod/templates/compiled/partials/_item_public_card.html"
ssh mdubiel@s30 "grep -c 'lucide' ~/beryl3-prod/templates/compiled/partials/_item_public_card.html"
# Should show 0 for lucide tags, >0 for <svg> tags
```

## Risks and Mitigation

### Risk 1: Build Failures

**Mitigation**:
- Keep original templates in git
- Compiled templates in .gitignore
- Fallback to originals if pre-rendering fails

### Risk 2: Icon Changes Not Reflected

**Mitigation**:
- Always re-run pre-rendering on deployment
- Clear compiled templates before building
- Version compiled templates with source hash

### Risk 3: Dynamic Icons (Variable Names)

**Problem**: `{% lucide item.icon %}` can't be pre-rendered

**Solution**:
- Use lucide_cached for dynamic icons
- Pre-render only static icon names
- Hybrid approach: static where possible, cached for dynamic

```python
# Pre-processor detects and skips dynamic icons
if re.match(r'^[a-z-]+$', icon_name):  # Static name
    # Pre-render
else:  # Variable like item.icon
    # Keep as {% lucide_cached %}
```

## Implementation Timeline

### Phase 1: Prototype (1-2 days)
- [ ] Create prerender_lucide_icons.py script
- [ ] Test on single template
- [ ] Verify correctness
- [ ] Measure performance improvement

### Phase 2: Integration (2-3 days)
- [ ] Integrate with deployment scripts
- [ ] Update settings for compiled templates
- [ ] Test on staging/QA
- [ ] Document rollback procedure

### Phase 3: Production (1 day)
- [ ] Deploy to production
- [ ] Monitor performance
- [ ] Verify icon rendering
- [ ] Measure actual improvement

### Phase 4: Optimization (ongoing)
- [ ] Add CI/CD integration
- [ ] Optimize pre-rendering speed
- [ ] Add caching for incremental builds
- [ ] Monitor and tune

## Expected Results

### Performance

**Current (with lucide_cached)**:
```
Template rendering per item: ~50ms
- Icon rendering: ~5-10ms (cached)
- Other template tags: ~40ms

25 items = 1,250ms
Total page: ~1.5s (cold), 0.5s (warm)
```

**After (with pre-rendered icons)**:
```
Template rendering per item: ~40-45ms
- Icon rendering: ~0ms (static HTML)
- Other template tags: ~40ms

25 items = 1,000-1,125ms
Total page: ~1.0s (cold), 0.3s (warm)
```

**Improvement**: Additional 20-30% reduction in template rendering time

### Build Time

- Pre-rendering 100 templates: ~1-2 seconds
- Incremental (10 changed templates): <0.5 seconds
- Acceptable overhead for deployment

## Conclusion

Pre-rendering lucide icons at build time provides:
- ✅ Best possible runtime performance (zero overhead)
- ✅ Simple rollback (remove compiled directory)
- ✅ Compatible with existing caching
- ✅ Scales well (build once, serve millions)

**Recommended**: Implement Approach 1 (Template Pre-processor) for maximum benefit with minimal risk.

**Next Steps**:
1. Create the pre-rendering script
2. Test locally with a few templates
3. Integrate with deployment pipeline
4. Monitor and measure improvement
