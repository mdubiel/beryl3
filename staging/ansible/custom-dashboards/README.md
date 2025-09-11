# Custom Grafana Dashboards

This directory contains custom Grafana dashboard JSON files that are deployed separately from the default infrastructure dashboards.

## Usage

1. Place your custom dashboard JSON files in this directory
2. Run the Grafana management playbook:
   ```bash
   ansible-playbook -i inventory/staging.yml grafana-management.yml --tags custom-dashboards
   ```

## Dashboard Naming

- Custom dashboard files will be prefixed with `custom-` when deployed
- Example: `my-dashboard.json` becomes `custom-my-dashboard.json` in Grafana

## Dashboard Export/Import

### Exporting from Grafana UI
1. Go to Dashboard → Settings → JSON Model
2. Copy the JSON content
3. Save as `dashboard-name.json` in this directory

### Importing via Ansible
1. Place JSON file in this directory
2. Run: `ansible-playbook -i inventory/staging.yml grafana-management.yml --tags custom-dashboards`
3. Grafana will automatically reload and provision the new dashboard

## Best Practices

- Use descriptive filenames without spaces
- Include version information in dashboard JSON if needed
- Test dashboards in Grafana UI before committing to automation
- Backup existing dashboards before deploying new versions