# Daily Metrics System Implementation Guide

**Status**: Phase 1 Complete - Foundation Built
**Date**: 2025-10-04
**Timezone**: Europe/Zurich

## Overview

This document outlines the complete implementation of the daily metrics collection system, including what's been completed and what remains.

## ✅ Phase 1: Foundation (COMPLETED)

### 1.1 DailyMetrics Model
**File**: `webapp/web/models_metrics.py`

Created comprehensive model with the following metric categories:

#### User Metrics
- Total users
- Active users (24h, 7d, 30d)
- New users (24h, 7d, 30d)

#### Collection & Item Metrics
- Total collections/items
- Collection visibility distribution (private/public/unlisted)
- Item status distribution (in collection, wanted, reserved, etc.)
- Item type distribution
- Attribute usage statistics

#### Link Metrics
- Total links
- Matched vs unmatched link patterns
- Link pattern distribution

#### Storage Metrics
- Total media files and storage bytes
- Recent uploads (24h, 7d, 30d)
- Orphaned and corrupted files
- Storage by file type

#### Email Metrics (Resend Integration)
- Total emails, pending, sent, failed
- Marketing opt-in/opt-out counts

#### Content Moderation
- Flagged content
- Pending review
- User violations
- Banned users

#### Engagement Metrics (Added)
- Favorite items total
- Items with images/attributes/links (percentages)
- Average attributes per item
- Average items per collection
- Activity metrics (items/collections created)

**Key Features**:
- `get_change()` method for comparing metrics across time periods
- `cleanup_old_records()` for data retention
- Indexed for performance

### 1.2 Management Command
**File**: `webapp/web/management/commands/collect_daily_metrics.py`

**Features**:
- Comprehensive metric collection with progress tracking
- Email report generation to superusers
- Europe/Zurich timezone support
- Verbose mode for debugging
- Custom date collection support
- Automatic cleanup of old records

**Usage**:
```bash
# Collect today's metrics
python manage.py collect_daily_metrics

# Collect for specific date
python manage.py collect_daily_metrics --date 2025-10-03

# Collect and send email report
python manage.py collect_daily_metrics --send-email

# Verbose output
python manage.py collect_daily_metrics --verbose --send-email
```

### 1.3 Email Templates
**Files**:
- `webapp/templates/emails/daily_metrics_report.html`
- `webapp/templates/emails/partials/_metric_change.html`

**Features**:
- Professional HTML email design
- Comparison with yesterday and week ago
- Color-coded trend indicators (green ↑, red ↓)
- Alert thresholds (10% warning, 25% critical)
- Executive summary section
- Tables for each metric category

---

## 🚧 Phase 2: Configuration & Deployment (TODO)

### 2.1 Environment Variables

Add to `workflows/envs/env.gold`:

```bash
# Metrics Configuration
METRICS_RETENTION_DAYS=365  # 🏠 365 🧪 365 🚀 365
METRICS_ALERT_THRESHOLD_WARNING=10  # 🏠 10 🧪 10 🚀 10
METRICS_ALERT_THRESHOLD_CRITICAL=25  # 🏠 25 🧪 25 🚀 25
```

Then run:
```bash
uv run python workflows/bin/sync-env-files.py local
uv run python workflows/bin/sync-env-files.py qa
uv run python workflows/bin/sync-env-files.py prod
```

### 2.2 Database Migration

Create and run migration:
```bash
python manage.py makemigrations web
python manage.py migrate
```

Expected migration will create `web_dailymetrics` table with all fields.

### 2.3 Cron Job Configuration

**For Django Europe Production**:

Add to crontab (runs at midnight Europe/Zurich):
```bash
# Daily metrics collection at midnight Europe/Zurich
0 0 * * * cd ~/beryl3-prod && source ~/.virtualenvs/beryl3-prod/bin/activate && python manage.py collect_daily_metrics --send-email >> ~/beryl3-prod/logs/metrics_cron.log 2>&1
```

**For Django Europe Preprod**:
```bash
# Daily metrics collection at midnight Europe/Zurich
0 0 * * * cd ~/beryl3-preprod && source ~/.virtualenvs/beryl3-preprod/bin/activate && python manage.py collect_daily_metrics --send-email >> ~/beryl3-preprod/logs/metrics_cron.log 2>&1
```

**Test cron manually**:
```bash
# SSH to production
ssh mdubiel@148.251.140.153

# Test collection
cd ~/beryl3-prod
source ~/.virtualenvs/beryl3-prod/bin/activate
python manage.py collect_daily_metrics --verbose --send-email
```

---

## 🚧 Phase 3: Dashboard UI (TODO)

### 3.1 Update /sys/metrics View

**File**: `webapp/web/views/sys.py` (or create new view)

**Requirements**:
- Table layout with columns: Metric Name | Current | vs Yesterday | vs 7 Days | vs 30 Days
- Color-coded trends: green (↑) for increases, red (↓) for decreases
- Display last collection date below action buttons
- Group metrics by category

**Template**: `webapp/templates/sys/metrics.html`

**Example Structure**:
```html
<div class="mb-4 text-sm text-gray-600">
    Last collection: {{ latest_metrics.collected_at|date:"Y-m-d H:i:s" }} ({{ latest_metrics.collection_duration_seconds }}s)
</div>

<table class="table table-zebra w-full">
    <thead>
        <tr>
            <th>Metric</th>
            <th>Current</th>
            <th>vs Yesterday</th>
            <th>vs 7 Days</th>
            <th>vs 30 Days</th>
        </tr>
    </thead>
    <tbody>
        <!-- User Metrics Section -->
        <tr class="bg-base-200">
            <td colspan="5" class="font-bold">👥 Users</td>
        </tr>
        {% with change_1d=latest_metrics.get_change.total_users.1 change_7d=latest_metrics.get_change.total_users.7 change_30d=latest_metrics.get_change.total_users.30 %}
        <tr>
            <td>Total Users</td>
            <td class="font-bold">{{ latest_metrics.total_users }}</td>
            <td>{% include 'partials/_trend_indicator.html' with change=change_1d %}</td>
            <td>{% include 'partials/_trend_indicator.html' with change=change_7d %}</td>
            <td>{% include 'partials/_trend_indicator.html' with change=change_30d %}</td>
        </tr>
        {% endwith %}
        <!-- Repeat for all metrics -->
    </tbody>
</table>
```

**Trend Indicator Partial** (`templates/partials/_trend_indicator.html`):
```html
{% if change.change is not None %}
    {% if change.direction == 1 %}
        <span class="text-success">↑ +{{ change.change }} (+{{ change.change_pct }}%)</span>
    {% elif change.direction == -1 %}
        <span class="text-error">↓ {{ change.change }} ({{ change.change_pct }}%)</span>
    {% else %}
        <span class="text-neutral">—</span>
    {% endif %}
{% else %}
    <span class="text-neutral opacity-50">N/A</span>
{% endif %}
```

### 3.2 View Logic

```python
from web.models import DailyMetrics

def sys_metrics_view(request):
    """Display daily metrics dashboard."""
    latest_metrics = DailyMetrics.objects.order_by('-collection_date').first()

    if not latest_metrics:
        # No metrics collected yet
        return render(request, 'sys/metrics.html', {
            'no_metrics': True
        })

    # Get historical data for charts (last 30 days)
    historical = DailyMetrics.objects.order_by('-collection_date')[:30]

    context = {
        'latest_metrics': latest_metrics,
        'historical': list(reversed(historical)),  # Oldest first for charts
    }

    return render(request, 'sys/metrics.html', context)
```

---

## 🚧 Phase 4: Prometheus Integration (TODO)

### 4.1 Update /sys/metrics/prometheus Endpoint

**File**: `webapp/web/views/sys.py`

```python
from django.http import HttpResponse

def prometheus_metrics(request):
    """Export metrics in Prometheus format."""
    latest = DailyMetrics.objects.order_by('-collection_date').first()

    if not latest:
        return HttpResponse('# No metrics available\n', content_type='text/plain')

    metrics = []

    # User metrics
    metrics.append(f'beryl_users_total {latest.total_users}')
    metrics.append(f'beryl_users_active_24h {latest.active_users_24h}')
    metrics.append(f'beryl_users_active_7d {latest.active_users_7d}')
    metrics.append(f'beryl_users_active_30d {latest.active_users_30d}')
    metrics.append(f'beryl_users_new_24h {latest.new_users_24h}')

    # Collection metrics
    metrics.append(f'beryl_collections_total {latest.total_collections}')
    metrics.append(f'beryl_collections_private {latest.collections_private}')
    metrics.append(f'beryl_collections_public {latest.collections_public}')
    metrics.append(f'beryl_collections_unlisted {latest.collections_unlisted}')

    # Item metrics
    metrics.append(f'beryl_items_total {latest.total_items}')
    metrics.append(f'beryl_items_in_collection {latest.items_in_collection}')
    metrics.append(f'beryl_items_wanted {latest.items_wanted}')
    metrics.append(f'beryl_items_reserved {latest.items_reserved}')

    # Storage metrics
    metrics.append(f'beryl_storage_files_total {latest.total_media_files}')
    metrics.append(f'beryl_storage_bytes_total {latest.total_storage_bytes}')
    metrics.append(f'beryl_storage_uploads_24h {latest.recent_uploads_24h}')
    metrics.append(f'beryl_storage_orphaned_files {latest.orphaned_files}')

    # Moderation metrics
    metrics.append(f'beryl_moderation_flagged {latest.flagged_content}')
    metrics.append(f'beryl_moderation_pending {latest.pending_review}')
    metrics.append(f'beryl_moderation_violations {latest.user_violations}')
    metrics.append(f'beryl_moderation_banned_users {latest.banned_users}')

    # Engagement metrics
    metrics.append(f'beryl_engagement_favorites {latest.favorite_items_total}')
    metrics.append(f'beryl_engagement_items_with_images_pct {latest.items_with_images_pct}')
    metrics.append(f'beryl_engagement_avg_attributes_per_item {latest.avg_attributes_per_item}')

    # Metadata
    metrics.append(f'beryl_metrics_collection_duration_seconds {latest.collection_duration_seconds}')

    return HttpResponse('\n'.join(metrics) + '\n', content_type='text/plain')
```

---

## 🚧 Phase 5: Grafana Dashboard (TODO)

### 5.1 Create Grafana Dashboard JSON

**File**: `workflows/grafana/daily_metrics_dashboard.json`

```json
{
  "dashboard": {
    "title": "Beryl Daily Metrics",
    "timezone": "Europe/Zurich",
    "panels": [
      {
        "title": "Total Users",
        "targets": [
          {
            "expr": "beryl_users_total",
            "legendFormat": "Total Users"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Active Users",
        "targets": [
          {
            "expr": "beryl_users_active_24h",
            "legendFormat": "24h"
          },
          {
            "expr": "beryl_users_active_7d",
            "legendFormat": "7d"
          },
          {
            "expr": "beryl_users_active_30d",
            "legendFormat": "30d"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Collections",
        "targets": [
          {
            "expr": "beryl_collections_total",
            "legendFormat": "Total"
          },
          {
            "expr": "beryl_collections_public",
            "legendFormat": "Public"
          },
          {
            "expr": "beryl_collections_private",
            "legendFormat": "Private"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Storage Usage",
        "targets": [
          {
            "expr": "beryl_storage_bytes_total",
            "legendFormat": "Total Storage"
          }
        ],
        "type": "graph"
      },
      {
        "title": "Content Moderation",
        "targets": [
          {
            "expr": "beryl_moderation_flagged",
            "legendFormat": "Flagged"
          },
          {
            "expr": "beryl_moderation_violations",
            "legendFormat": "Violations"
          },
          {
            "expr": "beryl_moderation_banned_users",
            "legendFormat": "Banned"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

### 5.2 Import to Grafana

```bash
# Using Grafana API
curl -X POST http://grafana:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d @workflows/grafana/daily_metrics_dashboard.json
```

---

## 🚧 Phase 6: Make Targets & Documentation (TODO)

### 6.1 Update Makefile

Add to `Makefile`:

```makefile
# Metrics commands
.PHONY: collect-metrics
collect-metrics:  ## Collect daily metrics
	python manage.py collect_daily_metrics --verbose

.PHONY: collect-metrics-email
collect-metrics-email:  ## Collect metrics and send email
	python manage.py collect_daily_metrics --verbose --send-email

.PHONY: view-metrics
view-metrics:  ## View latest metrics in terminal
	python manage.py shell -c "from web.models import DailyMetrics; m = DailyMetrics.objects.latest('collection_date'); print(f'Date: {m.collection_date}'); print(f'Users: {m.total_users}'); print(f'Collections: {m.total_collections}'); print(f'Items: {m.total_items}')"
```

### 6.2 Update Documentation

**File**: `docs/METRICS.md` (new file)

```markdown
# Daily Metrics System

## Overview
Automated daily metrics collection system that tracks users, collections, items, storage, and more.

## Metrics Collected
[List all metrics with descriptions]

## Running Manually
[Instructions for manual execution]

## Email Reports
[Email configuration and recipients]

## Dashboard
[Link to /sys/metrics dashboard]

## Prometheus/Grafana
[Monitoring integration details]
```

---

## 📝 Testing Checklist

### Local Testing
- [ ] Run migration: `python manage.py migrate`
- [ ] Collect metrics: `python manage.py collect_daily_metrics --verbose`
- [ ] Check database: Verify `web_dailymetrics` table has data
- [ ] Test email: `python manage.py collect_daily_metrics --send-email`
- [ ] View dashboard: Visit `/sys/metrics`
- [ ] Check Prometheus: Visit `/sys/metrics/prometheus`

### Production Deployment
- [ ] Sync environment variables
- [ ] Run migrations on production
- [ ] Set up cron job
- [ ] Test cron execution
- [ ] Verify email delivery
- [ ] Import Grafana dashboard
- [ ] Monitor for 7 days

---

## 🐛 Troubleshooting

### Issue: No metrics collected
**Solution**: Check cron job logs: `tail -f ~/beryl3-prod/logs/metrics_cron.log`

### Issue: Email not sent
**Solution**: Verify SMTP settings in `.env` and check superuser emails

### Issue: Missing data in dashboard
**Solution**: Ensure migration ran successfully and metrics were collected

### Issue: Prometheus endpoint empty
**Solution**: Run `collect_daily_metrics` at least once

---

## 🔄 Maintenance

### Daily
- Cron job runs automatically at midnight
- Email sent to superusers

### Weekly
- Review dashboard for trends
- Check for anomalies in email reports

### Monthly
- Review Grafana dashboards
- Adjust alert thresholds if needed

### Yearly
- Old metrics (>365 days) automatically cleaned up
- Adjust `METRICS_RETENTION_DAYS` if needed

---

## 📊 Metrics Reference

### User Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| total_users | Total registered users | N/A |
| active_users_24h | Users active in last 24h | -25% = critical |
| new_users_24h | New users in last 24h | +25% = investigate |

[Complete table for all metrics]

---

## Next Steps

1. **Immediate** (Phase A):
   - Add environment variables
   - Run migration
   - Test locally

2. **Short-term** (1-2 days):
   - Implement dashboard UI
   - Update Prometheus endpoint
   - Set up cron job

3. **Medium-term** (1 week):
   - Create Grafana dashboard
   - Deploy to production
   - Monitor and adjust

4. **Long-term** (ongoing):
   - Add more metrics as needed
   - Optimize collection performance
   - Enhance visualizations
