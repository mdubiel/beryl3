# Grafana + Loki Setup Guide

This guide walks you through configuring Grafana to use Loki as a datasource and creating basic dashboards for Django log visualization.

## Prerequisites

- Loki and Grafana containers running via docker-compose
- Django configured to forward logs to Loki
- Containers accessible at:
  - Grafana: http://localhost:3000
  - Loki: http://localhost:3100

## Step 1: Access Grafana

1. Open your browser and go to http://localhost:3000
2. Login credentials:
   - Username: `admin`
   - Password: `beryl3_logs_admin` (from docker-compose environment)

## Step 2: Add Loki Datasource

1. **Navigate to Datasources:**
   - Click on "Settings" (⚙️) in the left sidebar
   - Click "Data sources"
   - Click "Add data source"

2. **Select Loki:**
   - Find and click "Loki" from the list

3. **Configure Loki datasource:**
   - **Name:** `Loki`
   - **URL:** `http://loki:3100` (use Docker service name, not localhost)
   - **Access:** Server (default)
   - Leave other settings as default

4. **Test the connection:**
   - Click "Save & Test" at the bottom
   - You should see "Data source connected and logs found"

## Step 3: Create Basic Django Logs Dashboard

### Method A: Manual Dashboard Creation

1. **Create New Dashboard:**
   - Click "+" in left sidebar
   - Click "Create Dashboard"
   - Click "Add visualization"

2. **Configure Log Panel:**
   - Select "Loki" as datasource
   - In the query field, enter: `{application="beryl3"}`
   - Click "Run query"
   - You should see Django logs appearing

3. **Panel Settings:**
   - **Panel Title:** "Django Application Logs"
   - **Visualization:** Logs (default)
   - **Time range:** Last 15 minutes

4. **Save Dashboard:**
   - Click "Save dashboard" (💾 icon)
   - **Title:** "Django Application Monitoring"
   - **Folder:** General
   - Click "Save"

### Method B: Quick Dashboard Setup

Instead of importing complex JSON, use this simpler approach:

1. **Go to Explore:**
   - Click "Explore" (compass icon) in left sidebar
   - Select "Loki" datasource
   - Enter query: `{application="beryl3"}`
   - Click "Run query"

2. **Create Dashboard from Explore:**
   - Once logs are visible, click "Add to dashboard" 
   - Choose "New dashboard"
   - Click "Open dashboard"
   - Save with title: "Django Application Logs"

**Alternative - Manual Dashboard Creation:**
1. **Create New Dashboard:** Click "+" → "Dashboard"
2. **Add Panel:** Click "Add visualization"
3. **Configure:**
   - Datasource: Loki
   - Query: `{application="beryl3"}`
   - Visualization: Logs
   - Panel title: "Django Application Logs"
4. **Save Dashboard**

## Step 4: Useful LogQL Queries

Here are some useful queries for Django logs:

### Basic Queries
- All application logs: `{application="beryl3"}`
- Error logs only: `{application="beryl3"} |= "ERROR"`
- Warning logs: `{application="beryl3"} |= "WARNING"`
- Specific logger: `{application="beryl3", name="webapp"}`

### Advanced Queries
- User activity: `{application="beryl3"} |= "user" |= "activity"`
- Performance logs: `{application="beryl3", name="performance"}`
- Django framework logs: `{application="beryl3", name="django"}`
- Database queries: `{application="beryl3"} |= "SELECT" or |= "INSERT" or |= "UPDATE"`

### Log Analysis
- Count errors in last hour: `count_over_time({application="beryl3"} |= "ERROR" [1h])`
- Rate of logs: `rate({application="beryl3"} [5m])`
- Top log sources: `topk(10, sum by (name) (count_over_time({application="beryl3"} [1h])))`

## Step 5: Set up Alerts (Optional)

1. **Create Alert Rule:**
   - Go to Alerting → Alert rules
   - Click "New rule"

2. **Configure Error Alert:**
   - **Query:** `count_over_time({application="beryl3"} |= "ERROR" [5m])`
   - **Condition:** IS ABOVE 5 (adjust threshold as needed)
   - **Evaluation:** Every 1m for 2m

3. **Notification:**
   - Set up contact points (email, Slack, etc.)
   - Assign to notification policy

## Troubleshooting

### Datasource UID Not Found Error
- **Problem:** "Data source with UID 'xxxxx' not found" when importing dashboards
- **Solution:** 
  - Don't import pre-made dashboard JSON
  - Use **Method A** (Manual Dashboard Creation) or **Method B** (Quick Dashboard Setup)
  - Create dashboards manually after adding your Loki datasource

### Datasource Connection Issues
- **Problem:** "Data source connected but no logs found"
- **Solution:** 
  - Check that Django is generating logs: visit your Django app
  - Verify Loki URL uses `http://loki:3100` (Docker service name)
  - Check docker-compose logs: `docker-compose logs loki`

### No Logs Appearing
- **Problem:** Empty log panels
- **Solution:**
  - Test log generation: access Django debug endpoint or make requests
  - Check LogQL syntax: start with simple `{application="beryl3"}`
  - Verify time range (try "Last 1 hour" instead of "Last 15 minutes")

### Container Network Issues
- **Problem:** Connection refused to Loki
- **Solution:**
  - Ensure containers are on same Docker network
  - Use service names (`loki`, `grafana`) not `localhost` in container-to-container communication
  - Check container status: `docker-compose ps`

## Next Steps

1. **Create more specific dashboards** for different aspects:
   - User activity dashboard
   - Performance monitoring
   - Error tracking and analysis

2. **Set up log retention** in Loki configuration

3. **Configure log parsing** for structured logging

4. **Add more datasources** like Prometheus for metrics

Your log collection system is now ready for development and testing!