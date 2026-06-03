# django-rustfs: Project Plan & Competitive Analysis

## Executive Summary

`django-rustfs` is a dedicated Django storage backend for RustFS - an emerging high-performance, S3-compatible object storage built in Rust (~23K GitHub stars, Apache 2.0 licensed). While RustFS is fully S3-compatible and works with the generic `django-storages` + `boto3` combination today, there is **no Django-native package** that provides a purpose-built, RustFS-branded developer experience. This project fills that gap.

The core value proposition is **simplicity through focus**: by targeting only RustFS, we eliminate the configuration complexity of pretending to configure AWS S3, provide RustFS-native tooling (health checks, bucket initialization), and expose RustFS-specific features as they mature beyond beta.

---

## 1. Market Landscape Analysis

### 1.1 Object Storage for Django: Current Options

The Django ecosystem has several storage backends for object storage. Understanding each competitor's positioning is essential for carving out django-rustfs's niche.

| Project | Stars | Focus | Backend | Maintenance | Django Support |
|---------|-------|-------|---------|-------------|----------------|
| **django-storages** | ~5.8K | Multi-backend (S3, Azure, GCP, SFTP, FTP) | `boto3`, `azure-storage`, `google-cloud-storage` | Active | 4.2+ |
| **django-minio-storage** | 167 | MinIO only | `minio` Python SDK | Active | 3.2+ |
| **django-minio-backend** | ~200 | MinIO only | `minio` Python SDK | Active | 4.2+ |
| **django-s3-storage** | ~500 | AWS S3 only | `boto3` | Active | 4.2+ |
| **django-rustfs** *(this project)* | - | **RustFS only** | `boto3` *(RustFS-recommended SDK)* | **New** | **4.2+** |

### 1.2 How RustFS Is Currently Used with Django

Today, Django developers using RustFS follow one of two patterns:

**Pattern A: django-storages + boto3 (most common)**
```python
# settings.py - requires AWS-named settings for a non-AWS service
AWS_ACCESS_KEY_ID = "rustfs-key"
AWS_SECRET_ACCESS_KEY = "rustfs-secret"
AWS_STORAGE_BUCKET_NAME = "my-bucket"
AWS_S3_ENDPOINT_URL = "http://localhost:9000"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "private"
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
```
Pain points: AWS-branded settings for RustFS, 10+ configuration variables, no RustFS-specific tooling, bucket creation is manual.

**Pattern B: Raw boto3 in custom storage (advanced users)**
Developers implement their own thin storage class wrapping boto3. This is what `django-minio-storage` did for MinIO - using the MinIO Python SDK instead of boto3. RustFS [officially recommends using AWS S3 SDKs](https://docs.rustfs.com/developer/sdk/)[^25^] rather than vendor-specific SDKs, making boto3 the natural choice.

### 1.3 The Gap: Why django-rustfs?

| Pain Point with Current Approach | django-rustfs Solution |
|----------------------------------|----------------------|
| AWS-branded settings (`AWS_ACCESS_KEY_ID`, `AWS_S3_ENDPOINT_URL`) for a non-AWS service | Clean `RUSTFS_*` prefixed settings |
| ~15 settings to understand and configure | ~5 essential settings with sensible defaults |
| No bucket auto-creation - app crashes on first run if bucket missing | `RUSTFS_AUTO_CREATE_BUCKET = True` by default |
| No built-in health check - discover connectivity issues at runtime | `python manage.py rustfs_health` command |
| Manual bucket setup via RustFS console or CLI | `python manage.py rustfs_init_buckets` command |
| No RustFS-specific features exposed (replication, lifecycle, event notifications) | Roadmap: expose RustFS-native APIs |
| Static files require custom subclass | `RustFSStaticStorage` included with `public-read` defaults |
| Generic error messages from S3 layer | RustFS-specific error types (`RustFSError`, `RustFSBucketError`) |

---

## 2. Architecture Design

### 2.1 Design Principles

1. **Single responsibility**: Only RustFS. No Azure, no GCP, no SFTP.
2. **Use standard SDKs**: RustFS recommends AWS S3 SDKs[^25^]. We use `boto3` directly - no additional SDK dependency.
3. **Zero surprises**: Sensible defaults that work out of the box. The storage should not crash on first use.
4. **Django-native**: Follow Django's storage API exactly. Support both the `DEFAULT_FILE_STORAGE` and `STORAGES` (Django 4.2+) configuration patterns.
5. **Extensible**: Core is a thin boto3 wrapper. RustFS-specific features are added as methods, not breaking changes.

### 2.2 Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         django-rustfs                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────┐  │
│  │ RustFSStorage │  │RustFSStatic   │  │   conf.Settings   │  │
│  │   (core)      │  │   Storage     │  │   (validation)    │  │
│  │               │  │               │  │                   │  │
│  │ • _open()     │  │ • public-read │  │ • required check  │  │
│  │ • _save()     │  │ • no presign  │  │ • defaults        │  │
│  │ • delete()    │  │ • overwrite   │  │                   │  │  │
│  │ • exists()    │  │   enabled     │  │                   │  │
│  │ • size()      │  │               │  │                   │  │
│  │ • url()       │  │               │  │                   │  │
│  │ • listdir()   │  │               │  │                   │  │
│  └───────────────┘  └───────────────┘  └───────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           RustFS-Specific Convenience Methods            │   │
│  │                                                          │   │
│  │  get_object_metadata()  → etag, version_id, storage_class│   │
│  │  copy_object()          → server-side copy               │   │
│  │  get_presigned_post_url() → direct browser uploads       │   │
│  │  is_available()         → health check                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────┐  ┌──────────────────────────┐        │
│  │ rustfs_health        │  │   rustfs_init_buckets    │        │
│  │ (management command) │  │   (management command)   │        │
│  │                      │  │                          │        │
│  │ • Connectivity test  │  │ • Create media bucket    │        │
│  │ • Auth validation    │  │ • Create static bucket   │        │
│  │ • List operation     │  │ • Set public-read policy │        │
│  │ • Upload/download    │  │ • --dry-run support      │        │
│  │   roundtrip test     │  │                          │        │
│  └──────────────────────┘  └──────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                           boto3 (S3 client)                     │
│              ──→ HTTP/HTTPS ──→ RustFS Server                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Use boto3, not a RustFS-specific SDK** | RustFS officially recommends AWS S3 SDKs. No RustFS Python SDK exists. boto3 is mature, well-maintained, and battle-tested.[^25^] |
| **RUSTFS_* prefixed settings** | Eliminates confusion with AWS settings. Clear mental model: "I'm configuring RustFS, not pretending to configure AWS." |
| **Auto-create buckets by default** | Developer experience: `pip install`, configure, run - no manual bucket creation step. Can be disabled. |
| **Separate `RustFSStaticStorage` class** | Static files need different defaults (public-read, overwrite enabled). Following django-minio-backend's pattern.[^18^] |
| **Management commands for tooling** | Health checks and bucket init are operational concerns, not runtime code. Commands are the Django-idiomatic way to expose these. |
| **~400 LOC core** | Following django-minio-storage's philosophy: "thoroughly tested, small code base that delegates as much as possible to the [boto3] client."[^22^] |

---

## 3. Competitive Feature Matrix

### 3.1 Feature Comparison

| Feature | django-storages (S3) | django-minio-storage | django-minio-backend | **django-rustfs** |
|---------|---------------------|---------------------|---------------------|------------------|
| **Configuration clarity** | AWS-branded settings | MinIO-branded settings | MinIO-branded settings | **RustFS-branded settings** |
| **Required config vars** | ~10+ | ~5 | ~8 | **~3 essential** |
| **Bucket auto-creation** | No | Yes | Yes | **Yes (default)** |
| **Health check command** | No | No | `is_minio_available()` | **`rustfs_health`** |
| **Bucket init command** | No | No | `initialize_buckets` | **`rustfs_init_buckets`** |
| **Static storage class** | Custom subclass needed | `MinioStaticStorage` | `MinioBackendStatic` | **`RustFSStaticStorage`** |
| **Presigned POST for uploads** | Manual implementation | No | No | **`get_presigned_post_url()`** |
| **Object metadata access** | Raw boto3 response | Limited | Limited | **`get_object_metadata()`** |
| **Copy objects** | Manual boto3 | No | No | **`copy_object()`** |
| **URL caching** | No | No | Yes | *Planned* |
| **Django admin integration** | No | No | No | *Planned* |
| **Async support** | No | No | No | *Planned* |
| **Dependencies** | `django-storages`, `boto3` | `minio` | `minio` | **`boto3` only** |
| **License** | BSD-3 | MIT/Apache-2.0 | MIT | **MIT** |

### 3.2 Sizing Comparison

| Metric | django-storages (S3 only) | django-minio-storage | **django-rustfs** |
|--------|--------------------------|---------------------|------------------|
| **Core storage LOC** | ~1,500 | ~560 | **~400** |
| **Total package LOC** | ~3,000+ | ~800 | **~600** |
| **Test coverage** | ~85% | ~90% | **~90% (target)** |
| **Direct dependencies** | 2 (`boto3`, `botocore`) | 1 (`minio`) | **1 (`boto3`)** |
| **Installation size** | ~15 MB | ~8 MB | **~12 MB** |

---

## 4. RustFS-Specific Opportunity

### 4.1 What Makes RustFS Different

RustFS is not just "another S3-compatible storage." It has distinct characteristics that create opportunities for a dedicated Django backend:

| RustFS Characteristic | Implication for django-rustfs |
|----------------------|------------------------------|
| **Apache 2.0 license** (vs MinIO's AGPL-3.0) | Commercial-friendly - no license contamination risk for proprietary Django apps |
| **Built in Rust** - memory safety | Marketing angle: "memory-safe storage pipeline" |
| **~2.3x faster than MinIO** for 4KB objects[^9^] | Performance claims in documentation |
| **100% S3 compatibility**[^51^] | boto3 works perfectly - no compatibility shims needed |
| **Beta status** (v1.0.0-beta.x) | First-mover advantage - establish the "official" Django integration before v1.0 stable |
| **Built-in web console** (Vue.js) | Opportunity for Django admin integration |
| **Bucket replication, lifecycle, event notifications**[^50^] | Future: expose these via management commands and model methods |
| **No telemetry / GDPR compliant**[^6^] | Appeal for privacy-conscious European developers |

### 4.2 Roadmap: Beyond S3 Compatibility

As RustFS matures beyond beta, these features can be exposed through django-rustfs:

| RustFS Feature | django-rustfs Integration |
|----------------|--------------------------|
| **Bucket replication** | Management command `rustfs_replicate_setup` |
| **Lifecycle rules (ILM)** | Model signal hooks for automatic lifecycle configuration |
| **Event notifications (webhooks)** | Django signal integration - trigger actions on object events |
| **Object locking / WORM** | `save(locked=True)` parameter on FileField |
| **Multi-site replication** | `RustFSStorage(replica_endpoint=...)` for failover |
| **RustFS console API** | Django admin views for bucket browser |

---

## 5. Go-to-Market Strategy

### 5.1 Target Users

1. **Django developers already using or evaluating RustFS** - they're our primary audience. They want a cleaner DX than django-storages.
2. **Developers migrating from MinIO to RustFS** - RustFS's Apache 2.0 license is a key driver. django-minio-storage users need an equivalent.
3. **European/privacy-conscious teams** - RustFS's no-telemetry policy appeals to GDPR-conscious organizations.
4. **Performance-sensitive applications** - RustFS's speed claims attract developers building high-throughput file systems.

### 5.2 Distribution Strategy

| Channel | Action |
|---------|--------|
| **PyPI** | `pip install django-rustfs` - primary distribution |
| **GitHub** | Open-source repo with issues, discussions, PRs |
| **RustFS Community** | Post in RustFS Discussions, link from RustFS docs |
| **Django Community** | Post on django-users mailing list, Django forum |
| **Documentation** | ReadTheDocs with quickstart, API reference, recipes |
| **Blog Posts** | "Moving from MinIO to RustFS with Django", "django-rustfs: zero-config Django storage" |

### 5.3 Success Metrics

| Metric | 3-Month Target | 6-Month Target |
|--------|---------------|----------------|
| PyPI downloads | 500 | 2,000 |
| GitHub stars | 50 | 150 |
| Dependent projects | 5 | 20 |
| Test coverage | 90% | 95% |
| Open issues (unresolved) | < 5 | < 3 |

---

## 6. Technical Implementation Details

### 6.1 Package Structure

```
django-rustfs/
├── pyproject.toml              # Modern Python packaging (PEP 621)
├── README.md                   # Comprehensive documentation
├── LICENSE                     # MIT License
├── CHANGELOG.md                # Version history
├── django_rustfs/
│   ├── __init__.py             # Package init with version
│   ├── conf.py                 # Settings validation and defaults
│   ├── storage.py              # Core RustFSStorage + RustFSStaticStorage
│   └── management/
│       ├── __init__.py
│       └── commands/
│           ├── __init__.py
│           ├── rustfs_health.py        # Health check command
│           └── rustfs_init_buckets.py  # Bucket init command
└── tests/
    ├── __init__.py
    ├── settings.py             # Test Django settings
    ├── urls.py                 # Test URL config
    └── test_storage.py         # Comprehensive test suite
```

### 6.2 Testing Strategy

| Test Layer | Tools | Coverage Target |
|-----------|-------|----------------|
| **Unit tests** (mocked boto3) | `pytest`, `unittest.mock` | Core storage methods: 100% |
| **Integration tests** (moto S3 mock) | `moto`, `pytest-django` | Upload/download cycle, listdir | 
| **Management command tests** | `pytest-django`, `call_command` | Health check, bucket init |
| **Configuration tests** | `pytest`, `override_settings` | Settings validation, defaults |

### 6.3 Development Workflow

```bash
# Setup
git clone https://github.com/yourusername/django-rustfs
cd django-rustfs
pip install -e ".[dev]"

# Development
pytest                          # Run tests
pytest --cov=django_rustfs      # With coverage
black django_rustfs tests       # Format code
ruff check django_rustfs tests  # Lint
mypy django_rustfs              # Type check

# Release
python -m build                 # Build wheel and sdist
python -m twine upload dist/*   # Upload to PyPI
```

---

## 7. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| RustFS v1.0 changes S3 API behavior | Medium | High | Follow RustFS beta closely; use moto for S3-compatible testing; pin boto3 version range |
| django-storages adds RustFS-specific backend | Low | Medium | Our differentiation is focus and RustFS-native tooling, not just branding |
| boto3 introduces breaking change | Low | Medium | Pin `boto3>=1.28.0,<2.0.0`; test against latest boto3 in CI |
| RustFS project stalls or changes direction | Low | High | Code is ~400 LOC of boto3 wrapper - easily adaptable to any S3-compatible storage |
| Community prefers staying with django-storages | Medium | Low | Address via documentation showing concrete DX improvements; not a zero-sum game |

---

## 8. Conclusion

`django-rustfs` addresses a clear, well-defined gap in the Django storage ecosystem. RustFS is a rapidly growing project with ~23K stars and strong momentum. There is no Django-native integration for it today - developers must use the generic S3 backend and tolerate AWS-branded configuration.

By providing a focused, well-documented, and thoughtfully-designed storage backend, django-rustfs can become the **de facto standard** for using RustFS with Django, similar to how `django-minio-storage` serves the MinIO community.

The project's lean architecture (~400 LOC), comprehensive test suite, and clean API position it well for long-term maintenance and community adoption. The roadmap of RustFS-specific features provides a clear growth path as both projects mature.
