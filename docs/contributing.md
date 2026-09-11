# Contributing

Contributions are welcome! Here's how to get started.

## Development Setup

```bash
git clone https://github.com/CasualEngineerZombie/django-rustfs.git
cd django-rustfs
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=django_rustfs --cov-report=html
```

## Code Quality

```bash
ruff check .          # Linting
ruff format .         # Formatting
mypy django_rustfs    # Type checking
```

## Project Structure

```
django-rustfs/
├── django_rustfs/          # Main package
│   ├── storage.py          # Core storage backend
│   ├── conf.py             # Settings configuration
│   └── management/         # Management commands
│       └── commands/
│           ├── rustfs_health.py
│           └── rustfs_init_buckets.py
├── tests/                  # Test suite
├── docs/                   # Documentation
├── .github/workflows/      # CI/CD
├── pyproject.toml          # Package config
└── README.md
```

## Guidelines

- Write tests for new features
- Follow existing code style (ruff handles formatting)
- Keep PRs focused on a single change
- Update docs if adding user-facing features
