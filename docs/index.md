---
hide:
  - navigation
  - toc
---

<div class="hero" markdown>

# django-rustfs

**The Django storage backend for RustFS.**

S3-compatible object storage, without the AWS baggage.

[![PyPI version](https://badge.fury.io/py/django-rustfs.svg)](https://pypi.org/project/django-rustfs/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-rustfs.svg)](https://pypi.org/project/django-rustfs/)
[![Django versions](https://img.shields.io/badge/django-4.2%20%7C%205.0%20%7C%205.1%20%7C%205.2%20%7C%206.1-blue.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/CasualEngineerZombie/django-rustfs/blob/main/LICENSE)
[![Tests](https://github.com/CasualEngineerZombie/django-rustfs/workflows/Python%20package/badge.svg)](https://github.com/CasualEngineerZombie/django-rustfs/actions)

</div>

---

## Install in one line

```bash
pip install django-rustfs
```

---

## Why django-rustfs?

You *can* use RustFS with `django-storages` + `boto3` — but that means 10+ `AWS_*` settings for something that isn't AWS.

**django-rustfs** gives you a purpose-built backend with clean `RUSTFS_*` settings, built-in health checks, and bucket management out of the box.

<div class="grid-container" markdown>

<div class="grid-card" markdown>

<div class="card-icon" markdown>

:material-cog:{ .md-icon }

</div>

### Clean Configuration

Four settings and you're done — no `AWS_S3_ENDPOINT_URL` gymnastics.

</div>

<div class="grid-card" markdown>

<div class="card-icon" markdown>

:material-bucket:{ .md-icon }

</div>

### Bucket Management

Create and configure buckets with a single management command.

</div>

<div class="grid-card" markdown>

<div class="card-icon" markdown>

:material-heart-pulse:{ .md-icon }

</div>

### Health Checks

Verify connectivity, auth, and data roundtrips in one command.

</div>

<div class="grid-card" markdown>

<div class="card-icon" markdown>

:material-file-document:{ .md-icon }
</div>

### Static Files

`RustFSStaticStorage` included — no custom subclass needed.

</div>

</div>

---

## Quick comparison

| Feature | django-storages + boto3 | **django-rustfs** |
|---|---|---|
| Configuration | 10+ AWS-branded settings | **4 clean `RUSTFS_*` settings** |
| Bucket setup | Manual CLI / console | **`rustfs_init_buckets`** |
| Health checks | None | **`rustfs_health`** |
| Static files | Custom subclass required | **`RustFSStaticStorage` included** |
| Dependencies | `django-storages` + `boto3` | **`boto3` only** |

---

## Quick start

=== "1. Install"

    ```bash
    pip install django-rustfs
    ```

=== "2. Configure"

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

=== "3. Initialize"

    ```bash
    python manage.py rustfs_init_buckets
    python manage.py rustfs_health
    ```

---

## Requirements

| Dependency | Version |
|---|---|
| Python | 3.9+ |
| Django | 4.2 – 6.1 |
| boto3 | 1.28+ |

---

<div class="grid-container" markdown>

<div class="grid-card" markdown>

:material-github:{ .md-icon } [**GitHub**](https://github.com/CasualEngineerZombie/django-rustfs)

</div>

<div class="grid-card" markdown>

:material-package-variant:{ .md-icon } [**PyPI**](https://pypi.org/project/django-rustfs/)

</div>

<div class="grid-card" markdown>

:material-bug:{ .md-icon } [**Issue Tracker**](https://github.com/CasualEngineerZombie/django-rustfs/issues)

</div>

</div>
