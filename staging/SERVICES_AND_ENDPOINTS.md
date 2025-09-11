# Beryl3 Staging Environment - Services & Endpoints Reference

## Infrastructure Overview
- **Host**: 192.168.1.14 (staging-server)
- **Environment**: Staging (Local Network)
- **SSL**: Let's Encrypt certificates configured
- **Monitoring**: Comprehensive monitoring with Prometheus, Grafana, and Loki

---

## 🌐 Public Web Services

### Main Application (Beryl3 Django)
- **HTTP**: http://192.168.1.14:8000
- **HTTPS**: https://beryl3.staging.mdubiel.org
- **Container**: `beryl3_staging_webapp`
- **Description**: Main Django application for collection management
- **Network**: `beryl3_staging`, `monitoring`

### Grafana (Monitoring Dashboard)
- **HTTP**: http://192.168.1.14:3000
- **HTTPS**: https://grafana.staging.mdubiel.org
- **Container**: `grafana`
- **Credentials**: admin / admin123
- **Description**: Monitoring dashboards and log analysis
- **Network**: `monitoring`

### Prometheus (Metrics Collection)
- **HTTP**: http://192.168.1.14:9090
- **HTTPS**: https://prometheus.staging.mdubiel.org
- **Container**: `prometheus`
- **Description**: Metrics collection and alerting
- **Network**: `monitoring`

### Docker Registry
- **HTTP**: http://192.168.1.14:5000
- **HTTPS**: https://registry.staging.mdubiel.org
- **Container**: `docker-registry`
- **Credentials**: registry / registry123
- **Description**: Private Docker image registry
- **Network**: `registry`, `monitoring`

### Docker Registry UI
- **HTTP**: http://192.168.1.14:8082
- **Container**: `docker-registry-ui`
- **Description**: Web interface for Docker registry management
- **Network**: `registry`, `monitoring`

### Adminer (Database Management)
- **HTTP**: http://192.168.1.14:8084
- **Container**: `adminer`
- **Description**: PostgreSQL database management interface
- **Network**: `monitoring`, `projects`

---

## 📊 Metrics Endpoints

### Django Application Metrics
- **Django Middleware**: http://192.168.1.14:8000/metrics
  - Container: `beryl3_staging_webapp`
  - Type: Performance metrics (requests, response times, status codes)
  - Format: Prometheus format

- **Custom Business Metrics**: http://192.168.1.14:8000/sys/metrics/prometheus/
  - Container: `beryl3_staging_webapp`
  - Type: Application data (users, collections, items)
  - Format: Prometheus format

### Infrastructure Metrics Exporters
- **Node Exporter**: http://192.168.1.14:9100/metrics
  - Container: `node-exporter`
  - Type: System metrics (CPU, memory, disk, network)
  - Network: `monitoring`

- **cAdvisor**: http://192.168.1.14:8080/metrics
  - Container: `cadvisor`
  - Type: Container metrics (resource usage, performance)
  - Network: `monitoring`

- **Nginx Exporter**: http://192.168.1.14:9113/metrics
  - Container: `nginx-prometheus-exporter`
  - Type: Nginx web server metrics
  - Network: `monitoring`

- **Blackbox Exporter**: http://192.168.1.14:9115/metrics
  - Container: `blackbox-exporter`
  - Type: Health check probes and uptime monitoring
  - Network: `monitoring`

- **Grafana Metrics**: http://grafana:3000/metrics
  - Container: `grafana`
  - Type: Grafana internal metrics
  - Network: `monitoring` (internal)

- **Loki Metrics**: http://loki:3100/metrics
  - Container: `loki`
  - Type: Log storage metrics
  - Network: `monitoring` (internal)

- **Promtail Metrics**: http://192.168.1.14:9080/metrics
  - Container: `promtail`
  - Type: Log shipping metrics
  - Network: `monitoring`

---

## 🗃️ Database Services

### PostgreSQL (Main Application)
- **Internal**: postgres:5432 (from containers)
- **Container**: `beryl3_staging_postgres`
- **Database**: beryl3_staging
- **User**: beryl3_staging
- **Network**: `beryl3_staging`
- **Management**: Via Adminer at http://192.168.1.14:8084

### Redis (Caching/Queue)
- **Internal**: redis:6379 (from containers)
- **Container**: `beryl3_staging_redis`
- **Network**: `beryl3_staging`

---

## 📋 Log Services

### Loki (Log Storage)
- **HTTP**: http://192.168.1.14:3100
- **Container**: `loki`
- **Query**: http://192.168.1.14:3100/loki/api/v1/query
- **Description**: Centralized log storage
- **Network**: `monitoring`

### Promtail (Log Shipping)
- **HTTP**: http://192.168.1.14:9080
- **Container**: `promtail`
- **Metrics**: http://192.168.1.14:9080/metrics
- **Description**: Log collection and forwarding to Loki
- **Network**: `monitoring`

---

## ⚠️ Alert Services

### AlertManager
- **HTTP**: http://192.168.1.14:9093
- **Container**: `alertmanager`
- **Description**: Alert routing and notification management
- **Network**: `monitoring`

---

## 🔧 Reverse Proxy (Nginx)

### Nginx Proxy
- **HTTP**: http://192.168.1.14:80
- **HTTPS**: https://192.168.1.14:443
- **Container**: `nginx-proxy`
- **Config Path**: /opt/shared/nginx/config
- **SSL Certs**: /opt/ssl
- **Networks**: `monitoring`, `projects`, `registry`

### Proxy Routes
- `/` → beryl3_staging_webapp:8000
- `grafana.staging.mdubiel.org` → grafana:3000
- `prometheus.staging.mdubiel.org` → prometheus:9090
- `registry.staging.mdubiel.org` → docker-registry:5000

---

## 🔐 SSL Certificate Information

### Certificate Paths
- **Full Chain**: /opt/ssl/fullchain.pem
- **Private Key**: /opt/ssl/privkey.pem
- **Certificate**: /opt/ssl/cert.pem
- **Chain**: /opt/ssl/chain.pem

### Covered Domains
- beryl3.staging.mdubiel.org
- grafana.staging.mdubiel.org
- prometheus.staging.mdubiel.org
- registry.staging.mdubiel.org

### Renewal
- **Method**: Let's Encrypt with DNS challenges
- **Schedule**: Weekly via cron (Sundays at 12:00)
- **Manual Renewal**: `sudo certbot renew --manual --preferred-challenges=dns`

---

## 📊 Grafana Dashboards

### Available Dashboards
1. **Infrastructure Overview** - System metrics and health
2. **Container Monitoring** - Docker container performance
3. **Service Health** - Service availability and response times
4. **Nginx Performance** - Web server metrics
5. **Log Analysis** - Log aggregation and analysis
6. **Alert Management** - Alert status and history
7. **Beryl3 Django Application Logs** - Django application logs
8. **Beryl3 Django Application Metrics** - Django performance and business metrics

### Datasources
- **Prometheus**: http://prometheus:9090
- **Loki**: http://loki:3100

---

## 🐳 Docker Networks

### monitoring
- **Purpose**: Infrastructure monitoring services
- **Services**: prometheus, grafana, loki, promtail, alertmanager, node-exporter, cadvisor, blackbox-exporter, nginx-prometheus-exporter, adminer

### projects
- **Purpose**: Application project isolation
- **Services**: nginx-proxy, adminer

### registry
- **Purpose**: Docker registry services
- **Services**: docker-registry, docker-registry-ui, nginx-proxy

### beryl3_staging
- **Purpose**: Beryl3 application services
- **Subnet**: 172.20.0.0/16
- **Services**: beryl3_staging_webapp, beryl3_staging_postgres, beryl3_staging_redis, beryl3_staging_nginx, beryl3_staging_grafana_local, beryl3_staging_email_worker

---

## 🔍 Health Checks & Monitoring

### Blackbox Exporter Targets
- http://grafana.staging.mdubiel.org
- http://prometheus.staging.mdubiel.org
- http://registry.staging.mdubiel.org
- http://192.168.1.14:3000 (Grafana)
- http://192.168.1.14:9090 (Prometheus)
- http://192.168.1.14:5000 (Registry)

### Service Status Endpoints
- **Grafana Health**: http://192.168.1.14:3000/api/health
- **Prometheus Health**: http://192.168.1.14:9090/-/healthy
- **Django Health**: http://192.168.1.14:8000/ (custom health check)

---

## 💾 Storage & Data Persistence

### Docker Volumes
- `webapp_staging_media` - Django media files (fallback)
- `postgres_staging_data` - PostgreSQL database
- `redis_staging_data` - Redis persistence
- Prometheus data: /opt/shared/prometheus/data
- Grafana data: /opt/shared/grafana/data
- Loki data: /opt/shared/loki/data

### GCS Integration
- **Bucket**: beryl3-stage
- **Project**: mateusz-344213
- **Static Files**: https://storage.googleapis.com/beryl3-stage/static/
- **Media Files**: https://storage.googleapis.com/beryl3-stage/media/
- **Credentials**: /app/gcs-key.json (in containers)

---

## 🚀 Deployment & Management

### Ansible Playbooks
- **Infrastructure**: `playbooks/infra.yml`
- **SSL Setup**: `playbooks/ssl-setup.yml`
- **Grafana Management**: `playbooks/grafana-management.yml`

### Key Commands
```bash
# Deploy infrastructure
ansible-playbook -i inventory/staging.yml playbooks/infra.yml

# Setup SSL certificates
ansible-playbook -i inventory/staging.yml playbooks/ssl-setup.yml

# Restart services
ssh ansible@192.168.1.14 "docker restart nginx-proxy grafana prometheus"

# View logs
ssh ansible@192.168.1.14 "docker logs -f beryl3_staging_webapp"
```

### Access Credentials
- **Grafana**: admin / admin123
- **Docker Registry**: registry / registry123
- **PostgreSQL**: beryl3_staging / staging_secure_db_password_change_this

---

## 🏷️ Container Labels & Service Discovery

### Prometheus Scrape Labels
- `prometheus.scrape=true/false` - Enable/disable scraping
- `service.name` - Service identifier
- `service.component` - Component type
- `metrics.port` - Custom metrics port

### Service Components
- **reverse-proxy**: nginx-proxy
- **metrics-storage**: prometheus
- **visualization**: grafana
- **log-storage**: loki
- **log-shipping**: promtail
- **alert-routing**: alertmanager
- **system-metrics**: node-exporter
- **container-metrics**: cadvisor
- **artifact-storage**: docker-registry
- **database-management**: adminer
- **django-application**: beryl3_staging_webapp

This documentation provides a complete reference for all services, endpoints, and configurations in the Beryl3 staging environment.