# Contributing

Contributions are welcome! Here's how to get started.

---

## Development setup

```bash
git clone https://github.com/CasualEngineerZombie/django-rustfs.git
cd django-rustfs
pip install -e ".[dev]"
```

---

## Running tests

=== "All tests"

    ```bash
    pytest
    ```

=== "With coverage"

    ```bash
    pytest --cov=django_rustfs --cov-report=html
    ```

=== "Integration only"

    ```bash
    docker run --rm -d \
      --name rustfs \
      -p 9000:9000 \
      -e RUSTFS_ACCESS_KEY=test-access-key \
      -e RUSTFS_SECRET_KEY=test-secret-key \
      rustfs/rustfs:latest /data

    pytest -m integration --no-cov -v
    ```

---

## Code quality

```bash
ruff check .            # Linting
ruff format .           # Formatting
mypy django_rustfs      # Type checking
```

!!! tip "Pre-commit"
    Run all three before pushing:

    ```bash
    ruff check . && ruff format . && mypy django_rustfs
    ```

---

## Project structure

```
django-rustfs/
├── django_rustfs/
│   ├── __init__.py
│   ├── conf.py                  # Settings configuration
│   ├── storage.py               # Core storage backend
│   └── management/
│       └── commands/
│           ├── rustfs_health.py
│           └── rustfs_init_buckets.py
├── tests/
│   ├── settings.py
│   ├── test_storage.py          # Unit tests
│   ├── test_conf.py
│   ├── test_commands.py
│   └── test_rustfs_integration.py
├── docs/                        # Documentation
├── .github/workflows/           # CI/CD
├── pyproject.toml
└── README.md
```

---

## Guidelines

- Write tests for new features
- Follow existing code style (ruff handles formatting)
- Keep PRs focused on a single change
- Update docs if adding user-facing features
