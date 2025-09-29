# Django Europe Deployment Guide - Beryl3

## 🚀 Quick Deployment

### Initial Setup (One-time)
```bash
# 1. Upload GCS credentials (if not done)
scp webapp/workflows/envs/credentials/gcs_keys/beryl3-qa-storage.json mdubiel@148.251.140.153:~/beryl3-preprod/credentials/

# 2. Deploy the application
cd webapp
python workflows/bin/dje-deploy-all.py
```

### Regular Updates
```bash
cd webapp
python workflows/bin/dje-deploy-all.py --quick-update
```

## 📋 Deployment Components

### 🔧 Available Scripts

| Script | Purpose |
|--------|---------|
| `dje-deploy-all.py` | Complete deployment (env + dependencies + project) |
| `dje-deploy-project.py` | Deploy project files only |
| `dje-sync-dependencies.py` | Sync Python dependencies |
| `dje-upload-preprod-env.py` | Upload environment configuration |
| `beryl3-service.sh` | Service management script |

### 📁 Deployment Structure

**Django Europe Server Structure:**
```
~/beryl3-preprod/
├── beryl3-service.sh           # Service management script
├── RUN                         # Simple startup script  
├── config/
│   ├── settings/production.py # Production Django settings
│   └── wsgi.py                # WSGI configuration
├── credentials/
│   └── beryl3-qa-storage.json # GCS credentials
├── logs/                       # Application logs
│   ├── django.log             # Django framework logs
│   ├── web.log                # Application logs  
│   ├── security.log           # Security events
│   ├── db.log                 # Database queries
│   ├── access.log             # Gunicorn access logs
│   └── error.log              # Gunicorn error logs
├── static/                     # Static files (fallback)
└── [webapp project files]     # From git repository
```

## 🎛️ Service Management

### Using the Service Script
```bash
# SSH to server
ssh mdubiel@148.251.140.153

# Navigate to project
cd ~/beryl3-preprod

# Service commands
./beryl3-service.sh start      # Start the service
./beryl3-service.sh stop       # Stop the service
./beryl3-service.sh restart    # Restart the service
./beryl3-service.sh reload     # Reload configuration
./beryl3-service.sh status     # Check status
```

### Using Simple RUN Script
```bash
# Start in background
cd ~/beryl3-preprod
./RUN > logs/startup.log 2>&1 &

# Stop manually
pkill -f 'gunicorn.*beryl3'
```

## 🔍 Monitoring & Logs

### Log Files Location
- **Application Logs**: `~/beryl3-preprod/logs/`
- **Django**: `django.log` - Framework events
- **Web App**: `web.log` - Application logic
- **Security**: `security.log` - Security events  
- **Database**: `db.log` - DB queries (debug mode)
- **Gunicorn Access**: `access.log` - HTTP requests
- **Gunicorn Errors**: `error.log` - Server errors

### Monitoring Commands
```bash
# Check service status
./beryl3-service.sh status

# View recent logs
tail -f ~/beryl3-preprod/logs/django.log
tail -f ~/beryl3-preprod/logs/web.log

# Check gunicorn processes
ps aux | grep gunicorn | grep beryl3

# Check port binding
netstat -tln | grep 62059
```

## 🛠️ Configuration

### Environment Variables
- **File**: `webapp/workflows/envs/generated/preprod.env`
- **Deployed to**: `~/beryl3-preprod/.env`
- **Key settings**:
  - `USE_GCS_STORAGE=True`
  - `GCS_CREDENTIALS_PATH=/home/mdubiel/beryl3-preprod/credentials/beryl3-qa-storage.json`
  - `ALLOWED_HOSTS=beryl3-preprod.mdubiel.org`

### Application URLs
- **Production**: https://beryl3-preprod.mdubiel.org/
- **Admin**: https://beryl3-preprod.mdubiel.org/admin/

## 🚨 Troubleshooting

### Common Issues

**1. Application not responding**
```bash
# Check if gunicorn is running
ps aux | grep gunicorn | grep beryl3
netstat -tln | grep 62059

# Restart service
./beryl3-service.sh restart
```

**2. GCS connection errors**
```bash
# Verify credentials exist
ls -la ~/beryl3-preprod/credentials/
# Check logs
tail ~/beryl3-preprod/logs/django.log
```

**3. Database issues**
```bash
# Run migrations
cd ~/beryl3-preprod
source ~/.virtualenvs/beryl3-preprod/bin/activate
export DJANGO_SETTINGS_MODULE=config.settings.production
python manage.py migrate
```

**4. Static files not loading**
```bash
# Collect static files
python manage.py collectstatic --noinput
# Check GCS configuration in logs
```

### Emergency Recovery
```bash
# Stop all services
pkill -f 'gunicorn.*beryl3'

# Redeploy from scratch
cd /path/to/local/beryl3/webapp
python workflows/bin/dje-deploy-all.py

# Start service
ssh mdubiel@148.251.140.153
cd ~/beryl3-preprod
./beryl3-service.sh start
```

## 📊 Performance Monitoring

### Key Metrics to Watch
- **Gunicorn processes**: 2 workers running
- **Memory usage**: Monitor via `htop` or `ps aux`
- **Log file sizes**: Rotate if > 15MB (auto-configured)
- **Response times**: Check access.log
- **Error rates**: Monitor error.log and security.log

### Health Check
```bash
# Quick health check
curl -I https://beryl3-preprod.mdubiel.org/
# Should return HTTP/2 200

# Detailed check
curl -s https://beryl3-preprod.mdubiel.org/admin/login/ | grep -q "Django administration"
```

---

## 🎯 Production Checklist

- ✅ Git-based deployment configured
- ✅ Service management scripts deployed  
- ✅ Comprehensive logging configured
- ✅ GCS integration working
- ✅ Database migrations automated
- ✅ Environment variables secured
- ✅ nginx proxy configured correctly
- ✅ SSL/HTTPS working via Django Europe

**Application Status**: 🟢 **LIVE** at https://beryl3-preprod.mdubiel.org/