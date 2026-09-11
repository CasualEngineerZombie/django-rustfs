# django-rustfs

Django storage backend for **RustFS** — an S3-compatible object storage server built in Rust.

---

## Why django-rustfs?

You can use RustFS with Django via `django-storages` + `boto3`, but that means pretending RustFS is AWS S3 with 10+ `AWS_*` settings. **django-rustfs** is purpose-built for RustFS with clean, branded configuration.

| Feature | django-storages + boto3 | django-rustfs |
|---|---|---|
| **Configuration** | 10+ AWS-branded settings | 4 clean `RUSTFS_*` settings |
| **Bucket setup** | Manual CLI/console | `rustfs_init_buckets` command |
| **Health checks** | None | `rustfs_health` command |
| **Static files** | Custom subclass required | `RustFSStaticStorage` included |
| **Dependencies** | `django-storages` + `boto3` | `boto3` only |

---

## Quick Start

```bash
pip install django-rustfs
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "django_rustfs",
]

RUSTFS_ENDPOINT = "http://localhost:9000"
RUSTFS_ACCESS_KEY = "your-access-key"
RUSTFS_SECRET_KEY = "your-secret-key"

STORAGES = {
    "default": {
        "BACKEND": "django_rustfs.storage.RustFSStorage",
    },
    "staticfiles": {
        "BACKEND": "django_rustfs.storage.RustFSStaticStorage",
    },
}
```

```bash
python manage.py rustfs_init_buckets
python manage.py rustfs_health
```

---

## Requirements

- Python 3.9+
- Django 4.2 – 6.1
- boto3 1.28+

---

## Links

- [GitHub](https://github.com/CasualEngineerZombie/django-rustfs)
- [PyPI](https://pypi.org/project/django-rustfs/)
- [Issue Tracker](https://github.com/CasualEngineerZombie/django-rustfs/issues)
