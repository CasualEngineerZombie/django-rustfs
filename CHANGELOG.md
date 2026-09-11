# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-09-11

### Added
- Django 6.1 support across Python 3.12, 3.13, and 3.14
- RustFS integration test suite (`tests/test_rustfs_integration.py`) against real RustFS server
- GitHub Actions workflow for RustFS integration tests with Docker
- Full documentation site with MkDocs Material theme (https://django-rustfs.rianbarriga.com/)
- Documentation pages: installation, configuration, API reference, management commands, integration testing, contributing
- GitHub Pages auto-deploy workflow for documentation
- Custom domain support for documentation site

### Changed
- Restricted Django dependency to `>=4.2,<7.0` for compatibility
- Integration tests excluded from standard CI matrix (run separately in dedicated workflow)
- Presigned URL test made more generic to support different S3 implementations

### Fixed
- CI: Added `allow-prereleases: true` for Python 3.14 in all workflows
- CI: Fixed ruff formatting in integration test file
- CI: Handle 403 errors gracefully in public direct URL integration test

## [0.2.0] - 2026-06-04

### Added
- `CONTRIBUTING.md` - contribution guidelines and development setup
- `SECURITY.md` - security policy and vulnerability reporting
- `CODE_OF_CONDUCT.md` - Contributor Covenant code of conduct
- `RELEASE_GUIDE.md` - step-by-step release instructions
- Comprehensive test suite for management commands (`rustfs_health`, `rustfs_init_buckets`)
- Tests for settings configuration (`django_rustfs.conf`)
- Additional storage tests covering edge cases and error handling
- CI/CD pipeline with GitHub Actions for automated testing and PyPI publishing

### Changed
- Switched license from MIT to Apache 2.0 for better patent and trademark protection
- Updated all repository URLs to point to `github.com/CasualEngineerZombie/django-rustfs`
- Replaced `black` with `ruff` for both linting and formatting
- Updated `pyproject.toml` ruff configuration to use `[tool.ruff.lint]` section
- Increased test coverage requirement from 80% to 90%
- Fixed Python 3.9 compatibility by replacing `str | None` union syntax with `Optional[str]`
- Fixed mypy type annotations across storage backend

### Fixed
- Fixed `ruff check` deprecation warning by moving linter settings to `[tool.ruff.lint]`
- Fixed all ruff lint issues (F841, B904, F541, I001, F401)
- Fixed pytest execution by ensuring dev dependencies are properly installed
- Fixed `python-publish.yml` PyPI URL format and added distribution verification

## [0.1.0] - 2026-06-03

### Added
- Initial release of django-rustfs
- `RustFSStorage` - core Django storage backend for RustFS
- `RustFSStaticStorage` - dedicated static files storage with public-read defaults
- `rustfs_health` management command - connectivity, auth, and upload/download roundtrip tests
- `rustfs_init_buckets` management command - automated bucket creation with policy setup
- `get_object_metadata()` - structured access to RustFS object metadata (ETag, version ID, storage class)
- `copy_object()` - server-side copy without downloading
- `get_presigned_post_url()` - direct browser upload support
- `is_available()` - lightweight health check method
- Full test suite with moto mock S3 integration
- Support for Django 4.2, 5.0, 5.1, 5.2
- Support for Python 3.9, 3.10, 3.11, 3.12, 3.13
