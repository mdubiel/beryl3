# Beryl3 Project Documentation

Welcome to the comprehensive documentation hub for the Beryl3 collection management system. All project documentation is centralized here for easy access and maintenance.

## 📚 Documentation Overview

This directory contains all project documentation organized by category and purpose. All documentation should be created and maintained within this `docs/` directory.

---

## 🚀 Getting Started

### Project Overview & Setup
- **[project-overview.md](project-overview.md)** - Main project introduction and overview
- **[development-guide.md](development-guide.md)** - Comprehensive development setup, tools, and guidelines (CLAUDE.md)
- **[rules.md](rules.md)** - Development standards, Django best practices, and coding guidelines

### User Experience & Design
- **[user_journeys.md](user_journeys.md)** - User flows, personas, and experience mapping
- **[context.md](context.md)** - Project context and background information

---

## 🏗️ Infrastructure & Deployment

### Infrastructure Management
- **[infrastructure-architecture.md](infrastructure-architecture.md)** - Complete system architecture and service design
- **[infrastructure-services.md](infrastructure-services.md)** - Service catalog with URLs, ports, credentials, and management commands
- **[infrastructure-deployment.md](infrastructure-deployment.md)** - Infrastructure deployment procedures and troubleshooting

### Deployment Guides
- **[docker-deployment.md](docker-deployment.md)** - Docker containerization, build, and registry deployment
- **[ansible-deployment.md](ansible-deployment.md)** - Ansible-based deployment instructions and configuration
- **[deployment.md](deployment.md)** - General deployment procedures and workflows

### Environment-Specific
- **[staging-overview.md](staging-overview.md)** - Staging environment architecture and configuration
- **[beryl3-staging-environment.md](beryl3-staging-environment.md)** - Beryl3-specific staging deployment details

---

## 🔧 Development & Components

### Application Components
*(No specialized components currently documented)*

### Monitoring & Observability
- **[grafana-loki-setup.md](grafana-loki-setup.md)** - Grafana and Loki monitoring setup and configuration

---

## 📖 Quick Navigation Guide

### For New Team Members
1. **Start Here**: [project-overview.md](project-overview.md) - Understand what Beryl3 is
2. **Development Setup**: [development-guide.md](development-guide.md) - Get your environment running
3. **Coding Standards**: [rules.md](rules.md) - Learn our development practices
4. **User Context**: [user_journeys.md](user_journeys.md) - Understand our users

### For Developers
1. **Development Workflow**: [development-guide.md](development-guide.md)
2. **Local Development**: [staging-overview.md](staging-overview.md)
3. **Best Practices**: [rules.md](rules.md)
4. **Monitoring Setup**: [grafana-loki-setup.md](grafana-loki-setup.md)

### For DevOps/Infrastructure
1. **System Overview**: [infrastructure-architecture.md](infrastructure-architecture.md)
2. **Service Management**: [infrastructure-services.md](infrastructure-services.md)
3. **Deployment**: [ansible-deployment.md](ansible-deployment.md)
4. **Monitoring**: [grafana-loki-setup.md](grafana-loki-setup.md)

### For System Administrators
1. **Infrastructure**: [infrastructure-deployment.md](infrastructure-deployment.md)
2. **Services**: [infrastructure-services.md](infrastructure-services.md)
3. **Environments**: [staging-overview.md](staging-overview.md)
4. **Troubleshooting**: [ansible-deployment.md](ansible-deployment.md)

---

## 🎯 Infrastructure Quick Reference

### Key Services
- **Grafana**: `http://grafana.staging.mdubiel.org` (admin/admin123)
- **Prometheus**: `http://prometheus.staging.mdubiel.org`
- **Docker Registry**: `http://registry.staging.mdubiel.org` (registry/registry123)
- **Beryl3 App**: `http://beryl3.staging.mdubiel.org`

### Server Details
- **Host**: 192.168.1.14 (Arch Linux)
- **Services**: 11 containerized services
- **Networks**: monitoring, projects, registry
- **Monitoring**: Self-aware with comprehensive dashboards

*Full details in [infrastructure-services.md](infrastructure-services.md)*

---

## 📋 Documentation Standards

### Location
- **All documentation** must be placed in the `/docs` directory
- **No documentation files** should exist outside of `/docs`
- **Organize by category** using descriptive filenames

### Naming Conventions
- Use **kebab-case** for filenames (e.g., `infrastructure-services.md`)
- Use **descriptive names** that clearly indicate content
- **Prefix related docs** with common terms (e.g., `infrastructure-*`)

### Content Guidelines
- **Start with clear headings** and purpose statements
- **Include navigation aids** and cross-references
- **Update this index** when adding new documentation
- **Follow markdown standards** as specified in [rules.md](rules.md)

### Maintenance
- **Keep documentation current** with code changes
- **Review and update** during feature development
- **Check cross-references** when moving or renaming files

---

## 🔄 Document Maintenance

This index should be updated whenever documentation is added, removed, or significantly restructured. All project contributors are responsible for maintaining accurate and current documentation.

**Last Updated**: 2025-01-10  
**Total Documents**: 15  
**Categories**: Getting Started (5), Infrastructure (6), Development (1), Quick Reference Sections (3)

---

*For development workflow and project setup, start with [development-guide.md](development-guide.md)*