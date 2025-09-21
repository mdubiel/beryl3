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

### Unified Environment Management System
**Golden Source of Truth**: All environment variables are managed through a single golden file system located in `workflows/envs/`.

#### Golden Source File
- **Location**: `workflows/envs/env.gold`
- **Purpose**: Single source of truth for all environment variables
- **Format**: Contains environment-specific values using emoji indicators (🏠 DEV, 🧪 QA, 🚀 PROD)
- **Usage**: Update this file first, then run synchronization scripts

#### Environment Files
- **Local**: `webapp/.env` (development)
- **QA**: `workflows/envs/qa.env` 
- **Production**: `workflows/envs/prod.env`
- **Generation**: All files generated from golden source using `uv run python workflows/bin/sync-env-files.py`

#### Management Scripts
All environment management scripts are located in `workflows/bin/`:
- **`sync-env-files.py`**: Synchronize environment files from golden source
- **`compare-envs.py`**: Compare environments and detect configuration drift  
- **`scan-codebase.py`**: Scan codebase for environment variable usage
- **`secrets_manager.py`**: Manage Google Cloud secrets for QA/Production

#### Workflow
1. Update `workflows/envs/env.gold` with new variables and environment-specific values
2. Run `uv run python workflows/bin/sync-env-files.py [local|qa|prod]` to generate environment files
3. For QA/Prod: Run `uv run python workflows/bin/secrets_manager.py` to update cloud secrets
4. Validate with `uv run python workflows/bin/compare-envs.py qa prod`

### .env File Management
**Single Source of Truth**: Each environment should have only ONE .env file configuration source.

#### Development Environment
- **Location**: `webapp/.env` (local development)
- **Management**: Manual configuration for local development
- **Features**: SQLite database, local services, debug mode enabled

#### QA Environment
- **Location**: Generated from golden source of truth using `workflows/bin/sync-env-files.py`
- **Target**: `workflows/envs/qa.env` file in webapp directory
- **Generation**: Automated from `workflows/envs/env.gold` with QA-specific values
- **Features**: PostgreSQL database, Cloud Run deployment, Google Cloud services

#### Production Environment
- **Location**: Generated from golden source of truth using `workflows/bin/sync-env-files.py`
- **Target**: `workflows/envs/prod.env` file in webapp directory  
- **Management**: Managed via `workflows/bin/secrets_manager.py` and related scripts
- **Features**: PostgreSQL database, Google Cloud services, monitoring enabled

#### Key Configuration Requirements
- **Database Selection**: Determined by `DB_ENGINE` environment variable
- **Feature Flags**: Consolidated into `FEATURE_FLAGS` system with DEBUG-based defaults
- **External Service URLs**: Must use externally accessible FQDNs/IP addresses
- **Security**: Secrets stored in Google Cloud Secret Manager for QA/Production

#### Deployment Process
1. **Development**: Local `.env` file with SQLite and local services
2. **QA**: Python scripts generate configuration and deploy to Cloud Run
3. **Production**: Secret Manager integration with Cloud Run services

#### Common Issues to Avoid
- ❌ Multiple .env files (`.env`, `.env.staging`, etc.)
- ❌ Hardcoded database configuration instead of using `DB_ENGINE`
- ❌ Mixed production detection logic with feature flags
- ❌ Secrets committed to version control

#### Verification
After deployment, verify:
- Correct database backend is used based on `DB_ENGINE`
- Feature flags are properly configured for environment
- External service URLs are accessible
- Secrets are properly referenced from Secret Manager

## Deployment and Management Architecture

### Python-Based Workflow System
The project uses Python scripts in `workflows/bin/` for all deployment and management tasks, replacing previous Ansible-based infrastructure.

#### Core Management Scripts
- **`setup_qa_database.py`**: Sets up QA database environment in Google Cloud SQL
- **`manage_database.py`**: Start/stop/restart database instances
- **`secrets_manager.py`**: Manage Google Cloud Secret Manager integration
- **`deploy_webapp.py`**: Deploy webapp to Google Cloud Run
- **`build_images.py`** / **`push_images.py`**: Docker image management
- **`deploy_jobs.py`**: Deploy Cloud Run Jobs for background tasks
- **`status.py`**: Check status of all services and infrastructure

#### Environment-Specific Workflows

**Development**:
- Local `.env` configuration
- SQLite database
- Django development server (`make run-dev-server`)
- Local services (optional)

**QA Environment**:
- Google Cloud SQL PostgreSQL database
- Google Cloud Run for webapp deployment
- Google Cloud Storage for media files
- Google Cloud Secret Manager for configuration
- Automated via `make qa-*` targets

**Production Environment**:
- Same infrastructure as QA but with production-grade configuration
- Enhanced monitoring and logging
- Production-level resource allocation
- Managed via workflow scripts and Cloud Run Jobs

#### Key Benefits
- **No Ansible Dependency**: Pure Python scripts, easier to maintain and debug
- **Integrated Secrets Management**: Direct integration with Google Cloud Secret Manager
- **Consistent API**: All scripts follow similar patterns and error handling
- **Cloud-Native**: Designed specifically for Google Cloud Platform
- **Automated Tasks**: Cloud Run Jobs handle recurring maintenance tasks