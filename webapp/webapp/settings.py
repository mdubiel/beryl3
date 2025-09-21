# -*- coding: utf-8 -*-

# pylint: disable=missing-class-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=line-too-long

from pathlib import Path
import os
import logging

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT_DIR = Path(BASE_DIR).parent / "webapp" / "web"

# Initialize environ with defaults for optional settings only
# Critical settings (SECRET_KEY, database, etc.) have NO defaults and will raise errors if missing
env = environ.Env(
    # Development/Production mode (defaults to False for security)
    DEBUG=(bool, False),
    
    # Database engine (defaults to SQLite for development)
    DB_ENGINE=(str, 'django.db.backends.sqlite3'),
    
    # Email settings (development defaults)
    # USE_INBUCKET - moved to FEATURE_FLAGS system
    EMAIL_HOST=(str, 'localhost'),
    EMAIL_PORT=(int, 587),
    EMAIL_USE_TLS=(bool, True),
    EMAIL_HOST_USER=(str, ''),
    EMAIL_HOST_PASSWORD=(str, ''),
    INBUCKET_SMTP_PORT=(int, 2500),
    DEFAULT_FROM_EMAIL=(str, 'webmaster@localhost'),
    
    # Google Cloud Storage (optional)
    # USE_GCS_STORAGE - moved to FEATURE_FLAGS system
    GCS_BUCKET_NAME=(str, ''),
    GCS_PROJECT_ID=(str, ''),
    GCS_CREDENTIALS_PATH=(str, ''),
    GCS_LOCATION=(str, 'media'),
    
    # External service URLs (optional)
    EXTERNAL_DB_URL=(str, ''),
    EXTERNAL_INBUCKET_URL=(str, ''),
    EXTERNAL_MONITORING_URL=(str, ''),
    EXTERNAL_SENTRY_URL=(str, ''),
    EXTERNAL_LOKI_URL=(str, ''),
    EXTERNAL_GRAFANA_URL=(str, ''),
    EXTERNAL_RESEND_URL=(str, ''),
    
    # Application features
    # APPLICATION_ACTIVITY_LOGGING - moved to FEATURE_FLAGS system
    
    # Sentry configuration (optional)
    SENTRY_DSN=(str, ''),
    SENTRY_ENVIRONMENT=(str, 'development'),
    SENTRY_TRACES_SAMPLE_RATE=(float, 0.1),
    SENTRY_PROFILES_SAMPLE_RATE=(float, 0.1),
    
    # Log forwarding configuration (optional)
    LOKI_URL=(str, ''),
    # LOKI_ENABLED - moved to FEATURE_FLAGS system
    
    # Google Cloud Logging configuration
    # USE_GOOGLE_CLOUD_LOGGING - moved to FEATURE_FLAGS system
    GOOGLE_CLOUD_LOGGING_PROJECT_ID=(str, ''),
    GOOGLE_CLOUD_LOGGING_RESOURCE_TYPE=(str, 'gce_instance'),
    GOOGLE_CLOUD_LOGGING_CREDENTIALS_PATH=(str, '')
)

# Read variables from .env file (if it exists)
# In Docker containers, environment variables are usually provided directly
env_file_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file_path):
    env.read_env(env_file_path)
else:
    # Environment variables are provided directly (e.g., via Docker env_file)
    logging.debug("[ENV DEBUG] No .env file found, using system environment variables")


# CRITICAL SETTINGS - NO DEFAULTS, WILL RAISE ERROR IF MISSING
SECRET_KEY = env('SECRET_KEY')  # Required: Django secret key for cryptographic signing
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')  # Required: Specific domains for production

# =====================================
# FEATURE FLAGS SYSTEM
# =====================================
# Consolidated feature flags with DEBUG-based defaults and environment overrides
# Pattern: DEBUG=True sets development defaults, DEBUG=False sets production defaults
# Individual flags can be overridden via environment variables

def _get_feature_flag(flag_name: str, dev_default: bool, prod_default: bool) -> bool:
    """Get feature flag value with DEBUG-based defaults and environment override."""
    debug_based_default = dev_default if DEBUG else prod_default
    return env(flag_name, default=debug_based_default)

# Feature flags configuration
FEATURE_FLAGS = {
    # Storage backend: Local filesystem vs Google Cloud Storage
    'USE_GCS_STORAGE': _get_feature_flag('USE_GCS_STORAGE', dev_default=False, prod_default=True),
    
    # Email backend: Inbucket (dev) vs SMTP (prod)
    'USE_INBUCKET': _get_feature_flag('USE_INBUCKET', dev_default=True, prod_default=False),
    
    # Logging integrations
    'LOKI_ENABLED': _get_feature_flag('LOKI_ENABLED', dev_default=False, prod_default=False),
    'USE_GOOGLE_CLOUD_LOGGING': _get_feature_flag('USE_GOOGLE_CLOUD_LOGGING', dev_default=False, prod_default=True),
    
    # Development tools and debugging
    'BROWSER_RELOAD': _get_feature_flag('BROWSER_RELOAD', dev_default=True, prod_default=False),
    'DJANGO_TOOLBAR': _get_feature_flag('DJANGO_TOOLBAR', dev_default=False, prod_default=False),
    
    # Activity and audit logging  
    'APPLICATION_ACTIVITY_LOGGING': _get_feature_flag('APPLICATION_ACTIVITY_LOGGING', dev_default=True, prod_default=True),
    
    # Database backend: SQLite (dev) vs PostgreSQL (prod)
}

# Backward compatibility - expose individual flags as module-level variables
USE_GCS_STORAGE = FEATURE_FLAGS['USE_GCS_STORAGE']
USE_INBUCKET = FEATURE_FLAGS['USE_INBUCKET'] 
LOKI_ENABLED = FEATURE_FLAGS['LOKI_ENABLED']
USE_GOOGLE_CLOUD_LOGGING = FEATURE_FLAGS['USE_GOOGLE_CLOUD_LOGGING']
APPLICATION_ACTIVITY_LOGGING = FEATURE_FLAGS['APPLICATION_ACTIVITY_LOGGING']

# Debug logging for CSRF_TRUSTED_ORIGINS
csrf_env_value = os.environ.get('CSRF_TRUSTED_ORIGINS', 'NOT_SET')
logging.debug(f"[CSRF DEBUG] Environment variable CSRF_TRUSTED_ORIGINS: {csrf_env_value}")

parsed_csrf_origins = env.list('CSRF_TRUSTED_ORIGINS', default=[])
logging.debug(f"[CSRF DEBUG] Parsed CSRF_TRUSTED_ORIGINS: {parsed_csrf_origins}")

CSRF_TRUSTED_ORIGINS = parsed_csrf_origins
logging.debug(f"[CSRF DEBUG] Final CSRF_TRUSTED_ORIGINS setting: {CSRF_TRUSTED_ORIGINS}")

# Database configuration - determined by DB_ENGINE setting
db_engine = env('DB_ENGINE', default='django.db.backends.sqlite3')

if db_engine == 'django.db.backends.sqlite3':
    # SQLite database configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # PostgreSQL or other database configuration
    DATABASES = {
        'default': {
            'ENGINE': db_engine,
            'NAME': env('PG_DB'),      # Required: Database name
            'USER': env('PG_USER'),    # Required: Database user
            'PASSWORD': env('PG_PASSWORD'),  # Required: Database password
            'HOST': env('PG_HOST'),    # Required: Database host
            'PORT': env.int('PG_PORT'),  # Required: Database port
        }
    }

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'allauth',
    'allauth.account',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.humanize',
    'post_office',
    'lucide',
    'nanoid_field',
    'widget_tweaks',
    'django_htmx',
    'django_prometheus',
    'core.apps.CoreConfig',
    'web.apps.WebConfig',
    'api.apps.ApiConfig',

]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'webapp.logging_middleware.RequestUserInfoMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django_htmx.middleware.HtmxMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'webapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'web.context_processors.external_services',
                'web.context_processors.user_avatar',
            ],
        },
    },
]

# Development tools based on feature flags
if FEATURE_FLAGS['BROWSER_RELOAD']:
    INSTALLED_APPS.append("django_browser_reload")
    MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")

WSGI_APPLICATION = 'webapp.wsgi.application'

SITE_ID = 1

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Location of static files _before_ collectstatic
# it is projectfolder/local/static (not in "plate" directory)
STATICFILES_DIRS = (
    BASE_DIR / "static",
)

# collectstatic copy all static files into this directory
# Local development: filesystem path
# Production: will be overridden by GCS storage backend
STATIC_ROOT = BASE_DIR / "tmp" / "static"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login settings
LOGIN_REDIRECT_URL = 'dashboard'  # Redirect to index after login
LOGOUT_REDIRECT_URL = 'index'  # Redirect to index after logout
#LOGIN_URL = '/login/'

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    'django.contrib.auth.backends.ModelBackend',
    # `allauth` specific authentication methods, such as login by email
    'allauth.account.auth_backends.AuthenticationBackend',

]

# Allauth settings
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

# This is the setting you need to add or set to True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True

# While you're here, it's a good idea to set a minimum password length
ACCOUNT_PASSWORD_MIN_LENGTH = 8

# EMAIL CONFIGURATION
# Check for the development flag in your environment variables.
# os.getenv('USE_INBUCKET', 'False') == 'True' is a safe way to read a boolean
# from an environment variable.

# SMTP BACKEND CONFIGURATION (used by Post Office)
if FEATURE_FLAGS['USE_INBUCKET']:
    # DEVELOPMENT EMAIL SETTINGS (using Inbucket)
    SMTP_EMAIL_HOST = env('EMAIL_HOST')
    SMTP_EMAIL_PORT = env('INBUCKET_SMTP_PORT')
    SMTP_EMAIL_HOST_USER = ''
    SMTP_EMAIL_HOST_PASSWORD = ''
    SMTP_EMAIL_USE_TLS = False
else:
    # PRODUCTION EMAIL SETTINGS - REQUIRED for production deployment
    SMTP_EMAIL_HOST = env('EMAIL_HOST')          # Required in production
    SMTP_EMAIL_PORT = env('EMAIL_PORT')          # Required in production  
    SMTP_EMAIL_USE_TLS = env('EMAIL_USE_TLS')    # Required in production
    SMTP_EMAIL_HOST_USER = env('EMAIL_HOST_USER')        # Required in production
    SMTP_EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')  # Required in production

# Apply SMTP settings to Django email configuration
EMAIL_HOST = SMTP_EMAIL_HOST
EMAIL_PORT = SMTP_EMAIL_PORT
EMAIL_USE_TLS = SMTP_EMAIL_USE_TLS
EMAIL_HOST_USER = SMTP_EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = SMTP_EMAIL_HOST_PASSWORD

DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')  # Required: From address for emails

# DJANGO-POST-OFFICE CONFIGURATION
# Asynchronous email delivery with queue management and monitoring
EMAIL_BACKEND = 'post_office.EmailBackend'
POST_OFFICE = {
    'BACKENDS': {
        'default': 'django.core.mail.backends.smtp.EmailBackend',
    },
    'DEFAULT_PRIORITY': 'now',  # Send emails immediately in development, can be 'now', 'high', 'medium', 'low'
    'BATCH_SIZE': env.int('POST_OFFICE_BATCH_SIZE', default=100),  # Number of emails to send per batch
    'BATCH_DELIVERY_TIMEOUT': env.int('POST_OFFICE_BATCH_TIMEOUT', default=180),  # Timeout for each batch in seconds
    'LOG_LEVEL': 2 if DEBUG else 1,  # 0=none, 1=failed, 2=all
    'MAX_RETRIES': env.int('POST_OFFICE_MAX_RETRIES', default=3),  # Maximum retry attempts for failed emails
    'RETRY_INTERVAL': env.int('POST_OFFICE_RETRY_INTERVAL', default=15),  # Minutes between retries
    'MESSAGE_ID_ENABLED': True,  # Enable Message-ID header for email tracking
    'MESSAGE_ID_FQDN': env('POST_OFFICE_MESSAGE_ID_FQDN', default='localhost'),  # FQDN for Message-ID header
}

# LOG FORWARDING CONFIGURATION
LOKI_URL = env('LOKI_URL') if env('LOKI_URL') else None
# LOKI_ENABLED - now using FEATURE_FLAGS['LOKI_ENABLED']

# GOOGLE CLOUD LOGGING CONFIGURATION
# USE_GOOGLE_CLOUD_LOGGING - now using FEATURE_FLAGS['USE_GOOGLE_CLOUD_LOGGING']
GOOGLE_CLOUD_LOGGING_PROJECT_ID = env('GOOGLE_CLOUD_LOGGING_PROJECT_ID') if env('GOOGLE_CLOUD_LOGGING_PROJECT_ID') else None
GOOGLE_CLOUD_LOGGING_RESOURCE_TYPE = env('GOOGLE_CLOUD_LOGGING_RESOURCE_TYPE')
GOOGLE_CLOUD_LOGGING_CREDENTIALS_PATH = env('GOOGLE_CLOUD_LOGGING_CREDENTIALS_PATH') if env('GOOGLE_CLOUD_LOGGING_CREDENTIALS_PATH') else None

# LOGGING CONFIGURATION
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        # Filter that uses the class from Step 1
        "user_info": {
            "()": "webapp.logging_middleware.RequestUserInfoFilter",
        }
    },
    # FORMATTERS
    # Define how your log messages will look.
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
        },
        "webapp_json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(user)s %(path)s %(message)s",
        },
    },
    # HANDLERS
    # Define where your logs will go.
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs/django.log"),
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "performance_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs/performance.jsonl"),
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "json", 
        },
        "webapp_json_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "logs/webapp.jsonl"),
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "formatter": "webapp_json",
            "filters": ["user_info"],
        },
    },
    # ROOT LOGGER
    "root": {
        "level": "DEBUG",
        "handlers": ["console"],
    },
    # LOGGERS
    # Define which loggers to use.
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": True,
        },
        "performance": {
            # Use both handlers for development: JSON to the file, simple text to console
            "handlers": ["performance_file"],
            "level": "INFO",
            "propagate": False,
        },
        "webapp": {
            "handlers": ["console", "webapp_json_file"],
            "level": "DEBUG", # Capture all log levels
            "propagate": False,
        },
    },
}

# Add Loki handler if enabled
if FEATURE_FLAGS['LOKI_ENABLED'] and LOKI_URL:
    try:
        import logging_loki
        
        # Add Loki handler to LOGGING config
        LOGGING['handlers']['loki'] = {
            'class': 'logging_loki.LokiHandler',
            'url': f"{LOKI_URL}/loki/api/v1/push",
            'tags': {"application": "beryl3", "environment": env('SENTRY_ENVIRONMENT', default='development')},
            'version': "1",
            'formatter': 'json',
        }
        
        # Add Loki handler to existing loggers
        LOGGING['loggers']['django']['handlers'].append('loki')
        LOGGING['loggers']['webapp']['handlers'].append('loki')
        LOGGING['loggers']['performance']['handlers'].append('loki')
        
    except ImportError:
        pass  # Gracefully handle missing python-logging-loki dependency

# Add Google Cloud Logging handler if enabled
if FEATURE_FLAGS['USE_GOOGLE_CLOUD_LOGGING'] and GOOGLE_CLOUD_LOGGING_PROJECT_ID:
    try:
        import google.cloud.logging
        from google.cloud.logging_v2.handlers import CloudLoggingHandler
        
        # Set up credentials if path provided
        if GOOGLE_CLOUD_LOGGING_CREDENTIALS_PATH and os.path.exists(GOOGLE_CLOUD_LOGGING_CREDENTIALS_PATH):
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CLOUD_LOGGING_CREDENTIALS_PATH
        
        # Create client and handler
        client = google.cloud.logging.Client(project=GOOGLE_CLOUD_LOGGING_PROJECT_ID)
        
        # Add Google Cloud Logging handler to LOGGING config
        LOGGING['handlers']['google_cloud'] = {
            'class': 'google.cloud.logging_v2.handlers.CloudLoggingHandler',
            'client': client,
            'name': 'beryl3-webapp',
            'resource_type': GOOGLE_CLOUD_LOGGING_RESOURCE_TYPE,
        }
        
        # Add structured formatter for Google Cloud Logging
        LOGGING['formatters']['google_cloud'] = {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(module)s %(funcName)s %(user)s %(path)s %(message)s',
        }
        
        # Use the structured formatter for Google Cloud handler
        LOGGING['handlers']['google_cloud']['formatter'] = 'google_cloud'
        LOGGING['handlers']['google_cloud']['filters'] = ['user_info']
        
        # Add Google Cloud handler to existing loggers
        LOGGING['loggers']['django']['handlers'].append('google_cloud')
        LOGGING['loggers']['webapp']['handlers'].append('google_cloud')
        LOGGING['loggers']['performance']['handlers'].append('google_cloud')
        
    except ImportError:
        pass  # Gracefully handle missing google-cloud-logging dependency
    except Exception as e:
        # Log the error but don't break the application
        import logging
        logging.getLogger(__name__).warning(f"Failed to setup Google Cloud Logging: {e}")

# Configure logging for containerized environments  
# Remove file handlers for cloud logging (containerized deployment)
if FEATURE_FLAGS['LOKI_ENABLED'] and LOKI_URL or FEATURE_FLAGS['USE_GOOGLE_CLOUD_LOGGING']:
    # Build handler list for containerized deployment
    cloud_handlers = ['console']
    
    if FEATURE_FLAGS['LOKI_ENABLED'] and LOKI_URL:
        cloud_handlers.append('loki')
        
    if FEATURE_FLAGS['USE_GOOGLE_CLOUD_LOGGING'] and GOOGLE_CLOUD_LOGGING_PROJECT_ID:
        cloud_handlers.append('google_cloud')
    
    # Replace file handlers with cloud handlers
    LOGGING['loggers']['django']['handlers'] = cloud_handlers
    LOGGING['loggers']['webapp']['handlers'] = cloud_handlers
    
    # Performance logs go to cloud handlers only (no console spam)
    performance_handlers = []
    if FEATURE_FLAGS['LOKI_ENABLED'] and LOKI_URL:
        performance_handlers.append('loki')
    if FEATURE_FLAGS['USE_GOOGLE_CLOUD_LOGGING'] and GOOGLE_CLOUD_LOGGING_PROJECT_ID:
        performance_handlers.append('google_cloud')
    
    LOGGING['loggers']['performance']['handlers'] = performance_handlers if performance_handlers else ['console']
    
    # Remove file handlers from handlers config to prevent initialization errors
    if 'file' in LOGGING['handlers']:
        del LOGGING['handlers']['file']
    if 'performance_file' in LOGGING['handlers']:
        del LOGGING['handlers']['performance_file']
    if 'webapp_json_file' in LOGGING['handlers']:
        del LOGGING['handlers']['webapp_json_file']

# MEDIA FILE CONFIGURATION
# Configurable storage backend (local filesystem or Google Cloud Storage)

# Google Cloud Storage Configuration
# USE_GCS_STORAGE - now using FEATURE_FLAGS['USE_GCS_STORAGE']
GCS_BUCKET_NAME = env('GCS_BUCKET_NAME')
GCS_PROJECT_ID = env('GCS_PROJECT_ID')
GCS_CREDENTIALS_PATH = env('GCS_CREDENTIALS_PATH')
GCS_LOCATION = env('GCS_LOCATION')

# Set up GCS credentials if path is provided
if GCS_CREDENTIALS_PATH and os.path.exists(GCS_CREDENTIALS_PATH):
    # Set the Google Application Credentials environment variable
    # This is the standard way for Google libraries to find credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GCS_CREDENTIALS_PATH

# Storage configuration - separate logic for media vs static files
if DEBUG:
    # DEVELOPMENT MODE - Always serve static files locally, media files configurable
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    
    if FEATURE_FLAGS['USE_GCS_STORAGE']:
        # Development with GCS media but local static files
        MEDIA_URL = f'https://storage.googleapis.com/{GCS_BUCKET_NAME}/{GCS_LOCATION}/'
        STORAGES = {
            'default': {
                # Media files on GCS
                'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
                'OPTIONS': {
                    'bucket_name': GCS_BUCKET_NAME,
                    'project_id': GCS_PROJECT_ID,
                    'querystring_auth': False,
                    'location': GCS_LOCATION,
                }
            },
            'staticfiles': {
                # Static files served locally by Django
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            }
        }
    else:
        # Development with local media and static files
        MEDIA_ROOT = os.path.join(BASE_DIR, 'local_cdn', 'media')
        STORAGES = {
            'default': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
                'OPTIONS': {
                    'location': MEDIA_ROOT,
                    'base_url': MEDIA_URL,
                }
            },
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            }
        }
else:
    # PRODUCTION MODE - Check USE_GCS_STORAGE setting
    if FEATURE_FLAGS['USE_GCS_STORAGE']:
        # Both media and static files on GCS
        MEDIA_URL = f'https://storage.googleapis.com/{GCS_BUCKET_NAME}/{GCS_LOCATION}/'
        STATIC_URL = f'https://storage.googleapis.com/{GCS_BUCKET_NAME}/static/'
        
        STORAGES = {
            'default': {
                # Media files storage
                'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
                'OPTIONS': {
                    'bucket_name': GCS_BUCKET_NAME,
                    'project_id': GCS_PROJECT_ID,
                    'querystring_auth': False,
                    'location': GCS_LOCATION,
                }
            },
            'staticfiles': {
                # Static files storage (CSS, JS, admin files)
                'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
                'OPTIONS': {
                    'bucket_name': GCS_BUCKET_NAME,
                    'project_id': GCS_PROJECT_ID,
                    'querystring_auth': False,
                    'location': 'static',
                }
            }
        }
    else:
        # PRODUCTION MODE with local storage (staging/development)
        STATIC_URL = '/static/'
        MEDIA_URL = '/media/'
        MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
        
        STORAGES = {
            'default': {
                'BACKEND': 'django.core.files.storage.FileSystemStorage',
                'OPTIONS': {
                    'location': MEDIA_ROOT,
                    'base_url': MEDIA_URL,
                }
            },
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            }
        }

# Note: Media directories should be created by deployment process, not during settings import

# External service URLs for sys panel (optional)
EXTERNAL_DB_URL = env('EXTERNAL_DB_URL') if env('EXTERNAL_DB_URL') else None
EXTERNAL_INBUCKET_URL = env('EXTERNAL_INBUCKET_URL') if env('EXTERNAL_INBUCKET_URL') else None
EXTERNAL_MONITORING_URL = env('EXTERNAL_MONITORING_URL') if env('EXTERNAL_MONITORING_URL') else None
EXTERNAL_SENTRY_URL = env('EXTERNAL_SENTRY_URL') if env('EXTERNAL_SENTRY_URL') else None
EXTERNAL_LOKI_URL = env('EXTERNAL_LOKI_URL') if env('EXTERNAL_LOKI_URL') else None
EXTERNAL_GRAFANA_URL = env('EXTERNAL_GRAFANA_URL') if env('EXTERNAL_GRAFANA_URL') else None
EXTERNAL_RESEND_URL = env('EXTERNAL_RESEND_URL') if env('EXTERNAL_RESEND_URL') else None

# Site Domain Configuration
SITE_DOMAIN = env('SITE_DOMAIN', default='beryl3.localdomain')

# Application Activity Logging Configuration
# APPLICATION_ACTIVITY_LOGGING - now using FEATURE_FLAGS['APPLICATION_ACTIVITY_LOGGING']
