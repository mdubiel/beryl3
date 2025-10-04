#!/usr/bin/env python3
"""
Lucide Icon Validator

This script validates all Lucide icons used in Django templates and Python code
to ensure they exist in the lucide-py library. It prevents runtime errors caused
by invalid icon names.

Usage:
    python validate_lucide.py [--fix]

Options:
    --fix    Automatically fix common icon name issues
"""

import sys
import os
import re
from pathlib import Path
from collections import defaultdict

# Add webapp to path for Django imports
WEBAPP_DIR = Path(__file__).resolve().parent.parent.parent / 'webapp'
sys.path.insert(0, str(WEBAPP_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
import django
django.setup()

from lucide import _load_icon


# Icon name mappings for common mistakes
ICON_FIXES = {
    'plus-circle': 'circle-plus',
    'alert-triangle': 'triangle-alert',
    'home': 'house',
    'more-horizontal': 'ellipsis',
    'x-circle': 'circle-x',
    'edit': 'pencil',
    'minus-circle': 'circle-minus',
}


def validate_icon(icon_name):
    """Check if an icon exists in Lucide library"""
    try:
        _load_icon(icon_name)
        return True
    except:
        return False


def extract_template_icons(template_dir):
    """Extract all Lucide icon names from Django templates"""
    icons = defaultdict(list)
    template_pattern = re.compile(r"{%\s*lucide\s+'([^']+)'")

    for template_file in Path(template_dir).rglob('*.html'):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
            matches = template_pattern.findall(content)
            for icon in matches:
                icons[icon].append(str(template_file))

    return icons


def extract_python_icons(code_dirs):
    """Extract hardcoded icon names from Python code"""
    icons = defaultdict(list)
    # Match: icon="name" or icon='name'
    icon_pattern = re.compile(r'icon\s*=\s*["\']([^"\']+)["\']')

    for code_dir in code_dirs:
        for py_file in Path(code_dir).rglob('*.py'):
            # Skip migrations
            if '/migrations/' in str(py_file):
                continue

            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = icon_pattern.findall(content)
                for icon in matches:
                    icons[icon].append(str(py_file))

    return icons


def extract_js_icons(template_dir):
    """Extract icon names from JavaScript code in templates"""
    icons = defaultdict(list)

    for template_file in Path(template_dir).rglob('*.html'):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # Only look for specific commonIcons arrays
            if 'commonIcons' in content:
                # Extract the commonIcons array
                match = re.search(r'const\s+commonIcons\s*=\s*\[(.*?)\]', content, re.DOTALL)
                if match:
                    array_content = match.group(1)
                    # Extract quoted strings
                    icon_pattern = re.compile(r"['\"]([a-z][a-z0-9-]*)['\"]")
                    matches = icon_pattern.findall(array_content)
                    for icon in matches:
                        icons[icon].append(str(template_file))

    return icons


def check_database_icons():
    """Check icons stored in database models"""
    from web.models import RecentActivity, ItemType, LinkPattern

    issues = []

    # Check RecentActivity
    for activity in RecentActivity.objects.all():
        if activity.icon and not validate_icon(activity.icon):
            issues.append(f"RecentActivity #{activity.id}: '{activity.icon}' is invalid")

    # Check ItemType
    for item_type in ItemType.objects.filter(icon__isnull=False):
        if not validate_icon(item_type.icon):
            issues.append(f"ItemType #{item_type.id} ({item_type.name}): '{item_type.icon}' is invalid")

    # Check LinkPattern
    for pattern in LinkPattern.objects.filter(icon__isnull=False):
        if not validate_icon(pattern.icon):
            issues.append(f"LinkPattern #{pattern.id} ({pattern.name}): '{pattern.icon}' is invalid")

    return issues


def fix_template_file(file_path, old_icon, new_icon):
    """Fix icon name in a template file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace in lucide tags
    pattern = re.compile(rf"{{% lucide '{old_icon}'")
    new_content = pattern.sub(f"{{% lucide '{new_icon}'", content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def fix_python_file(file_path, old_icon, new_icon):
    """Fix icon name in a Python file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace icon="old" with icon="new"
    patterns = [
        (re.compile(rf'icon\s*=\s*"{old_icon}"'), f'icon="{new_icon}"'),
        (re.compile(rf"icon\s*=\s*'{old_icon}'"), f"icon='{new_icon}'"),
    ]

    new_content = content
    for pattern, replacement in patterns:
        new_content = pattern.sub(replacement, new_content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def fix_js_icons(file_path, old_icon, new_icon):
    """Fix icon name in JavaScript code"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace 'old-icon' with 'new-icon' in JS code
    patterns = [
        (re.compile(rf"'{old_icon}'"), f"'{new_icon}'"),
        (re.compile(rf'"{old_icon}"'), f'"{new_icon}"'),
    ]

    new_content = content
    for pattern, replacement in patterns:
        new_content = pattern.sub(replacement, new_content)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    """Main validation logic"""
    fix_mode = '--fix' in sys.argv

    print("=" * 60)
    print("LUCIDE ICON VALIDATOR")
    print("=" * 60)
    print()

    template_dir = WEBAPP_DIR / 'templates'
    code_dirs = [WEBAPP_DIR / 'web', WEBAPP_DIR / 'webapp']

    # Extract all icon references
    print("Scanning templates...")
    template_icons = extract_template_icons(template_dir)

    print("Scanning Python code...")
    python_icons = extract_python_icons(code_dirs)

    print("Scanning JavaScript code...")
    js_icons = extract_js_icons(template_dir)

    # Combine all icons
    all_icons = defaultdict(set)
    for icon, files in template_icons.items():
        all_icons[icon].update(files)
    for icon, files in python_icons.items():
        all_icons[icon].update(files)
    for icon, files in js_icons.items():
        all_icons[icon].update(files)

    print(f"Found {len(all_icons)} unique icon names in code")
    print()

    # Validate icons
    invalid_icons = {}
    valid_count = 0

    for icon in sorted(all_icons.keys()):
        if validate_icon(icon):
            valid_count += 1
        else:
            invalid_icons[icon] = list(all_icons[icon])

    # Check database
    print("Checking database icons...")
    db_issues = check_database_icons()
    print()

    # Report results
    print("-" * 60)
    print(f"VALIDATION RESULTS")
    print("-" * 60)
    print(f"✓ Valid icons: {valid_count}")
    print(f"✗ Invalid icons: {len(invalid_icons)}")
    print(f"✗ Database issues: {len(db_issues)}")
    print()

    if invalid_icons:
        print("INVALID ICONS FOUND:")
        print()

        fixed_count = 0
        for icon in sorted(invalid_icons.keys()):
            files = invalid_icons[icon]
            suggested_fix = ICON_FIXES.get(icon, '?')

            print(f"  ✗ '{icon}' (suggested: '{suggested_fix}')")
            for file in sorted(files)[:3]:  # Show first 3 files
                rel_path = os.path.relpath(file, WEBAPP_DIR.parent)
                print(f"      {rel_path}")
            if len(files) > 3:
                print(f"      ... and {len(files) - 3} more files")
            print()

            # Auto-fix if enabled and we have a known fix
            if fix_mode and suggested_fix != '?':
                print(f"    Fixing '{icon}' → '{suggested_fix}'...")
                for file in files:
                    if file.endswith('.html'):
                        if 'lucide' in Path(file).read_text():
                            if fix_template_file(file, icon, suggested_fix):
                                fixed_count += 1
                        if '<script' in Path(file).read_text():
                            if fix_js_icons(file, icon, suggested_fix):
                                fixed_count += 1
                    elif file.endswith('.py'):
                        if fix_python_file(file, icon, suggested_fix):
                            fixed_count += 1
                print(f"    ✓ Fixed {fixed_count} files")
                print()

    if db_issues:
        print("DATABASE ISSUES:")
        print()
        for issue in db_issues:
            print(f"  ✗ {issue}")
        print()

    # Final summary
    print("-" * 60)
    if invalid_icons or db_issues:
        print("❌ VALIDATION FAILED")
        print()
        if fix_mode:
            print(f"Fixed {fixed_count} files automatically.")
            print("Please review changes and re-run validation.")
        else:
            print("Run with --fix to automatically correct known issues:")
            print("  python validate_lucide.py --fix")
        print()
        sys.exit(1)
    else:
        print("✅ ALL ICONS VALIDATED SUCCESSFULLY")
        print()
        print(f"All {valid_count} icons are valid and working!")
        print()
        sys.exit(0)


if __name__ == '__main__':
    main()
