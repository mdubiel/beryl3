# Google Cloud Logging Setup for Beryl3

## Overview
This document outlines the Google Cloud Logging integration for Beryl3 QA and production environments, providing centralized log management and monitoring.

## Configuration

### Environment Variables
Add these variables to your environment configuration (qa.env, production.env):

```bash
# Google Cloud Logging Configuration
USE_GOOGLE_CLOUD_LOGGING=True
GOOGLE_CLOUD_LOGGING_PROJECT_ID=beryl3
GOOGLE_CLOUD_LOGGING_RESOURCE_TYPE=gce_instance
GOOGLE_CLOUD_LOGGING_CREDENTIALS_PATH=/path/to/service-account-key.json
```

### Service Account Permissions
The service account requires the following IAM role:
- `roles/logging.logWriter` - Write access to Cloud Logging

### Django Integration
The logging integration provides:
- **Structured JSON logging** with request context (user, path)
- **Multiple log levels**: DEBUG, INFO, WARNING, ERROR
- **Three logger categories**: `django`, `webapp`, `performance`
- **Automatic fallback** to console/file logging if Cloud Logging unavailable

## Monitoring and Dashboards

### Google Cloud Console Access
1. Navigate to [Google Cloud Console > Logging > Logs Explorer](https://console.cloud.google.com/logs/query)
2. Select project: `beryl3`

### Useful Log Queries

#### Filter by Application
```
resource.type="gce_instance" 
jsonPayload.name="beryl3-webapp"
```

#### Filter by Log Level
```
resource.type="gce_instance" 
jsonPayload.name="beryl3-webapp"
severity>=WARNING
```

#### Filter by Logger
```
resource.type="gce_instance" 
jsonPayload.name="beryl3-webapp"
jsonPayload.name="webapp"
```

#### Filter by User Activity
```
resource.type="gce_instance" 
jsonPayload.name="beryl3-webapp"
jsonPayload.user!="Anonymous"
```

### Log-based Metrics
Create custom metrics for monitoring:

1. **Error Rate**: Count of ERROR level logs
2. **User Activity**: Count of logs with authenticated users
3. **Performance Issues**: Count of performance logger messages

### Alerting
Set up alerts for:
- High error rates (>10 errors/minute)
- Application startup/shutdown events
- Performance degradation indicators

## Log Structure
Example structured log entry:
```json
{
  "timestamp": "2025-09-18T13:47:23.123Z",
  "severity": "INFO",
  "jsonPayload": {
    "asctime": "2025-09-18 13:47:23,123",
    "levelname": "INFO", 
    "name": "webapp",
    "module": "views",
    "funcName": "user_login",
    "user": "john.doe@example.com",
    "path": "/auth/login/",
    "message": "User login successful"
  },
  "resource": {
    "type": "gce_instance",
    "labels": {
      "instance_id": "beryl3-qa"
    }
  }
}
```

## Testing
Run the test script to verify logging integration:
```bash
cd webapp
python test_google_logging.py
```

Expected output:
- ✅ Configuration loaded
- ✅ Google Cloud handler configured  
- ✅ Log messages sent successfully

## Troubleshooting

### Common Issues
1. **Missing permissions**: Ensure service account has `roles/logging.logWriter`
2. **Credentials not found**: Verify `GOOGLE_CLOUD_LOGGING_CREDENTIALS_PATH` points to valid key file
3. **Project not found**: Confirm `GOOGLE_CLOUD_LOGGING_PROJECT_ID` matches your GCP project

### Debug Mode
Enable debug logging to troubleshoot:
```python
import logging
logging.getLogger('google.cloud.logging').setLevel(logging.DEBUG)
```

## Migration Notes
- Existing Loki and file logging continue to work alongside Google Cloud Logging
- No changes required to application logging calls
- Gradual migration possible by environment (dev → QA → prod)