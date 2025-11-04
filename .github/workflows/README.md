# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated deployment.

## Available Workflows

### 🚀 Deploy to Django Europe Production

**File**: `deploy-dje-production.yml`

**Purpose**: Deploy a specific release tag to Django Europe production server

**Trigger**: Manual (workflow_dispatch)

**Requirements**:
- GitHub secrets configured (see setup guide below)
- Valid release tag (format: `vX.Y.Z`)

**Usage**:
1. Go to **Actions** tab → **Deploy to Django Europe Production**
2. Click **Run workflow**
3. Enter release tag (e.g., `v0.2.122`)
4. Click **Run workflow**

**Jobs** (8 sequential jobs):
1. ✅ Validate Release Tag
2. 💾 Backup ~/beryl3 Directory
3. 🛑 Stop Gunicorn Service
4. 🔄 Rotate Application Logs
5. 📦 Deploy Code from Git
6. 🔄 Run Database Migrations
7. 📦 Collect Static Files
8. 🚀 Start Gunicorn Service

## 📚 Documentation

**Detailed Documentation**:
- [GitHub Actions Deployment Guide](../../docs/github-actions-deployment.md) - Complete workflow documentation
- [GitHub Secrets Setup Guide](../../docs/github-secrets-setup.md) - Step-by-step secret configuration

**Quick Links**:
- [Makefile](../../webapp/Makefile) - Manual deployment targets
- [Django Europe Deployment](../../DJANGO_EUROPE_DEPLOYMENT.md) - Manual deployment process

## 🔑 Required GitHub Secrets

Before running workflows, configure these secrets:

| Secret Name | Description |
|-------------|-------------|
| `DJE_SSH_PRIVATE_KEY` | SSH private key for server authentication |
| `DJE_SSH_KNOWN_HOSTS` | SSH known hosts entry for server verification |

**Setup Instructions**: See [GitHub Secrets Setup Guide](../../docs/github-secrets-setup.md)

## 🎯 Quick Start

### First-Time Setup

1. **Generate SSH key**:
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/beryl3-github-actions
   ```

2. **Copy public key to server**:
   ```bash
   ssh-copy-id -i ~/.ssh/beryl3-github-actions.pub mdubiel@148.251.140.153
   ```

3. **Get known hosts**:
   ```bash
   ssh-keyscan -H 148.251.140.153
   ```

4. **Add secrets to GitHub**:
   - Repository Settings → Secrets and variables → Actions
   - Add `DJE_SSH_PRIVATE_KEY` (private key content)
   - Add `DJE_SSH_KNOWN_HOSTS` (ssh-keyscan output)

### Running a Deployment

1. **Create release tag**:
   ```bash
   git tag -a v0.2.123 -m "Release v0.2.123"
   git push origin v0.2.123
   ```

2. **Run workflow**:
   - GitHub → Actions → Deploy to Django Europe Production
   - Run workflow with tag `v0.2.123`

3. **Monitor deployment**:
   - Watch workflow progress in Actions tab
   - Check each job completes successfully

4. **Verify deployment**:
   ```bash
   curl http://beryl3.mdubiel.org/
   ```

## 🔍 Monitoring

### View Workflow Logs

- GitHub → Actions → Click on workflow run
- Click on individual jobs to see detailed logs

### Check Server Status

```bash
ssh mdubiel@148.251.140.153
cd ~/beryl3
./beryl3-service.sh status
tail -50 logs/error.log
```

## 🚨 Troubleshooting

### Workflow Fails to Connect

**Problem**: SSH authentication error

**Solution**: Verify secrets are configured correctly
```bash
# Test SSH access locally
ssh -i ~/.ssh/beryl3-github-actions mdubiel@148.251.140.153
```

### Deployment Fails

**Problem**: Job fails during deployment

**Solution**: Check workflow logs for specific error
- Job 5 fails → Check .env and credentials/ exist on server
- Job 6 fails → Check database connection
- Job 7 fails → Check GCS credentials
- Job 8 fails → Check application logs on server

### Rollback

**If deployment fails**:

1. **Restore from backup**:
   ```bash
   ssh mdubiel@148.251.140.153
   cd ~/beryl3-backups
   tar -xzf beryl3_backup_<timestamp>.tar.gz -C ~
   cd ~/beryl3
   ./beryl3-service.sh restart
   ```

2. **Deploy previous release**:
   - Run workflow again with previous release tag

## 📋 Workflow Environment

**Production Server**:
- Host: `148.251.140.153`
- User: `mdubiel`
- Project: `~/beryl3`
- Venv: `~/.virtualenvs/beryl3`
- Port: `62079`

**Preserved Files** (not from git):
- `.env` - Environment configuration
- `credentials/*.json` - GCS service account key

**Runtime Files**:
- `gunicorn.pid` - Service PID
- `logs/` - Application logs
- `production_settings.py` - Generated settings

## 📖 Additional Resources

- [Main README](../../README.md)
- [Deployment Documentation](../../docs/)
- [Makefile Targets](../../webapp/Makefile)
