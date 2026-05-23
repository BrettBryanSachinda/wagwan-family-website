"""
Django settings for config project.
"""

from pathlib import Path
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
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-^36=lm9ntfyjp-tzm5tks!8yla8)56a%=c$q%6i5i7k=dz4h4_'
)

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

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
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'WagwanFamily'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
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
STATIC_ROOT = BASE_DIR / 'staticfiles'  # needed for collectstatic in production

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

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