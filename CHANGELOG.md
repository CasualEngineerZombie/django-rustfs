# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-03

### Added
- Initial release of django-rustfs
- `RustFSStorage` — core Django storage backend for RustFS
- `RustFSStaticStorage` — dedicated static files storage with public-read defaults
- `rustfs_health` management command — connectivity, auth, and upload/download roundtrip tests
- `rustfs_init_buckets` management command — automated bucket creation with policy setup
- `get_object_metadata()` — structured access to RustFS object metadata (ETag, version ID, storage class)
- `copy_object()` — server-side copy without downloading
- `get_presigned_post_url()` — direct browser upload support
- `is_available()` — lightweight health check method
- Full test suite with moto mock S3 integration
- Support for Django 4.2, 5.0, 5.1, 5.2
- Support for Python 3.9, 3.10, 3.11, 3.12, 3.13
