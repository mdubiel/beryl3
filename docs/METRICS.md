# Daily Metrics System

**Status**: ✅ Implemented and Production-Ready
**Timezone**: Europe/Zurich
**Collection Frequency**: Daily at midnight (via cron)
**Retention Period**: 365 days (configurable)

## Overview

The Beryl daily metrics system automatically collects comprehensive platform statistics daily and provides:

- **Historical tracking** of all key metrics over time
- **Email reports** with trend analysis sent to superusers
- **Web dashboard** at `/sys/metrics` with visual trends
- **Prometheus endpoint** at `/sys/metrics/prometheus` for Grafana integration
- **Make targets** for manual collection and viewing

All metrics are stored in the `DailyMetrics` model, collected once per day, eliminating expensive real-time queries.

## Metrics Collected

### User Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `total_users` | Total registered users | N/A |
| `active_users_24h` | Users who logged in within last 24 hours | -25% = critical |
| `active_users_7d` | Users who logged in within last 7 days | -25% = critical |
| `active_users_30d` | Users who logged in within last 30 days | -25% = critical |
| `new_users_24h` | Users registered in last 24 hours | +25% = investigate |
| `new_users_7d` | Users registered in last 7 days | +25% = investigate |
| `new_users_30d` | Users registered in last 30 days | +25% = investigate |

### Collection Metrics
| Metric | Description |
|--------|-------------|
| `total_collections` | Total number of collections |
| `collections_private` | Private collections count |
| `collections_public` | Public collections count |
| `collections_unlisted` | Unlisted collections count |
| `collections_created_24h` | Collections created in last 24 hours |
| `collections_created_7d` | Collections created in last 7 days |
| `collections_created_30d` | Collections created in last 30 days |

### Item Metrics
| Metric | Description |
|--------|-------------|
| `total_items` | Total items across all collections |
| `items_in_collection` | Items with status: In Collection |
| `items_wanted` | Items with status: Wanted |
| `items_reserved` | Items with status: Reserved |
| `items_ordered` | Items with status: Ordered |
| `items_lent` | Items with status: Lent |
| `items_previously_owned` | Items with status: Previously Owned |
| `items_sold` | Items with status: Sold |
| `items_given_away` | Items with status: Given Away |
| `favorite_items_total` | Total favorited items |
| `items_created_24h` | Items created in last 24 hours |
| `items_created_7d` | Items created in last 7 days |
| `items_created_30d` | Items created in last 30 days |
| `item_types_count` | Total item types defined |
| `item_type_distribution` | Distribution by type (JSON) |

### Link Metrics
| Metric | Description |
|--------|-------------|
| `total_links` | Total links in items and collections |
| `matched_link_patterns` | Links matching defined patterns |
| `unmatched_link_patterns` | Links not matching any pattern |
| `link_pattern_distribution` | Usage by pattern (JSON) |

### Storage Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `total_media_files` | Total media files | N/A |
| `total_storage_bytes` | Total storage used in bytes | Monitor growth |
| `recent_uploads_24h` | Files uploaded in last 24 hours | N/A |
| `recent_uploads_7d` | Files uploaded in last 7 days | N/A |
| `recent_uploads_30d` | Files uploaded in last 30 days | N/A |
| `orphaned_files` | Files not linked to items/collections | >0 = review |
| `corrupted_files` | Files that failed integrity check | >0 = critical |
| `storage_by_type` | Storage distribution by file type (JSON) | N/A |

### Attribute Metrics
| Metric | Description |
|--------|-------------|
| `total_attributes` | Total attribute definitions |
| `attribute_usage` | Attribute usage statistics (JSON) |

### Email Metrics
| Metric | Description |
|--------|-------------|
| `total_emails` | Total emails tracked (nullable) |
| `emails_pending` | Emails pending delivery (nullable) |
| `emails_sent` | Emails successfully sent (nullable) |
| `emails_failed` | Emails that failed to send (nullable) |
| `marketing_opt_in` | Users opted in to marketing (nullable) |
| `marketing_opt_out` | Users opted out of marketing (nullable) |
| `emails_synced_resend` | Whether stats are synced with Resend |

### Content Moderation Metrics
| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `flagged_content` | Content items flagged for review | >10 = review |
| `pending_review` | Content items pending moderation | >20 = attention |
| `user_violations` | Total user violations | Monitor trend |
| `banned_users` | Currently banned users | Monitor trend |

### Engagement Metrics
| Metric | Description |
|--------|-------------|
| `items_with_images_pct` | Percentage of items with images |
| `items_with_attributes_pct` | Percentage of items with custom attributes |
| `items_with_links_pct` | Percentage of items with links |
| `avg_attributes_per_item` | Average attributes per item |
| `avg_items_per_collection` | Average items per collection |

### Metadata
| Metric | Description |
|--------|-------------|
| `collection_date` | Date of metrics snapshot (unique) |
| `collected_at` | Timestamp when metrics were collected |
| `collection_duration_seconds` | How long collection took |

## Running Manually

### Using Make Targets (Recommended)

```bash
# Collect metrics (verbose output)
make collect-metrics

# Collect metrics and send email report
make collect-metrics-email

# View latest metrics in terminal
make view-metrics
```

### Using Management Command

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

### Using Django Shell

```python
from web.models import DailyMetrics

# View latest metrics
latest = DailyMetrics.objects.order_by('-collection_date').first()
print(f"Users: {latest.total_users}")
print(f"Collections: {latest.total_collections}")
print(f"Items: {latest.total_items}")

# Get trend (vs 7 days ago)
change = latest.get_change('total_users', days_ago=7)
print(f"User change: {change['change']} ({change['change_pct']}%)")

# Cleanup old records (older than retention period)
DailyMetrics.cleanup_old_records()
```

## Email Reports

Email reports are automatically sent to all superusers when using `--send-email` flag.

**Report Contents:**
- Executive summary with key metrics
- Comparison with yesterday and week ago
- Color-coded trend indicators (↑ green, ↓ red)
- Alert highlights for critical changes (≥25%)
- Warning highlights for significant changes (≥10%)
- Tables for each metric category
- Collection duration and timestamp

**Configuration:**
```bash
# Environment variables
METRICS_ALERT_THRESHOLD_WARNING=10   # Yellow warning at 10% change
METRICS_ALERT_THRESHOLD_CRITICAL=25  # Red alert at 25% change
METRICS_RETENTION_DAYS=365           # Keep metrics for 1 year
```

**Recipients:** All users with `is_superuser=True`

## Dashboard

### Web Dashboard

**URL**: `/sys/metrics`

**Features:**
- Table layout with current values
- Trend indicators for yesterday, 7 days, 30 days
- Color-coded changes (green ↑, red ↓, yellow/red thresholds)
- Last collection timestamp
- Auto-refresh every 5 minutes
- 6 metric categories in separate tables

**Access:** Requires application admin permission

### Prometheus Endpoint

**URL**: `/sys/metrics/prometheus`

**Format:** Prometheus text format with HELP and TYPE annotations

**Features:**
- 40+ metrics exported
- Labels for dimensional data (period, status, visibility, etc.)
- JSON field distributions (item types, link patterns, storage by type)
- Ready for Grafana scraping

**Example Output:**
```
# HELP beryl_users_total Total number of users
# TYPE beryl_users_total gauge
beryl_users_total 150

# HELP beryl_users_active Active users by time period
# TYPE beryl_users_active gauge
beryl_users_active{period="24h"} 45
beryl_users_active{period="7d"} 89
beryl_users_active{period="30d"} 120
```

## Prometheus/Grafana Integration

### Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'beryl'
    scrape_interval: 5m
    scrape_timeout: 30s
    metrics_path: '/sys/metrics/prometheus'
    static_configs:
      - targets: ['your-beryl-instance:port']
        labels:
          environment: 'production'
```

### Grafana Dashboard

**Location**: `workflows/grafana/beryl_daily_metrics_dashboard.json`

**Import Methods:**
1. **UI**: Dashboards → Import → Upload JSON file
2. **API**: `curl -X POST http://grafana:3000/api/dashboards/db -H "Authorization: Bearer KEY" -d @beryl_daily_metrics_dashboard.json`
3. **Provisioning**: Copy to `/var/lib/grafana/dashboards/`

**Dashboard Features:**
- 23 panels (time-series graphs + singlestats)
- 30-day default time range
- Auto-refresh every 5 minutes
- Alert on storage file issues
- Sparklines on key metrics

**See**: `workflows/grafana/README.md` for detailed instructions

## Automated Collection (Cron)

### Production Setup (Django Europe)

**Cron Job** (runs at midnight Europe/Zurich):

```bash
# /etc/crontab or user crontab
0 0 * * * cd ~/beryl3-prod && source ~/.virtualenvs/beryl3-prod/bin/activate && python manage.py collect_daily_metrics --send-email >> ~/beryl3-prod/logs/metrics_cron.log 2>&1
```

**Preprod Setup:**

```bash
0 0 * * * cd ~/beryl3-preprod && source ~/.virtualenvs/beryl3-preprod/bin/activate && python manage.py collect_daily_metrics --send-email >> ~/beryl3-preprod/logs/metrics_cron.log 2>&1
```

**Testing Cron:**

```bash
# SSH to server
ssh mdubiel@148.251.140.153

# Run manually
cd ~/beryl3-prod
source ~/.virtualenvs/beryl3-prod/bin/activate
python manage.py collect_daily_metrics --verbose --send-email

# Check logs
tail -f ~/beryl3-prod/logs/metrics_cron.log
```

## Troubleshooting

### No Metrics Collected

**Symptoms:** Dashboard shows "No Metrics Available"

**Solutions:**
1. Run collection manually: `make collect-metrics`
2. Check if migration ran: `python manage.py showmigrations web | grep daily`
3. Check database: `python manage.py dbshell` → `SELECT * FROM web_dailymetrics;`
4. Check cron logs: `tail -f ~/beryl3-prod/logs/metrics_cron.log`

### Email Not Sent

**Symptoms:** Metrics collected but no email received

**Solutions:**
1. Verify superusers exist: `python manage.py shell -c "from django.contrib.auth import get_user_model; print(list(get_user_model().objects.filter(is_superuser=True).values_list('email', flat=True)))"`
2. Check email settings in `.env`: `EMAIL_HOST`, `EMAIL_PORT`, `DEFAULT_FROM_EMAIL`
3. Test email manually: `make collect-metrics-email`
4. Check email queue: Visit `/sys/emails` dashboard

### Missing Data in Dashboard

**Symptoms:** Some metrics show 0 or N/A

**Solutions:**
1. Verify collection ran successfully (check logs)
2. Ensure data exists in database (check actual counts)
3. Re-run collection: `make collect-metrics`
4. Check for errors in collection command output

### Prometheus Endpoint Empty

**Symptoms:** `/sys/metrics/prometheus` returns "No metrics available"

**Solutions:**
1. Run collection at least once: `make collect-metrics`
2. Verify DailyMetrics records exist in database
3. Check application logs for errors

### Trend Indicators Show "N/A"

**Symptoms:** Comparisons show N/A instead of change values

**Solutions:**
- Trends require historical data (wait 1-30 days for full data)
- Yesterday comparison needs 2 days of data
- 7-day comparison needs 8 days of data
- 30-day comparison needs 31 days of data

## Maintenance

### Daily
- ✅ Automated: Cron job runs at midnight
- ✅ Automated: Email sent to superusers
- Manual: Review email report for anomalies

### Weekly
- Review dashboard trends
- Check for unexpected changes
- Investigate any alert thresholds exceeded

### Monthly
- Review Grafana dashboards
- Analyze long-term trends
- Adjust alert thresholds if needed
- Check storage growth

### Yearly
- ✅ Automated: Old metrics (>365 days) auto-cleaned
- Review retention period (`METRICS_RETENTION_DAYS`)
- Archive historical data if needed

## Configuration

### Environment Variables

```bash
# Metrics Configuration
METRICS_RETENTION_DAYS=365              # Keep metrics for 1 year
METRICS_ALERT_THRESHOLD_WARNING=10      # 10% change = yellow warning
METRICS_ALERT_THRESHOLD_CRITICAL=25     # 25% change = red critical
```

### Model Configuration

**File**: `web/models_metrics.py`

**Key Methods:**
- `get_change(field_name, days_ago)` - Calculate trend vs N days ago
- `cleanup_old_records()` - Remove metrics older than retention period

### Collection Command

**File**: `web/management/commands/collect_daily_metrics.py`

**Options:**
- `--date YYYY-MM-DD` - Collect for specific date (default: today)
- `--send-email` - Send email report to superusers
- `--verbose` - Show detailed progress output

## Performance

**Collection Duration:** < 1 second for typical datasets (tested with 3 users, 15 collections, 487 items)

**Database Impact:**
- Read-only queries during collection
- Single INSERT per day (one DailyMetrics record)
- Indexed on `collection_date` and `collected_at`

**Dashboard Performance:**
- No real-time queries (reads from DailyMetrics table)
- Pre-computed trend calculations
- Minimal database load

**Prometheus Performance:**
- Reads single latest DailyMetrics record
- Text format generation (< 200 lines)
- Suitable for 5-minute scrape interval

## Files Reference

### Core Implementation
- `web/models_metrics.py` - DailyMetrics model (380 lines)
- `web/management/commands/collect_daily_metrics.py` - Collection command (500 lines)
- `web/migrations/0025_dailymetrics.py` - Database schema

### Views
- `web/views/sys.py::sys_metrics` - Dashboard view
- `web/views/sys.py::sys_prometheus_metrics` - Prometheus endpoint

### Templates
- `templates/sys/metrics.html` - Dashboard UI
- `templates/emails/daily_metrics_report.html` - Email report
- `templates/emails/partials/_metric_change.html` - Trend indicator
- `templates/partials/_trend_indicator.html` - Trend partial

### Configuration
- `workflows/grafana/beryl_daily_metrics_dashboard.json` - Grafana dashboard
- `workflows/grafana/README.md` - Grafana import instructions
- `Makefile` - Make targets (collect-metrics, view-metrics)

### Documentation
- `docs/reports/daily_metrics_implementation.md` - Implementation guide
- `docs/METRICS.md` - This file

## Future Enhancements

**Potential Additions:**
- Comparison charts in web dashboard
- Export metrics to CSV/JSON
- Custom metric alerts via webhooks
- Metrics API for external integrations
- Per-user collection metrics
- Performance regression detection
- Automated anomaly detection

## Support

For issues or questions:
1. Check this documentation
2. Review implementation guide: `docs/reports/daily_metrics_implementation.md`
3. Check application logs
4. Review cron logs for automated collection issues
