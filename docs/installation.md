# Installation

## pip install

```bash
pip install django-rustfs
```

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.9+ |
| Django | 4.2 – 6.1 |
| boto3 | 1.28+ |

## Django Compatibility

| Django | Python |
|---|---|
| 4.2 | 3.9 – 3.12 |
| 5.0 | 3.10 – 3.12 |
| 5.1 | 3.10 – 3.13 |
| 5.2 | 3.10 – 3.14 |
| 6.1 | 3.12 – 3.14 |

## Setup

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_rustfs",
]
```

### 2. Configure Connection

```python
# settings.py
RUSTFS_ENDPOINT = "http://localhost:9000"
RUSTFS_ACCESS_KEY = "your-access-key"
RUSTFS_SECRET_KEY = "your-secret-key"
```

### 3. Set as Default Storage

**Django 4.2+** (recommended):

```python
STORAGES = {
    "default": {
        "BACKEND": "django_rustfs.storage.RustFSStorage",
    },
    "staticfiles": {
        "BACKEND": "django_rustfs.storage.RustFSStaticStorage",
    },
}
```

**Django < 4.2**:

```python
DEFAULT_FILE_STORAGE = "django_rustfs.storage.RustFSStorage"
STATICFILES_STORAGE = "django_rustfs.storage.RustFSStaticStorage"
```

### 4. Initialize Buckets

```bash
python manage.py rustfs_init_buckets
```

### 5. Verify Everything Works

```bash
python manage.py rustfs_health
```
