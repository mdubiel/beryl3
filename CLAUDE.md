# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Beryl is a Django-based collection management system with user authentication, item tracking, and sharing capabilities. The project uses a monorepo structure managed with uv workspace, combining Python Django backend with Tailwind CSS frontend.

## Development Commands

### Essential Commands
```bash
# Run development server
cd webapp && make run-dev-server

# Build Tailwind CSS
cd webapp && make build-css

# Build CSS with watch mode
cd webapp && make build-css-watch

# Database migrations
cd webapp && make makemigrations
cd webapp && make migrate

# Clean up generated files
cd webapp && make clean

# Run using Docker
docker compose --file docker/docker-compose.yaml --env-file webapp/.env up
```

### Python/Django Commands
All Python commands use uv and should be run from the `webapp/` directory:
```bash
# Run management commands
uv run python manage.py <command>

# Run development server directly
uv run python manage.py runserver 0.0.0.0:8000

# Create superuser
uv run python manage.py createsuperuser

# Run shell
uv run python manage.py shell
```

## Project Structure

### Workspace Configuration
- Root `pyproject.toml` defines the workspace with `webapp/` as a member
- `webapp/pyproject.toml` contains the Django app dependencies
- Uses uv for Python package management

### Django Architecture
```
webapp/
├── webapp/          # Django project settings
│   ├── settings.py  # Main settings with env-based configuration
│   ├── urls.py      # Root URL configuration
│   └── ...
├── web/             # Main Django app
│   ├── models.py    # Core models (BerylModel, Collection, CollectionItem)
│   ├── views/       # Organized view modules
│   │   ├── collection.py
│   │   ├── items.py
│   │   ├── public.py
│   │   └── ...
│   └── ...
├── core/            # Core utilities app
├── api/             # API app
└── templates/       # Django templates
```

### Key Models and Features
- **BerylModel**: Base model with soft deletion (`is_deleted` field) and NanoidField for hashes
- **Collection**: User collections with visibility controls (public/private)
- **CollectionItem**: Items within collections with status tracking
- **RecentActivity**: User activity logging
- **Sharing**: Collections can be shared via public URLs

### Authentication
- Uses django-allauth for authentication
- Email-based authentication (no usernames required)
- Email verification mandatory
- Login redirects to `/dashboard/`, logout to `/`

### Frontend Stack
- **Tailwind CSS**: Version 4.x with DaisyUI components
- **HTMX**: For dynamic interactions (`django-htmx`)
- **Lucide Icons**: Icon library
- Build process uses `@tailwindcss/cli` via npm

### Database Configuration
- PostgreSQL in production (configured via environment variables)
- SQLite for development (db.sqlite3)
- Database settings in `webapp/settings.py` use django-environ

### Environment Configuration
- Environment variables loaded from `webapp/.env`
- Key variables: `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, database settings
- Email configuration supports both development (Inbucket) and production modes

### Logging
- JSON logging with custom middleware for request/user context
- Multiple log files: `django.log`, `performance.jsonl`, `webapp.jsonl`
- Performance logging available via `logging.getLogger("performance")`

## URL Structure
- `/` - Landing page
- `/dashboard/` - User dashboard (login required)
- `/collections/` - Collection management
- `/share/collections/<hash>/` - Public collection sharing
- `/items/` - Item management
- `/activity/` - Recent activity
- HTMX endpoints for dynamic updates

## Testing and Quality
- No test framework currently configured in package.json
- Check `webapp/web/tests.py` for any existing tests
- Uses pylint with Django plugin (`pylint-django`)