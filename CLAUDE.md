# Claude Code Workflow Documentation

## TODO Processing Workflow

When user says "process TODO", execute the following workflow:

### Process:
1. **Read TODO.md file** to get the list of tasks
2. **Take tasks one by one** in order
3. **Complete each assignment** treating each item as a complete prompt/request
4. **Create detailed reports** in `docs/reports/taskxxx.md` documenting the work performed
5. **Mark items as fixed** in TODO.md (change format or add status)
6. **Proceed to next task** until all are completed

### Report Format:
- File: `docs/reports/task001.md`, `task002.md`, etc.
- Include: task description, analysis, changes made, verification steps, outcome
- Document all code changes, file modifications, deployment steps

### Task Completion:
- Mark completed tasks in TODO.md
- Create a git commit for each completed task
- Ensure all changes are tested and working
- Create comprehensive documentation for each task

### Commit Strategy:
- One commit per completed TODO task
- Commit message format: "task: [Task number] - [Brief description]"
- Include all related changes in single commit

This workflow ensures systematic completion of all TODO items with proper documentation, version control, and verification.

## Environment Configuration Standards

### .env File Management
**Single Source of Truth**: Each environment should have only ONE .env file configuration source.

#### Staging Environment
- **Location**: `/staging/ansible/playbooks/templates/beryl3.env.j2` (Ansible template)
- **Deployment**: Generated during deployment via `ansible/playbooks/deploy-app.yml`
- **Target**: `/opt/beryl3/.env` on staging server
- **DO NOT**: Use static `.env` or `.env.staging` files in staging directory

#### Key Configuration Requirements
- **External Service URLs**: Must use externally accessible FQDNs/IP addresses, NOT container names
- **HTTPS**: All external URLs must use HTTPS in staging/production
- **Domain Configuration**: Use proper domain names from inventory variables

#### External Services Template Variables
External service URLs are generated using Ansible variables:
```yaml
EXTERNAL_DB_URL=https://{{ ansible_host }}:8084
EXTERNAL_GRAFANA_URL=https://{{ ansible_host }}:3000
EXTERNAL_LOKI_URL=https://{{ ansible_host }}:3100
EXTERNAL_MONITORING_URL=https://{{ ansible_host }}:9090
EXTERNAL_REGISTRY_URL=https://{{ ansible_host }}:8082
EXTERNAL_RESEND_URL=https://resend.com/dashboard
SITE_DOMAIN={{ beryl3_app.domain | default('beryl3.staging.mdubiel.org') }}
```

#### Deployment Process
1. **deploy-app.yml**: Generates `.env` from template with proper variables
2. **docker-compose.yaml**: Uses `${VARIABLE}` syntax to read from `.env`
3. **Container**: Receives all environment variables from docker-compose

#### Common Issues to Avoid
- ❌ Multiple .env files (`.env`, `.env.staging`, etc.)
- ❌ Container names in external URLs (`http://grafana:3000`)  
- ❌ HTTP URLs in staging/production environments
- ❌ Hardcoded environment variables in docker-compose
- ❌ Static .env files copied by Ansible playbooks

#### Verification
After deployment, verify external services panel shows:
- All services with HTTPS URLs
- Externally accessible IP addresses/domains
- Working links to each service

## Nginx Proxy Configuration Standards

### Staging Environment Proxy
**Template Location**: `/staging/ansible/playbooks/templates/staging-proxy.conf.j2`
**Deployment**: Generated during deployment via `deploy-app.yml`
**Target**: `/opt/shared/nginx/config/default.conf` on staging server

#### Configured Subdomains (HTTPS with SSL)
- `beryl3.staging.mdubiel.org` → beryl3-webapp:8000
- `grafana.staging.mdubiel.org` → grafana:3000  
- `prometheus.staging.mdubiel.org` → prometheus:9090
- `loki.staging.mdubiel.org` → loki:3100
- `adminer.staging.mdubiel.org` → adminer:8080
- `registry.staging.mdubiel.org` → docker-registry:5000
- `monitoring.staging.mdubiel.org` → redirects to Grafana

#### Features
- HTTP to HTTPS redirect for all subdomains
- Let's Encrypt challenge support (/.well-known/acme-challenge/)
- Modern SSL/TLS configuration (TLSv1.2, TLSv1.3)
- Security headers (HSTS, X-Frame-Options, etc.)
- Service-specific optimizations (Docker registry large uploads, etc.)

#### Persistence
**IMPORTANT**: Never manually edit nginx configuration files on the server. All changes must be made in the Ansible template `staging-proxy.conf.j2` to ensure persistence across deployments.