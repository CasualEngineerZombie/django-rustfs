<div align="center">

# django-rustfs

Django storage backend for RustFS; an S3-compatible object storage server.

[![PyPI version](https://badge.fury.io/py/django-rustfs.svg)](https://badge.fury.io/py/django-rustfs)
[![Python versions](https://img.shields.io/pypi/pyversions/django-rustfs.svg)](https://pypi.org/project/django-rustfs/)
[![Django versions](https://img.shields.io/badge/django-4.2%20%7C%205.0%20%7C%205.1%20%7C%205.2%20%7C%206.1-blue.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Tests](https://github.com/CasualEngineerZombie/django-rustfs/workflows/Python%20package/badge.svg)](https://github.com/CasualEngineerZombie/django-rustfs/actions)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen.svg)](https://github.com/CasualEngineerZombie/django-rustfs)

```bash
pip install django-rustfs
```

[Installation](#installation) - [Quick Start](#quick-start) - [Configuration](#configuration) - [Advanced Usage](#advanced-usage) - [Contributing](#contributing)

</div>

---

## Why django-rustfs?

You can already use RustFS with Django via `django-storages` + `boto3`. So why another package?

### The Problem

**django-storages** is great for AWS S3, but using it with RustFS means:
- Pretending RustFS is AWS (`AWS_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`...)
- Configuring 10+ settings you do not need
- No built-in health checks or bucket setup tools
- Writing custom code for static files

### The Solution

**django-rustfs** is purpose-built for RustFS:

| Feature | django-storages + boto3 | django-rustfs |
|---|---|---|
| **Configuration** | 10+ AWS-branded settings | **4 clean settings** (`RUSTFS_ENDPOINT`, `RUSTFS_ACCESS_KEY`, `RUSTFS_SECRET_KEY`, `RUSTFS_BUCKET_NAME`) |
| **Scope** | General-purpose (S3, Azure, GCP...) | **Built exclusively for RustFS** |
| **Bucket setup** | Manual CLI/console | **`python manage.py rustfs_init_buckets`** |
| **Health checks** | None | **`python manage.py rustfs_health`** |
| **Static files** | Custom subclass required | **`RustFSStaticStorage` included** |
| **Dependencies** | `django-storages` + `boto3` | `boto3` only |
| **Codebase** | ~1,500 lines | **~400 lines focused on RustFS** |

> **Bottom line:** If you are using RustFS, `django-rustfs` removes the mental overhead of pretending you are configuring AWS S3.

---

## Installation

```bash
pip install django-rustfs
```

**Requirements:**
- Python 3.9+
- Django 4.2 through 6.1
- boto3 1.28+

### Django compatibility

| Django | Python |
|---|---|
| 4.2 | 3.9 - 3.12 |
| 5.0 | 3.10 - 3.12 |
| 5.1 | 3.10 - 3.13 |
| 5.2 | 3.10 - 3.14 |
| 6.1 | 3.12 - 3.14 |

Django 6.1 support is tested against Python 3.12, 3.13, and 3.14 in CI.

---

## Quick Start

### 1. Add to Installed Apps

```python
# settings.py

INSTALLED_APPS = [
    # ... your apps
    "django_rustfs",
]
```

### 2. Configure Connection

```python
# settings.py

# Required
RUSTFS_ENDPOINT = "http://localhost:9000"
RUSTFS_ACCESS_KEY = "your-access-key"
RUSTFS_SECRET_KEY = "your-secret-key"

# Optional (defaults shown)
RUSTFS_BUCKET_NAME = "django-media"
RUSTFS_AUTO_CREATE_BUCKET = True
```

### 3. Set as Default Storage

**Django 4.2+** (recommended):
```python
# settings.py

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

Output:
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

---

## Configuration

All settings use the `RUSTFS_` prefix for clarity.

### Required Settings

| Setting | Description |
|---------|-------------|
| `RUSTFS_ENDPOINT` | RustFS server URL, e.g. `"http://localhost:9000"` |
| `RUSTFS_ACCESS_KEY` | RustFS access key |
| `RUSTFS_SECRET_KEY` | RustFS secret key |

### Optional Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RUSTFS_BUCKET_NAME` | `"django-media"` | Default bucket for media files |
| `RUSTFS_STATIC_BUCKET_NAME` | `"django-static"` | Bucket for static files |
| `RUSTFS_AUTO_CREATE_BUCKET` | `True` | Auto-create buckets on first use |
| `RUSTFS_CUSTOM_DOMAIN` | `""` | CDN domain, e.g. `"cdn.example.com"` |
| `RUSTFS_SECURE_URLS` | `True` | Use HTTPS in generated URLs |
| `RUSTFS_URL_EXPIRATION` | `3600` | Presigned URL expiry (seconds) |
| `RUSTFS_DEFAULT_ACL` | `"private"` | Default ACL (`private`, `public-read`) |
| `RUSTFS_FILE_OVERWRITE` | `False` | Allow overwriting existing files |
| `RUSTFS_LOCATION` | `""` | Prefix path for uploads, e.g. `"media/"` |
| `RUSTFS_REGION` | `"us-east-1"` | Region name |
| `RUSTFS_USE_SSL` | `False` | Use SSL/TLS for connections |
| `RUSTFS_VERIFY_SSL` | `True` | Verify SSL certificates |

---

### HTTP/HTTPS and TLS configuration

The connection protocol has one source of truth: `RUSTFS_USE_SSL`. It controls the boto3 client and the protocol used for direct URLs. `RUSTFS_ENDPOINT` may include a scheme, but when it does, that scheme must match `RUSTFS_USE_SSL`.

Supported configurations:

| `RUSTFS_ENDPOINT` | `RUSTFS_USE_SSL` | Result |
|---|---:|---|
| `http://localhost:9000` | `False` | HTTP |
| `https://localhost:9443` | `True` | HTTPS |
| `localhost:9000` | `False` | HTTP (scheme added) |
| `localhost:9443` | `True` | HTTPS (scheme added) |

Custom ports are preserved. Contradictory combinations such as an HTTPS endpoint with `RUSTFS_USE_SSL=False`, or an HTTP endpoint with `RUSTFS_USE_SSL=True`, are rejected with `ImproperlyConfigured`.

`RUSTFS_VERIFY_SSL` controls TLS certificate verification passed to boto3. It defaults to `True`. Set it to `False` only when certificate verification is intentionally disabled, such as when using a development certificate that is not trusted by the system.

`RUSTFS_SECURE_URLS` does not override the connection protocol. Direct and custom-domain URLs use the protocol resolved from `RUSTFS_ENDPOINT` and `RUSTFS_USE_SSL`, while presigned URLs are generated by boto3 for the same configured endpoint.

---

## Management Commands

### `rustfs_health`

Check connectivity, authentication, and run an upload/download roundtrip test:

```bash
python manage.py rustfs_health
python manage.py rustfs_health --bucket=my-bucket
```

### `rustfs_init_buckets`

Create and configure RustFS buckets:

```bash
python manage.py rustfs_init_buckets              # Create all buckets
python manage.py rustfs_init_buckets --bucket=X   # Create specific bucket
python manage.py rustfs_init_buckets --public     # Make buckets public
python manage.py rustfs_init_buckets --dry-run    # Preview changes
```

---

## Advanced Usage

### Per-Field Storage Configuration

Configure different buckets for different model fields:

```python
from django.db import models
from django_rustfs.storage import RustFSStorage

# Private storage for documents
private_storage = RustFSStorage(
    bucket_name="user-documents",
    default_acl="private",
)

# Public storage for avatars
public_storage = RustFSStorage(
    bucket_name="public-avatars",
    default_acl="public-read",
    presign_urls=False,
)


class UserProfile(models.Model):
    avatar = models.ImageField(storage=public_storage, upload_to="avatars/")
    documents = models.FileField(storage=private_storage, upload_to="docs/")
```

### Direct Browser Uploads (Presigned POST)

Let browsers upload directly to RustFS without going through your Django server:

```python
from django_rustfs.storage import RustFSStorage

storage = RustFSStorage()
post_data = storage.get_presigned_post_url(
    name="uploads/user123/photo.jpg",
    expires_in=600,
)

# Returns:
# {
#   "url": "http://localhost:9000/django-media",
#   "fields": {
#     "key": "uploads/user123/photo.jpg",
#     "AWSAccessKeyId": "...",
#     "policy": "...",
#     "signature": "..."
#   }
# }
```

### Object Metadata Access

```python
storage = RustFSStorage()
meta = storage.get_object_metadata("uploads/photo.jpg")

print(meta["etag"])  # "d41d8cd98f00b204e9800998ecf8427e"
print(meta["content_length"])  # 2048
print(meta["storage_class"])  # "STANDARD"
print(meta["version_id"])  # "uuid-v1"
```

### Copy Objects

```python
storage.copy_object("uploads/photo.jpg", "backups/photo-backup.jpg")
```

---

## Architecture

```
┌─────────────┐      ┌─────────────────┐      ┌─────────────┐
│   Django    │──────│  django-rustfs  │──────│    boto3    │
│             │      │  (this package) │      │  (AWS SDK)  │
└─────────────┘      └────────┬────────┘      └──────┬──────┘
                              │                       │
                              └────── HTTP/HTTPS ─────┘
                                      │
                                ┌─────────────┐
                                │    RustFS    │
                                │    Server    │
                                └─────────────┘
```

django-rustfs uses **boto3** to communicate with RustFS. RustFS is fully S3-compatible, so the AWS SDK works out of the box - we just wrap it in a purpose-built API.

---

## Development

### Setup

```bash
git clone https://github.com/CasualEngineerZombie/django-rustfs.git
cd django-rustfs
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=django_rustfs --cov-report=html
```

### Code Quality

```bash
ruff check .          # Linting
ruff format .         # Formatting
mypy django_rustfs    # Type checking
```

### Project Structure

```
django-rustfs/
├── django_rustfs/          # Main package
│   ├── storage.py          # Core storage backend
│   ├── conf.py             # Settings configuration
│   └── management/         # Management commands
│       └── commands/
│           ├── rustfs_health.py
│           └── rustfs_init_buckets.py
├── tests/                  # Test suite
├── .github/workflows/      # CI/CD
├── pyproject.toml          # Package config
└── README.md               # This file
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start for contributors:
```bash
git clone https://github.com/CasualEngineerZombie/django-rustfs.git
cd django-rustfs
pip install -e ".[dev]"
pytest
```

---

## Roadmap

- [ ] **RustFS-native features** - Expose RustFS-specific capabilities (replication, lifecycle rules, event notifications)
- [ ] **Django Admin integration** - View bucket contents and storage statistics
- [ ] **Management commands** - `sync_to_rustfs`, `sync_from_rustfs`, `clean_orphaned`
- [ ] **Async support** - `aioboto3`-based async storage backend
- [ ] **URL caching** - Cache presigned URLs with Django's cache framework
- [ ] **Multipart upload** - Resumable multipart uploads for large files
- [ ] **Streaming responses** - Memory-efficient `FileResponse` wrapper

---

## License

Apache 2.0 - see [LICENSE](LICENSE) file.
