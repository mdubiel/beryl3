from pathlib import Path
import os

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT_DIR = Path(BASE_DIR).parent / "webapp" / "web"

# Initialize environ
env = environ.Env(
    # set casting and default value for DEBUG
    DEBUG=(bool, False),
    # Email settings
    USE_INBUCKET=(bool, False),
    EMAIL_HOST=(str, 'localhost'), # Default to localhost if not in docker
    INBUCKET_SMTP_PORT=(int, 2500),
    DEFAULT_FROM_EMAIL=(str, 'webmaster@localhost')
)

# Read variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1'])

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': env('PG_DB'),
        'USER': env('PG_USER'),
        'PASSWORD': env('PG_PASSWORD'),
        'HOST': env('PG_HOST'),
        'PORT': env.int('PG_PORT'),  
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
    'lucide',
    'nanoid_field',
    'widget_tweaks',
    'core.apps.CoreConfig',
    'web.apps.WebConfig',
    'api.apps.ApiConfig',
    

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
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
            ],
        },
    },
]


if DEBUG:
    INSTALLED_APPS.append("django_browser_reload")
    MIDDLEWARE.append("django_browser_reload.middleware.BrowserReloadMiddleware")

WSGI_APPLICATION = 'webapp.wsgi.application'


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
# this should be done only for local files delivery
# production should be on GCS/S3
#STATIC_ROOT = BASE_DIR / "tmp" / "static"
#logger.debug(f"STATIC_ROOT = {STATIC_ROOT}")

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login settings
#LOGIN_REDIRECT_URL = 'index'  # Redirect to index after login
#LOGOUT_REDIRECT_URL = 'index'  # Redirect to index after logout
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

# ==============================================================================
# EMAIL CONFIGURATION
# ==============================================================================

# Check for the development flag in your environment variables.
# os.getenv('USE_INBUCKET', 'False') == 'True' is a safe way to read a boolean
# from an environment variable.

if env('USE_INBUCKET'):
    # --- DEVELOPMENT EMAIL SETTINGS (using Inbucket) ---
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = env('EMAIL_HOST')
    EMAIL_PORT = env('INBUCKET_SMTP_PORT') # Reads the SMTP port from .env
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_USE_TLS = False

else:
    # --- PRODUCTION EMAIL SETTINGS ---
    # In production, you would have different env variables for a real service
    # e.g., SENDGRID_API_KEY = env('SENDGRID_API_KEY')
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Default from email is set for both environments from .env
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

