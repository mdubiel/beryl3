# Infrastructure Deployment Summary

## Overview

Successfully created a dedicated infrastructure deployment system with the following components:

### 1. Infrastructure Playbook (`playbooks/infra.yml`)

**Purpose**: Deploys all shared infrastructure services in a containerized environment using `community.docker` modules.

**Services Deployed**:
- **Nginx Proxy** (Port 80/443) - Reverse proxy for all services
- **Docker Registry** (Port 5000) - Private artifact registry for custom images
- **Prometheus** (Port 9090) - Metrics collection and monitoring
- **Grafana** (Port 3000) - Monitoring dashboards and visualization
- **Loki** (Port 3100) - Log aggregation
- **AlertManager** (Port 9093) - Alert routing and management
- **Node Exporter** (Port 9100) - System metrics
- **cAdvisor** (Port 8080) - Container metrics
- **Promtail** (Port 9080) - Log shipping to Loki

### 2. Docker Registry (Artifact Registry)

**Configuration**:
- **URL**: `registry.staging.mdubiel.org` (via nginx proxy)
- **Direct Access**: `192.168.1.14:5000`
- **Authentication**: `registry` / `registry123`
- **Storage**: `/opt/shared/registry/data`

**Usage Example**:
```bash
# Login to registry
docker login registry.staging.mdubiel.org -u registry -p registry123

# Tag an image for the registry
docker tag myapp:latest registry.staging.mdubiel.org/myapp:latest

# Push to registry
docker push registry.staging.mdubiel.org/myapp:latest

# Pull from registry
docker pull registry.staging.mdubiel.org/myapp:latest
```

### 3. Restructured Architecture

**Before**: Role-based deployment with shell commands
```
site.yml → roles/shared-monitoring → shell: docker-compose
```

**After**: Infrastructure-first approach with proper Docker modules
```
site.yml → infra.yml → community.docker modules
       → applications.yml → project deployment
```

**Benefits**:
- ✅ Idiomatic Ansible practices
- ✅ Better error handling and reporting  
- ✅ Explicit dependency management
- ✅ Cleaner separation of infrastructure vs applications
- ✅ More reliable container lifecycle management

### 4. Cleanup Tools

**Ansible Playbook**: `playbooks/cleanup.yml`
```bash
ansible-playbook -i inventory/staging.yml playbooks/cleanup.yml
```

**Shell Script**: `scripts/cleanup.sh`
```bash
./scripts/cleanup.sh
```

**Features**:
- Stops all containers gracefully
- Removes containers, networks, images, and volumes
- Cleans data directories
- Prepares system for fresh deployment
- Provides deployment instructions

### 5. Domain Configuration

**DNS Records Needed**:
```
A registry.staging.mdubiel.org → 192.168.1.14
A grafana.staging.mdubiel.org → 192.168.1.14  
A prometheus.staging.mdubiel.org → 192.168.1.14
A beryl3.staging.mdubiel.org → 192.168.1.14
A monitoring.staging.mdubiel.org → 192.168.1.14
```

### 6. Deployment Commands

**Full Infrastructure Deployment**:
```bash
ansible-playbook -i inventory/staging.yml playbooks/infra.yml
```

**Full Stack Deployment**:
```bash
ansible-playbook -i inventory/staging.yml playbooks/site.yml
```

**Infrastructure Only**:
```bash
ansible-playbook -i inventory/staging.yml playbooks/site.yml --tags infra
```

**Verification**:
```bash
ansible-playbook -i inventory/staging.yml playbooks/infra.yml --tags verify
```

### 7. Service Endpoints

| Service | Internal URL | External URL | Purpose |
|---------|-------------|--------------|---------|
| Nginx Proxy | - | http://staging.mdubiel.org | Reverse proxy |
| Docker Registry | docker-registry:5000 | http://registry.staging.mdubiel.org | Private registry |
| Grafana | grafana:3000 | http://grafana.staging.mdubiel.org | Dashboards |
| Prometheus | prometheus:9090 | http://prometheus.staging.mdubiel.org | Metrics |
| Loki | loki:3100 | - | Logs (internal) |
| AlertManager | alertmanager:9093 | - | Alerts (internal) |

### 8. Docker Networks

- **monitoring**: Core monitoring services (prometheus, grafana, loki, etc.)
- **projects**: Application containers and reverse proxy
- **registry**: Docker registry and monitoring integration

### 9. Data Persistence

All service data is stored under `/opt/shared/` with proper permissions:
```
/opt/shared/
├── nginx/config/          # Nginx configurations
├── registry/data/         # Docker registry storage  
├── registry/auth/         # Registry authentication
├── prometheus/data/       # Prometheus metrics data
├── grafana/data/          # Grafana dashboards and config
├── loki/data/            # Loki log storage
└── alertmanager/data/    # AlertManager state
```

### 10. Security Features

- **Docker Registry**: HTTP Basic Auth with bcrypt password hashing
- **Grafana**: Admin credentials via environment variables
- **Container Isolation**: Dedicated networks for different service types
- **File Permissions**: Proper ownership for service data directories

## Next Steps

1. **SSL/TLS**: Configure Let's Encrypt certificates for HTTPS
2. **Monitoring**: Configure Grafana dashboards and Prometheus rules
3. **Alerting**: Set up AlertManager notification channels
4. **Backup Strategy**: Implement data backup procedures
5. **Log Rotation**: Configure log retention and rotation policies

## Troubleshooting

**Container Issues**:
```bash
# Check container status
ansible staging -m shell -a "docker ps" -u ansible

# Check specific container logs
ansible staging -m shell -a "docker logs <container-name> --tail=20" -u ansible
```

**Registry Issues**:
```bash
# Test registry authentication
ansible staging -m shell -a "curl -u registry:registry123 http://localhost:5000/v2/" -u ansible

# Check registry logs
ansible staging -m shell -a "docker logs docker-registry --tail=10" -u ansible
```

**Clean Deployment**:
```bash
# Full cleanup and redeploy
./scripts/cleanup.sh
ansible-playbook -i inventory/staging.yml playbooks/infra.yml
```