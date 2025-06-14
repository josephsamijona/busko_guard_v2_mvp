"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 5.2.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

import base64
import tempfile

from django.core.exceptions import ImproperlyConfigured

from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta
import dj_database_url

from django.utils.translation import gettext_lazy as _
from django.core.management.utils import get_random_secret_key

# Charger les variables d'environnement
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
SECRET_KEY = os.getenv('SECRET_KEY')
ENCRYPTION_KEY=os.getenv('ENCRYPTION_KEY')
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# Variable pour déterminer si on est en environnement de développement
IS_DEVELOPMENT = os.getenv('IS_DEVELOPMENT', 'False') 

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',') if os.getenv('ALLOWED_HOSTS') else []


# Application definition

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',  # WhiteNoise pour les fichiers statiques
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    # Applications tierces
    'corsheaders',
    'crispy_forms',
    'crispy_bootstrap5',
    'qr_code',
    'widget_tweaks',
    'storages',
    'import_export',
    'simple_history',
    'allauth',
    'allauth.account',
    #'allauth.socialaccount',
    
    # Sécurité et authentification avancée
    #'defender',
    #'django_otp',
    #'django_otp.plugins.otp_totp',
    #'django_otp.plugins.otp_static',
    
    # Vos applications
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # WhiteNoise pour les statiques
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Pour l'internationalisation
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    #'defender.middleware.DefenderMiddleware',  # Protection contre les attaques brute force
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / 'templates',
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                #'social_django.context_processors.backends',
                #'social_django.context_processors.login_redirect',
            ],
        },
    },
]
WSGI_APPLICATION = 'config.wsgi.application' 
AUTH_USER_MODEL = 'core.User'
# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Configuration de la base de données en fonction de l'environnement
if IS_DEVELOPMENT:
    # Utilisation de SQLite en développement
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Utilisation de MySQL en production
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('MYSQL_URL'),
            conn_max_age=600
        )
    }


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/
# Internationalization - Configuration pour Haïti
LANGUAGE_CODE = 'fr-ht'  # Français d'Haïti
TIME_ZONE = 'America/Port-au-Prince'  # Fuseau horaire de Port-au-Prince
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Langues disponibles
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
    ('ht', 'Kreyòl Ayisyen'),  # Créole haïtien
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Configuration du stockage des médias en fonction de l'environnement
if IS_DEVELOPMENT:
    # Stockage local des médias en développement
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }
else:
    # Configuration Backblaze B2 pour la production
    AWS_ACCESS_KEY_ID = os.getenv('B2_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('B2_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('B2_BUCKET_NAME')
    AWS_S3_ENDPOINT_URL = os.getenv('B2_ENDPOINT_URL')  # Gardé pour compatibilité
    AWS_S3_REGION_NAME = os.getenv('B2_REGION_NAME')

    # Configuration S3/B2
    AWS_DEFAULT_ACL = None
    AWS_BUCKET_ACL = None
    AWS_QUERYSTRING_AUTH = False  # False pour URLs publiques, True pour URLs présignées
    AWS_S3_FILE_OVERWRITE = False
    AWS_LOCATION = 'media'
    AWS_S3_SIGNATURE_VERSION = 's3v4'  # Gardé pour compatibilité

    # Configuration URL publique
    # Note: Le custom domain n'est utilisé que si AWS_QUERYSTRING_AUTH = False
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.backblazeb2.com'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_LOCATION}/'

    # Configuration moderne des storages
    # Utilise maintenant le storage B2 natif qui évite les problèmes de compatibilité
    STORAGES = {
        "default": {
            "BACKEND": "custom_storages.MediaStorage",  # Pointe vers le nouveau storage B2 natif
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        }
    }


# Configuration JWT pour l'API
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 900))),     # 15 min par défaut
    'REFRESH_TOKEN_LIFETIME': timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', 604800))), # 7 jours par défaut
    'ROTATE_REFRESH_TOKENS': True,                   # Rotation des tokens de rafraîchissement
    'BLACKLIST_AFTER_ROTATION': True,                # Blacklister les anciens tokens après rotation
    'UPDATE_LAST_LOGIN': False,                      # Ne pas mettre à jour last_login à chaque connexion
    
    'ALGORITHM': 'HS256',                            # Algorithme de signature
    'SIGNING_KEY': os.getenv('JWT_SECRET_KEY', SECRET_KEY),  # Clé de signature
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),                # Type d'en-tête d'authentification
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',        # Nom de l'en-tête d'authentification
    'USER_ID_FIELD': 'id',                           # Champ pour identifier l'utilisateur
    'USER_ID_CLAIM': 'user_id',                      # Claim dans le token pour l'ID de l'utilisateur
}

# CORS Settings
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',') if os.getenv('CORS_ALLOWED_ORIGINS') else []
CORS_ALLOW_CREDENTIALS = os.getenv('CORS_ALLOW_CREDENTIALS', 'True') == 'True'
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if os.getenv('CSRF_TRUSTED_ORIGINS') else []

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
QUOTE_NOTIFICATION_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
CONTACT_NOTIFICATION_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

# Configuration de Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# Login/Logout URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_URL = 'logout'
LOGOUT_REDIRECT_URL = 'login'
# Paramètres de session
SESSION_COOKIE_AGE = 1209600  # 2 semaines en secondes (pour "Se souvenir de moi")
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Session expirée à la fermeture du navigateur par défaut

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Configuration de REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',  # JWT pour l'API
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}