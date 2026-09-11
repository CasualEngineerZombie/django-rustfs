# Management Commands

## rustfs_health

Check connectivity, authentication, and run an upload/download roundtrip test.

```bash
python manage.py rustfs_health
python manage.py rustfs_health --bucket=my-bucket
python manage.py rustfs_health --verbose
```

### Options

| Option | Description |
|---|---|
| `--bucket` | Specific bucket to check (defaults to `RUSTFS_BUCKET_NAME`) |
| `--verbose` | Show detailed response information |

### What It Checks

1. **Bucket accessibility** — verifies the configured bucket exists and is reachable
2. **List operation** — confirms you can list objects in the bucket
3. **Roundtrip test** — uploads a test file, downloads it, verifies contents, and cleans up

### Example Output

```
🔍 Checking RustFS health...
   Endpoint: http://localhost:9000
   Bucket:   django-media

  ✅ Bucket 'django-media' is accessible
     Response time: 12.3ms
  ✅ List operation works (0 objects visible)

  🧪 Running upload/download roundtrip test...
  ✅ Upload/download roundtrip successful

✅ RustFS health check completed successfully!
```

---

## rustfs_init_buckets

Create and configure RustFS buckets for Django media and static files.

```bash
python manage.py rustfs_init_buckets
python manage.py rustfs_init_buckets --bucket=my-custom-bucket
python manage.py rustfs_init_buckets --public
python manage.py rustfs_init_buckets --dry-run
```

### Options

| Option | Description |
|---|---|
| `--bucket` | Create only this specific bucket |
| `--skip-static` | Skip creating the static files bucket |
| `--public` | Make the bucket public-readable |
| `--dry-run` | Show what would be done without making changes |

### What It Does

1. Creates the media bucket (`RUSTFS_BUCKET_NAME`) if it doesn't exist
2. Creates the static bucket (`RUSTFS_STATIC_BUCKET_NAME`) if it doesn't exist
3. Sets public-read policy on buckets when `--public` is used

### Example Output

```
🪣 Initializing RustFS buckets...

  📦 Bucket: django-media
     Status: Created ✓

  📦 Bucket: django-static
     Status: Created ✓
     Policy: public-read ✓

==================================================
RESULTS
==================================================
  ✅ Created:   django-media
  ✅ Created:   django-static

✅ All done: 2 bucket(s) ready to use
```
