# GitHub Actions Deployment to Django Europe Production

This document describes the GitHub Actions workflow for deploying the Beryl3 application to the Django Europe production environment.

## 📋 Overview

The workflow deploys a specific release tag to the production server at `148.251.140.153` using SSH. It consists of **8 separate jobs** that run sequentially to ensure safe deployment.

**Workflow File**: `.github/workflows/deploy-dje-production.yml`

## 🔑 Required GitHub Secrets

Before using the workflow, you must configure these secrets in your GitHub repository:

### 1. DJE_SSH_PRIVATE_KEY

**Description**: SSH private key for authentication to Django Europe server

**How to generate**:
```bash
# Generate a new SSH key pair (if you don't have one)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/beryl3-deploy

# Copy the private key (this goes in GitHub secret)
cat ~/.ssh/beryl3-deploy

# Copy the public key to the server
ssh-copy-id -i ~/.ssh/beryl3-deploy.pub mdubiel@148.251.140.153
```

**To add to GitHub**:
1. Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
2. Name: `DJE_SSH_PRIVATE_KEY`
3. Value: Paste the entire private key (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)

### 2. DJE_SSH_KNOWN_HOSTS

**Description**: SSH known hosts entry for server verification

**How to generate**:
```bash
# Get the known hosts entry
ssh-keyscan -H 148.251.140.153
```

**To add to GitHub**:
1. Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
2. Name: `DJE_SSH_KNOWN_HOSTS`
3. Value: Paste the output from ssh-keyscan (one or more lines)

### 3. DJE_PROD_ENV_FILE

**Description**: Complete `.env` file content for production environment

**How to create**:
```bash
# Get the current .env from production server
ssh mdubiel@148.251.140.153 "cat ~/beryl3/.env"

# Or create from template (see Environment Configuration section below)
```

**To add to GitHub**:
1. Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
2. Name: `DJE_PROD_ENV_FILE`
3. Value: Paste the entire `.env` file content (all KEY=value pairs)

**Important**: This secret is deployed to `~/beryl3/.env` on every deployment. Old `.env` is backed up to `~/backup/.env.backup_TIMESTAMP`.

### 4. DJE_GCS_CREDENTIALS_JSON

**Description**: Google Cloud Storage service account credentials JSON

**How to create**:
```bash
# Option 1: Get from production server
ssh mdubiel@148.251.140.153 "cat ~/beryl3/credentials/beryl3-storage.json"

# Option 2: Download from Google Cloud Console
# - Go to: IAM & Admin → Service Accounts
# - Find service account for Beryl3
# - Actions → Manage keys → Add key → Create new key → JSON
```

**To add to GitHub**:
1. Go to: `Settings` → `Secrets and variables` → `Actions` → `New repository secret`
2. Name: `DJE_GCS_CREDENTIALS_JSON`
3. Value: Paste the entire JSON file content (including `{ }` braces)

**Important**: This secret is deployed to `~/beryl3/credentials/beryl3-storage.json` on every deployment. Old credentials are backed up to `~/backup/credentials/gcs_backup_TIMESTAMP.json`

## 🚀 How to Use the Workflow

### Manual Deployment

1. Go to the **Actions** tab in your GitHub repository
2. Select **"Deploy to Django Europe Production"** workflow
3. Click **"Run workflow"** button
4. Fill in the parameters:
   - **release_tag**: The git tag to deploy (e.g., `v0.2.122`)
   - **skip_backup**: Leave unchecked (backup is recommended)
5. Click **"Run workflow"**

### Workflow Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `release_tag` | Yes | - | Git tag to deploy (format: `vX.Y.Z`) |
| `skip_backup` | No | `false` | Skip backup step (NOT RECOMMENDED) |

## 📦 Deployment Jobs

The workflow executes 8 jobs in sequence:

### Job 1: Validate Release Tag ✅

**Purpose**: Ensure the release tag exists and is valid

**Actions**:
- Validates tag format (must be `vX.Y.Z`)
- Checks tag exists in git repository
- Shows tag details (commit SHA, message)

**Failure conditions**:
- Invalid tag format
- Tag doesn't exist in repository

---

### Job 2: Backup ~/beryl3 Directory 💾

**Purpose**: Create a complete backup of the production directory

**Actions**:
- Creates timestamped backup: `~/beryl3-backups/beryl3_backup_YYYYMMDD_HHMMSS.tar.gz`
- Includes:
  - All code files
  - `.env` configuration file
  - `credentials/` directory (GCS JSON)
  - Excludes: log files, `__pycache__`
- Keeps only last 5 backups (auto-cleanup)

**Skip conditions**:
- Can be skipped if `skip_backup` parameter is `true` (not recommended)

**Output**:
- Backup file size
- List of available backups

---

### Job 3: Stop Gunicorn Service 🛑

**Purpose**: Gracefully stop the running application

**Actions**:
- Checks if gunicorn is running (via PID file)
- Executes `./beryl3-service.sh stop`
- Sends QUIT signal for graceful shutdown
- Waits up to 30 seconds for process to stop
- Force kills if necessary
- Verifies service has stopped

**Failure conditions**:
- Service fails to stop

---

### Job 4: Rotate Application Logs 🔄

**Purpose**: Archive current log files before deployment

**Actions**:
- Executes logrotate with force flag
- Uses config: `~/beryl3/workflows/logrotate.conf`
- Rotates files at 5MB, keeps 5 copies, compresses old logs
- Shows current log files

**Skip conditions**:
- Skipped if logrotate.conf doesn't exist (warning shown)

---

### Job 5: Deploy Code and Configuration 📦🔐

**Purpose**: Deploy new code from git and configuration from GitHub secrets

**Actions**:
1. **Create backup directory**:
   - Ensures `~/backup/credentials/` exists

2. **Backup existing configuration**:
   - Backs up current `.env` to `~/backup/.env.backup_TIMESTAMP`
   - Backs up GCS credentials to `~/backup/credentials/gcs_backup_TIMESTAMP.json`
   - Keeps last 10 backup copies

3. **Clone repository**:
   - Clones to temporary directory `~/beryl3-tmp`
   - Checks out specified release tag
   - Shows commit SHA

4. **Deploy new code**:
   - Removes old `~/beryl3/webapp` directory
   - Creates `~/beryl3/credentials/` directory
   - Copies new code from git

5. **Deploy configuration from GitHub secrets**:
   - Deploys `.env` from `DJE_PROD_ENV_FILE` secret
   - Deploys GCS credentials from `DJE_GCS_CREDENTIALS_JSON` secret
   - Sets proper permissions (600) on GCS credentials

6. **Verify deployment**:
   - Checks `.env` exists and is not empty
   - Checks GCS credentials exist
   - Validates GCS JSON format

7. **Cleanup**:
   - Removes temporary clone directory

**Configuration sources**:
- `.env` → GitHub secret `DJE_PROD_ENV_FILE`
- `credentials/beryl3-storage.json` → GitHub secret `DJE_GCS_CREDENTIALS_JSON`

**Backups created**:
- `~/backup/.env.backup_TIMESTAMP`
- `~/backup/credentials/gcs_backup_TIMESTAMP.json`

**Failure conditions**:
- GitHub secrets not configured
- `.env` secret is empty
- GCS credentials JSON is invalid
- Git clone/checkout fails

---

### Job 6: Run Database Migrations 🔄

**Purpose**: Apply any pending database migrations

**Actions**:
- Activates virtual environment: `~/.virtualenvs/beryl3`
- Sets Django settings: `production_settings`
- Shows pending migrations
- Executes `python manage.py migrate --noinput`

**Failure conditions**:
- Migration fails
- Database connection error

---

### Job 7: Collect Static Files 📦

**Purpose**: Upload static files to Google Cloud Storage

**Actions**:
- Activates virtual environment
- Sets Django settings: `production_settings`
- Verifies GCS credentials exist
- Executes `python manage.py collectstatic --noinput --clear`
- Uploads CSS, JavaScript, images to GCS bucket

**Failure conditions**:
- GCS credentials invalid
- GCS bucket not accessible
- Upload fails

**Note**: If GCS credentials are missing, a warning is shown but deployment continues

---

### Job 8: Start Gunicorn Service 🚀

**Purpose**: Start the application and verify it's running

**Actions**:
- Executes `./beryl3-service.sh start`
- Starts gunicorn daemon on port `62079`
- Waits 5 seconds for startup
- Verifies service status via PID file
- Performs HTTP health check
- Shows service information

**Failure conditions**:
- Service fails to start
- PID file not created
- Process not running

**Health check**:
- Tests: `http://127.0.0.1:62079/health/`
- Failure is a warning, not a hard error (app may still be initializing)

**Output**:
- Service status
- Gunicorn configuration
- Application URLs

---

## 🏗️ Server Directory Structure

```
~/beryl3/
├── config/              # Django configuration (from git)
├── web/                 # Django app (from git)
├── templates/           # Django templates (from git)
├── workflows/           # Deployment scripts (from git)
├── static/              # Static files (generated)
├── credentials/         # ⚠️ Deployed from GitHub secret DJE_GCS_CREDENTIALS_JSON
│   └── beryl3-storage.json     # GCS service account key
├── .env                 # ⚠️ Deployed from GitHub secret DJE_PROD_ENV_FILE
├── beryl3-service.sh    # Service management script
├── production_settings.py  # Generated Django settings
├── gunicorn.pid         # Runtime PID file
└── logs/                # Application logs
    ├── gunicorn.log
    ├── access.log
    ├── error.log
    └── *.log.gz         # Rotated logs

~/backup/                # Configuration backups
├── .env.backup_TIMESTAMP       # .env backups (last 10)
└── credentials/
    └── gcs_backup_TIMESTAMP.json  # GCS credentials backups (last 10)

~/beryl3-backups/        # Full project backups
└── beryl3_backup_TIMESTAMP.tar.gz  # Complete backups (last 5)
```

## 🔧 Environment Configuration

### Production .env File

The `.env` file must exist on the server and contain:

```bash
# Django Settings
DEBUG=False
SECRET_KEY=<secret-key>
ALLOWED_HOSTS=beryl3.mdubiel.org,148.251.140.153

# Database (PostgreSQL)
DB_ENGINE=django.db.backends.postgresql
PG_DB=beryl3_production
PG_USER=beryl3
PG_PASSWORD=<password>
PG_HOST=localhost
PG_PORT=5432

# Email Configuration
DEFAULT_FROM_EMAIL=noreply@beryl3.mdubiel.org
EMAIL_HOST=<smtp-host>
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=<email-user>
EMAIL_HOST_PASSWORD=<email-password>

# Google Cloud Storage
USE_GCS_STORAGE=True
GCS_BUCKET_NAME=beryl3-production-bucket
GCS_PROJECT_ID=beryl3
GCS_CREDENTIALS_PATH=/home/mdubiel/beryl3/credentials/beryl3-qa-storage.json
GCS_LOCATION=media

# Feature Flags
ALLOW_USER_REGISTRATION=False
CONTENT_MODERATION_ENABLED=True
APPLICATION_ACTIVITY_LOGGING=True
```

### GCS Credentials

The GCS service account JSON file must exist at the path specified in `GCS_CREDENTIALS_PATH`.

**Location**: `~/beryl3/credentials/beryl3-qa-storage.json`

**To create**:
1. Go to Google Cloud Console
2. Navigate to: `IAM & Admin` → `Service Accounts`
3. Create service account with `Storage Admin` role
4. Create JSON key
5. Upload to server: `scp service-account.json mdubiel@148.251.140.153:~/beryl3/credentials/`

## 🔍 Monitoring Deployment

### View Workflow Progress

1. Go to **Actions** tab in GitHub repository
2. Click on the running workflow
3. Watch each job execute in real-time
4. Click on individual jobs to see detailed logs

### Check Deployment on Server

```bash
# SSH to production server
ssh mdubiel@148.251.140.153

# Check service status
cd ~/beryl3
./beryl3-service.sh status

# View service info
./beryl3-service.sh info

# Check recent logs
tail -50 ~/beryl3/logs/error.log
tail -50 ~/beryl3/logs/access.log

# Check application health
curl http://127.0.0.1:62079/health/
```

## 🚨 Troubleshooting

### Deployment Fails at Job 5 (Deploy Code)

**Problem**: Missing `.env` or `credentials/` directory

**Solution**:
```bash
# SSH to server
ssh mdubiel@148.251.140.153

# Verify .env exists
ls -la ~/beryl3/.env

# Verify credentials exist
ls -la ~/beryl3/credentials/*.json

# If missing, restore from backup
cd ~/beryl3-backups
tar -xzf beryl3_backup_<timestamp>.tar.gz -C ~ beryl3/.env beryl3/credentials/
```

### Service Fails to Start (Job 8)

**Problem**: Service starts but health check fails

**Solution**:
```bash
# Check error logs
ssh mdubiel@148.251.140.153
tail -100 ~/beryl3/logs/error.log

# Common issues:
# 1. Database connection error -> Check PG_* settings in .env
# 2. GCS credentials error -> Verify GCS_CREDENTIALS_PATH
# 3. Port already in use -> Check for stale gunicorn process
```

### Rollback to Previous Version

**If deployment fails and you need to rollback**:

```bash
# Option 1: Restore from backup
ssh mdubiel@148.251.140.153
cd ~/beryl3-backups
# Find latest backup
ls -lt beryl3_backup_*.tar.gz | head -1
# Restore
tar -xzf beryl3_backup_<timestamp>.tar.gz -C ~
cd ~/beryl3
./beryl3-service.sh restart

# Option 2: Deploy previous release tag via workflow
# Go to GitHub Actions and run workflow with previous release tag
```

### SSH Authentication Fails

**Problem**: Workflow can't connect to server

**Solution**:
```bash
# Test SSH connection locally
ssh -i ~/.ssh/beryl3-deploy mdubiel@148.251.140.153

# If fails, verify:
# 1. Public key is in ~/.ssh/authorized_keys on server
# 2. GitHub secret DJE_SSH_PRIVATE_KEY contains correct private key
# 3. GitHub secret DJE_SSH_KNOWN_HOSTS contains server fingerprint

# Regenerate known hosts
ssh-keyscan -H 148.251.140.153
# Copy output to DJE_SSH_KNOWN_HOSTS secret
```

## 📝 Best Practices

### Before Deployment

1. ✅ **Create a release tag** in git:
   ```bash
   git tag -a v0.2.123 -m "Release v0.2.123 - Description"
   git push origin v0.2.123
   ```

2. ✅ **Test in preprod first** (if available)

3. ✅ **Verify backups exist**:
   ```bash
   ssh mdubiel@148.251.140.153 "ls -lh ~/beryl3-backups/"
   ```

4. ✅ **Check database migration status**:
   ```bash
   ssh mdubiel@148.251.140.153 "cd ~/beryl3 && source ~/.virtualenvs/beryl3/bin/activate && python manage.py showmigrations | grep '[ ]'"
   ```

### During Deployment

1. 🔍 **Monitor workflow progress** in GitHub Actions
2. 🔍 **Watch for warnings** in job outputs
3. 🔍 **Verify each job completes successfully**

### After Deployment

1. ✅ **Verify application is accessible**:
   - http://beryl3.mdubiel.org/
   - http://148.251.140.153:62079/

2. ✅ **Check service health**:
   ```bash
   curl http://148.251.140.153:62079/health/
   ```

3. ✅ **Monitor logs for errors**:
   ```bash
   ssh mdubiel@148.251.140.153 "tail -f ~/beryl3/logs/error.log"
   ```

4. ✅ **Test critical functionality**:
   - User login
   - Database queries
   - File uploads (GCS)
   - Email sending

## 🔗 Related Documentation

- [Makefile Deployment Targets](../webapp/Makefile) - Local deployment commands
- [Django Europe Deployment Guide](DJANGO_EUROPE_DEPLOYMENT.md) - Manual deployment process
- [Environment Configuration](../webapp/workflows/envs/env.gold) - Environment variables

## 🆘 Support

If you encounter issues not covered in this documentation:

1. Check the **workflow logs** in GitHub Actions for detailed error messages
2. SSH to the server and check **application logs** in `~/beryl3/logs/`
3. Review the **backup files** in `~/beryl3-backups/` for recovery options
4. Consult the **Makefile** targets for manual deployment commands
