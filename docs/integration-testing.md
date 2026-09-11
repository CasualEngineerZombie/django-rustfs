# Integration Testing

The integration suite in `tests/test_rustfs_integration.py` runs the Django storage backend against a real RustFS S3-compatible server. The existing test suite continues to use Moto for fast unit/compatibility tests.

---

## Run locally

Start RustFS with Docker using the same credentials as the integration fixture:

```bash
docker run --rm -d \
  --name django-rustfs-test \
  -p 9000:9000 \
  -e RUSTFS_ACCESS_KEY=test-access-key \
  -e RUSTFS_SECRET_KEY=test-secret-key \
  rustfs/rustfs:latest \
  /data
```

Install the development dependencies and run only the integration tests:

```bash
pip install -e ".[dev]"
pytest -m integration --no-cov -v
```

!!! info "Environment variables"
    The tests default to `http://127.0.0.1:9000`, `test-access-key`, and `test-secret-key`. Override them with:

    | Variable | Default |
    |---|---|
    | `RUSTFS_ENDPOINT` | `http://127.0.0.1:9000` |
    | `RUSTFS_ACCESS_KEY` | `test-access-key` |
    | `RUSTFS_SECRET_KEY` | `test-secret-key` |
    | `RUSTFS_REGION` | `us-east-1` |

Stop the local container when finished:

```bash
docker stop django-rustfs-test
```

---

## CI

GitHub Actions starts an isolated RustFS container for the integration job. The integration job currently runs against Python 3.14 and Django 6.1, while the normal unit-test matrix remains unchanged.

The integration suite creates a unique bucket per test and removes its objects and bucket during fixture cleanup, so tests do not depend on shared or public RustFS infrastructure.

---

## What is covered

The integration suite exercises observable storage behavior including:

- Bucket connectivity
- Upload, open, existence, size, and delete operations
- Binary and empty files
- Nested paths and directory listing
- Location prefixes
- Unicode filenames and paths
- Overwrite and non-overwrite behavior
- Object metadata and server-side copy
- Private presigned GET URLs
- Public direct URLs
- Presigned POST generation
- Missing-object error handling
- `RustFSStaticStorage`
- Django `STORAGES` configuration
- Settings-based location configuration
