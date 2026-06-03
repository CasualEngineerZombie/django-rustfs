# Contributing to django-rustfs

Thank you for your interest in contributing to django-rustfs! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Install development dependencies

```bash
git clone https://github.com/CasualEngineerZombie/django-rustfs.git
cd django-rustfs
pip install -e ".[dev]"
```

## Development Setup

### Running Tests

```bash
pytest
```

### Code Quality

All code must pass linting and type checking:

```bash
ruff check .
mypy django_rustfs
```

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check existing issues. When reporting bugs, include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Python and Django versions
- RustFS version (if applicable)
- Any relevant code snippets or error messages

### Suggesting Features

Feature requests are welcome! Please:

- Check if the feature has already been requested
- Describe the use case clearly
- Explain why this feature would be useful to most users

### Pull Requests

1. Create a new branch for your feature or bug fix
2. Make your changes with clear, focused commits
3. Add or update tests as needed
4. Ensure all tests pass and code quality checks pass
5. Update documentation if necessary
6. Submit a pull request with a clear description

## Code Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write docstrings for public methods and classes
- Keep functions focused and modular
- Add tests for new functionality

## Commit Messages

Use clear, descriptive commit messages:

```
feat: add support for custom endpoint configurations
fix: resolve bucket creation race condition
docs: update configuration examples
test: add integration tests for static storage
```

## Questions?

Feel free to open an issue for questions or join discussions in existing issues.

Thank you for contributing!
