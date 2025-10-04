# Beryl Grafana Dashboards

This directory contains Grafana dashboard JSON files for visualizing Beryl metrics.

## Available Dashboards

### `beryl_daily_metrics_dashboard.json`

Comprehensive dashboard for daily metrics collected by the `collect_daily_metrics` management command.

**Metrics Displayed:**
- **User Metrics**: Total users, active users (24h/7d/30d), new users by period
- **Collection Metrics**: Total collections, by visibility, created by period
- **Item Metrics**: Total items, by status, favorites, created by period
- **Storage Metrics**: Files, bytes, uploads, orphaned/corrupted files
- **Link Metrics**: Total links, matched/unmatched patterns
- **Content Moderation**: Flagged content, pending review, violations, banned users
- **Engagement**: Items with images/attributes/links, averages
- **Performance**: Metrics collection duration

**Dashboard Features:**
- 23 panels (graphs and singlestat)
- Europe/Zurich timezone
- 30-day time range by default
- Auto-refresh every 5 minutes
- Sparklines on key metrics
- Alert on storage file issues

## Prerequisites

1. **Grafana Installation**: You need a Grafana instance (v7.0+)
2. **Prometheus Data Source**: Configure Prometheus to scrape your Beryl instance
3. **Beryl Metrics Endpoint**: Ensure `/sys/metrics/prometheus` is accessible

## Prometheus Configuration

Add this scrape config to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'beryl'
    scrape_interval: 5m
    scrape_timeout: 30s
    metrics_path: '/sys/metrics/prometheus'
    static_configs:
      - targets: ['your-beryl-instance:port']
        labels:
          environment: 'production'  # or 'qa', 'development'
```

## Importing the Dashboard

### Method 1: Grafana UI

1. Log in to your Grafana instance
2. Navigate to **Dashboards** → **Import**
3. Click **Upload JSON file**
4. Select `beryl_daily_metrics_dashboard.json`
5. Select your Prometheus data source
6. Click **Import**

### Method 2: Grafana API

```bash
# Set your Grafana URL and API key
GRAFANA_URL="http://your-grafana:3000"
API_KEY="your-api-key"

# Import the dashboard
curl -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${API_KEY}" \
  -d @beryl_daily_metrics_dashboard.json
```

### Method 3: Grafana Provisioning

Copy the dashboard file to your Grafana provisioning directory:

```bash
# For Docker installations
cp beryl_daily_metrics_dashboard.json /var/lib/grafana/dashboards/

# Update your provisioning config (provisioning/dashboards/dashboard.yml)
apiVersion: 1
providers:
  - name: 'Beryl Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
```

## Dashboard Customization

After importing, you can customize:

1. **Time Range**: Adjust default time range (currently 30 days)
2. **Refresh Interval**: Change auto-refresh rate (currently 5 minutes)
3. **Alerts**: Configure alert notifications for critical metrics
4. **Panel Layout**: Rearrange or resize panels
5. **Thresholds**: Set custom thresholds for gauges and alerts

## Troubleshooting

### No Data Shown

1. **Check Prometheus**: Verify Prometheus is scraping your Beryl instance
   ```bash
   # Check Prometheus targets
   curl http://prometheus:9090/api/v1/targets
   ```

2. **Check Metrics Endpoint**: Verify metrics are being exported
   ```bash
   curl http://your-beryl-instance/sys/metrics/prometheus
   ```

3. **Check Data Source**: Verify Grafana data source configuration
   - Navigate to **Configuration** → **Data Sources**
   - Test the Prometheus connection

### Metrics Not Updating

1. **Check Collection**: Verify daily metrics are being collected
   ```bash
   python manage.py collect_daily_metrics --verbose
   ```

2. **Check Cron Job**: Ensure cron job is running (see deployment docs)

3. **Check Time Range**: Metrics are collected daily, adjust time range accordingly

### Permission Errors

- Ensure API key has sufficient permissions (Editor or Admin role)
- Check firewall rules allow access to Prometheus and Beryl instance

## Maintenance

- **Dashboard Updates**: When new metrics are added, update the JSON file
- **Version Control**: Keep dashboard JSON in version control
- **Backup**: Export dashboard JSON regularly from Grafana UI

## Related Documentation

- [Daily Metrics Implementation Guide](../../docs/reports/daily_metrics_implementation.md)
- [Prometheus Endpoint Documentation](../../docs/reports/daily_metrics_implementation.md#phase-4-prometheus-integration)
- [Metrics Collection Command](../../web/management/commands/collect_daily_metrics.py)
