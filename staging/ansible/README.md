# Beryl3 Staging Infrastructure

**📚 Documentation has been moved!**

All infrastructure documentation has been centralized in the project root documentation directory.

## 📍 Find Documentation Here

**Main Documentation Hub**: [`../../docs/index.md`](../../docs/index.md)

### Infrastructure Documentation
- **[Ansible Deployment Guide](../../docs/ansible-deployment.md)** - Complete deployment instructions
- **[Infrastructure Services](../../docs/infrastructure-services.md)** - Service catalog and management  
- **[Infrastructure Architecture](../../docs/infrastructure-architecture.md)** - System design overview
- **[Infrastructure Deployment](../../docs/infrastructure-deployment.md)** - Deployment procedures

## 🚀 Quick Commands

```bash
# Deploy full infrastructure (run from this directory)
ansible-playbook -i inventory/staging.yml playbooks/infra.yml

# Deploy full stack
ansible-playbook -i inventory/staging.yml playbooks/site.yml

# Verify deployment
ansible-playbook -i inventory/staging.yml playbooks/infra.yml --tags verify
```

**Complete instructions**: [`../../docs/ansible-deployment.md`](../../docs/ansible-deployment.md)

## 🌐 Service Access

- **Grafana**: http://grafana.staging.mdubiel.org (admin/admin123)
- **Prometheus**: http://prometheus.staging.mdubiel.org
- **Registry**: http://registry.staging.mdubiel.org (registry/registry123)

**Full service details**: [`../../docs/infrastructure-services.md`](../../docs/infrastructure-services.md)

---

*All documentation is now centralized in [`../../docs/`](../../docs/) for better organization and maintenance.*