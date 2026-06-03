"""
django-rustfs: A plug-and-play Django storage backend for RustFS.

RustFS is a high-performance, S3-compatible object storage built in Rust.
This package provides a clean, purpose-built Django storage backend that
feels native to RustFS — no AWS-named settings, no multi-backend baggage.

Usage:
    1. Install: pip install django-rustfs
    2. Add 'django_rustfs' to INSTALLED_APPS
    3. Set RUSTFS_* settings in settings.py
    4. Set DEFAULT_FILE_STORAGE = 'django_rustfs.storage.RustFSStorage'
"""

__version__ = "0.1.0"
__all__ = ["RustFSStorage"]
