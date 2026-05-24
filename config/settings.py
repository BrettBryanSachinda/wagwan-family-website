"""
Django settings for config project.
"""

from pathlib import Path
import dj_database_url
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ================================================================
# ENVIRONMENT VARIABLES
# Load from .env file if python-dotenv is installed.
# Run: pip install python-dotenv
# Then create a .env file in the project root (same folder as manage.py)
# ================================================================
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    pass  # dotenv not installed — use system env vars or defaults below

# ================================================================
# SECURITY
# ================================================================
SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,.onrender.com,wagwanfamily.co.zw,www.wagwanfamily.co.zw').split(',')

# ================================================================
# APPLICATIONS
# ================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'storages', # ADD THIS (Replaced Cloudinary)
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# ================================================================
# DATABASE
# ================================================================
# Check if we are running on Render's servers
IS_ON_RENDER = os.environ.get('RENDER') == 'true'

DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        # Enforce SSL only on Render, keep it off for local Windows development
        ssl_require=IS_ON_RENDER 
    )
}

# ================================================================
# PASSWORD VALIDATION
# ================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ================================================================
# INTERNATIONALISATION
# ================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Harare'
USE_I18N = True
USE_TZ = True

# ================================================================
# STATIC & MEDIA FILES
# ================================================================
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ================================================================
# SUPABASE S3 MEDIA STORAGE
# ================================================================
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('AWS_S3_ENDPOINT_URL')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')

# Ensure files aren't overwritten if they happen to share the exact same name
AWS_S3_FILE_OVERWRITE = False

# CRITICAL FIXES FOR SUPABASE:
AWS_S3_ADDRESSING_STYLE = 'path'
AWS_QUERYSTRING_AUTH = False

# THE MAGIC FIX: Force Django to use Supabase's specific public viewing URL format
if AWS_STORAGE_BUCKET_NAME:
    AWS_S3_CUSTOM_DOMAIN = f'gzlnhhhezabayboxregl.supabase.co/storage/v1/object/public/{AWS_STORAGE_BUCKET_NAME}'

# Tell Django to use this for all user-uploaded media (profile pics, etc.)
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# ================================================================
# AUTHENTICATION
# ================================================================
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'my_arsenal'
LOGOUT_REDIRECT_URL = 'home'

# ================================================================
# EMAIL CONFIGURATION
# ================================================================
# HOW TO SET UP:
# 1. Create a Gmail account for Wagwan Family (e.g. noreply@wagwanfamily.com or a Gmail)
# 2. Enable 2-Factor Authentication on that Google account
# 3. Go to: Google Account > Security > App Passwords
# 4. Generate an App Password for "Mail" — it will give you a 16-character code
# 5. Put that code in your .env file as EMAIL_HOST_PASSWORD
# 6. Never commit your .env file to git — add it to .gitignore

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Wagwan Family <wagwanfamilyhq@gmail.com>')
EMAIL_SUBJECT_PREFIX = '[Wagwan Family] '

# During development, if you haven't set up Gmail yet,
# uncomment the line below to print emails to the terminal instead:
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ================================================================
# DEFAULT PRIMARY KEY
# ================================================================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

