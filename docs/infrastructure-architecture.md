# Beryl3 Staging Environment Architecture

## Overview

The staging environment is designed to maximize resource efficiency by separating **common infrastructure services** (shared across multiple projects) from **project-specific services** (unique to Beryl3). This approach allows multiple staging projects to share monitoring, logging, and other infrastructure while maintaining isolation for application-specific components.

## Service Architecture

### Common Infrastructure Services (Shared)
*These services are deployed once per staging server and shared across multiple projects*

#### Monitoring & Observability Stack
- **Grafana** (grafana.staging.mdubiel.org) - Centralized dashboard and visualization
- **Prometheus** (prometheus.staging.mdubiel.org) - Metrics collection and alerting
- **Loki** (loki.staging.mdubiel.org) - Centralized log aggregation
- **Alertmanager** (alerts.staging.mdubiel.org) - Alert routing and notification

#### Infrastructure Services
- **Nginx** (staging.mdubiel.org) - Reverse proxy and SSL termination
- **Portainer** (portainer.staging.mdubiel.org) - Docker container management
- **Redis Cluster** - Shared caching layer (multiple instances for HA)

#### Development Tools
- **GitLab Runner** - CI/CD execution environment
- **Registry Mirror** - Docker image caching
- **Backup Service** - Automated backup orchestration

### Project-Specific Services (Beryl3)
*These services are unique to the Beryl3 project*

#### Application Layer
- **Beryl3 Web App** (beryl3-stage.mdubiel.org) - Django application
- **Beryl3 Email Worker** - Background email processing
- **Beryl3 Celery Workers** - Task queue processing

#### Data Layer
- **Beryl3 PostgreSQL** - Dedicated database instance
- **Beryl3 Redis** - Project-specific cache/sessions

#### Project Tools
- **Beryl3 Nginx** - Application-specific proxy configuration

## Network Architecture

### Network Segmentation
```
┌─────────────────────────────────────────────────────────────┐
│                    Staging Server                           │
├─────────────────────────────────────────────────────────────┤
│  Common Network (172.19.0.0/16)                           │
│  ├── Nginx (Host Level) - Entry point                    │
│  ├── Grafana (172.19.0.20) - Shared monitoring           │
│  ├── Prometheus (172.19.0.21) - Shared metrics           │
│  ├── Loki (172.19.0.22) - Shared logs                    │
│  └── Redis Cluster (172.19.0.30-32)                      │
├─────────────────────────────────────────────────────────────┤
│  Beryl3 Network (172.20.0.0/16)                          │
│  ├── Beryl3 App (172.20.0.20)                            │
│  ├── Beryl3 PostgreSQL (172.20.0.10)                     │
│  ├── Beryl3 Redis (172.20.0.11)                          │
│  └── Beryl3 Workers (172.20.0.25-29)                     │
├─────────────────────────────────────────────────────────────┤
│  Other Projects...                                         │
│  └── Project-X Network (172.21.0.0/16)                   │
└─────────────────────────────────────────────────────────────┘
```

### Domain Strategy
- **Common services:** `service.staging.mdubiel.org`
- **Project services:** `project-stage.mdubiel.org`
- **SSL:** Wildcard certificate for `*.staging.mdubiel.org` and individual certs for projects

## Resource Allocation

### Common Services Resource Limits
```yaml
grafana:
  memory: 512MB
  cpu: 0.5 cores
  
prometheus:
  memory: 2GB
  cpu: 1 core
  
loki:
  memory: 1GB
  cpu: 0.5 cores
  
nginx:
  memory: 256MB
  cpu: 0.2 cores
```

### Beryl3 Services Resource Limits
```yaml
webapp:
  memory: 1GB
  cpu: 1 core
  replicas: 2
  
postgres:
  memory: 1GB
  cpu: 0.5 cores
  
redis:
  memory: 256MB
  cpu: 0.1 cores
  
workers:
  memory: 512MB
  cpu: 0.5 cores
  replicas: 2
```

## Deployment Strategy

### Phase 1: Common Infrastructure
1. **Base system setup** (Docker, networking, SSL)
2. **Deploy Nginx** with automatic SSL (Let's Encrypt)
3. **Deploy monitoring stack** (Prometheus, Grafana, Loki)
4. **Configure shared services** (Redis cluster, backup)

### Phase 2: Project-Specific Deployment
1. **Create project network** and volumes
2. **Deploy database** with initialization
3. **Deploy application** with health checks
4. **Configure monitoring integration** (metrics endpoints, log forwarding)
5. **Run migrations** and setup tasks

### Phase 3: Integration Testing
1. **Health check validation**
2. **Log flow verification** (app → Loki → Grafana)
3. **Metric collection testing** (app → Prometheus → Grafana)
4. **SSL certificate validation**
5. **Backup procedure testing**

## Monitoring Integration

### Metrics Collection
```yaml
# Beryl3 app exposes metrics on /metrics endpoint
# Prometheus scrapes via service discovery
prometheus_scrape_configs:
  - job_name: 'beryl3-staging'
    static_configs:
      - targets: ['172.20.0.20:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Log Forwarding
```yaml
# All Beryl3 services forward logs to shared Loki
loki_config:
  clients:
    - url: http://172.19.0.22:3100/loki/api/v1/push
      tenant_id: beryl3-staging
```

### Dashboard Structure
- **Infrastructure Overview** - Common services status
- **Beryl3 Application** - Project-specific metrics and logs  
- **System Resources** - Server utilization across all services

## Data Management

### Backup Strategy
```yaml
backup_jobs:
  common:
    - grafana_config: daily
    - prometheus_data: weekly
    - loki_indexes: daily
    
  beryl3_specific:
    - postgres_db: daily + weekly + monthly
    - media_files: daily (GCS handles this)
    - application_logs: 14 days retention
```

### Volume Management
```yaml
common_volumes:
  grafana_data: /var/lib/docker/volumes/common_grafana
  prometheus_data: /var/lib/docker/volumes/common_prometheus
  loki_data: /var/lib/docker/volumes/common_loki

beryl3_volumes:
  postgres_data: /var/lib/docker/volumes/beryl3_postgres
  redis_data: /var/lib/docker/volumes/beryl3_redis
```

## Security Architecture

### Network Security
- **Nginx handles all external access** - no direct container exposure
- **Internal networks isolated** - projects cannot access each other
- **Common services accessible** via controlled service discovery
- **SSL termination** at Nginx level

### Access Control
```yaml
access_matrix:
  grafana:
    - beryl3_team: editor
    - monitoring_team: admin
    - developers: viewer
    
  nginx_status:
    - ops_team: admin
    - developers: viewer
```

### Secret Management
- **Common secrets:** Stored in `/opt/staging/common/secrets/`
- **Project secrets:** Stored in `/opt/staging/projects/beryl3/secrets/`
- **Vault integration:** For production-like secret rotation

## Deployment Automation

### Ansible Playbook Structure
```
staging-deploy/
├── inventories/
│   ├── staging/
│   │   ├── hosts.yml
│   │   └── group_vars/
├── roles/
│   ├── common/
│   │   ├── docker/
│   │   ├── nginx/
│   │   ├── monitoring/
│   │   └── networking/
│   └── beryl3/
│       ├── database/
│       ├── application/
│       └── workers/
├── playbooks/
│   ├── common-infrastructure.yml
│   ├── beryl3-deploy.yml
│   └── full-stack.yml
└── vars/
    ├── common.yml
    └── beryl3.yml
```

### Deployment Commands
```bash
# Deploy common infrastructure (run once)
ansible-playbook -i inventories/staging common-infrastructure.yml

# Deploy Beryl3 project
ansible-playbook -i inventories/staging beryl3-deploy.yml

# Full deployment (infrastructure + all projects)
ansible-playbook -i inventories/staging full-stack.yml

# Update only Beryl3 application
ansible-playbook -i inventories/staging beryl3-deploy.yml --tags app
```

## Configuration Management

### Environment Variables
```yaml
common_env_vars:
  GRAFANA_ADMIN_PASSWORD: "{{ vault_grafana_password }}"
  PROMETHEUS_RETENTION: "30d"
  LOKI_RETENTION: "14d"
  
beryl3_env_vars:
  SECRET_KEY: "{{ vault_beryl3_secret_key }}"
  DATABASE_URL: "postgresql://beryl3:{{ vault_db_password }}@172.20.0.10:5432/beryl3_staging"
  REDIS_URL: "redis://:{{ vault_redis_password }}@172.20.0.11:6379/0"
  LOKI_URL: "http://172.19.0.22:3100"
```

### Service Discovery
```yaml
# Nginx upstream configuration
nginx_upstreams:
  beryl3-backend:
    servers:
      - "127.0.0.1:8080"
    
  grafana-backend:
    servers:
      - "127.0.0.1:3000"
      
  prometheus-backend:
    servers:
      - "127.0.0.1:9090"
```

## Operational Procedures

### Health Monitoring
```bash
# Check common services
curl -f https://grafana.staging.mdubiel.org/api/health
curl -f https://prometheus.staging.mdubiel.org/-/healthy
curl -f https://staging.mdubiel.org/nginx_status

# Check Beryl3 services  
curl -f https://beryl3-stage.mdubiel.org/health/
docker exec beryl3_postgres pg_isready
```

### Scaling Procedures
```yaml
# Scale Beryl3 workers
docker service scale beryl3_celery_workers=4

# Scale common services (if needed)
docker service scale common_redis=3
```

### Maintenance Windows
- **Common services updates:** Monthly, coordinated across all projects
- **Project updates:** Independent, no impact on other projects
- **SSL renewal:** Automatic via Nginx + Let's Encrypt (Certbot)

## Cost Optimization

### Resource Sharing Benefits
- **Single Grafana instance** serves multiple projects
- **Shared Redis cluster** for non-sensitive caching
- **Common Prometheus** with multi-tenant labeling
- **Shared SSL certificates** for staging subdomains

### Resource Monitoring
```yaml
resource_alerts:
  cpu_usage: > 80% for 5 minutes
  memory_usage: > 85% for 5 minutes
  disk_usage: > 90%
  
cost_tracking:
  monthly_target: $150
  per_project_allocation: 60%
  shared_infrastructure: 40%
```

This architecture provides clear separation between shared infrastructure and project-specific components, enabling efficient resource utilization while maintaining proper isolation and scalability.