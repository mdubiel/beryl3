# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Rules & Guidelines

**IMPORTANT**: Always consult `docs/rules.md` for comprehensive development guidelines, Django best practices, and coding standards. This file contains essential rules for:
- Project architecture and patterns
- Django best practices and anti-patterns
- Security guidelines and what to avoid
- Code quality standards
- Future development guidelines

The rules in `docs/rules.md` take precedence and should be followed for all development work.

## Project Overview

Beryl is a Django-based collection management system with user authentication, item tracking, and sharing capabilities. The project uses a monorepo structure managed with uv workspace, combining Python Django backend with Tailwind CSS frontend.

## Development Commands

### Essential Commands
```bash
# Run development server (user manages this separately - do not start automatically)
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

**Note**: Development server is managed externally - do not start automatically with `make run-dev-server` or background processes.

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
- **Collection**: User collections with visibility controls (public/private/unlisted)
- **CollectionItem**: Items within collections with comprehensive features:
  - Status tracking (In Collection, Wanted, Reserved, etc.)
  - Favorites system with `is_favorite` field and star icons
  - Dynamic attributes via JSONField for flexible metadata
  - Guest reservation system with email-based confirmation
  - Item type categorization (books, LEGO sets, vinyl records, etc.)
- **ItemType**: Database-driven item categorization system with icons
- **ItemAttribute**: Flexible attribute definitions per item type with validation
- **RecentActivity**: Comprehensive user activity logging with standardized format
- **Guest Reservations**: Secure token-based system for anonymous users

### Authentication
- Uses django-allauth for authentication
- Email-based authentication (no usernames required)
- Email verification mandatory
- Login redirects to `/dashboard/`, logout to `/`

### Frontend Stack
- **Tailwind CSS**: Version 4.x with DaisyUI components and responsive design
- **HTMX**: Extensive dynamic interactions for:
  - Item status updates and favorite toggling
  - Real-time attribute management (add/edit/remove)
  - Item type selection with instant UI updates
  - Guest reservation forms with email validation
- **Lucide Icons**: Icon library for UI elements
- **Email Templates**: Professional HTML templates with fallback text versions
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
- **Standardized logging format**: All functions log with object types and hashes
- **Activity tracking**: Comprehensive logging for favorites, reservations, and attribute changes
- **Email notifications**: Logging for guest reservation confirmations and failures

## URL Structure
- `/` - Landing page
- `/dashboard/` - User dashboard (login required)
- `/collections/` - Collection management with enhanced UI
- `/share/collections/<hash>/` - Public collection sharing with item type distribution
- `/items/` - Item management with attribute support
- `/activity/` - Recent activity with detailed logging
- **HTMX endpoints for dynamic updates:**
  - `/items/<hash>/toggle-favorite/` - Favorite toggling
  - `/items/<hash>/change-type/` - Item type selection
  - `/items/<hash>/add-attribute/` - Add new attributes
  - `/items/<hash>/edit-attribute/<name>/` - Edit existing attributes
  - `/items/<hash>/save-attribute/` - Save attribute changes
  - `/items/<hash>/remove-attribute/<name>/` - Remove attributes
- **Guest reservation system:**
  - `/item/<hash>/book/guest/` - Guest booking with email
  - `/item/<hash>/book/release/<token>/` - Secure unreservation via email link

## Testing and Quality
- No test framework currently configured in package.json
- Check `webapp/web/tests.py` for any existing tests
- Uses pylint with Django plugin (`pylint-django`)
- **Code quality improvements**: All imports organized per PEP 8 standards
- **Pylint compliance**: Code refactored to meet pylint standards
- **Professional code patterns**: Removed unnecessary try/catch blocks and improved error handling

## Feature Implementation Details

### Favorites System
- Database field: `CollectionItem.is_favorite` with index for performance
- HTMX-powered toggle functionality with visual feedback
- DaisyUI warning colors for consistent theming
- Activity logging for favorite/unfavorite actions

### Dynamic Item Types and Attributes
- **Database-driven design**: ItemType and ItemAttribute models for flexibility
- **Supported attribute types**: TEXT, LONG_TEXT, NUMBER, DATE, URL, BOOLEAN, CHOICE
- **Validation system**: Comprehensive validation with skip_validation flag for edge cases
- **Real-time editing**: HTMX-powered in-place editing for all attribute operations
- **Attribute preservation**: Changing item types preserves existing attributes

### Email-Based Guest Reservations
- **Security**: Secure token generation using `secrets.token_urlsafe(32)`
- **Email validation**: Django's built-in email validation with user feedback
- **Professional emails**: HTML templates with plain text fallbacks
- **Unreservation flow**: Secure token-based cancellation via email links
- **Error handling**: Comprehensive success/error pages for user guidance

### Enhanced Public Collections
- **Hero-style headers**: Collection information with statistics
- **Item type distribution**: Visual breakdown of collection contents
- **Responsive design**: Mobile-first approach with DaisyUI components
- **Attribute display**: Professional badge-based attribute presentation

### Admin Interface Enhancements
- **Inline editing**: ItemAttribute management within ItemType admin
- **Custom admin views**: Enhanced list displays with relevant fields
- **Fieldset organization**: Logical grouping of fields for better UX
- **JSON widget styling**: Improved attributes field editing

## Email Configuration
```python
# Development setup with Inbucket
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 2500

# Production configuration via environment variables
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=True)
```

## Database Migrations
Recent migrations include:
- `0008_collectionitem_is_favorite_alter_recentactivity_name.py` - Favorites system
- `0009_collectionitem_attributes_itemtype_and_more.py` - Item types and attributes
- `0010_auto_20250718_1955.py` - Data migration for existing items
- `0011_add_guest_reservation_token.py` - Guest reservation tokens

## Performance Considerations
- Database indexes on frequently queried fields (`is_favorite`, `guest_reservation_token`)
- Efficient queryset usage with `select_related` and `prefetch_related`
- Optimized HTMX responses for minimal data transfer
- Proper foreign key relationships for data integrity

## PixelCube Image Generator System
The project includes a comprehensive PixelCube image generator library for creating Minecraft-inspired pixelized isometric cube images. **COMPLETED ENHANCEMENT**: The system now supports multiple cubes, background options, and improved 3D perspective.

### Core Features
- **T-shirt sizes**: xs (16×16), s (32×32), m (64×64), l (128×128), xl (256×256)
- **Multiple cubes**: Support for 1-20 cubes with intelligent positioning
- **Background options**: Transparent, palette colors, or custom hex colors
- **Enhanced 3D perspective**: 30-degree isometric angles for better depth
- **Gaming color palette**: 40+ retro 16-bit era inspired colors
- **Pattern types**: solid, mixed, gradient, random

### Template Usage
```django
{% load pixelcube %}
{% pixelcube size='l' cube_count=3 background='palette' %}
{% pixelcube 'm' color='#FF0000' pattern='gradient' %}
{% pixelcube size='xl' min_cubes=2 max_cubes=6 css_class='rounded-lg' %}
```

### API Endpoints
- **Showcase**: `/core/pixelcube/showcase/` - Interactive demonstration
- **Direct API**: `/core/pixelcube/?size=l&cubes=3&background=palette&pattern=mixed`

### Key Files
- `core/pixelcube.py` - Main library with PixelCubeGenerator class
- `core/templatetags/pixelcube.py` - Django template tags
- `core/views.py` - Showcase and API views
- `templates/core/pixelcube_showcase.html` - Interactive demo with JavaScript controls

## Lucide Icons System
The project uses a comprehensive Lucide icons system with validation, autocomplete, and professional error handling managed through `core/lucide.py`.

### Usage in Templates
```django
{% load lucide %}
{% lucide 'icon-name' size=16 class='additional-css-classes' %}
```

### VALID LUCIDE ICONS (115+ icons available)
**ALWAYS check this list before using icons in templates!**

**Navigation & Interface:** `arrow-down`, `arrow-left`, `arrow-right`, `arrow-up`, `chevron-down`, `chevron-left`, `chevron-right`, `chevron-up`, `menu`, `ellipsis`, `x`, `x-circle`, `x-octagon`, `x-square`, `plus`, `plus-circle`, `plus-square`, `minus`, `check`, `check-circle`, `external-link`, `link`, `link-2`

**Content & Media:** `book`, `bookmark`, `file`, `file-text`, `folder`, `folder-open`, `image`, `video`, `video-off`, `music`, `headphones`, `disc`, `film`, `camera`, `mic`, `mic-off`, `volume`, `volume-1`, `volume-2`, `volume-x`, `play`, `play-circle`, `pause`, `pause-circle`, `stop-circle`, `skip-back`, `skip-forward`, `fast-forward`, `rewind`

**Communication:** `mail`, `message-circle`, `message-square`, `phone`, `phone-call`, `phone-forwarded`, `phone-incoming`, `phone-missed`, `phone-off`, `phone-outgoing`, `send`, `share`, `share-2`, `at-sign`, `bell`, `rss`

**User & Account:** `user`, `user-check`, `user-minus`, `user-plus`, `user-x`, `users`, `crown`, `shield`, `shield-off`, `key`, `lock`, `lock-open`, `unlock`, `log-in`, `log-out`

**System & Settings:** `settings`, `tool`, `cog`, `sliders`, `command`, `terminal`, `cpu`, `server`, `database`, `hard-drive`, `wifi`, `wifi-off`, `bluetooth`, `cast`, `radio`, `power`, `zap`, `zap-off`

**Shopping & Commerce:** `shopping-bag`, `shopping-cart`, `credit-card`, `dollar-sign`, `tag`, `gift`, `package`, `box`, `truck`, `award`

**Location & Navigation:** `map`, `map-pin`, `compass`, `navigation`, `navigation-2`, `globe`, `home`, `building`

**Time & Calendar:** `clock`, `calendar`, `sunrise`, `sunset`, `sun`, `moon`, `watch`

**Weather & Nature:** `cloud`, `umbrella`, `wind`, `thermometer`, `droplets`

**Gaming & Entertainment:** `gamepad-2`, `dice-1`, `dice-2`, `dice-3`, `dice-4`, `dice-5`, `dice-6`, `puzzle`

**Actions & Tools:** `edit`, `edit-2`, `edit-3`, `pencil`, `pen-tool`, `scissors`, `copy`, `clipboard`, `save`, `download`, `upload`, `upload-cloud`, `refresh-ccw`, `refresh-cw`, `rotate-ccw`, `rotate-cw`, `repeat`, `shuffle`, `trash`, `trash-2`, `delete`, `archive`, `search`, `filter`, `sort-asc`, `sort-desc`

**Layout & Design:** `layout`, `grid`, `list`, `columns`, `rows`, `sidebar`, `align-left`, `align-center`, `align-right`, `align-justify`, `bold`, `italic`, `underline`, `type`

**Status & Feedback:** `info`, `help-circle`, `alert-circle`, `alert-triangle`, `alert-octagon`, `activity`, `loader`, `target`, `crosshair`, `eye`, `eye-off`, `heart`, `star`, `flag`

**Geometry & Shapes:** `circle`, `square`, `triangle`, `octagon`, `diamond`, `hexagon`

**Social Media:** `facebook`, `twitter`, `instagram`, `linkedin`, `youtube`, `github`, `slack`

**Transportation:** `car`, `plane`, `train`, `bike`, `bus`

**Business & Work:** `briefcase`, `building-2`, `factory`, `store`, `office-building`

**Health & Medical:** `heart-pulse`, `pill`, `syringe`, `stethoscope`, `cross`

**Miscellaneous:** `anchor`, `coffee`, `utensils`, `wine`, `beer`, `ice-cream`, `pizza`, `smartphone`, `tablet`, `laptop`, `monitor`, `tv`, `keyboard`, `mouse-pointer`, `printer`, `scanner`, `projector`, `speaker`, `battery`, `plug`

### Icon Validation
```python
from core.lucide import LucideIcons
# Always validate: LucideIcons.is_valid('icon-name')
```

### Common Working Icons
These icons are confirmed working in current templates: `arrow-left`, `arrow-right`, `plus`, `check`, `x`, `pencil`, `save`, `trash-2`, `copy`, `search`, `star`, `package`, `user`, `users`, `log-in`, `log-out`, `settings`, `activity`, `database`, `shield`, `globe`, `link`, `book`, `disc`, `eye`, `download`, `upload`, `refresh-cw`, `alert-circle`, `info`