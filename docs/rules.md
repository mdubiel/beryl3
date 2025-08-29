# Development Rules & Guidelines

## Project Overview

Beryl is a Django-based collection management system that enables users to catalog, organize, and share their collections. The application follows a monorepo structure using uv workspace, combining a Python Django backend with Tailwind CSS frontend. Key features include:

- **User Authentication**: Email-based authentication via django-allauth
- **Collection Management**: Create, organize, and share collections with visibility controls
- **Item Management**: Dynamic item types with flexible attributes, favorites, and status tracking
- **Guest Reservations**: Email-based anonymous reservation system for wanted items
- **Activity Logging**: Comprehensive user action tracking and timeline
- **Media Management**: GCS-integrated file storage with verification
- **Real-time Interactions**: HTMX-powered dynamic UI updates

The system is designed for simplicity, maintainability, and extensibility while providing a robust platform for personal collection management and sharing.

## Application Architecture Planes

Beryl operates on a three-plane architecture that separates concerns and provides different levels of access:

### 1. User Plane (Primary Application)
- **Purpose**: User-facing application for collection management
- **Access**: All authenticated users
- **Features**: Collection CRUD, item management, sharing, guest reservations
- **URL Patterns**: `/`, `/dashboard/`, `/collections/`, `/items/`, `/share/`
- **Responsibilities**: Core business functionality, user experience, public interfaces

### 2. SYS Plane (System Administration)
- **Purpose**: Application-specific administrative control panel
- **Access**: Administrators and application owners only
- **Features**: User management, system statistics, ItemType/Attribute management, media file oversight
- **URL Patterns**: `/sys/` (protected routes)
- **Responsibilities**: Application monitoring, user support, business intelligence, system configuration
- **Styling**: Uses terminal-themed CSS classes (`terminal-bg`, `terminal-text`, `terminal-accent`) for consistent admin interface
- **Logging Policy**: SYS plane functions do NOT require ApplicationActivity logging as they are administrative functions performed by system administrators

### 3. Admin Plane (Django Admin)
- **Purpose**: Standard Django administrative interface
- **Access**: Superusers and staff members
- **Features**: Direct database model management, user administration, low-level data manipulation
- **URL Patterns**: `/admin/`
- **Responsibilities**: Data management, model administration, technical maintenance

**Architectural Principle**: Regular user requests flow through the User Plane. Administrative tasks use the SYS Plane for application-specific management, while technical/database operations use the Django Admin Plane. This separation ensures clear boundaries between user functionality, business administration, and technical management.

## Developer Profile

**Mateusz Dubiel** (mdubiel@gmail.com) is the lead developer and architect of Beryl. Based on the codebase analysis, Mateusz demonstrates:

- **Strong Django expertise**: Proper use of Django patterns, ORM relationships, and best practices
- **Code quality focus**: Consistent pylint compliance, organized imports, and professional error handling
- **Modern development practices**: HTMX integration, JSON logging, environment-based configuration
- **User experience orientation**: Thoughtful UI/UX with DaisyUI components and responsive design
- **Security mindset**: Token-based guest systems, proper validation, and defensive programming
- **Documentation discipline**: Comprehensive CLAUDE.md with detailed project guidance
- **Performance awareness**: Database indexing, query optimization, and efficient data handling

The development approach prioritizes simplicity (KISS), write-once-use-many methodologies, and maintainable code architecture.

## Django Best Practices

### Model Design
- **Inheritance**: Use abstract base models (BerylModel) for common functionality
- **Soft Deletion**: Implement `is_deleted` fields instead of hard deletion for data integrity
- **Relationships**: Use appropriate ForeignKey relationships with proper `on_delete` behavior
- **Validation**: Implement model-level validation with custom `clean()` methods
- **Managers**: Create custom managers for filtered querysets (e.g., exclude deleted items)
- **Properties**: Use `@property` decorators for computed fields and business logic

### View Organization
- **Function-based views**: Prefer FBVs for simplicity and explicit control flow
- **Decorators**: Use `@login_required`, `@require_POST`, and custom decorators consistently
- **Error Handling**: Use `get_object_or_404` for object retrieval with ownership checks
- **Permissions**: Always verify user ownership before allowing operations
- **Logging**: Log all significant user actions with structured logging
- **Transactions**: Use `@transaction.atomic` for multi-model operations
- **ApplicationActivity Logging**: Every function call MUST create ApplicationActivity log at the end with success or failure status

### Database Operations
- **Indexing**: Add database indexes on frequently queried fields
- **Query Optimization**: Use `select_related` and `prefetch_related` for performance
- **Annotations**: Leverage database-level aggregations and annotations
- **Bulk Operations**: Use bulk operations for performance when processing multiple records

### Form Handling
- **ModelForms**: Use ModelForms for database-backed forms
- **Validation**: Implement both field-level and form-level validation
- **Security**: Always use CSRF protection and validate user permissions
- **Messages**: Provide clear user feedback via Django's messages framework

### Template Structure
- **Inheritance**: Use template inheritance with logical base templates
- **Context Processors**: Create custom context processors for commonly needed data
- **Tags**: Develop custom template tags for reusable functionality
- **Performance**: Minimize database queries in templates

### Configuration Management
- **Environment Variables**: Use django-environ for configuration management
- **Settings Organization**: Separate development and production settings appropriately
- **Security**: Never commit secrets; use environment variables for sensitive data

## ApplicationActivity Logging Requirements

### Mandatory Logging (User Plane Only)
- **User Plane Functions**: All view functions in User Plane MUST implement ApplicationActivity logging
- **SYS Plane Exemption**: SYS plane functions (sys.py) do NOT require ApplicationActivity logging as they are administrative functions
- **Success Logging**: Use `ApplicationActivity.log_info()` for successful operations
- **Failure Logging**: Use `ApplicationActivity.log_error()` or `log_warning()` for failures
- **Function Arguments**: Include `function_args` in meta field with relevant parameters passed to the function
- **Object Context**: Include object type, hash, name when applicable
- **Result Status**: Always include result status (success, validation_error, system_error, access_denied, etc.)

### Comprehensive Implementation Status
✅ **Fully Implemented**: All User Plane view functions now have complete ApplicationActivity logging:
- `web/views/landing.py` - Landing page access with success/error scenarios
- `web/views/collection.py` - All collection CRUD operations (5 functions)
- `web/views/collection_hx.py` - HTMX collection visibility updates
- `web/views/items.py` - All item CRUD operations (6+ functions)
- `web/views/items_hx.py` - All HTMX item operations (15+ functions including status, favorites, types, attributes, links)
- `web/views/user.py` - Dashboard, favorites, and activity views (3 functions)
- `web/views/public.py` - Public collection access and guest reservations
- `web/views/index.py` - Index page access

### Logging Pattern
```python
# Success example
ApplicationActivity.log_info('function_name', 
    'Success message', user=request.user, meta={
        'action': 'created', 'object_type': 'Model',
        'object_hash': obj.hash, 'result': 'success',
        'function_args': {'param1': value1, 'param2': value2}
    })

# Error example  
ApplicationActivity.log_error('function_name',
    f'Operation failed: {str(e)}', user=request.user, meta={
        'action': 'creation_failed', 'error': str(e),
        'result': 'system_error', 'function_args': {'param1': value1}
    })

# Unauthorized access example
ApplicationActivity.log_warning('function_name',
    f'Unauthorized attempt to access {obj.name}', user=request.user, meta={
        'action': 'unauthorized_access', 'object_type': 'Model',
        'object_hash': obj.hash, 'result': 'access_denied',
        'function_args': {'param1': value1}
    })
```

### Safe User Handling
- Always use `user=request.user` (handles anonymous users safely)
- For system operations, use `user=None`
- ApplicationActivity model handles None users gracefully
- Anonymous users are properly logged for public access scenarios

## SYS Plane Styling Guidelines

### Terminal Theme Classes
- **Background**: `terminal-bg` for card/section backgrounds
- **Text**: `terminal-text` for primary text content
- **Accent**: `terminal-accent` for highlights and important text
- **Typography**: Use `font-mono` for technical data (IDs, emails, functions)

### Component Patterns
- **Headers**: Use `terminal-accent text-lg font-bold` with `>` prefix
- **Cards**: Apply `terminal-bg` with `p-6` padding
- **Tables**: Use standard table classes with `hover:bg-blue-100`
- **Buttons**: Use DaisyUI button classes (`btn btn-primary`, `btn btn-outline`)
- **Level Indicators**: Color-coded text without backgrounds
  - ERROR: `text-red-500`
  - WARNING: `text-orange-500`  
  - INFO: `text-green-500`

### Consistency Requirements
- All SYS templates must use terminal theme classes
- Maintain consistent spacing with `space-y-6`
- Use `font-mono` for technical identifiers and timestamps
- Follow established pagination patterns with `btn-group`

## What to Avoid

### Anti-Patterns
- **Hard Deletion**: Never permanently delete user data; always use soft deletion
- **Direct Database Access**: Avoid raw SQL unless absolutely necessary for performance
- **Inline Styles**: Don't use inline CSS; leverage Tailwind classes and utilities
- **Magic Numbers**: Use named constants and choices for status values
- **Tight Coupling**: Keep views, models, and templates loosely coupled
- **Premature Optimization**: Follow KISS principle; optimize only when needed
- **Missing ApplicationActivity**: Never skip ApplicationActivity logging in User Plane view functions
- **Incorrect Plane Logging**: Do NOT add ApplicationActivity logging to SYS plane functions (administrative functions don't need user activity tracking)

### Security Issues
- **User Input**: Never trust user input; always validate and sanitize
- **Permission Bypass**: Always verify ownership before database operations
- **SQL Injection**: Use ORM queries; avoid string concatenation in raw SQL
- **XSS Vulnerabilities**: Always escape output in templates
- **CSRF Bypass**: Don't disable CSRF protection for convenience

### Code Quality Issues
- **Long Functions**: Keep functions focused and under 50 lines when possible
- **Deep Nesting**: Avoid deeply nested conditionals; use early returns
- **Unused Code**: Remove dead code and unused imports regularly
- **Inconsistent Naming**: Follow Python naming conventions consistently
- **Missing Documentation**: Document complex business logic and edge cases

### Performance Killers
- **N+1 Queries**: Always use select_related/prefetch_related for relationships
- **Large Querysets**: Implement pagination for large data sets
- **Synchronous I/O**: Avoid blocking operations in request/response cycle
- **Memory Leaks**: Be cautious with large file uploads and processing

### UI/UX Mistakes
- **Non-responsive Design**: Always test on mobile devices
- **Poor Error Messages**: Provide clear, actionable error messages
- **Missing Loading States**: Show loading indicators for async operations
- **Inconsistent Icons**: Stick to the validated Lucide icon set
- **Accessibility Issues**: Ensure proper semantic HTML and ARIA labels

## Future Rules Placeholder

### Planned Enhancements
- **API Development**: REST API guidelines for mobile/external integrations
- **Testing Strategy**: Comprehensive test coverage requirements and patterns
- **Caching Strategy**: Redis/Memcached integration for performance optimization
- **Monitoring**: Application performance monitoring and alerting rules
- **Deployment**: CI/CD pipeline requirements and deployment strategies
- **Internationalization**: Multi-language support implementation guidelines
- **Scalability**: Database sharding and microservice transition considerations

### Code Review Standards
- **Pull Request Requirements**: Minimum review criteria and testing standards
- **Documentation Updates**: Requirements for updating docs with code changes
- **Performance Benchmarks**: Acceptable performance thresholds for new features
- **Security Review**: Security checklist for all user-facing features

### Architecture Evolution
- **Microservice Migration**: Guidelines for breaking monolith when needed
- **Event-Driven Architecture**: Message queue integration for async processing
- **Real-time Features**: WebSocket integration for live updates
- **Search Integration**: Elasticsearch/Solr implementation for advanced search

### Team Collaboration
- **Code Style Enforcement**: Automated linting and formatting requirements
- **Feature Flag Strategy**: A/B testing and gradual rollout implementation
- **Error Tracking**: Centralized error monitoring and alerting setup
- **Performance Monitoring**: Key metrics tracking and optimization targets

## Action Button Layout Standards

All action buttons across the application MUST follow the unified layout pattern established for optimal user experience and visual consistency.

### Layout Structure
Action buttons MUST be organized into logical groups using DaisyUI's `btn-group` class:

```html
<div class="flex items-center justify-end gap-2">
    {# Main Actions Group #}
    <div class="btn-group">
        <!-- Primary action with text label (always first) -->
        <a href="#" class="btn btn-secondary btn-sm">
            {% lucide 'icon-name' size=16 class='mr-2' %} Action Label
        </a>
        
        <!-- Secondary actions (icon-only buttons) -->
        <button class="btn btn-ghost btn-square btn-sm" title="Tooltip Text">
            {% lucide 'icon-name' size=18 %}
        </button>
        
        <!-- Dropdown actions -->
        <div class="dropdown dropdown-end dropdown-bottom">
            <button tabindex="0" class="btn btn-ghost btn-square btn-sm" title="Action Name">
                {% lucide 'icon-name' size=18 %}
            </button>
            <ul tabindex="0" class="dropdown-content menu p-2 shadow bg-base-100 rounded-box w-52 z-10">
                <!-- Dropdown items -->
            </ul>
        </div>
    </div>

    {# Danger Actions Group - Always Separated #}
    <div class="btn-group">
        <!-- Delete/destructive actions -->
        <div class="dropdown dropdown-end dropdown-bottom">
            <button tabindex="0" class="btn btn-ghost btn-square btn-sm text-error" title="Delete">
                {% lucide 'trash-2' size=18 %}
            </button>
            <!-- Delete confirmation dropdown -->
        </div>
    </div>
</div>
```

### Styling Requirements

#### Button Classes
- **Primary action**: `btn btn-secondary btn-sm` (with text and icon)
- **Secondary actions**: `btn btn-ghost btn-square btn-sm` (icon-only)
- **Danger actions**: `btn btn-ghost btn-square btn-sm text-error` (icon-only, red text)

#### Icon Standards
- **Primary action icons**: `size=16` with `class='mr-2'` spacing
- **Secondary/dropdown icons**: `size=18` (larger for better touch targets)
- **Always include tooltips** via `title` attribute for icon-only buttons

#### Standardized Icon Usage
- **Sharing/Visibility**: Use `share-2` for sharing controls, visibility settings, and collection sharing dropdowns
- **External Links**: Use `external-link` for opening links in new tabs/windows
- **Copy Actions**: Use `copy` for clipboard copy functionality

#### Datetime Formatting Standards
- **Relative Time Display**: Use Django's `timesince` filter for showing elapsed time
- **Format**: `{{ object.updated|timesince }} ago` (e.g., "2 hours, 15 minutes ago", "3 days, 4 hours ago")
- **Benefits**: Natural breakdown into appropriate units (minutes → hours → days → weeks → months)
- **Consistency**: Provides automatic rounding and handles all time calculations
- **Avoid**: Custom time formatting logic or truncation that loses precision
- **Examples**: 
  - Recent: "3 minutes ago", "2 hours, 30 minutes ago"
  - Medium: "1 day, 4 hours ago", "5 days, 2 hours ago" 
  - Older: "2 weeks, 3 days ago", "3 months, 1 week ago"

#### Grouping Rules
1. **Main Actions Group**: Contains the primary action (first, with text) followed by secondary actions
2. **Danger Actions Group**: Always separated on the right, contains delete/destructive actions only
3. **Utility Groups**: Additional groups (e.g., share) can be added between main and danger groups

### Implementation Examples

#### Collection Detail Page
```html
{# Main Actions Group #}
<div class="btn-group">
    <a href="{% url 'item_create' collection.hash %}" class="btn btn-secondary btn-sm">
        {% lucide 'plus' size=16 class='mr-2' %} Add New Item
    </a>
    <div class="dropdown"><!-- Visibility dropdown --></div>
    <a href="{% url 'collection_manage_images' collection.hash %}" class="btn btn-ghost btn-square btn-sm" title="Manage Images">
        {% lucide 'images' size=18 %}
    </a>
    <a href="{% url 'collection_update' collection.hash %}" class="btn btn-ghost btn-square btn-sm" title="Edit Collection">
        {% lucide 'pencil' size=18 %}
    </a>
</div>
{# Danger Actions Group #}
<div class="btn-group">
    <!-- Delete dropdown -->
</div>
```

#### Collection List Page
```html
<a href="{% url 'collection_create' %}" class="btn btn-secondary btn-sm">
    {% lucide 'plus' size=16 class='mr-2' %} Create New Collection
</a>
```

### Consistency Requirements
- **ALL action button sections** must use this pattern
- **Primary buttons** must have consistent size (`btn-sm`) across all pages
- **Icon sizes** must be consistent (16px with text, 18px icon-only)
- **Delete actions** must always be separated in their own group
- **Tooltips** are mandatory for all icon-only buttons
- **Dropdown positioning** should be `dropdown-end dropdown-bottom` unless space constraints require otherwise

### HTMX Integration
When using HTMX with action buttons:
- Use appropriate `hx-target` and `hx-swap` attributes
- Include CSRF tokens: `hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'`
- Consider `hx-swap-oob` for updating multiple page elements
- Add proper error handling and loading states

This pattern ensures consistent user experience, proper visual hierarchy, and maintainable code across all pages.

---

*This document should be updated as the project evolves and new patterns emerge. Always prioritize simplicity, security, and user experience in development decisions.*