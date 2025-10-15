# Task 36: Implement Daily Metrics Collection System

**Status:** ✅ Completed
**Verified:** Yes
**Commit IDs:** bd5aa52, 3988d23, 1db1269, c193dd3, c930ab8

## Task Description

Implement daily metrics collection system with comprehensive tracking and reporting across all system areas.

## Implementation Summary

### Complete System Overview

The daily metrics system provides comprehensive tracking and reporting across 6 major categories with 50+ individual metrics, automated collection, email reports, web dashboard, and Grafana integration.

## Phase 1-6: Core Implementation

### DailyMetrics Model

**Location:** `web/models.py`

**6 Metric Categories:**

1. **User Metrics** (9 fields)
   - Total users, new users (day/week/month)
   - Active users, verified emails
   - Marketing consent counts

2. **Collection Metrics** (10 fields)
   - Total collections by visibility
   - New collections (day/week/month)
   - Average items per collection

3. **Item Metrics** (11 fields)
   - Total items, new items
   - Items by status (in collection, wanted, reserved)
   - Items with images, links, attributes
   - Average attributes per item

4. **Storage Metrics** (8 fields)
   - Total images, storage used
   - Images by type (collection/item)
   - Images by storage backend (local/GCS)
   - Average image size

5. **Engagement Metrics** (7 fields)
   - Recent activity count
   - Guest reservations
   - Public collections
   - Email queue size

6. **Moderation Metrics** (6 fields)
   - Images by moderation status
   - Flagged content count
   - Banned users count

**Total:** 51 metric fields + metadata fields

### Management Command

**Command:** `python manage.py collect_daily_metrics`

**Features:**
- Collects all metrics in single transaction
- Stores in DailyMetrics model
- Calculates trends (yesterday, 7 days, 30 days)
- Optional email report generation
- Structured logging

**Usage:**
```bash
# Collect metrics only
python manage.py collect_daily_metrics

# Collect and send email report
python manage.py collect_daily_metrics --send-email
```

### Email Reports

**Template:** `templates/emails/daily_metrics_report.html`

**Features:**
- HTML formatted email
- All 6 metric categories
- Trend indicators (↑ ↓ →)
- Color-coded changes (green/red/gray)
- Previous values shown in parentheses
- Comparison periods: Yesterday, 7 days ago, 30 days ago

**Recipients:** Configurable via settings

**Example:**
```
Daily Metrics Report - 2025-10-13

User Metrics:
- Total Users: 142 (vs Yesterday: 141 ↑)
- New Users (today): 1 (vs 7 days ago: 2 ↓)
```

### Web Dashboard

**URL:** `/sys/metrics`

**Features:**
- Table layout with 6 sections
- Trend indicators with symbols (↑ ↓ →)
- Color-coded changes:
  - Green: positive changes
  - Red: negative changes
  - Gray: no change
- Previous values displayed in gray text
- Collapsible historical data tables (last 10 entries)
- Toggle buttons: "Show/Hide Historical Data"

**Historical Data Tables:**
Each section includes expandable table showing:
- Date
- Key metrics from that date
- Sortable by date
- Last 10 entries displayed

### Prometheus Endpoint

**URL:** `/sys/metrics/prometheus`

**Features:**
- Prometheus-compatible format
- All metrics exposed with proper naming
- Help text for each metric
- Type definitions (gauge/counter)
- Latest metrics only

**Example Output:**
```prometheus
# HELP beryl_users_total Total number of users
# TYPE beryl_users_total gauge
beryl_users_total 142

# HELP beryl_collections_total Total number of collections
# TYPE beryl_collections_total gauge
beryl_collections_total 89
```

### Grafana Dashboard

**File:** `docs/grafana/daily_metrics_dashboard.json`

**Features:**
- 23 panels covering all metric categories
- Time-series graphs
- Stat panels for current values
- Trend indicators
- Color thresholds
- Auto-refresh every 5 minutes

**Panel Categories:**
- User Growth & Activity (4 panels)
- Collections Overview (4 panels)
- Items & Content (5 panels)
- Storage & Media (4 panels)
- Engagement Metrics (3 panels)
- Content Moderation (3 panels)

### Automation

**Cron Configuration:**
```bash
# Collect metrics daily at midnight
0 0 * * * cd /path/to/beryl3 && python manage.py collect_daily_metrics --send-email
```

**Make Targets:**
```makefile
# Collect metrics manually
make collect-metrics

# Collect and send email
make collect-metrics-email

# View metrics in browser
make view-metrics
```

### Data Retention

**Policy:** 365 days (1 year)

**Cleanup:**
- Automatic deletion of metrics older than 365 days
- Runs during daily collection
- Maintains database size
- Preserves trend analysis capability

## Phase 7: Enhanced Display

**Commit:** 1db1269, c193dd3

### Improvements Made

1. **Removed Broken Charts**
   - Removed Chart.js visualizations
   - Charts had rendering issues
   - Historical tables more reliable

2. **Enhanced Comparison Columns**
   - Show previous values in gray
   - Format: "Current value (Previous value) ↑"
   - Example: "142 (141) ↑"
   - Clearer context for trends

3. **Updated Column Headers**
   - Before: "vs Yesterday", "vs 7 Days", "vs 30 Days"
   - After: "Yesterday", "7 Days Ago", "30 Days Ago"
   - More intuitive labeling

4. **Historical Data Tables**
   - Added to all 6 sections
   - Show/Hide toggle buttons
   - Last 10 entries displayed
   - Date + key metrics per row

5. **Email Report Updates**
   - Match web dashboard display
   - Previous values alongside trends
   - Consistent formatting
   - Better readability

## Technical Implementation

### Alert Thresholds

**Warning Levels:**
- 10% change: Warning (yellow)
- 25% change: Critical (red)

**Applied to:**
- User growth/decline
- Storage increases
- Moderation flags
- Error rates

### Database Schema

```python
class DailyMetrics(models.Model):
    # Metadata
    date = models.DateField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # 51 metric fields across 6 categories
    users_total = models.IntegerField()
    collections_total = models.IntegerField()
    items_total = models.IntegerField()
    storage_used_mb = models.DecimalField()
    # ... and 47 more fields

    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Daily Metrics"
```

### Trend Calculation

```python
def calculate_trend(current, previous):
    if previous == 0 or previous is None:
        return '→' if current == 0 else '↑'

    change_percent = ((current - previous) / previous) * 100

    if abs(change_percent) < 1:  # Less than 1% change
        return '→'
    elif change_percent > 0:
        return '↑'
    else:
        return '↓'
```

## Files Created/Modified

### Created
- `web/models.py` - DailyMetrics model
- `web/management/commands/collect_daily_metrics.py` - Collection command
- `templates/emails/daily_metrics_report.html` - Email template
- `templates/sys/metrics.html` - Web dashboard
- `web/views/sys.py` - Metrics views (metrics_dashboard, metrics_prometheus)
- `docs/grafana/daily_metrics_dashboard.json` - Grafana dashboard
- `docs/METRICS.md` - Complete documentation

### Modified
- `web/urls.py` - Added metrics URLs
- `Makefile` - Added make targets
- `docs/TODO.md` - Task completion tracking

## Testing Checklist

- ✅ Management command runs successfully
- ✅ All 51 metrics collected correctly
- ✅ Trends calculated accurately
- ✅ Email reports sent successfully
- ✅ Web dashboard displays properly
- ✅ Historical data tables work
- ✅ Toggle buttons functional
- ✅ Prometheus endpoint responds
- ✅ Grafana dashboard imports correctly
- ✅ Cron automation working
- ✅ Data retention cleanup works
- ✅ Color coding applied correctly
- ✅ Previous values shown
- ✅ Make targets functional

## Usage Examples

### Manual Collection
```bash
# Collect metrics
make collect-metrics

# Collect and email
make collect-metrics-email

# View dashboard
make view-metrics
# Opens: http://localhost:8000/sys/metrics
```

### View Latest Metrics
```bash
# Web browser
open http://localhost:8000/sys/metrics

# Prometheus format
curl http://localhost:8000/sys/metrics/prometheus
```

### Query Historical Data
```python
from web.models import DailyMetrics
from datetime import timedelta

# Get last 30 days
metrics = DailyMetrics.objects.filter(
    date__gte=timezone.now().date() - timedelta(days=30)
)

# Calculate average users
avg_users = metrics.aggregate(Avg('users_total'))
```

## Documentation

**Complete Guide:** `docs/METRICS.md`

**Sections:**
1. Overview and goals
2. Metric categories breakdown
3. Collection process
4. Email reports configuration
5. Web dashboard usage
6. Prometheus integration
7. Grafana setup
8. Automation and scheduling
9. Data retention policy
10. Troubleshooting

## Related Tasks

- Task 35: System administration interface enhancements
- Task 33: Content moderation metrics
- Task 25: Email marketing metrics

## Commit References

```
bd5aa52 - feat: Complete Phase 6 - Make targets and comprehensive metrics documentation
3988d23 - feat: Add historical trend charts to metrics dashboard
1db1269 - fix: Remove broken charts and enhance metrics display with historical values
c193dd3 - fix: Update daily metrics email to show previous values
c930ab8 - docs: Update Task 36 with metrics display enhancements
```

## Benefits

1. **Visibility:** Complete system health at a glance
2. **Trends:** Identify growth patterns and issues
3. **Alerting:** Automated notifications of significant changes
4. **History:** 365 days of historical data
5. **Integration:** Works with existing monitoring (Grafana)
6. **Automation:** Zero manual intervention required
7. **Actionable:** Clear indicators for decision making

## Future Enhancements

Potential additions:
- Custom metric definitions
- Metric annotations (mark significant events)
- Comparison with custom date ranges
- Export to CSV/PDF
- Slack/Discord notifications
- Metric predictions using ML
