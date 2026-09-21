"""
Tests for django-rustfs storage backend.

Uses moto to mock S3 operations, providing a realistic test environment
without needing a real RustFS server.
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile

from django_rustfs.storage import (
    RustFSError,
    RustFSStaticStorage,
    RustFSStorage,
)


class TestRustFSStorageConfig:
    """Test storage configuration and validation."""

    def test_missing_endpoint_raises(self):
        """Storage should raise ImproperlyConfigured when endpoint is missing."""
        with pytest.raises(ImproperlyConfigured):
            RustFSStorage(
                access_key="test",
                secret_key="test",
                endpoint_url="",
            )

    def test_missing_access_key_raises(self):
        """Storage should raise ImproperlyConfigured when access key is missing."""
        with pytest.raises(ImproperlyConfigured):
            RustFSStorage(
                endpoint_url="http://localhost:9000",
                access_key="",
                secret_key="test",
            )

    def test_missing_secret_key_raises(self):
        """Storage should raise ImproperlyConfigured when secret key is missing."""
        with pytest.raises(ImproperlyConfigured):
            RustFSStorage(
                endpoint_url="http://localhost:9000",
                access_key="test",
                secret_key="",
            )

    def test_valid_config_initializes(self):
        """Storage should initialize with valid configuration."""
        storage = RustFSStorage(
            endpoint_url="http://localhost:9000",
            access_key="test-key",
            secret_key="test-secret",
            bucket_name="django-media",
        )
        assert storage.endpoint_url == "http://localhost:9000"
        assert storage.access_key == "test-key"
        assert storage.secret_key == "test-secret"
        assert storage.bucket_name == "django-media"

    @pytest.mark.parametrize(
        ("endpoint_url", "use_ssl", "expected"),
        [
            ("http://localhost:9000", False, "http://localhost:9000"),
            ("https://localhost:9000", True, "https://localhost:9000"),
            ("localhost:9000", False, "http://localhost:9000"),
            ("localhost:9000", True, "https://localhost:9000"),
        ],
    )
    def test_endpoint_and_ssl_are_resolved(self, endpoint_url, use_ssl, expected):
        """Storage should resolve the endpoint scheme from the SSL setting."""
        storage = RustFSStorage(
            endpoint_url=endpoint_url,
            use_ssl=use_ssl,
            access_key="test",
            secret_key="test",
            auto_create_bucket=False,
        )
        assert storage.endpoint_url == expected
        assert storage.use_ssl is use_ssl

    @pytest.mark.parametrize(
        ("endpoint_url", "use_ssl"),
        [
            ("https://localhost:9000", False),
            ("http://localhost:9000", True),
        ],
    )
    def test_contradictory_endpoint_and_ssl_raises(self, endpoint_url, use_ssl):
        """Storage should reject contradictory endpoint and SSL settings."""
        with pytest.raises(
            ImproperlyConfigured,
            match="RUSTFS_ENDPOINT and RUSTFS_USE_SSL disagree",
        ):
            RustFSStorage(
                endpoint_url=endpoint_url,
                use_ssl=use_ssl,
                access_key="test",
                secret_key="test",
                auto_create_bucket=False,
            )

    def test_custom_bucket_name(self):
        """Storage should accept custom bucket name."""
        storage = RustFSStorage(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
            bucket_name="my-custom-bucket",
        )
        assert storage.bucket_name == "my-custom-bucket"

    def test_settings_from_django_settings(self):
        """Storage should read settings from Django settings module."""
        storage = RustFSStorage()
        assert storage.endpoint_url == settings.RUSTFS_ENDPOINT
        assert storage.access_key == settings.RUSTFS_ACCESS_KEY
        assert storage.bucket_name == settings.RUSTFS_BUCKET_NAME


class TestRustFSStorageOperations:
    """Test storage file operations with mocked S3 client."""

    @pytest.fixture
    def storage(self):
        """Create a RustFSStorage instance with mocked client."""
        storage = RustFSStorage(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
            bucket_name="test-bucket",
            auto_create_bucket=False,
        )
        # Mock the client
        storage._client = MagicMock()
        storage._bucket_exists = True
        # Default: make head_object raise 404 so exists() returns False
        # Tests that need exists()=True can override this
        storage.client.head_object.side_effect = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadObject",
        )
        return storage

    def test_normalize_name_with_location(self, storage):
        """Test that location prefix is correctly applied."""
        storage.location = "media/uploads"
        result = storage._normalize_name("photo.jpg")
        assert result == "media/uploads/photo.jpg"

    def test_normalize_name_without_location(self, storage):
        """Test normalization without location prefix."""
        storage.location = ""
        result = storage._normalize_name("photo.jpg")
        assert result == "photo.jpg"

    def test_normalize_name_strips_leading_slash(self, storage):
        """Test that leading slashes are stripped."""
        storage.location = ""
        result = storage._normalize_name("/photo.jpg")
        assert result == "photo.jpg"

    def test_get_content_type(self, storage):
        """Test content type detection."""
        assert storage._get_content_type("photo.jpg") == "image/jpeg"
        assert storage._get_content_type("file.pdf") == "application/pdf"
        assert storage._get_content_type("unknown.unknownext") == "application/octet-stream"

    def test_exists_true(self, storage):
        """Test exists() when object exists."""
        storage.client.head_object.side_effect = None
        storage.client.head_object.return_value = {"ContentLength": 100}
        assert storage.exists("photo.jpg") is True
        storage.client.head_object.assert_called_once_with(Bucket="test-bucket", Key="photo.jpg")

    def test_exists_false(self, storage):
        """Test exists() when object does not exist."""
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadObject",
        )
        storage.client.head_object.side_effect = error
        assert storage.exists("photo.jpg") is False

    def test_exists_raises_on_other_errors(self, storage):
        """Test exists() re-raises unexpected errors."""
        error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "HeadObject",
        )
        storage.client.head_object.side_effect = error
        with pytest.raises(RustFSError):
            storage.exists("photo.jpg")

    def test_delete(self, storage):
        """Test delete() calls S3 delete_object."""
        storage.delete("photo.jpg")
        storage.client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="photo.jpg")

    def test_delete_raises_on_error(self, storage):
        """Test delete() raises RustFSError on failure."""
        error = ClientError(
            {"Error": {"Code": "403", "Message": "Access Denied"}},
            "DeleteObject",
        )
        storage.client.delete_object.side_effect = error
        with pytest.raises(RustFSError):
            storage.delete("photo.jpg")

    def test_size(self, storage):
        """Test size() returns ContentLength."""
        storage.client.head_object.side_effect = None
        storage.client.head_object.return_value = {"ContentLength": 1024}
        assert storage.size("photo.jpg") == 1024

    def test_url_with_custom_domain(self, storage):
        """Test URL generation with custom domain."""
        storage.custom_domain = "cdn.example.com"
        storage.secure_urls = True
        url = storage.url("photo.jpg")
        assert url == "https://cdn.example.com/photo.jpg"

    def test_url_with_custom_domain_insecure(self, storage):
        """Test URL generation with custom domain and HTTP."""
        storage.custom_domain = "cdn.example.com"
        storage.secure_urls = False
        url = storage.url("photo.jpg")
        assert url == "http://cdn.example.com/photo.jpg"

    def test_url_presigned(self, storage):
        """Test presigned URL generation."""
        storage.presign_urls = True
        storage.default_acl = "private"
        storage.custom_domain = ""
        storage.client.generate_presigned_url.return_value = "http://presigned-url"
        url = storage.url("photo.jpg")
        assert url == "http://presigned-url"
        storage.client.generate_presigned_url.assert_called_once()

    def test_url_direct_for_public(self, storage):
        """Test direct URL for public ACL."""
        storage.presign_urls = True
        storage.default_acl = "public-read"
        storage.custom_domain = ""
        url = storage.url("photo.jpg")
        assert "test-bucket" in url
        assert "photo.jpg" in url

    def test_open(self, storage):
        """Test _open() returns a File object with correct content."""
        storage.client.get_object.return_value = {"Body": io.BytesIO(b"file content")}
        file_obj = storage._open("test.txt")
        assert file_obj.read() == b"file content"

    def test_open_raises_on_error(self, storage):
        """Test _open() raises RustFSError on failure."""
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "GetObject",
        )
        storage.client.get_object.side_effect = error
        with pytest.raises(RustFSError):
            storage._open("missing.txt")

    def test_save(self, storage):
        """Test _save() uploads file to S3."""
        content = ContentFile(b"test content", name="test.txt")
        result = storage._save("uploads/test.txt", content)
        assert result == "uploads/test.txt"
        storage.client.put_object.assert_called_once()
        call_kwargs = storage.client.put_object.call_args.kwargs
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == "uploads/test.txt"
        assert call_kwargs["ContentType"] == "text/plain"

    def test_save_raises_on_error(self, storage):
        """Test _save() raises RustFSError on upload failure."""
        error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "PutObject",
        )
        storage.client.put_object.side_effect = error
        content = ContentFile(b"test content")
        with pytest.raises(RustFSError):
            storage._save("test.txt", content)

    def test_listdir(self, storage):
        """Test listdir() returns directories and files."""
        storage.client.get_paginator.return_value.paginate.return_value = [
            {
                "CommonPrefixes": [
                    {"Prefix": "media/images/"},
                    {"Prefix": "media/docs/"},
                ],
                "Contents": [
                    {"Key": "media/file1.txt"},
                    {"Key": "media/file2.jpg"},
                ],
            }
        ]
        dirs, files = storage.listdir("media")
        assert "images" in dirs
        assert "docs" in dirs
        assert "file1.txt" in files
        assert "file2.jpg" in files

    def test_get_object_metadata(self, storage):
        """Test get_object_metadata() returns parsed metadata."""
        from datetime import datetime, timezone

        timestamp = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        storage.client.head_object.side_effect = None
        storage.client.head_object.return_value = {
            "ETag": '"abc123"',
            "LastModified": timestamp,
            "ContentType": "image/jpeg",
            "ContentLength": 2048,
            "StorageClass": "STANDARD",
            "Metadata": {"custom": "value"},
            "VersionId": "v1",
        }
        meta = storage.get_object_metadata("photo.jpg")
        assert meta["etag"] == "abc123"
        assert meta["content_type"] == "image/jpeg"
        assert meta["content_length"] == 2048
        assert meta["storage_class"] == "STANDARD"
        assert meta["metadata"]["custom"] == "value"

    def test_copy_object(self, storage):
        """Test copy_object() calls S3 copy."""
        storage.copy_object("source.txt", "dest.txt")
        storage.client.copy_object.assert_called_once()
        call_kwargs = storage.client.copy_object.call_args.kwargs
        assert call_kwargs["Bucket"] == "test-bucket"
        assert call_kwargs["Key"] == "dest.txt"
        assert call_kwargs["CopySource"]["Bucket"] == "test-bucket"
        assert call_kwargs["CopySource"]["Key"] == "source.txt"

    def test_get_presigned_post_url(self, storage):
        """Test get_presigned_post_url() generates POST data."""
        storage.client.generate_presigned_post.return_value = {
            "url": "http://localhost:9000/test-bucket",
            "fields": {"key": "uploads/file.jpg"},
        }
        result = storage.get_presigned_post_url("uploads/file.jpg")
        assert result["url"] == "http://localhost:9000/test-bucket"
        assert result["fields"]["key"] == "uploads/file.jpg"

    def test_is_available_true(self, storage):
        """Test is_available() returns True when healthy."""
        storage.client.head_bucket.return_value = {}
        assert storage.is_available() is True

    def test_is_available_false(self, storage):
        """Test is_available() returns False when connection fails."""
        storage.client.head_bucket.side_effect = Exception("Connection refused")
        assert storage.is_available() is False

    def test_path_raises(self, storage):
        """Test path() raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            storage.path("test.txt")

    def test_size_raises_on_error(self, storage):
        """Test size() raises RustFSError on failure."""
        error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "HeadObject",
        )
        storage.client.head_object.side_effect = error
        with pytest.raises(RustFSError):
            storage.size("photo.jpg")

    def test_url_presigned_raises_on_error(self, storage):
        """Test url() raises RustFSError when presign fails."""
        storage.presign_urls = True
        storage.default_acl = "private"
        storage.custom_domain = ""
        error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "GetObject",
        )
        storage.client.generate_presigned_url.side_effect = error
        with pytest.raises(RustFSError):
            storage.url("photo.jpg")

    def test_get_available_name_with_overwrite(self, storage):
        """Test get_available_name when file_overwrite is True."""
        storage.file_overwrite = True
        result = storage.get_available_name("photo.jpg")
        assert result == "photo.jpg"

    def test_get_object_metadata_raises_on_error(self, storage):
        """Test get_object_metadata raises RustFSError on failure."""
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadObject",
        )
        storage.client.head_object.side_effect = error
        with pytest.raises(RustFSError):
            storage.get_object_metadata("photo.jpg")

    def test_copy_object_raises_on_error(self, storage):
        """Test copy_object raises RustFSError on failure."""
        error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "CopyObject",
        )
        storage.client.copy_object.side_effect = error
        with pytest.raises(RustFSError):
            storage.copy_object("source.txt", "dest.txt")

    def test_get_presigned_post_url_raises_on_error(self, storage):
        """Test get_presigned_post_url raises RustFSError on failure."""
        error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "GeneratePresignedPost",
        )
        storage.client.generate_presigned_post.side_effect = error
        with pytest.raises(RustFSError):
            storage.get_presigned_post_url("uploads/file.jpg")


class TestRustFSStaticStorage:
    """Test RustFSStaticStorage specific behavior."""

    def test_static_defaults(self):
        """Static storage should have public-read defaults."""
        with patch.object(RustFSStaticStorage, "_validate_config"):
            storage = RustFSStaticStorage(
                endpoint_url="http://localhost:9000",
                access_key="test",
                secret_key="test",
                bucket_name="static-bucket",
            )
            # Don't check _bucket_exists since we mocked _validate_config
            assert storage.bucket_name == "static-bucket"

    def test_static_url_no_presign(self):
        """Static URLs should not use presigned URLs."""
        with patch.object(RustFSStaticStorage, "_validate_config"):
            storage = RustFSStaticStorage(
                endpoint_url="http://localhost:9000",
                access_key="test",
                secret_key="test",
            )
            storage._client = MagicMock()
            url = storage.url("css/style.css")
            # Should be a direct URL, not call generate_presigned_url
            storage.client.generate_presigned_url.assert_not_called()
            assert "css/style.css" in url

    def test_static_url_with_custom_domain(self):
        """Test RustFSStaticStorage.url with custom domain."""
        with patch.object(RustFSStaticStorage, "_validate_config"):
            storage = RustFSStaticStorage(
                endpoint_url="http://localhost:9000",
                access_key="test",
                secret_key="test",
                custom_domain="cdn.example.com",
                secure_urls=True,
            )
            url = storage.url("css/style.css")
            assert url == "https://cdn.example.com/static/css/style.css"


class TestIntegrationWithMoto:
    """Integration tests using moto mock S3."""

    @pytest.fixture
    def mock_s3(self):
        """Set up moto mock S3 environment."""
        from moto import mock_aws

        with mock_aws():
            # Create the S3 service with our endpoint
            import boto3

            conn = boto3.client(
                "s3",
                region_name="us-east-1",
                aws_access_key_id="test",
                aws_secret_access_key="test",
            )
            conn.create_bucket(Bucket="test-bucket")
            yield conn

    @pytest.fixture
    def real_storage(self, mock_s3):
        """Create a storage instance that uses the mock S3."""
        storage = RustFSStorage(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
            bucket_name="test-bucket",
            auto_create_bucket=False,
            region="us-east-1",
        )
        # Replace client with mock
        storage._client = mock_s3
        storage._bucket_exists = True
        return storage

    def test_full_upload_download_delete_cycle(self, real_storage):
        """Test complete file lifecycle with moto."""
        # Upload
        content = ContentFile(b"Hello, RustFS!", name="hello.txt")
        saved_name = real_storage.save("hello.txt", content)
        assert saved_name == "hello.txt"

        # Check exists
        assert real_storage.exists("hello.txt") is True

        # Get size
        assert real_storage.size("hello.txt") == 14

        # Download
        file_obj = real_storage.open("hello.txt")
        assert file_obj.read() == b"Hello, RustFS!"

        # Delete
        real_storage.delete("hello.txt")
        assert real_storage.exists("hello.txt") is False

    def test_listdir_with_moto(self, real_storage):
        """Test listdir with moto mock."""
        # Create some objects
        real_storage.client.put_object(Bucket="test-bucket", Key="prefix/folder1/", Body=b"")
        real_storage.client.put_object(
            Bucket="test-bucket", Key="prefix/file1.txt", Body=b"content1"
        )
        real_storage.client.put_object(
            Bucket="test-bucket", Key="prefix/file2.jpg", Body=b"content2"
        )

        dirs, files = real_storage.listdir("prefix")
        assert "folder1" in dirs
        assert "file1.txt" in files
        assert "file2.jpg" in files

    def test_client_property_creates_boto3_client(self):
        """Test that client property creates a real boto3 client."""
        storage = RustFSStorage(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
            auto_create_bucket=False,
        )
        # Access client property - should create boto3 client
        client = storage.client
        assert client is not None
        assert storage._client is not None

    def test_ensure_bucket_exists(self):
        """Test _ensure_bucket when bucket already exists."""
        storage = RustFSStorage(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
            auto_create_bucket=False,
        )
        storage._client = MagicMock()
        storage._bucket_exists = False
        storage.client.head_bucket.return_value = {}

        storage._ensure_bucket()
        assert storage._bucket_exists is True
        storage.client.head_bucket.assert_called_once_with(Bucket=storage.bucket_name)

    def test_ensure_bucket_creates_when_missing(self):
        """Test _ensure_bucket creates bucket when it doesn't exist."""
        storage = RustFSStorage(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
            auto_create_bucket=False,
        )
        storage._client = MagicMock()
        storage._bucket_exists = False
        error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        storage.client.head_bucket.side_effect = error
        storage.client.create_bucket.return_value = {}

        storage._ensure_bucket()
        assert storage._bucket_exists is True
        storage.client.create_bucket.assert_called_once_with(Bucket=storage.bucket_name)

    def test_ensure_bucket_create_fails(self):
        """Test _ensure_bucket raises when create fails."""
        from django_rustfs.storage import RustFSBucketError

        storage = RustFSStorage(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
            auto_create_bucket=False,
        )
        storage._client = MagicMock()
        storage._bucket_exists = False
        head_error = ClientError(
            {"Error": {"Code": "404", "Message": "Not Found"}},
            "HeadBucket",
        )
        storage.client.head_bucket.side_effect = head_error
        create_error = ClientError(
            {"Error": {"Code": "500", "Message": "Internal Error"}},
            "CreateBucket",
        )
        storage.client.create_bucket.side_effect = create_error

        with pytest.raises(RustFSBucketError) as exc_info:
            storage._ensure_bucket()

        assert "Failed to create bucket" in str(exc_info.value)

    def test_ensure_bucket_other_error(self):
        """Test _ensure_bucket raises on non-404 head_bucket error."""
        from django_rustfs.storage import RustFSBucketError

        storage = RustFSStorage(
            endpoint_url="http://localhost:9000",
            access_key="test",
            secret_key="test",
            auto_create_bucket=False,
        )
        storage._client = MagicMock()
        storage._bucket_exists = False
        error = ClientError(
            {"Error": {"Code": "403", "Message": "Access Denied"}},
            "HeadBucket",
        )
        storage.client.head_bucket.side_effect = error

        with pytest.raises(RustFSBucketError) as exc_info:
            storage._ensure_bucket()

        assert "Failed to check bucket" in str(exc_info.value)
