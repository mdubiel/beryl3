# Beryl3 Public Views Security Analysis - Documentation Index

## Quick Links

- **Full Analysis Report**: [security_analysis_public_views.md](security_analysis_public_views.md)
- **Executive Summary**: See section below

## Overview

This security analysis examines the isolation and protection of public views in the beryl3 webapp from unauthorized access and data leakage. The analysis covers:

1. **Public Collection View** (`/share/collections/<hash>/`)
   - Displays sharable collections with visibility controls
   - Implements proper access controls based on collection visibility

2. **Public User Profile View** (`/u/<username>/`)
   - Shows user's public profile and public collections only
   - Filters data to only display PUBLIC visibility items

3. **Supporting Endpoints**
   - Item image lazy loading
   - Guest item reservation system
   - Token-based item unreservation

## Key Findings

### Overall Assessment: 9/10 (Excellent)

The public views in beryl3 demonstrate **excellent security practices** with:
- ✓ Proper separation from authenticated views
- ✓ No critical vulnerabilities found
- ✓ Well-implemented visibility filtering
- ✓ Safe data exposure practices
- ✓ Optimized database queries
- ✓ CSRF protection on forms

### Critical Points

#### What IS Exposed
- Collection/item names, descriptions, images
- Item attributes, links, and metadata
- Collection owner's display name (not email or real name)
- Favorite status and item status badges
- Aggregated statistics (counts only)

#### What is NOT Exposed
- User email addresses ✓
- Real names (only display names) ✓
- Private/unlisted collection data ✓
- Reserved by name/email (not in public templates) ✓
- User IDs (only hashes used) ✓
- Admin controls or settings ✓
- Passwords or security tokens ✓

### Visibility Filtering

The implementation uses a **3-tier visibility model**:

```
PRIVATE    → Http404 (hidden completely)
UNLISTED   → Accessible via direct link
PUBLIC     → Discoverable and accessible
```

Key mechanism:
```python
if collection.visibility == Collection.Visibility.PRIVATE:
    raise Http404("Collection not found or is private.")
```

This prevents information leakage by returning 404 instead of 403.

### Authentication & Access Control

#### Protected Views (require @login_required)
- All collection/item creation, update, delete operations
- All authenticated user dashboard views
- All HTMX editing endpoints
- User settings and profile management

#### Public Views (NO authentication required)
- Public collection viewing
- User profile viewing
- Item image lazy loading
- Guest item reservation (email validation instead)

#### Guest Reservation System
- No authentication required
- Email validation for guest bookings
- Token-based unreservation (one-time use)
- Proper error handling

### Database Security

**Zero SQL Injection Risk**
- All queries use Django ORM (parameterized)
- User input only used with `.filter()` calls
- No string concatenation in queries
- Proper query optimization with prefetch_related

**Query Optimization**
- No N+1 query problems found
- Proper use of select_related for foreign keys
- Proper use of prefetch_related for reverse relations
- Database-level aggregation for statistics
- Visibility filtering at database level (WHERE clause)

### Template Security

**Strong Points**
- ✓ CSRF tokens in all HTMX forms
- ✓ No edit/delete buttons in public templates
- ✓ Proper variable scoping
- ✓ Safe attribute access

**Items Needing Review**
- ⚠ `markdown_safe` filter used for collection descriptions
  - User-controlled input
  - Needs audit for XSS vulnerability
  - Recommend django-bleach if not already sanitizing

### URL Security

**User Profile URLs**
- Primary: Hash-based (`/u/<hash>/`)
- Secondary: Nickname-based (`/u/<nickname>/`)
- Not vulnerable to sequential enumeration (nanoid hashes)
- Email and user ID never exposed

**Collection URLs**
- Hash-based (`/share/collections/<hash>/`)
- 10-character nanoid (2^50+ combinations)
- Proper 404 on not found

## Recommendations

### HIGH PRIORITY

1. **Audit `markdown_safe` Filter**
   - Verify it properly sanitizes/escapes user input
   - Consider django-bleach integration if not already
   - Test with XSS payloads

2. **Add Rate Limiting to User Profile Lookups**
   - Current risk: Profile enumeration via hash guessing
   - Mitigation: Limit to 10 failed lookups per minute per IP
   - File: `/webapp/web/views/public.py` line 476-490

### MEDIUM PRIORITY

3. **Document Public API Contract**
   - Define response formats
   - Document rate limits
   - Add API versioning

4. **Add User Privacy Setting**
   - Allow users to hide profile completely
   - Would need URL mechanism to prevent direct access

### LOW PRIORITY

5. **Add View Count Analytics**
   - Track public view access for metrics
   - Already has good logging infrastructure

## File Locations

### View Files
- `/webapp/web/views/public.py` - All public views
- `/webapp/web/decorators.py` - Authentication decorators
- `/webapp/web/models.py` - Collection/Item models
- `/webapp/web/models_user_profile.py` - UserProfile model

### Template Files
- `/templates/public/collection_public_detail.html` - Collection view
- `/templates/public/user_profile.html` - User profile view
- `/templates/partials/_item_public_card.html` - Item card (public)
- `/templates/base_public.html` - Public base template

### Configuration
- `/webapp/web/urls.py` - URL patterns
- `/webapp/web/forms.py` - Form validation

## Testing Checklist

Tests that should exist:

- [ ] PRIVATE collection returns 404
- [ ] PUBLIC collection returns 200
- [ ] UNLISTED collection returns 200
- [ ] Inactive user profile returns 404
- [ ] Active user with no public collections returns 200
- [ ] Profile shows only PUBLIC collections
- [ ] Profile excludes PRIVATE collections
- [ ] Profile excludes UNLISTED collections
- [ ] Flagged image returns placeholder
- [ ] Reserved by info not exposed in templates
- [ ] Email address not exposed in public views
- [ ] Real name not exposed (only display name)
- [ ] CSRF token required for guest booking
- [ ] Guest token prevents multiple unreservations

## References

### Related Code
- Collection visibility model: `models.py` line 653-666
- Visibility check logic: `public.py` line 48-59
- User profile filtering: `public.py` line 516-546
- Item image safety: `models.py` line 191-217

### External Resources
- Django Security Documentation: https://docs.djangoproject.com/en/stable/topics/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- GDPR Compliance: https://gdpr-info.eu/

## Report Maintenance

This analysis was generated on: **2025-11-03**

**Next Review Recommended**: 
- After implementing rate limiting
- After template filter audit
- After adding test suite
- Quarterly for ongoing security validation

---

**Analysis Conducted By**: Security Audit Process
**Overall Rating**: 9/10 (Excellent)
**Status**: Ready for deployment with recommendations

For detailed findings, see [security_analysis_public_views.md](security_analysis_public_views.md)
