"""
Django settings for running tests.
"""

import os

# Build paths inside the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-rustfs-test-secret-key-not-for-production"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "django.contrib.staticfiles",
    "django_rustfs",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "tests.urls"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# RustFS test settings
RUSTFS_ENDPOINT = "http://localhost:9000"
RUSTFS_ACCESS_KEY = "test-access-key"
RUSTFS_SECRET_KEY = "test-secret-key"
RUSTFS_BUCKET_NAME = "test-bucket"
RUSTFS_AUTO_CREATE_BUCKET = True
RUSTFS_REGION = "us-east-1"
