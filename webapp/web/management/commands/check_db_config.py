"""
Management command to check database configuration.
"""
import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Check database configuration and environment variables'

    def handle(self, *args, **options):
        self.stdout.write('Database Configuration Check')
        self.stdout.write('=' * 40)
        
        # Check environment variables
        env_vars = ['PG_DB', 'PG_USER', 'PG_PASSWORD', 'PG_HOST', 'PG_PORT', 'DB_ENGINE']
        
        self.stdout.write('\nEnvironment Variables:')
        for var in env_vars:
            value = os.environ.get(var, 'NOT_SET')
            # Mask password for security
            if var == 'PG_PASSWORD' and value != 'NOT_SET':
                value = '***MASKED***'
            self.stdout.write(f'  {var}: {value}')
        
        # Check Django database configuration
        self.stdout.write('\nDjango Database Configuration:')
        db_config = settings.DATABASES['default']
        for key, value in db_config.items():
            # Mask password for security
            if key == 'PASSWORD' and value:
                value = '***MASKED***'
            self.stdout.write(f'  {key}: {value}')
        
        # Check if we can import the database backend
        self.stdout.write('\nDatabase Backend Check:')
        try:
            from django.db import connection
            backend = connection.vendor
            self.stdout.write(f'  Backend: {backend}')
            
            # Try to get database info
            if backend == 'postgresql':
                self.stdout.write('  ✅ PostgreSQL backend detected')
            elif backend == 'sqlite':
                self.stdout.write('  ⚠️  SQLite backend detected')
            else:
                self.stdout.write(f'  ❓ Unknown backend: {backend}')
                
        except Exception as e:
            self.stdout.write(f'  ❌ Error checking backend: {e}')
        
        self.stdout.write('\nConfiguration Check Complete')