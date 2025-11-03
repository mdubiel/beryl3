#!/usr/bin/env python
"""
Task 65 - Hot patch for default_image property to use prefetch cache
This is a temporary inline patch for production testing.

Usage on production:
    scp workflows/tasks/task65_patch_default_image.py mdubiel@s30:~/beryl3/
    ssh mdubiel@s30
    cd ~/beryl3
    source .virtualenvs/beryl3/bin/activate
    python task65_patch_default_image.py
"""
import os
import sys

# Path to models.py
MODELS_FILE = '/home/mdubiel/beryl3/webapp/web/models.py'

# Backup file
BACKUP_FILE = '/home/mdubiel/beryl3/webapp/web/models.py.bak-task65'

def create_backup():
    """Create backup of models.py"""
    import shutil
    if not os.path.exists(BACKUP_FILE):
        shutil.copy2(MODELS_FILE, BACKUP_FILE)
        print(f"✅ Created backup: {BACKUP_FILE}")
    else:
        print(f"ℹ️  Backup already exists: {BACKUP_FILE}")

def apply_patch():
    """Apply the patch to fix default_image property"""

    # Read the file
    with open(MODELS_FILE, 'r') as f:
        content = f.read()

    # Find and replace the default_image property for CollectionItem
    old_code = '''    @property
    def default_image(self):
        """Get the default image for this collection item"""
        return self.images.filter(is_default=True).first()'''

    new_code = '''    @property
    def default_image(self):
        """Get the default image for this collection item (uses prefetch cache when available)"""
        # Task 65: Use prefetch cache if available to avoid N+1 queries
        if hasattr(self, '_prefetched_objects_cache') and 'images' in self._prefetched_objects_cache:
            # Use prefetched data - iterate through cached images
            for img in self.images.all():  # Uses prefetch cache
                if img.is_default:
                    return img
            return None
        # Fallback to database query if not prefetched
        return self.images.filter(is_default=True).first()'''

    if old_code in content:
        content = content.replace(old_code, new_code)

        # Write back
        with open(MODELS_FILE, 'w') as f:
            f.write(content)

        print("✅ Patch applied successfully!")
        print("\n📝 Changed CollectionItem.default_image property to use prefetch cache")
        return True
    else:
        print("⚠️  Could not find the exact code to replace.")
        print("The file may have already been patched or has changed.")
        return False

def verify_patch():
    """Verify the patch was applied"""
    with open(MODELS_FILE, 'r') as f:
        content = f.read()

    if '_prefetched_objects_cache' in content and "Task 65: Use prefetch cache" in content:
        print("✅ Patch verification successful - new code is present")
        return True
    else:
        print("❌ Patch verification failed - code not found")
        return False

def restart_service():
    """Instructions to restart the service"""
    print("\n" + "="*80)
    print("🔄 NEXT STEPS:")
    print("="*80)
    print("\n1. Restart the Django application:")
    print("   sudo systemctl restart beryl3-service")
    print("\n2. Check the service status:")
    print("   sudo systemctl status beryl3-service")
    print("\n3. Test the collection:")
    print("   https://beryl3.com/share/collections/j6qJIB8loJ/")
    print("\n4. To rollback if needed:")
    print(f"   cp {BACKUP_FILE} {MODELS_FILE}")
    print("   sudo systemctl restart beryl3-service")
    print("\n" + "="*80)

if __name__ == '__main__':
    print("="*80)
    print("Task 65: Hot Patch - Fix default_image Property")
    print("="*80)
    print()

    # Check if file exists
    if not os.path.exists(MODELS_FILE):
        print(f"❌ Error: {MODELS_FILE} not found!")
        print("Make sure you're running this on the production server in the correct directory.")
        sys.exit(1)

    # Create backup
    create_backup()

    # Apply patch
    if apply_patch():
        # Verify
        if verify_patch():
            print("\n✅ Patch applied and verified successfully!")
            restart_service()
        else:
            print("\n❌ Patch verification failed!")
            sys.exit(1)
    else:
        print("\n❌ Patch application failed!")
        sys.exit(1)
