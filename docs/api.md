# API Reference

---

## RustFSStorage

The main storage backend for media files. Implements Django's `Storage` API backed by RustFS via boto3.

```python
from django_rustfs.storage import RustFSStorage

storage = RustFSStorage()
```

### Constructor

All `RUSTFS_*` settings can be passed as keyword arguments (without the prefix, lowercase):

```python
storage = RustFSStorage(
    endpoint_url="http://localhost:9000",
    access_key="your-key",
    secret_key="your-secret",
    bucket_name="my-bucket",
    auto_create_bucket=True,
    default_acl="private",
    presign_urls=True,
    location="uploads/",
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `endpoint_url` | `str` | `""` | RustFS server URL |
| `access_key` | `str` | `""` | Access key |
| `secret_key` | `str` | `""` | Secret key |
| `bucket_name` | `str` | `"django-media"` | Bucket name |
| `auto_create_bucket` | `bool` | `True` | Auto-create bucket |
| `custom_domain` | `str` | `""` | CDN domain |
| `secure_urls` | `bool` | `True` | Use HTTPS |
| `url_expiration` | `int` | `3600` | Presigned URL expiry |
| `default_acl` | `str` | `"private"` | Default ACL |
| `file_overwrite` | `bool` | `False` | Allow overwrites |
| `object_parameters` | `dict` | `{}` | Extra S3 params |
| `location` | `str` | `""` | Key prefix |
| `region` | `str` | `"us-east-1"` | AWS region |
| `presign_urls` | `bool` | `True` | Generate presigned URLs |

---

### Django Storage API

#### `_open(name, mode="rb")`

Open a file from storage.

```python
with storage.open("documents/readme.txt", "rb") as f:
    content = f.read()
```

#### `_save(name, content)`

Save a file to storage. Returns the final file name.

```python
from django.core.files.base import ContentFile

name = storage.save("documents/readme.txt", ContentFile(b"hello"))
```

#### `delete(name)`

Delete a file from storage.

```python
storage.delete("documents/readme.txt")
```

#### `exists(name)`

Check if a file exists.

```python
if storage.exists("documents/readme.txt"):
    print("File exists")
```

#### `size(name)`

Get file size in bytes.

```python
size = storage.size("documents/readme.txt")  # 1024
```

#### `url(name)`

Get the URL for a file. Generates a presigned URL for private files, or a direct URL for public files.

```python
url = storage.url("documents/readme.txt")
# "http://localhost:9000/my-bucket/documents/readme.txt?X-Amz-..."
```

#### `listdir(path="")`

List directories and files. Returns a tuple of `(directories, files)`.

```python
directories, files = storage.listdir("media")
# (["images", "docs"], ["root.txt"])
```

---

### RustFS-Specific Methods

#### `get_object_metadata(name)`

Get full metadata for an object.

```python
meta = storage.get_object_metadata("uploads/photo.jpg")
```

Returns:

| Key | Type | Description |
|---|---|---|
| `etag` | `str` | Object ETag |
| `last_modified` | `datetime` | Last modified timestamp |
| `content_type` | `str` | MIME type |
| `content_length` | `int` | Size in bytes |
| `storage_class` | `str` | Storage class (e.g., `"STANDARD"`) |
| `metadata` | `dict` | Custom metadata |
| `version_id` | `str` | Version ID |

#### `copy_object(source_name, dest_name)`

Copy an object within the same bucket.

```python
storage.copy_object("uploads/photo.jpg", "backups/photo-backup.jpg")
```

#### `get_presigned_post_url(name, expires_in=3600)`

Generate a presigned POST URL for direct browser uploads.

```python
result = storage.get_presigned_post_url("uploads/photo.jpg", expires_in=600)
# {
#     "url": "http://localhost:9000/my-bucket",
#     "fields": {
#         "key": "uploads/photo.jpg",
#         "AWSAccessKeyId": "...",
#         "policy": "...",
#         "signature": "..."
#     }
# }
```

#### `is_available()`

Check if the RustFS server is reachable.

```python
if storage.is_available():
    print("RustFS is healthy")
```

---

## RustFSStaticStorage

Storage backend for Django static files. Uses a separate bucket with `public-read` ACL by default.

```python
from django_rustfs.storage import RustFSStaticStorage

storage = RustFSStaticStorage()
```

### Defaults

| Setting | Value |
|---|---|
| `bucket_name` | `RUSTFS_STATIC_BUCKET_NAME` or `"django-static"` |
| `location` | `RUSTFS_STATIC_LOCATION` or `"static"` |
| `default_acl` | `"public-read"` |
| `presign_urls` | `False` |
| `file_overwrite` | `True` |

### Usage

```python
STORAGES = {
    "staticfiles": {
        "BACKEND": "django_rustfs.storage.RustFSStaticStorage",
    },
}
```

Or instantiate directly:

```python
storage = RustFSStaticStorage()
name = storage.save("css/app.css", ContentFile(b"body {}"))
url = storage.url("css/app.css")
# "http://localhost:9000/django-static/static/css/app.css"
```

---

## Exceptions

### RustFSError

Base exception for all RustFS storage errors.

```python
from django_rustfs.storage import RustFSError

try:
    storage.open("missing.txt")
except RustFSError as e:
    print(f"Storage error: {e}")
```

### RustFSBucketError

Raised when a bucket operation fails. Inherits from `RustFSError`.

```python
from django_rustfs.storage import RustFSBucketError
```
