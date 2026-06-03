# Release Guide: Publishing django-rustfs to PyPI

This guide explains how to publish a new version of django-rustfs to PyPI using GitHub Releases and the automated CD pipeline.

## Prerequisites

Before you can publish, you must configure **Trusted Publishing** on PyPI (one-time setup).

### Step 1: Configure PyPI Trusted Publishing

1. Go to [pypi.org/manage/account/publishing](https://pypi.org/manage/account/publishing)
2. Click **"Add a new pending publisher"**
3. Fill in the form:
   - **PyPI Project Name**: `django-rustfs`
   - **Owner**: `CasualEngineerZombie`
   - **Repository name**: `django-rustfs`
   - **Workflow name**: `python-publish.yml`
   - **Environment name**: `pypi`
4. Click **"Add"**

This tells PyPI to trust the GitHub Actions workflow running in this repository.

## Preparing a Release

### Step 1: Update the Version

Edit `pyproject.toml` and bump the version:

```toml
[project]
name = "django-rustfs"
version = "0.2.0"  # <-- bump this
```

Follow [Semantic Versioning](https://semver.org/):
- `MAJOR` — breaking changes
- `MINOR` — new features, backward compatible
- `PATCH` — bug fixes

### Step 2: Update the Changelog

Add a section to `CHANGELOG.md`:

```markdown
## 0.2.0 (2026-06-04)

### Added
- New feature X

### Fixed
- Bug fix Y

### Changed
- Improvement Z
```

### Step 3: Commit and Push

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Release v0.2.0"
git push origin main
```

### Step 4: Verify CI Passes

Go to [GitHub Actions](https://github.com/CasualEngineerZombie/django-rustfs/actions) and make sure:
- `Python package` workflow passes on all Python versions
- `Lint` workflow passes

**Do NOT create a release if CI is failing.**

## Creating the GitHub Release

### Method 1: Via GitHub Web UI

1. Go to your repository on GitHub: `https://github.com/CasualEngineerZombie/django-rustfs`
2. Click **"Releases"** in the right sidebar (or go to `/releases`)
3. Click **"Draft a new release"**
4. Click **"Choose a tag"** and type the new version: `v0.2.0`
5. Click **"Create new tag: v0.2.0"**
6. Set **Target**: `main` (or the commit you want to release)
7. Set **Release title**: `v0.2.0`
8. In the **Description** box, paste the changelog for this version:
   ```markdown
   ## What's Changed
   
   ### Added
   - New feature X
   
   ### Fixed
   - Bug fix Y
   ```
9. Leave **"Set as a pre-release"** unchecked (unless it's alpha/beta)
10. Leave **"Set as the latest release"** checked
11. Click **"Publish release"**

### Method 2: Via Git CLI

```bash
# Create an annotated tag
git tag -a v0.2.0 -m "Release v0.2.0"

# Push the tag to GitHub
git push origin v0.2.0
```

Then go to GitHub Releases and edit the tag to add release notes.

## What Happens Next (Automated)

After you click **"Publish release"**, GitHub Actions automatically:

1. **Triggers** the `python-publish.yml` workflow
2. **Builds** the package (`python -m build`)
3. **Verifies** the distributions (`twine check dist/*`)
4. **Uploads** artifacts to GitHub
5. **Publishes** to PyPI using trusted publishing

### Monitoring the Release

1. Go to [GitHub Actions](https://github.com/CasualEngineerZombie/django-rustfs/actions)
2. Watch the **"Upload Python Package"** workflow run
3. It should complete in ~2-3 minutes

### Verifying the Release

Once the workflow completes:

1. Go to [PyPI](https://pypi.org/project/django-rustfs/)
2. You should see the new version listed
3. The release URL will be: `https://pypi.org/project/django-rustfs/0.2.0/`

Users can now install it:

```bash
pip install django-rustfs==0.2.0
```

## Troubleshooting

### "Trusted publishing" error

**Symptom**: Publish step fails with `invalid-publisher` or similar.

**Fix**: 
- Double-check the PyPI trusted publisher config matches exactly:
  - Owner: `CasualEngineerZombie`
  - Repository: `django-rustfs`
  - Workflow: `python-publish.yml`
  - Environment: `pypi`
- Make sure you created the release from the correct repository (not a fork)

### "Environment not found" error

**Symptom**: Workflow fails waiting for environment approval.

**Fix**:
- Go to repository **Settings > Environments**
- Create an environment named `pypi` if it doesn't exist
- (Optional) Add protection rules (require review, deployment branches)

### Build fails

**Symptom**: `release-build` job fails.

**Fix**:
- Check that `pyproject.toml` is valid
- Make sure `README.md` exists (required for PyPI)
- Verify `hatchling` build backend works: `python -m build` locally

### Wrong version uploaded

**Symptom**: PyPI shows old version or wrong version number.

**Fix**:
- Make sure you bumped `version` in `pyproject.toml` **before** creating the release
- The release tag (e.g., `v0.2.0`) should match the package version (`0.2.0`)

## Release Checklist

Before every release, verify:

- [ ] Version bumped in `pyproject.toml`
- [ ] `CHANGELOG.md` updated
- [ ] CI passing on `main` branch
- [ ] All tests passing locally: `pytest`
- [ ] Linting clean: `ruff check .`
- [ ] Code formatted: `ruff format .`
- [ ] Types clean: `mypy django_rustfs`
- [ ] PyPI trusted publisher configured (one-time)
- [ ] GitHub Release created with tag matching version
