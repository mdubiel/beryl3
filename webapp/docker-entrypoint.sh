#!/bin/bash
set -e

echo "🚀 Starting Beryl3 Django Application"

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for database to be ready..."
    
    # Extract database info from environment
    if [[ "$DATABASE_URL" =~ postgres://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        DB_HOST="${BASH_REMATCH[3]}"
        DB_PORT="${BASH_REMATCH[4]}"
        echo "🔍 Detected PostgreSQL at $DB_HOST:$DB_PORT"
        
        # Wait for PostgreSQL using Python socket check
        while ! python -c "import socket; sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM); result = sock.connect_ex(('$DB_HOST', int('$DB_PORT'))); sock.close(); exit(0 if result == 0 else 1)" 2>/dev/null; do
            echo "⏳ PostgreSQL is unavailable - sleeping"
            sleep 1
        done
        echo "✅ PostgreSQL is up!"
    else
        echo "📝 Using SQLite database"
    fi
}

# Function to run database migrations
run_migrations() {
    echo "🗄️  Running database migrations..."
    uv run python manage.py migrate --noinput
    echo "✅ Migrations completed"
}

# Function to collect static files
collect_static() {
    echo "📦 Collecting static files..."
    uv run python manage.py collectstatic --noinput --clear
    echo "✅ Static files collected"
}

# Function to set up required groups and initial data
setup_initial_data() {
    echo "🔐 Setting up required groups and permissions..."
    
    # Set up Application admin group
    uv run python manage.py setup_admin_group
    
    echo "✅ Initial data setup completed"
}

# Function to create superuser and add to admin group
create_superuser() {
    if [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
        echo "👤 Creating superuser if it doesn't exist..."
        uv run python manage.py shell << EOF
import os
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

if email and password:
    user, created = User.objects.get_or_create(
        email=email,
        defaults={'username': email}
    )
    
    if created:
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"✅ Superuser created: {email}")
    else:
        print(f"ℹ️  Superuser already exists: {email}")
    
    # Add superuser to Application admin group
    try:
        admin_group = Group.objects.get(name='Application admin')
        if not user.groups.filter(name='Application admin').exists():
            user.groups.add(admin_group)
            print(f"✅ Added {email} to Application admin group")
        else:
            print(f"ℹ️  {email} already in Application admin group")
    except Group.DoesNotExist:
        print("⚠️  Application admin group not found - run setup_admin_group command")
else:
    print("ℹ️  Superuser credentials not provided")
EOF
    fi
}

# Main execution
echo "🔧 Environment: ${DEBUG:-production}"

# Wait for database
wait_for_db

# Run migrations
run_migrations

# Set up required groups and initial data
setup_initial_data

# Collect static files
collect_static

# Create superuser if specified
create_superuser

# Execute the main command
echo "🎯 Starting application with command: $@"
exec "$@"