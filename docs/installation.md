# Installation

## Install from PyPI

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

---

## Setup

### Step 1 — Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_rustfs",
]
```

### Step 2 — Configure connection

```python
# settings.py
RUSTFS_ENDPOINT = "http://localhost:9000"
RUSTFS_ACCESS_KEY = "your-access-key"
RUSTFS_SECRET_KEY = "your-secret-key"
```

!!! tip "Tip"
    You only need these three settings to get started. All other settings have sensible defaults.

### Step 3 — Set as default storage

=== "Django 4.2+ (recommended)"

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

=== "Django < 4.2"

    ```python
    DEFAULT_FILE_STORAGE = "django_rustfs.storage.RustFSStorage"
    STATICFILES_STORAGE = "django_rustfs.storage.RustFSStaticStorage"
    ```

### Step 4 — Initialize buckets

```bash
python manage.py rustfs_init_buckets
```

### Step 5 — Verify everything works

```bash
python manage.py rustfs_health
```

!!! success "Expected output"
    ```
    🔍 Checking RustFS health...
       Endpoint: http://localhost:9000
       Bucket:   django-media

      ✅ Bucket 'django-media' is accessible
         Response time: 12.3ms
      ✅ List operation works (0 objects visible)

      🧪 Running upload/download roundtrip test...
      ✅ Upload/download roundtrip successful

    ✅ RustFS health check completed successfully!
    ```
