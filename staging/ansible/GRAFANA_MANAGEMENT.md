# Grafana Management Guide

## Overview
The Grafana management system allows independent updates to dashboards and datasources without affecting the main infrastructure deployment.

## File Organization

```
ansible/
├── playbooks/
│   └── grafana-management.yml          # Main management playbook
├── roles/shared-monitoring/
│   ├── files/grafana/dashboards/       # Standard dashboards (JSON)
│   └── templates/                      # Configuration templates
│       ├── grafana-datasources.yml.j2
│       ├── grafana-dashboards.yml.j2
│       └── grafana.ini.j2
└── custom-dashboards/                  # Custom dashboard files
    └── README.md
```

## Available Dashboards

### Standard Infrastructure Dashboards
1. **alert-management.json** - Alert status and history
2. **container-monitoring.json** - Docker container performance
3. **grafana-django-logs-dashboard.json** - Django application logs
4. **grafana-django-metrics-dashboard.json** - Django performance and business metrics
5. **infrastructure-overview.json** - System metrics and health
6. **log-analysis.json** - Log aggregation and analysis
7. **nginx-performance.json** - Web server metrics
8. **service-health.json** - Service availability and response times

## Management Commands

### Deploy All Configuration
```bash
ansible-playbook -i inventory/staging.yml grafana-management.yml
```

### Update Only Dashboards
```bash
ansible-playbook -i inventory/staging.yml grafana-management.yml --tags dashboards
```

### Update Only Datasources
```bash
ansible-playbook -i inventory/staging.yml grafana-management.yml --tags datasources
```

### Deploy Custom Dashboards
```bash
ansible-playbook -i inventory/staging.yml grafana-management.yml --tags custom-dashboards
```

### Restart Grafana
```bash
ansible-playbook -i inventory/staging.yml grafana-management.yml --tags restart
```

### Create Backup
```bash
ansible-playbook -i inventory/staging.yml grafana-management.yml --tags backup
```

### Verify Configuration
```bash
ansible-playbook -i inventory/staging.yml grafana-management.yml --tags verify
```

## Adding New Dashboards

### Standard Dashboards
1. Place JSON file in `roles/shared-monitoring/files/grafana/dashboards/`
2. Update `playbooks/infra.yml` to include the new file in the loop
3. Run: `ansible-playbook -i inventory/staging.yml grafana-management.yml --tags dashboards`

### Custom Dashboards
1. Place JSON file in `custom-dashboards/`
2. Run: `ansible-playbook -i inventory/staging.yml grafana-management.yml --tags custom-dashboards`

## Dashboard Development Workflow

### 1. Create Dashboard in Grafana UI
- Access: http://192.168.1.14:3000 (admin/admin123)
- Create and test your dashboard
- Configure all panels, queries, and settings

### 2. Export Dashboard JSON
- Go to Dashboard → Settings → JSON Model
- Copy the entire JSON content
- Clean up any instance-specific IDs if needed

### 3. Save to File
```bash
# Standard dashboard
cat > roles/shared-monitoring/files/grafana/dashboards/my-new-dashboard.json << 'EOF'
{
  "dashboard": {
    "id": null,
    "uid": "my-dashboard-uid",
    "title": "My New Dashboard",
    ...
  }
}
EOF

# Custom dashboard
cat > custom-dashboards/my-custom-dashboard.json << 'EOF'
{
  "dashboard": {
    ...
  }
}
EOF
```

### 4. Deploy via Ansible
```bash
# Standard dashboard
ansible-playbook -i inventory/staging.yml grafana-management.yml --tags dashboards

# Custom dashboard  
ansible-playbook -i inventory/staging.yml grafana-management.yml --tags custom-dashboards
```

## Configuration Files

### Datasources Configuration
- File: `roles/shared-monitoring/templates/grafana-datasources.yml.j2`
- Contains: Prometheus, Loki datasource definitions
- Auto-configures internal service URLs

### Dashboard Provisioning
- File: `roles/shared-monitoring/templates/grafana-dashboards.yml.j2`  
- Contains: Dashboard discovery and loading configuration
- Monitors `/var/lib/grafana/dashboards/` for JSON files

### Main Configuration
- File: `roles/shared-monitoring/templates/grafana.ini.j2`
- Contains: Grafana server settings, security, auth configuration

## Backup and Recovery

### Automatic Backups
- Created before each configuration update
- Stored in: `/opt/shared/grafana/backups/`
- Keeps last 5 backups automatically
- Includes: provisioning configs and dashboard files

### Manual Backup
```bash
ansible-playbook -i inventory/staging.yml grafana-management.yml --tags backup
```

### Restore from Backup
```bash
# SSH to server
ssh ansible@192.168.1.14

# Stop Grafana
docker stop grafana

# Extract backup
cd /opt/shared/grafana
tar -xzf backups/grafana-config-TIMESTAMP.tar.gz

# Start Grafana
docker start grafana
```

## Troubleshooting

### Dashboard Not Appearing
1. Check Grafana logs: `docker logs grafana`
2. Verify file permissions in `/opt/shared/grafana/dashboards/`
3. Check dashboard JSON syntax
4. Restart Grafana: `--tags restart`

### Datasource Issues
1. Verify Prometheus/Loki are running
2. Check network connectivity from Grafana container
3. Review datasource configuration template
4. Test queries in Grafana UI

### Permission Errors
1. Ensure files are owned by ansible user and docker group
2. Check directory permissions (755)
3. Verify Docker volume mounts

### Configuration Not Loading
1. Restart Grafana container
2. Check provisioning directory structure
3. Verify YAML syntax in configuration files
4. Review Grafana startup logs

## Advanced Usage

### Environment-Specific Dashboards
Create different dashboard sets for different environments by organizing files in subdirectories and using conditional deployment based on inventory groups.

### Automated Dashboard Updates
Set up Git hooks or CI/CD to automatically deploy dashboard changes when JSON files are updated in the repository.

### Dashboard Versioning
Include version information in dashboard JSON metadata to track changes over time.

This management system provides full control over Grafana configuration while maintaining infrastructure as code principles.