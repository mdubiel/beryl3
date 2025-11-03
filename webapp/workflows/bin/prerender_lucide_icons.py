#!/usr/bin/env python
"""
Pre-render lucide icons in Django templates.

Scans templates for {% lucide %} or {% lucide_cached %} tags, renders them to SVG,
and creates optimized templates with inline SVG.

Usage:
    python workflows/bin/prerender_lucide_icons.py
    python workflows/bin/prerender_lucide_icons.py --dry-run
    python workflows/bin/prerender_lucide_icons.py --template-dir webapp/templates/partials
"""
import os
import re
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional

# Setup Django
SCRIPT_DIR = Path(__file__).parent.resolve()
WEBAPP_DIR = SCRIPT_DIR.parent.parent
PROJECT_ROOT = WEBAPP_DIR.parent

sys.path.insert(0, str(WEBAPP_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')

import django
django.setup()

from lucide.templatetags.lucide import lucide as original_lucide


class IconPrerenderer:
    """Pre-renders lucide icons in Django templates"""

    # Regex to match {% lucide 'name' size=X class='...' %} or {% lucide_cached ... %}
    LUCIDE_PATTERN = re.compile(
        r"{%\s*lucide(?:_cached)?\s+"
        r"(?:'(?P<name1>[^']+)'|\"(?P<name2>[^\"]+)\")"
        r"(?:\s+size=(?P<size>\d+))?"
        r"(?P<kwargs>(?:\s+\w+(?:_\w+)*=(?:'[^']*'|\"[^\"]*\"))*)"
        r"\s*%}",
        re.MULTILINE
    )

    def __init__(self, template_dir: Path, output_dir: Optional[Path] = None):
        self.template_dir = Path(template_dir)
        self.output_dir = Path(output_dir) if output_dir else self.template_dir.parent / 'templates_compiled'
        self.icon_cache: Dict[str, str] = {}
        self.stats = {
            'files_processed': 0,
            'files_with_icons': 0,
            'total_icons': 0,
            'unique_icons': 0,
        }

    def parse_kwargs(self, kwargs_str: str) -> dict:
        """Parse kwargs from template tag string"""
        kwargs = {}
        if not kwargs_str:
            return kwargs

        # Match key='value' or key="value", handle underscores in keys
        pattern = r"(\w+(?:_\w+)*)=(?:'([^']*)'|\"([^\"]*)\")"
        for match in re.finditer(pattern, kwargs_str):
            key = match.group(1)
            value = match.group(2) or match.group(3)
            # Convert underscores to hyphens for HTML attributes
            key = key.replace('_', '-')
            kwargs[key] = value

        return kwargs

    def render_icon(self, name: str, size: int = 24, **kwargs) -> str:
        """Render a lucide icon to SVG string"""
        # Convert hyphenated kwargs back to underscored for lucide
        lucide_kwargs = {k.replace('-', '_'): v for k, v in kwargs.items()}

        cache_key = f"{name}:{size}:{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"

        if cache_key in self.icon_cache:
            return self.icon_cache[cache_key]

        try:
            # Use original lucide function
            svg = original_lucide(name, size=size, **lucide_kwargs)
            self.icon_cache[cache_key] = svg
            return svg
        except Exception as e:
            # If icon rendering fails, return a comment with error
            error_msg = f"<!-- Error rendering icon '{name}': {e} -->"
            self.icon_cache[cache_key] = error_msg
            return error_msg

    def prerender_template(self, template_path: Path) -> Tuple[str, int]:
        """
        Pre-render lucide icons in a template.
        Returns: (rendered_content, replacement_count)
        """
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()

        replacement_count = 0

        def replace_icon(match):
            nonlocal replacement_count

            # Extract parameters
            name = match.group('name1') or match.group('name2')
            size_str = match.group('size')
            size = int(size_str) if size_str else 24
            kwargs_str = match.group('kwargs') or ''
            kwargs = self.parse_kwargs(kwargs_str)

            # Render icon
            svg = self.render_icon(name, size, **kwargs)

            replacement_count += 1

            # Format the replacement with comment for debugging
            kwargs_display = ' '.join(f'{k}={v}' for k, v in kwargs.items())
            comment = f"{{# lucide '{name}' size={size} {kwargs_display} - pre-rendered #}}"

            return f"{comment}\n{svg}"

        # Replace all lucide tags
        rendered_content = self.LUCIDE_PATTERN.sub(replace_icon, content)

        return rendered_content, replacement_count

    def process_template_file(self, template_path: Path, dry_run: bool = False) -> int:
        """
        Process a single template file.
        Returns: Number of icons pre-rendered
        """
        try:
            rendered_content, count = self.prerender_template(template_path)

            if count == 0:
                return 0

            rel_path = template_path.relative_to(self.template_dir)
            print(f"  {rel_path}: {count} icon(s)")

            if not dry_run:
                # Create output directory
                output_path = self.output_dir / rel_path
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Write rendered template
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(rendered_content)

            self.stats['files_with_icons'] += 1
            self.stats['total_icons'] += count
            return count

        except Exception as e:
            print(f"  ERROR processing {template_path.name}: {e}")
            return 0

    def process_all_templates(self, dry_run: bool = False, pattern: str = '**/*.html'):
        """Process all templates matching pattern"""
        template_files = list(self.template_dir.glob(pattern))

        if not template_files:
            print(f"No templates found matching pattern: {pattern}")
            return

        print(f"Found {len(template_files)} template file(s)")
        print()

        for template_path in sorted(template_files):
            self.stats['files_processed'] += 1
            self.process_template_file(template_path, dry_run)

        self.stats['unique_icons'] = len(self.icon_cache)

    def print_summary(self, dry_run: bool = False):
        """Print summary statistics"""
        print()
        print("="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Files processed:       {self.stats['files_processed']}")
        print(f"Files with icons:      {self.stats['files_with_icons']}")
        print(f"Total icons rendered:  {self.stats['total_icons']}")
        print(f"Unique icon variants:  {self.stats['unique_icons']}")

        if dry_run:
            print()
            print("DRY RUN - No files were modified")
        else:
            print()
            print(f"Output directory:      {self.output_dir}")
            print()
            print("✅ Pre-rendering complete!")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Pre-render lucide icons in Django templates',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Pre-render all templates
  python workflows/bin/prerender_lucide_icons.py

  # Dry run to see what would happen
  python workflows/bin/prerender_lucide_icons.py --dry-run

  # Pre-render only partials
  python workflows/bin/prerender_lucide_icons.py --template-dir webapp/templates/partials

  # Custom output directory
  python workflows/bin/prerender_lucide_icons.py --output-dir /tmp/compiled
        """
    )

    parser.add_argument(
        '--template-dir',
        default='webapp/templates',
        help='Template directory to process (default: webapp/templates)'
    )
    parser.add_argument(
        '--output-dir',
        help='Output directory (default: <template-dir>/../templates_compiled)'
    )
    parser.add_argument(
        '--pattern',
        default='**/*.html',
        help='File pattern to match (default: **/*.html)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without writing files'
    )

    args = parser.parse_args()

    # Resolve paths
    template_dir = Path(args.template_dir)
    if not template_dir.is_absolute():
        template_dir = WEBAPP_DIR / args.template_dir

    output_dir = None
    if args.output_dir:
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = WEBAPP_DIR / args.output_dir

    if not template_dir.exists():
        print(f"ERROR: Template directory not found: {template_dir}")
        sys.exit(1)

    # Print header
    print("="*80)
    print("LUCIDE ICON PRE-RENDERING")
    print("="*80)
    print(f"Template dir:  {template_dir}")
    print(f"Output dir:    {output_dir or template_dir.parent / 'templates_compiled'}")
    print(f"Pattern:       {args.pattern}")
    print(f"Dry run:       {args.dry_run}")
    print()

    # Create prerenderer and process templates
    prerenderer = IconPrerenderer(template_dir, output_dir)
    prerenderer.process_all_templates(dry_run=args.dry_run, pattern=args.pattern)
    prerenderer.print_summary(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
