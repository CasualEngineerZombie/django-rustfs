# django-rustfs

A **plug-and-play Django storage backend** for [RustFS](https://rustfs.com/) — the high-performance, S3-compatible object storage built in Rust.

```bash
pip install django-rustfs
```

---

## Why django-rustfs?

You can already use RustFS with Django today via `django-storages` + `boto3`. So why another package?

| | **django-storages + boto3** | **django-rustfs** |
|---|---|---|
| **Configuration** | 10+ AWS-named settings (`AWS_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_SIGNATURE_VERSION`, `AWS_S3_FILE_OVERWRITE`, `AWS_DEFAULT_ACL`, `AWS_S3_VERIFY`, `AWS_S3_MAX_MEMORY_SIZE`...) | **5 clean, RustFS-branded settings** (`RUSTFS_ENDPOINT`, `RUSTFS_ACCESS_KEY`, `RUSTFS_SECRET_KEY`, `RUSTFS_BUCKET_NAME`) |
| **Scope** | General-purpose (S3, Azure, GCP, FTP, SFTP...) | **Built exclusively for RustFS** — nothing more, nothing less |
| **Bucket setup** | Manual — create buckets via RustFS console or CLI | **`python manage.py rustfs_init_buckets`** — creates buckets automatically |
| **Health checks** | None built-in | **`python manage.py rustfs_health`** — connectivity, auth, upload/download roundtrip |
| **Static files** | Requires custom subclass | **`RustFSStaticStorage`** included with `public-read` defaults |
| **Dependencies** | `django-storages`, `boto3` (~2 packages to configure) | `boto3` only (~1 direct dependency) |
| **Codebase** | ~1,500 lines for S3 backend (handles many edge cases for AWS) | **~400 lines focused on RustFS** — lean, readable, auditable |

> **Bottom line:** If you're using RustFS, `django-rustfs` removes the mental overhead of pretending you're configuring AWS S3.

---

## Quick Start

### 1. Install

```bash
pip install django-rustfs
```

### 2. Configure Django Settings

```python
# settings.py

INSTALLED_APPS = [
    # ... your apps
    "django_rustfs",
]

# RustFS connection (required)
RUSTFS_ENDPOINT = "http://localhost:9000"      # Your RustFS server URL
RUSTFS_ACCESS_KEY = "your-access-key"          # RustFS access key
RUSTFS_SECRET_KEY = "your-secret-key"          # RustFS secret key

# Bucket configuration (optional — defaults shown)
RUSTFS_BUCKET_NAME = "django-media"            # Media files bucket
RUSTFS_STATIC_BUCKET_NAME = "django-static"    # Static files bucket
RUSTFS_AUTO_CREATE_BUCKET = True               # Auto-create buckets on first use

# Use RustFS for media files
DEFAULT_FILE_STORAGE = "django_rustfs.storage.RustFSStorage"
```

### 3. Initialize Buckets (Optional but Recommended)

```bash
python manage.py rustfs_init_buckets
```

This creates your media and static buckets with the correct permissions.

### 4. Health Check

```bash
python manage.py rustfs_health
```

Checks connectivity, authentication, and runs an upload/download roundtrip test.

---

## Full Configuration Reference

All settings use the `RUSTFS_` prefix for clarity and to avoid conflicts.

### Required Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RUSTFS_ENDPOINT` | *(none)* | RustFS server URL, e.g. `"http://localhost:9000"` |
| `RUSTFS_ACCESS_KEY` | *(none)* | RustFS access key (or `AWS_ACCESS_KEY_ID` from RustFS console) |
| `RUSTFS_SECRET_KEY` | *(none)* | RustFS secret key |

### Bucket Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RUSTFS_BUCKET_NAME` | `"django-media"` | Default bucket for media files |
| `RUSTFS_STATIC_BUCKET_NAME` | `"django-static"` | Bucket for static files (used by `RustFSStaticStorage`) |
| `RUSTFS_AUTO_CREATE_BUCKET` | `True` | Automatically create buckets if they don't exist |

### URL & Access Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RUSTFS_CUSTOM_DOMAIN` | `""` | CDN domain, e.g. `"cdn.example.com"` |
| `RUSTFS_SECURE_URLS` | `True` | Use HTTPS in generated URLs |
| `RUSTFS_URL_EXPIRATION` | `3600` | Presigned URL expiry in seconds |
| `RUSTFS_DEFAULT_ACL` | `"private"` | Default ACL for uploaded objects (`private`, `public-read`) |
| `RUSTFS_FILE_OVERWRITE` | `False` | Allow overwriting existing files |

### File Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RUSTFS_LOCATION` | `""` | Prefix path for all uploads, e.g. `"media/"` |
| `RUSTFS_OBJECT_PARAMETERS` | `{}` | Extra parameters passed to boto3 `put_object()` |

### Connection Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `RUSTFS_REGION` | `"us-east-1"` | Region name (RustFS uses `us-east-1` by default) |
| `RUSTFS_USE_SSL` | `False` | Use SSL/TLS for connections |
| `RUSTFS_VERIFY_SSL` | `True` | Verify SSL certificates |

---

## Static Files Configuration

Django 4.2+ uses the `STORAGES` dictionary:

```python
# settings.py

STORAGES = {
    "default": {
        "BACKEND": "django_rustfs.storage.RustFSStorage",
        "OPTIONS": {
            "bucket_name": "my-media-bucket",
        },
    },
    "staticfiles": {
        "BACKEND": "django_rustfs.storage.RustFSStaticStorage",
        "OPTIONS": {
            "bucket_name": "my-static-bucket",
            "location": "static/",
        },
    },
}
```

For Django < 4.2:

```python
DEFAULT_FILE_STORAGE = "django_rustfs.storage.RustFSStorage"
STATICFILES_STORAGE = "django_rustfs.storage.RustFSStaticStorage"
```

`RustFSStaticStorage` automatically uses `public-read` ACL so your CSS/JS/images are directly accessible.

---

## Management Commands

### `rustfs_health`

Check connectivity, authentication, and run an upload/download roundtrip test:

```bash
python manage.py rustfs_health
# 🔍 Checking RustFS health...
#    Endpoint: http://localhost:9000
#    Bucket:   django-media
# 
#   ✅ Bucket 'django-media' is accessible
#      Response time: 12.3ms
#   ✅ List operation works (0 objects visible)
# 
#   🧪 Running upload/download roundtrip test...
#   ✅ Upload/download roundtrip successful
# 
# ✅ RustFS health check completed successfully!
```

Options:
- `--bucket <name>` — Check a specific bucket
- `--verbose` — Show detailed response information

### `rustfs_init_buckets`

Create and configure RustFS buckets:

```bash
python manage.py rustfs_init_buckets
# 🪣 Initializing RustFS buckets...
# 
#   📦 Bucket: django-media
#      Status: Created ✓
#      Policy: private (default)
# 
#   📦 Bucket: django-static
#      Status: Created ✓
#      Policy: public-read ✓
# 
# ✅ All done: 2 bucket(s) ready to use
```

Options:
- `--bucket <name>` — Create only a specific bucket
- `--public` — Make the bucket public-readable
- `--skip-static` — Don't create the static files bucket
- `--dry-run` — Preview what would be done

---

## Advanced Usage

### Per-Field Storage Configuration

Configure different buckets for different model fields:

```python
from django.db import models
from django_rustfs.storage import RustFSStorage

# Private storage for user documents
private_storage = RustFSStorage(
    bucket_name="user-documents",
    default_acl="private",
)

# Public storage for avatars
public_storage = RustFSStorage(
    bucket_name="public-avatars",
    default_acl="public-read",
    presign_urls=False,  # Direct URLs, no presigning needed
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

# Generate a presigned POST URL for the browser
post_data = storage.get_presigned_post_url(
    name="uploads/user123/photo.jpg",
    expires_in=600,  # 10 minutes
)

# Return this to your frontend:
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

Access RustFS-specific metadata like ETag, version ID, and storage class:

```python
storage = RustFSStorage()
meta = storage.get_object_metadata("uploads/photo.jpg")

print(meta["etag"])           # "d41d8cd98f00b204e9800998ecf8427e"
print(meta["content_length"]) # 2048
print(meta["storage_class"])  # "STANDARD"
print(meta["version_id"])     # "uuid-v1"
```

### Copy Objects

Copy files within RustFS without downloading them:

```python
storage.copy_object("uploads/photo.jpg", "backups/photo-backup.jpg")
```

---

## Comparison: django-rustfs vs. django-storages + boto3

### Configuration Verbosity

**django-storages (S3 backend):**
```python
# settings.py
AWS_ACCESS_KEY_ID = "your-key"
AWS_SECRET_ACCESS_KEY = "your-secret"
AWS_STORAGE_BUCKET_NAME = "my-bucket"
AWS_S3_ENDPOINT_URL = "http://localhost:9000"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "private"
AWS_S3_VERIFY = True
AWS_S3_USE_SSL = False
AWS_S3_REGION_NAME = "us-east-1"
AWS_S3_OBJECT_PARAMETERS = {}
AWS_QUERYSTRING_AUTH = True
AWS_S3_CUSTOM_DOMAIN = ""
# ... and more

DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
```

**django-rustfs:**
```python
# settings.py
RUSTFS_ENDPOINT = "http://localhost:9000"
RUSTFS_ACCESS_KEY = "your-key"
RUSTFS_SECRET_KEY = "your-secret"
RUSTFS_BUCKET_NAME = "my-bucket"

DEFAULT_FILE_STORAGE = "django_rustfs.storage.RustFSStorage"
```

### Runtime Behavior

| Feature | django-storages | django-rustfs |
|---------|----------------|---------------|
| Bucket auto-creation | No (fails if bucket missing) | Yes (on by default) |
| Built-in health check | No | `rustfs_health` command |
| Bucket initialization | Manual via CLI/console | `rustfs_init_buckets` command |
| Presigned POST for direct uploads | Requires manual implementation | `get_presigned_post_url()` method |
| Object metadata access | Raw boto3 response | Structured `get_object_metadata()` |
| Copy within storage | Manual boto3 call | `copy_object()` method |
| Static files setup | Custom subclass needed | `RustFSStaticStorage` included |

---

## How It Works

django-rustfs uses **boto3** to communicate with RustFS. RustFS is fully S3-compatible, so the AWS SDK works out of the box — we just wrap it in a cleaner API:

```
┌─────────────┐      ┌─────────────────┐      ┌─────────────┐
│   Django    │──────│  django-rustfs  │──────│    boto3    │
│             │      │  (this package) │      │  (AWS SDK)  │
└─────────────┘      └─────────────────┘      └──────┬──────┘
                                                      │
                                               HTTP/HTTPS
                                                      │
                                                ┌─────────┐
                                                │  RustFS │
                                                │  Server │
                                                └─────────┘
```

---

## Requirements

- Python 3.9+
- Django 4.2+
- boto3 1.28+

---

## Roadmap

- [ ] **RustFS-native features** — Expose RustFS-specific capabilities (bucket replication, lifecycle rules, event notifications) as they stabilize beyond beta
- [ ] **Django Admin integration** — View bucket contents, object metadata, and storage statistics in Django admin
- [ ] **Management commands** — `sync_to_rustfs`, `sync_from_rustfs`, `clean_orphaned`
- [ ] **Async support** — `aioboto3`-based async storage backend for ASGI deployments
- [ ] **URL caching** — Cache presigned URLs with Django's cache framework to reduce S3 API calls
- [ ] **Multipart upload** — Support large file uploads with resumable multipart uploads
- [ ] **Streaming responses** — Memory-efficient `FileResponse` wrapper for serving large files

---

## License

Apache 2.0 License — see [LICENSE](LICENSE) file.

---

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

```bash
git clone https://github.com/CasualEngineerZombie/django-rustfs
cd django-rustfs
pip install -e ".[dev]"
pytest
```

---

Built with ❤️ for the RustFS community.
