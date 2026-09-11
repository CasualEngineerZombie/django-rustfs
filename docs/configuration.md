# Configuration

All settings use the `RUSTFS_` prefix.

## Required Settings

| Setting | Description | Example |
|---|---|---|
| `RUSTFS_ENDPOINT` | RustFS server URL | `"http://localhost:9000"` |
| `RUSTFS_ACCESS_KEY` | RustFS access key | `"your-access-key"` |
| `RUSTFS_SECRET_KEY` | RustFS secret key | `"your-secret-key"` |

## Optional Settings

### Bucket Settings

| Setting | Default | Description |
|---|---|---|
| `RUSTFS_BUCKET_NAME` | `"django-media"` | Default bucket for media files |
| `RUSTFS_STATIC_BUCKET_NAME` | `"django-static"` | Bucket for static files |
| `RUSTFS_AUTO_CREATE_BUCKET` | `True` | Auto-create buckets on first use |

### URL Generation

| Setting | Default | Description |
|---|---|---|
| `RUSTFS_CUSTOM_DOMAIN` | `""` | CDN domain (e.g., `"cdn.example.com"`) |
| `RUSTFS_SECURE_URLS` | `True` | Use HTTPS in generated URLs |
| `RUSTFS_URL_EXPIRATION` | `3600` | Presigned URL expiry in seconds |

### File Behavior

| Setting | Default | Description |
|---|---|---|
| `RUSTFS_DEFAULT_ACL` | `"private"` | Default ACL (`"private"`, `"public-read"`) |
| `RUSTFS_PUBLIC_ACL` | `"public-read"` | ACL for public files |
| `RUSTFS_FILE_OVERWRITE` | `False` | Allow overwriting existing files |
| `RUSTFS_OBJECT_PARAMETERS` | `{}` | Extra parameters passed to S3 `put_object` |
| `RUSTFS_LOCATION` | `""` | Prefix path for uploads (e.g., `"media/"`) |
| `RUSTFS_STATIC_LOCATION` | `""` | Prefix path for static files |

### Connection

| Setting | Default | Description |
|---|---|---|
| `RUSTFS_REGION` | `"us-east-1"` | AWS region name |
| `RUSTFS_USE_SSL` | `False` | Use SSL/TLS for connections |
| `RUSTFS_VERIFY_SSL` | `True` | Verify SSL certificates |
| `RUSTFS_MAX_POOL_CONNECTIONS` | `10` | Max boto3 connection pool size |
| `RUSTFS_CONNECT_TIMEOUT` | `5` | Connection timeout in seconds |
| `RUSTFS_READ_TIMEOUT` | `30` | Read timeout in seconds |

### Performance

| Setting | Default | Description |
|---|---|---|
| `RUSTFS_PRESIGN_URLS` | `True` | Generate presigned URLs for private objects |
| `RUSTFS_REDUCED_REDUNDANCY` | `False` | Use reduced redundancy storage |
| `RUSTFS_ENCRYPTION` | `False` | Enable server-side encryption |

## Example Configuration

```python
# settings.py

# Required
RUSTFS_ENDPOINT = "http://localhost:9000"
RUSTFS_ACCESS_KEY = "your-access-key"
RUSTFS_SECRET_KEY = "your-secret-key"

# Buckets
RUSTFS_BUCKET_NAME = "my-media"
RUSTFS_STATIC_BUCKET_NAME = "my-static"
RUSTFS_AUTO_CREATE_BUCKET = True

# URLs
RUSTFS_CUSTOM_DOMAIN = "cdn.example.com"
RUSTFS_SECURE_URLS = True
RUSTFS_URL_EXPIRATION = 3600

# File behavior
RUSTFS_DEFAULT_ACL = "private"
RUSTFS_FILE_OVERWRITE = False
RUSTFS_LOCATION = "uploads/"

# Connection
RUSTFS_REGION = "us-east-1"
RUSTFS_USE_SSL = False
```

## Per-Instance Overrides

You can override settings when instantiating the storage backend directly:

```python
from django_rustfs.storage import RustFSStorage

private_storage = RustFSStorage(
    endpoint_url="http://localhost:9000",
    access_key="key",
    secret_key="secret",
    bucket_name="private-bucket",
    default_acl="private",
    presign_urls=True,
)
```
