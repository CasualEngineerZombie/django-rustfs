"""Tests for django-rustfs management commands."""

import io
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError

from django_rustfs.storage import RustFSStorage


class TestRustFSHealthCommand:
    """Test rustfs_health management command."""

    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage with configurable client."""
        storage = MagicMock(spec=RustFSStorage)
        storage.endpoint_url = "http://localhost:9000"
        storage.bucket_name = "test-bucket"
        storage.client = MagicMock()
        return storage

    def test_health_check_success(self, mock_storage):
        """Test successful health check."""
        out = io.StringIO()
        mock_storage.client.head_bucket.return_value = {}
        mock_storage.client.list_objects_v2.return_value = {"KeyCount": 0}
        mock_storage.client.get_object.return_value = {
            "Body": io.BytesIO(b"django-rustfs health check")
        }

        with patch(
            "django_rustfs.management.commands.rustfs_health.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_health", stdout=out)

        output = out.getvalue()
        assert "Checking RustFS health" in output
        assert "is accessible" in output
        assert "List operation works" in output
        assert "Upload/download roundtrip successful" in output
        assert "health check completed successfully" in output

    def test_health_check_custom_bucket(self, mock_storage):
        """Test health check with custom bucket."""
        out = io.StringIO()
        mock_storage.client.head_bucket.return_value = {}
        mock_storage.client.list_objects_v2.return_value = {"KeyCount": 0}
        mock_storage.client.get_object.return_value = {
            "Body": io.BytesIO(b"django-rustfs health check")
        }

        with patch(
            "django_rustfs.management.commands.rustfs_health.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_health", bucket="custom-bucket", stdout=out)

        assert mock_storage.bucket_name == "custom-bucket"

    def test_health_check_bucket_404(self, mock_storage):
        """Test health check when bucket doesn't exist."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error
        mock_storage.client.list_objects_v2.return_value = {"KeyCount": 0}
        mock_storage.client.get_object.return_value = {
            "Body": io.BytesIO(b"django-rustfs health check")
        }

        with patch(
            "django_rustfs.management.commands.rustfs_health.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_health", stdout=out)

        output = out.getvalue()
        assert "does not exist" in output
        assert "rustfs_init_buckets" in output

    def test_health_check_auth_error(self, mock_storage):
        """Test health check with authentication failure."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "403", "Message": "Access Denied"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error

        with (
            patch(
                "django_rustfs.management.commands.rustfs_health.RustFSStorage",
                return_value=mock_storage,
            ),
            pytest.raises(CommandError) as exc_info,
        ):
            call_command("rustfs_health", stdout=out)

        assert "Authentication failed" in str(exc_info.value)

    def test_health_check_invalid_access_key(self, mock_storage):
        """Test health check with InvalidAccessKeyId error."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "InvalidAccessKeyId", "Message": "Invalid key"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error

        with (
            patch(
                "django_rustfs.management.commands.rustfs_health.RustFSStorage",
                return_value=mock_storage,
            ),
            pytest.raises(CommandError) as exc_info,
        ):
            call_command("rustfs_health", stdout=out)

        assert "Authentication failed" in str(exc_info.value)

    def test_health_check_signature_error(self, mock_storage):
        """Test health check with SignatureDoesNotMatch error."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "SignatureDoesNotMatch", "Message": "Bad signature"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error

        with (
            patch(
                "django_rustfs.management.commands.rustfs_health.RustFSStorage",
                return_value=mock_storage,
            ),
            pytest.raises(CommandError) as exc_info,
        ):
            call_command("rustfs_health", stdout=out)

        assert "Authentication failed" in str(exc_info.value)

    def test_health_check_bucket_other_error(self, mock_storage):
        """Test health check with other bucket error."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error

        with (
            patch(
                "django_rustfs.management.commands.rustfs_health.RustFSStorage",
                return_value=mock_storage,
            ),
            pytest.raises(CommandError) as exc_info,
        ):
            call_command("rustfs_health", stdout=out)

        assert "Bucket check failed" in str(exc_info.value)

    def test_health_check_connection_error(self, mock_storage):
        """Test health check with connection failure."""
        out = io.StringIO()
        mock_storage.client.head_bucket.side_effect = Exception("Connection refused")

        with (
            patch(
                "django_rustfs.management.commands.rustfs_health.RustFSStorage",
                return_value=mock_storage,
            ),
            pytest.raises(CommandError) as exc_info,
        ):
            call_command("rustfs_health", stdout=out)

        assert "Cannot connect to RustFS" in str(exc_info.value)

    def test_health_check_config_error(self):
        """Test health check with storage configuration error."""
        out = io.StringIO()

        with (
            patch(
                "django_rustfs.management.commands.rustfs_health.RustFSStorage",
                side_effect=ImproperlyConfigured("Missing endpoint"),
            ),
            pytest.raises(CommandError) as exc_info,
        ):
            call_command("rustfs_health", stdout=out)

        assert "Configuration error" in str(exc_info.value)

    def test_health_check_list_error(self, mock_storage):
        """Test health check when list operation fails."""
        out = io.StringIO()
        mock_storage.client.head_bucket.return_value = {}
        error = ClientError(
            {"Error": {"Code": "403", "Message": "Access Denied"}},
            "ListObjectsV2",
        )
        mock_storage.client.list_objects_v2.side_effect = error
        mock_storage.client.get_object.return_value = {
            "Body": io.BytesIO(b"django-rustfs health check")
        }

        with patch(
            "django_rustfs.management.commands.rustfs_health.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_health", stdout=out)

        output = out.getvalue()
        assert "List operation failed" in output
        assert "health check completed successfully" in output

    def test_health_check_roundtrip_mismatch(self, mock_storage):
        """Test health check when upload/download data mismatches."""
        out = io.StringIO()
        mock_storage.client.head_bucket.return_value = {}
        mock_storage.client.list_objects_v2.return_value = {"KeyCount": 0}
        mock_storage.client.get_object.return_value = {"Body": io.BytesIO(b"wrong content")}

        with patch(
            "django_rustfs.management.commands.rustfs_health.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_health", stdout=out)

        output = out.getvalue()
        assert "Data mismatch" in output
        assert "health check completed successfully" in output

    def test_health_check_roundtrip_error(self, mock_storage):
        """Test health check when roundtrip fails."""
        out = io.StringIO()
        mock_storage.client.head_bucket.return_value = {}
        mock_storage.client.list_objects_v2.return_value = {"KeyCount": 0}
        mock_storage.client.put_object.side_effect = Exception("Upload failed")

        with patch(
            "django_rustfs.management.commands.rustfs_health.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_health", stdout=out)

        output = out.getvalue()
        assert "Roundtrip test failed" in output
        assert "health check completed successfully" in output


class TestRustFSInitBucketsCommand:
    """Test rustfs_init_buckets management command."""

    @pytest.fixture
    def mock_storage(self):
        """Create a mock storage with configurable client."""
        storage = MagicMock(spec=RustFSStorage)
        storage.endpoint_url = "http://localhost:9000"
        storage.bucket_name = "django-media"
        storage.default_acl = "private"
        storage.client = MagicMock()
        return storage

    def test_init_buckets_success(self, mock_storage):
        """Test successful bucket initialization."""
        out = io.StringIO()
        # Bucket doesn't exist initially
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error
        mock_storage.client.create_bucket.return_value = {}

        with (
            patch(
                "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
                return_value=mock_storage,
            ),
            patch(
                "django_rustfs.management.commands.rustfs_init_buckets.RustFSStaticStorage"
            ) as mock_static,
        ):
            mock_static_storage = MagicMock()
            mock_static_storage.bucket_name = "django-static"
            mock_static.return_value = mock_static_storage
            call_command("rustfs_init_buckets", stdout=out)

        output = out.getvalue()
        assert "Initializing RustFS buckets" in output
        assert "Created" in output or "All done" in output

    def test_init_buckets_dry_run(self, mock_storage):
        """Test dry run mode."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error

        with patch(
            "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_init_buckets", dry_run=True, stdout=out)

        output = out.getvalue()
        assert "DRY RUN" in output
        assert "Would create bucket" in output

    def test_init_buckets_existing_bucket(self, mock_storage):
        """Test when bucket already exists."""
        out = io.StringIO()
        mock_storage.client.head_bucket.return_value = {}

        with patch(
            "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_init_buckets", stdout=out)

        output = out.getvalue()
        assert "Existing" in output or "All done" in output

    def test_init_buckets_specific_bucket(self, mock_storage):
        """Test creating a specific bucket."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error
        mock_storage.client.create_bucket.return_value = {}

        with patch(
            "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_init_buckets", bucket="my-bucket", public=True, stdout=out)

        output = out.getvalue()
        assert "my-bucket" in output

    def test_init_buckets_skip_static(self, mock_storage):
        """Test skipping static bucket creation."""
        out = io.StringIO()
        mock_storage.client.head_bucket.return_value = {}

        with patch(
            "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_init_buckets", skip_static=True, stdout=out)

        output = out.getvalue()
        assert "All done" in output or "RESULTS" in output

    def test_init_buckets_config_error(self):
        """Test with storage configuration error."""
        out = io.StringIO()

        with (
            patch(
                "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
                side_effect=ImproperlyConfigured("Missing endpoint"),
            ),
            pytest.raises(CommandError) as exc_info,
        ):
            call_command("rustfs_init_buckets", stdout=out)

        assert "Configuration error" in str(exc_info.value)

    def test_init_buckets_static_storage_error(self, mock_storage):
        """Test when static storage configuration fails."""
        out = io.StringIO()
        mock_storage.client.head_bucket.return_value = {}

        with (
            patch(
                "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
                return_value=mock_storage,
            ),
            patch(
                "django_rustfs.management.commands.rustfs_init_buckets.RustFSStaticStorage",
                side_effect=Exception("Static config error"),
            ),
        ):
            call_command("rustfs_init_buckets", stdout=out)

        output = out.getvalue()
        assert "Could not configure static storage" in output

    def test_init_buckets_head_bucket_error(self, mock_storage):
        """Test when head_bucket fails with non-404 error."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "403", "Message": "Access Denied"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error

        with patch(
            "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_init_buckets", stdout=out)

        output = out.getvalue()
        assert "Failed" in output

    def test_init_buckets_create_bucket_error(self, mock_storage):
        """Test when create_bucket fails."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error
        create_error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "CreateBucket",
        )
        mock_storage.client.create_bucket.side_effect = create_error

        with patch(
            "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_init_buckets", stdout=out)

        output = out.getvalue()
        assert "Failed" in output

    def test_init_buckets_public_policy(self, mock_storage):
        """Test creating public bucket with policy."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error
        mock_storage.client.create_bucket.return_value = {}
        mock_storage.client.put_bucket_policy.return_value = {}

        with patch(
            "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_init_buckets", bucket="public-bucket", public=True, stdout=out)

        output = out.getvalue()
        assert "public-bucket" in output
        mock_storage.client.put_bucket_policy.assert_called_once()

    def test_init_buckets_public_policy_error(self, mock_storage):
        """Test when setting public policy fails."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error
        mock_storage.client.create_bucket.return_value = {}
        policy_error = ClientError(
            {"Error": {"Code": "403", "Message": "Access Denied"}},
            "PutBucketPolicy",
        )
        mock_storage.client.put_bucket_policy.side_effect = policy_error

        with patch(
            "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_init_buckets", bucket="public-bucket", public=True, stdout=out)

        output = out.getvalue()
        assert "Could not set public-read" in output

    def test_init_buckets_with_errors_summary(self, mock_storage):
        """Test summary when there are errors."""
        out = io.StringIO()
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        mock_storage.client.head_bucket.side_effect = error
        create_error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "CreateBucket",
        )
        mock_storage.client.create_bucket.side_effect = create_error

        with patch(
            "django_rustfs.management.commands.rustfs_init_buckets.RustFSStorage",
            return_value=mock_storage,
        ):
            call_command("rustfs_init_buckets", stdout=out)

        output = out.getvalue()
        assert "error(s)" in output
