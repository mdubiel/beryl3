# Staging Environment Documentation

## Overview

The staging environment is designed to mirror production while optimizing resource usage through shared monitoring infrastructure and project-specific application services.

### Server Specifications
- **Host OS**: Arch Linux (rolling release)
- **IP Address**: 192.168.1.14  
- **Domain**: staging.mdubiel.org
- **Package Manager**: pacman
- **Python Version**: 3.13.7 (required for Ansible)
- **Ansible User**: ansible (with passwordless sudo)

## Prerequisites & Initial Setup

### Arch Linux Host Preparation

The staging server runs Arch Linux, which requires specific setup steps:

#### 1. Python Installation (Required for Ansible)
```bash
# Connect to server as root or existing user
ssh root@192.168.1.14

# Install Python (required for Ansible modules)
sudo pacman -Sy python --noconfirm

# Verify installation
python3 --version  # Should show Python 3.13.7+
```

#### 2. Ansible User Creation
```bash
# Create ansible user with home directory
sudo useradd -m -s /bin/bash ansible

# Add to wheel group (Arch Linux equivalent of sudo)
sudo usermod -aG wheel ansible

# Configure passwordless sudo
echo 'ansible ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/ansible
sudo chmod 440 /etc/sudoers.d/ansible

# Create SSH directory
sudo mkdir -p /home/ansible/.ssh
sudo chmod 700 /home/ansible/.ssh
sudo chown ansible:ansible /home/ansible/.ssh
```

#### 3. SSH Key Setup (Local Machine)
```bash
# Generate SSH key without passphrase (for automation)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/ansible_staging -N "" -C "ansible@staging"

# Manually copy public key to server (paste the output):
cat ~/.ssh/ansible_staging.pub

# On server, add to authorized_keys:
echo "PASTE_PUBLIC_KEY_HERE" | sudo tee /home/ansible/.ssh/authorized_keys
sudo chmod 600 /home/ansible/.ssh/authorized_keys
sudo chown ansible:ansible /home/ansible/.ssh/authorized_keys
```

#### 4. Connectivity Verification
```bash
# Test SSH connection
ssh -i ~/.ssh/ansible_staging ansible@192.168.1.14 "echo 'Connection successful'"

# Test sudo privileges
ssh -i ~/.ssh/ansible_staging ansible@192.168.1.14 "sudo whoami"  # Should return 'root'

# Test Ansible connectivity
cd /path/to/ansible/directory
ansible staging -m ping  # Should return SUCCESS
ansible staging -m shell -a "whoami"  # Should return 'root'
```

### DNS Configuration

The following DNS records must be configured in mdubiel.org zone:

```
A beryl3.staging.mdubiel.org → 192.168.1.14
A monitoring.staging.mdubiel.org → 192.168.1.14  
A grafana.staging.mdubiel.org → 192.168.1.14
A prometheus.staging.mdubiel.org → 192.168.1.14
```

## Architecture Principles - Docker-Based Deployment

### Shared Services (Cross-Project) - Single Docker Stack
- **Grafana**: Single containerized instance for all project monitoring dashboards
- **Prometheus**: Centralized metrics collection from all project containers
- **Loki**: Centralized log aggregation with container log drivers
- **AlertManager**: Unified alerting across all projects
- **Node Exporter**: System metrics collection on host
- **cAdvisor**: Container metrics collection for Docker stats
- **Nginx**: Main reverse proxy routing to project-specific containers

### Project-Specific Services (Per Project) - Individual Docker Stacks
- **PostgreSQL**: Dedicated database container per project for data isolation
- **Redis**: Project-specific cache container
- **Django Web App**: Containerized application with uv package management
- **Nginx**: Project-specific reverse proxy container with SSL termination
- **Worker/Scheduler**: Background task containers (optional)
- **Monitoring Exporters**: PostgreSQL, Redis, and Nginx exporters per project

## Infrastructure Layout - Docker Containerized

```
staging-server/
├── /opt/shared/ (monitoring stack)
│   ├── docker-compose.yml
│   ├── prometheus/
│   │   ├── config/prometheus.yml
│   │   └── data/
│   ├── grafana/
│   │   ├── config/grafana.ini
│   │   └── data/
│   ├── loki/
│   │   ├── config/loki.yml
│   │   └── data/
│   └── nginx/config/
└── /opt/projects/
    ├── beryl3/
    │   ├── app/ (git repository)
    │   ├── docker-compose.yml
    │   ├── config/
    │   │   ├── .env
    │   │   └── nginx.conf
    │   ├── data/
    │   │   ├── postgresql/
    │   │   └── redis/
    │   ├── ssl/ (Let's Encrypt webroot)
    │   └── logs/
    └── project2/
        ├── app/
        ├── docker-compose.yml
        ├── config/
        ├── data/
        ├── ssl/
        └── logs/
```

## Service Configuration

### Shared Services Configuration

#### Prometheus
- **Port**: 9090
- **Data Retention**: 30 days
- **Scrape Targets**: All project databases, applications, and system metrics
- **Config Path**: `/opt/shared/prometheus/prometheus.yml`

#### Grafana
- **Port**: 3000
- **Admin User**: `admin`
- **Data Sources**: Prometheus, Loki
- **Dashboards**: Per-project folders for organization
- **Persistent Storage**: `/opt/shared/grafana/data`

#### Loki
- **Port**: 3100
- **Log Retention**: 14 days
- **Storage**: Local filesystem with compression
- **Config Path**: `/opt/shared/loki/loki.yml`

### Project-Specific Configuration

#### PostgreSQL (per project)
- **Port Range**: 5432+ (5432 for beryl3, 5433 for project2, etc.)
- **Data Path**: `/opt/projects/{project_name}/postgresql/data`
- **Backup Strategy**: Daily dumps to `/opt/backups/{project_name}`
- **Connection Limits**: 100 per project database

#### Nginx (per project)
- **Port Range**: 80/443 with host-based routing
- **SSL**: Let's Encrypt certificates per project domain
- **Config Path**: `/opt/projects/{project_name}/nginx/`
- **Upstream**: Project-specific application servers

#### Application Services
- **Django**: uv-managed Python environment
- **Port Range**: 8000+ (8000 for beryl3, 8001 for project2, etc.)
- **Environment**: Project-specific `.env` files
- **Static Files**: Served via Nginx
- **Media Files**: Local storage or cloud integration

## Resource Allocation

### Server Requirements
- **CPU**: 4+ cores (shared monitoring ~1 core, projects ~1 core each)
- **RAM**: 8GB+ (Prometheus 1GB, Grafana 512MB, PostgreSQL 1GB per project)
- **Storage**: 100GB+ SSD (logs, metrics, databases)
- **Network**: 1Gbps for log/metric ingestion

### Port Allocation Strategy
```
Shared Services:
- Grafana: 3000
- Prometheus: 9090
- Loki: 3100
- AlertManager: 9093

Project Services (beryl3):
- PostgreSQL: 5432
- Django: 8000
- Redis: 6379

Project Services (project2):
- PostgreSQL: 5433  
- Django: 8001
- Redis: 6380
```

## Monitoring Strategy

### Metrics Collection
- **Application Metrics**: Django custom metrics via prometheus_client
- **Database Metrics**: postgres_exporter per database
- **System Metrics**: node_exporter on staging server
- **Container Metrics**: cadvisor if using Docker

### Log Aggregation
- **Application Logs**: JSON structured logs to Loki via promtail
- **Nginx Logs**: Access and error logs aggregated
- **System Logs**: journald integration
- **Database Logs**: PostgreSQL query and error logs

### Alerting Rules
- **Database**: Connection count, query performance, disk usage
- **Application**: Error rates, response times, queue depths
- **System**: CPU, memory, disk usage, service availability
- **SSL**: Certificate expiration alerts

## Deployment Strategy - Docker with Ansible

### Ansible Playbook Structure
```
staging/ansible/
├── inventory/
│   └── staging.yml (server and project configuration)
├── group_vars/
│   ├── all.yml (global settings)
│   ├── staging.yml (environment-specific settings)
│   └── vault.yml (encrypted secrets)
├── roles/
│   ├── common/ (system setup, Docker installation)
│   ├── security/ (firewall, SSH hardening)
│   └── shared-monitoring/ (Docker-based monitoring stack)
├── playbooks/
│   ├── site.yml (main deployment playbook)
│   └── project-deploy.yml (per-project Docker stack)
└── templates/
    ├── docker-compose-monitoring.yml.j2
    ├── docker-compose-project.yml.j2
    ├── Dockerfile.j2
    ├── nginx-project.conf.j2
    └── project.env.j2
```

### Deployment Phases - Docker Containerized
1. **Infrastructure Setup**: Docker installation, user accounts, firewall, networks
2. **Shared Monitoring Stack**: Single Docker Compose stack for monitoring
3. **Project Docker Stacks**: Individual Docker Compose per project
4. **SSL Certificate Generation**: Let's Encrypt certificates for domains
5. **Service Integration**: Container networking and monitoring configuration

### Docker Networks
- **monitoring**: Shared network for monitoring services to scrape metrics
- **projects**: External network for main reverse proxy routing
- **{project_name}**: Internal network per project for service isolation

## Security Considerations

### Network Security
- **Firewall**: UFW with specific port access rules
- **SSL/TLS**: Let's Encrypt for all public endpoints
- **Internal Communication**: Service-to-service authentication
- **Database Access**: Restricted to application users only

### Authentication
- **Grafana**: LDAP/OAuth integration planned
- **Prometheus**: Basic auth for scraping endpoints
- **Applications**: Standard authentication per project
- **SSH**: Key-based authentication only

## Backup Strategy

### Database Backups
- **Frequency**: Daily automated dumps
- **Retention**: 30 days local, 90 days remote
- **Testing**: Weekly restore verification
- **Location**: `/opt/backups/` with cloud sync

### Configuration Backups
- **Ansible Configs**: Version controlled in Git
- **Service Configs**: Backed up with databases
- **SSL Certificates**: Automatic renewal with backup

## Monitoring Dashboards

### Shared Dashboards
- **System Overview**: CPU, memory, disk, network across all services
- **Monitoring Health**: Prometheus, Grafana, Loki status
- **Alert Summary**: Current alerts across all projects

### Project-Specific Dashboards
- **Application Performance**: Response times, error rates, throughput
- **Database Performance**: Connections, query performance, growth
- **Infrastructure**: Project-specific resource usage

## Maintenance Procedures

### Regular Tasks
- **Security Updates**: Monthly OS and package updates
- **Certificate Renewal**: Automated via cron jobs
- **Log Rotation**: Automated cleanup of old logs
- **Backup Verification**: Weekly restore tests

### Scaling Considerations
- **Horizontal Scaling**: Additional project onboarding process
- **Resource Monitoring**: Alerts for resource exhaustion
- **Capacity Planning**: Monthly resource usage reviews

## Environment Variables

### Shared Service Variables
```bash
# Prometheus
PROMETHEUS_RETENTION_TIME=30d
PROMETHEUS_STORAGE_PATH=/opt/shared/prometheus/data

# Grafana
GRAFANA_ADMIN_PASSWORD=<secure_password>
GRAFANA_DATABASE_PATH=/opt/shared/grafana/data

# Loki
LOKI_RETENTION_PERIOD=14d
LOKI_STORAGE_PATH=/opt/shared/loki/data
```

### Project-Specific Variables (beryl3)
```bash
# Database
POSTGRES_DB=beryl3_staging
POSTGRES_USER=beryl3_user
POSTGRES_PASSWORD=<secure_password>
POSTGRES_PORT=5432

# Application
DJANGO_SECRET_KEY=<secure_key>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=staging-beryl3.example.com
DATABASE_URL=postgresql://beryl3_user:password@localhost:5432/beryl3_staging

# Email
EMAIL_HOST=localhost
EMAIL_PORT=1025
```

## DNS and Domain Configuration

### Domain Strategy
- **Shared Services**: `monitoring.staging.example.com` (Grafana, Prometheus)
- **Project Services**: `{project}.staging.example.com` (beryl3.staging.example.com)
- **Internal Services**: Internal IP addressing for database connections

### SSL Certificate Management
- **Let's Encrypt**: Automated certificate generation and renewal
- **Wildcard Certificates**: `*.staging.example.com` for cost efficiency
- **Certificate Storage**: `/etc/letsencrypt/` with backup integration

## Troubleshooting Guide

### Ansible Connectivity Issues

#### Python Missing Error
```bash
# Error: "The module interpreter '/usr/bin/python3' was not found"
# Solution: Install Python on Arch Linux host
ssh -i ~/.ssh/ansible_staging ansible@192.168.1.14 "sudo pacman -Sy python --noconfirm"
```

#### SSH Authentication Failures
```bash
# Error: "Permission denied (publickey,password)"
# Solution 1: Verify SSH key is properly added
ssh -i ~/.ssh/ansible_staging ansible@192.168.1.14 "echo 'test'"

# Solution 2: Regenerate key without passphrase
ssh-keygen -t rsa -b 4096 -f ~/.ssh/ansible_staging -N "" -C "ansible@staging"

# Solution 3: Manually copy key to server
cat ~/.ssh/ansible_staging.pub
# Then on server: echo "PASTE_KEY_HERE" | sudo tee /home/ansible/.ssh/authorized_keys
```

#### Privilege Escalation Issues
```bash
# Error: Sudo password required
# Solution: Verify passwordless sudo is configured
ssh -i ~/.ssh/ansible_staging ansible@192.168.1.14 "sudo whoami"

# If fails, add to sudoers:
echo 'ansible ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/ansible
sudo chmod 440 /etc/sudoers.d/ansible
```

#### Arch Linux Specific Issues
```bash
# Package manager differences (pacman vs apt/yum)
# Playbooks may need arch-specific package names
# Group differences: wheel (Arch) vs sudo (Ubuntu/Debian)

# Verify groups:
ssh -i ~/.ssh/ansible_staging ansible@192.168.1.14 "groups ansible"
# Should include 'wheel' group
```

### Deployment Issues

#### SSL Certificate Generation
```bash
# Let's Encrypt may fail on first run
# Check domain DNS resolution first:
dig +short beryl3.staging.mdubiel.org  # Should return 192.168.1.14

# Manual certificate generation:
ansible staging -m shell -a "sudo certbot certonly --webroot --webroot-path=/var/www/html --email admin@staging.mdubiel.org --agree-tos --no-eff-email -d beryl3.staging.mdubiel.org"
```

### Common Issues
- **Service Discovery**: Prometheus target configuration
- **Log Ingestion**: Promtail configuration for new projects
- **Resource Constraints**: Memory/CPU allocation adjustments
- **Database Connections**: Connection pool tuning
- **Package Manager**: Arch Linux uses `pacman` instead of `apt`/`yum`

### Health Checks
- **Service Status**: `systemctl status` for all services
- **Port Availability**: `ss -tlnp` for port conflicts (modern replacement for netstat)
- **Log Analysis**: Centralized logging for issue diagnosis
- **Metric Availability**: Prometheus target health monitoring
- **Ansible Connectivity**: `ansible staging -m ping`
- **Python Availability**: `ansible staging -m shell -a "python3 --version"`

## Future Enhancements

### Planned Improvements
- **Container Orchestration**: Docker/Podman integration
- **Auto Scaling**: Resource-based scaling triggers
- **Multi-Server Setup**: Database replication and load balancing
- **Advanced Monitoring**: Custom dashboards and SLO tracking
- **Backup Automation**: Cloud-based backup integration