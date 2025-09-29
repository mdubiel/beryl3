"""
Management command to clear Django cache and force browser cache refresh.
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Clear Django cache and provide cache-busting guidance'

    def handle(self, *args, **options):
        # Clear Django cache
        try:
            cache.clear()
            self.stdout.write(self.style.SUCCESS("✓ Django cache cleared successfully"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠ Could not clear cache: {e}"))
        
        self.stdout.write("\n=== Cache Clearing Guide ===")
        self.stdout.write("1. Django cache: Cleared above")
        self.stdout.write("2. Browser cache: Press Ctrl+F5 (or Cmd+Shift+R on Mac) to hard refresh")
        self.stdout.write("3. CDN cache: If using a CDN, consider purging its cache")
        self.stdout.write("4. Restart Django server to clear any in-memory caches")
        
        self.stdout.write("\n=== If image still shows in browser ===")
        self.stdout.write("- Open browser developer tools (F12)")
        self.stdout.write("- Go to Network tab and check 'Disable cache'")
        self.stdout.write("- Refresh the page to force reload all resources")
        self.stdout.write("- Check if the image request returns 404 or shows a safe placeholder")