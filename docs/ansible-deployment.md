# Docker-Based Staging Environment Deployment

This Ansible playbook deploys a complete containerized staging environment with shared monitoring services and project-specific Docker stacks.

**Note**: All Ansible commands should be run from the `staging/ansible/` directory relative to the project root.

## Quick Start

1. **Configure inventory**:
   ```bash
   cp inventory/staging.yml.example inventory/staging.yml
   # Edit with your server details and project configuration
   ```

2. **Set up vault for secrets**:
   ```bash
   ansible-vault create group_vars/vault.yml
   ```
   Add these secrets:
   ```yaml
   vault_grafana_admin_password: "secure_password"
   vault_django_secret_key: "your_django_secret_key"
   vault_db_password: "secure_db_password"
   ```

3. **Deploy everything**:
   ```bash
   ansible-playbook -i inventory/staging.yml playbooks/site.yml --ask-vault-pass
   ```

## Docker-Based Architecture

### Shared Monitoring Stack (`/opt/shared/`)
- Single Docker Compose stack for all monitoring services
- Grafana, Prometheus, Loki, AlertManager, Node Exporter, cAdvisor
- Main Nginx reverse proxy for monitoring endpoints

### Project-Specific Stacks (`/opt/projects/{project}/`)
- Individual Docker Compose stack per project
- PostgreSQL, Redis, Django app, Nginx, Worker containers
- Monitoring exporters (postgres-exporter, redis-exporter, nginx-exporter)

## Deployment Commands

### Full deployment:
```bash
ansible-playbook -i inventory/staging.yml playbooks/site.yml --ask-vault-pass
```

### Shared services only:
```bash
ansible-playbook -i inventory/staging.yml playbooks/site.yml --tags "shared,monitoring" --ask-vault-pass
```

### Specific project:
```bash
ansible-playbook -i inventory/staging.yml playbooks/site.yml --tags "projects" --limit beryl3 --ask-vault-pass
```

### Restart monitoring stack:
```bash
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/shared && docker-compose restart" --ask-vault-pass
```

### Restart project stack:
```bash
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/beryl3 && docker-compose restart" --ask-vault-pass
```

## Docker Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HOST SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│  monitoring (bridge network)                                   │
│  ├─ grafana:3000                                              │
│  ├─ prometheus:9090                                           │
│  ├─ loki:3100                                                │
│  ├─ node-exporter:9100                                       │
│  └─ cadvisor:8080                                            │
├─────────────────────────────────────────────────────────────────┤
│  projects (bridge network)                                    │
│  ├─ nginx-monitoring:80,443 (main reverse proxy)             │
│  └─ project containers for external routing                   │
├─────────────────────────────────────────────────────────────────┤
│  beryl3 (bridge network)                                      │
│  ├─ beryl3-postgres:5432                                     │
│  ├─ beryl3-redis:6379                                        │
│  ├─ beryl3-web:8000                                          │
│  ├─ beryl3-nginx:80,443                                      │
│  ├─ beryl3-postgres-exporter:9187                            │
│  └─ beryl3-redis-exporter:9121                               │
└─────────────────────────────────────────────────────────────────┘
```

## Service URLs After Deployment

### Monitoring Services
- **Grafana**: https://monitoring.staging.example.com:3000
- **Prometheus**: https://monitoring.staging.example.com:9090

### Project Services
- **Beryl3 App**: https://beryl3.staging.example.com
- **Direct container access**: http://server-ip:8000 (bypasses nginx)

## Container Management

### View running containers:
```bash
ansible staging -i inventory/staging.yml -m shell -a "docker ps" --ask-vault-pass
```

### View container logs:
```bash
ansible staging -i inventory/staging.yml -m shell -a "docker logs beryl3-web" --ask-vault-pass
```

### Execute commands in containers:
```bash
# Django management commands
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/beryl3 && docker-compose exec web python manage.py shell" --ask-vault-pass

# Database access
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/beryl3 && docker-compose exec postgres psql -U beryl3_user beryl3_staging" --ask-vault-pass
```

### Update application code:
```bash
# Pull latest code and rebuild
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/beryl3 && git pull && docker-compose build web && docker-compose up -d" --ask-vault-pass
```

## Docker Volumes and Data Persistence

### Shared monitoring data:
- `prometheus_data`: Prometheus metrics storage
- `grafana_data`: Grafana dashboards and settings
- `loki_data`: Log storage

### Project-specific data:
- `{project}_postgres_data`: Database storage
- `{project}_redis_data`: Redis cache storage  
- `{project}_static_files`: Django static files
- `{project}_media_files`: User uploaded files

### Backup volumes:
```bash
# Backup project database
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/beryl3 && docker-compose exec postgres pg_dump -U beryl3_user beryl3_staging > /opt/backups/beryl3-$(date +%Y%m%d).sql" --ask-vault-pass

# Backup Grafana settings
ansible staging -i inventory/staging.yml -m shell -a "docker run --rm -v shared_grafana_data:/data -v /opt/backups:/backup alpine tar czf /backup/grafana-$(date +%Y%m%d).tar.gz -C /data ." --ask-vault-pass
```

## Troubleshooting

### Container won't start:
```bash
# Check container logs
ansible staging -i inventory/staging.yml -m shell -a "docker logs container-name" --ask-vault-pass

# Check Docker Compose status
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/beryl3 && docker-compose ps" --ask-vault-pass
```

### Database connection issues:
```bash
# Test database connectivity
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/beryl3 && docker-compose exec postgres pg_isready -U beryl3_user" --ask-vault-pass

# Check environment variables
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/beryl3 && docker-compose exec web env | grep DATABASE" --ask-vault-pass
```

### SSL certificate renewal:
```bash
# Renew certificates
ansible staging -i inventory/staging.yml -m shell -a "certbot renew --dry-run" --ask-vault-pass

# Restart nginx containers after renewal
ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/beryl3 && docker-compose restart nginx" --ask-vault-pass
```

### Resource monitoring:
```bash
# Check container resource usage
ansible staging -i inventory/staging.yml -m shell -a "docker stats --no-stream" --ask-vault-pass

# Check disk usage
ansible staging -i inventory/staging.yml -m shell -a "docker system df" --ask-vault-pass
```

## Performance Optimization

### Container resource limits (add to docker-compose.yml):
```yaml
services:
  web:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

### Log rotation for containers:
```yaml
services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Adding New Projects

1. **Add project to inventory**:
   ```yaml
   projects:
     - name: newproject
       domain: "newproject.staging.example.com"
       port: 8001
       db_port: 5433
       redis_port: 6380
   ```

2. **Run deployment**:
   ```bash
   ansible-playbook -i inventory/staging.yml playbooks/site.yml --tags "projects" --ask-vault-pass
   ```

3. **Verify deployment**:
   ```bash
   ansible staging -i inventory/staging.yml -m shell -a "cd /opt/projects/newproject && docker-compose ps" --ask-vault-pass
   ```

## Security Features

- **Container isolation**: Each project runs in isolated Docker networks
- **Non-root containers**: Applications run as non-root users inside containers
- **SSL encryption**: All external traffic encrypted with Let's Encrypt certificates
- **Firewall**: UFW configured to only allow necessary ports
- **Secrets management**: Environment variables stored in encrypted Ansible vault
- **Log aggregation**: All container logs centralized in Loki for security monitoring