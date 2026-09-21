"""
RustFS storage backend for Django.

This module provides the core RustFSStorage class that implements Django's
file storage API, backed by RustFS's S3-compatible interface via boto3.
"""

import io
import mimetypes
import posixpath
from typing import Any, Optional

import boto3
import botocore.config
from botocore.exceptions import ClientError
from django.conf import settings as django_settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.encoding import filepath_to_uri

from django_rustfs.conf import DEFAULTS, Settings, resolve_endpoint


class RustFSError(Exception):
    """Base exception for RustFS storage errors."""

    pass


class RustFSBucketError(RustFSError):
    """Raised when a bucket operation fails."""

    pass


@deconstructible
class RustFSStorage(Storage):
    """
    Django storage backend for RustFS object storage.

    RustFS is a high-performance, S3-compatible object storage built in Rust.
    This storage class uses boto3 to communicate with RustFS, providing a
    clean, purpose-built API that feels native to the RustFS ecosystem.

    Quick start:
        # settings.py
        RUSTFS_ENDPOINT = "http://localhost:9000"
        RUSTFS_ACCESS_KEY = "your-access-key"
        RUSTFS_SECRET_KEY = "your-secret-key"
        RUSTFS_BUCKET_NAME = "my-bucket"

        DEFAULT_FILE_STORAGE = "django_rustfs.storage.RustFSStorage"

    For static files:
        STORAGES = {
            "default": {
                "BACKEND": "django_rustfs.storage.RustFSStorage",
            },
            "staticfiles": {
                "BACKEND": "django_rustfs.storage.RustFSStaticStorage",
            },
        }

    Attributes:
        endpoint_url: The RustFS server endpoint (e.g., "http://localhost:9000")
        bucket_name: The default bucket for file storage
        auto_create_bucket: Whether to create the bucket if it doesn't exist
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the RustFS storage backend.

        Args:
            **kwargs: Override any setting at initialization time.
                      All RUSTFS_* settings can be passed as kwargs
                      without the RUSTFS_ prefix (lowercase).
        """
        # Collect all settings
        # Note: kwarg_key maps the attribute name to the expected kwarg name
        self.endpoint_url = self._setting("ENDPOINT", kwargs, kwarg_key="endpoint_url")
        self.access_key = self._setting("ACCESS_KEY", kwargs, kwarg_key="access_key")
        self.secret_key = self._setting("SECRET_KEY", kwargs, kwarg_key="secret_key")
        self.bucket_name = self._setting(
            "BUCKET_NAME", kwargs, "django-media", kwarg_key="bucket_name"
        )
        self.auto_create_bucket = self._setting(
            "AUTO_CREATE_BUCKET", kwargs, True, kwarg_key="auto_create_bucket"
        )
        self.custom_domain = self._setting("CUSTOM_DOMAIN", kwargs, "", kwarg_key="custom_domain")
        self.secure_urls = self._setting("SECURE_URLS", kwargs, True, kwarg_key="secure_urls")
        self.url_expiration = self._setting(
            "URL_EXPIRATION", kwargs, 3600, kwarg_key="url_expiration"
        )
        self.default_acl = self._setting("DEFAULT_ACL", kwargs, "private", kwarg_key="default_acl")
        self.public_acl = self._setting("PUBLIC_ACL", kwargs, "public-read", kwarg_key="public_acl")
        self.file_overwrite = self._setting(
            "FILE_OVERWRITE", kwargs, False, kwarg_key="file_overwrite"
        )
        self.object_parameters = self._setting(
            "OBJECT_PARAMETERS", kwargs, {}, kwarg_key="object_parameters"
        )
        self.location = self._setting("LOCATION", kwargs, "", kwarg_key="location").lstrip("/")
        self.region = self._setting("REGION", kwargs, "us-east-1", kwarg_key="region")
        self.use_ssl = self._setting("USE_SSL", kwargs, False, kwarg_key="use_ssl")
        self.endpoint_url = resolve_endpoint(self.endpoint_url, self.use_ssl)
        self.verify_ssl = self._setting("VERIFY_SSL", kwargs, True, kwarg_key="verify_ssl")
        self.max_pool_connections = self._setting(
            "MAX_POOL_CONNECTIONS", kwargs, 10, kwarg_key="max_pool_connections"
        )
        self.presign_urls = self._setting("PRESIGN_URLS", kwargs, True, kwarg_key="presign_urls")
        self.connect_timeout = self._setting(
            "CONNECT_TIMEOUT", kwargs, 5, kwarg_key="connect_timeout"
        )
        self.read_timeout = self._setting("READ_TIMEOUT", kwargs, 30, kwarg_key="read_timeout")

        # Validate required settings
        self._validate_config()

        # Initialize boto3 client (lazy)
        self._client = None
        self._resource = None

        # Cache for bucket existence check
        self._bucket_exists = False

        super().__init__()

    def _setting(
        self, name: str, kwargs: dict, default: Any = "", kwarg_key: Optional[str] = None
    ) -> Any:
        """
        Get a setting value from kwargs or Django settings.

        Priority:
            1. kwargs (direct override)
            2. Django settings (RUSTFS_*)
            3. Default value

        Args:
            name: The setting name (used to build RUSTFS_* setting key).
            kwargs: The kwargs dict passed to __init__.
            default: Default value if not found elsewhere.
            kwarg_key: Optional custom kwarg key. Defaults to name.lower().
        """
        key = kwarg_key or name.lower()
        if key in kwargs:
            return kwargs.pop(key)
        if name in DEFAULTS:
            return Settings.get(name)
        return getattr(django_settings, f"RUSTFS_{name}", default)

    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.endpoint_url:
            raise ImproperlyConfigured(
                "django-rustfs: 'endpoint_url' (RUSTFS_ENDPOINT) is required. "
                "Example: RUSTFS_ENDPOINT = 'http://localhost:9000'"
            )
        if not self.access_key:
            raise ImproperlyConfigured(
                "django-rustfs: 'access_key' (RUSTFS_ACCESS_KEY) is required."
            )
        if not self.secret_key:
            raise ImproperlyConfigured(
                "django-rustfs: 'secret_key' (RUSTFS_SECRET_KEY) is required."
            )

    @property
    def client(self) -> Any:
        """Lazy-initialized boto3 S3 client for RustFS."""
        if self._client is None:
            config = botocore.config.Config(
                max_pool_connections=self.max_pool_connections,
                connect_timeout=self.connect_timeout,
                read_timeout=self.read_timeout,
            )
            self._client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region,
                use_ssl=self.use_ssl,
                verify=self.verify_ssl,
                config=config,
            )
            # Ensure bucket exists on first access
            if self.auto_create_bucket:
                self._ensure_bucket()
        return self._client

    def _ensure_bucket(self) -> None:
        """Create the bucket if it doesn't exist."""
        if self._bucket_exists:
            return

        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            self._bucket_exists = True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "404":
                try:
                    self.client.create_bucket(Bucket=self.bucket_name)
                    self._bucket_exists = True
                except ClientError as create_error:
                    raise RustFSBucketError(
                        f"Failed to create bucket '{self.bucket_name}': {create_error}"
                    ) from create_error
            else:
                raise RustFSBucketError(f"Failed to check bucket '{self.bucket_name}': {e}") from e

    def _normalize_name(self, name: str) -> str:
        """
        Normalize the file name by prepending the location prefix.

        Args:
            name: The file name/path.

        Returns:
            The normalized path with location prefix.
        """
        name = name.replace("\\", "/")
        if self.location:
            name = posixpath.join(self.location, name)
        return name.lstrip("/")

    def _get_content_type(self, name: str) -> str:
        """Guess the content type from the file name."""
        content_type, _ = mimetypes.guess_type(name)
        return content_type or "application/octet-stream"

    def _get_write_parameters(self, name: str) -> dict:
        """
        Build the parameters for S3 put_object.

        Args:
            name: The file name/path.

        Returns:
            Dictionary of S3 put_object parameters.
        """
        params = {
            "Bucket": self.bucket_name,
            "Key": self._normalize_name(name),
            "ContentType": self._get_content_type(name),
            "ACL": self.default_acl,
        }
        params.update(self.object_parameters)
        return params

    # ------------------------------------------------------------------
    # Django Storage API implementation
    # ------------------------------------------------------------------

    def _open(self, name: str, mode: str = "rb") -> File:
        """
        Open a file from RustFS storage.

        Args:
            name: The file name/path in storage.
            mode: The file mode (only 'rb' is supported for remote storage).

        Returns:
            A Django File-like object wrapping the S3 object content.
        """
        key = self._normalize_name(name)
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=key)
            content = response["Body"].read()
            return File(io.BytesIO(content), name=name)
        except ClientError as e:
            raise RustFSError(f"Failed to open '{name}' from RustFS: {e}") from e

    def _save(self, name: str, content: File) -> str:
        """
        Save a file to RustFS storage.

        Args:
            name: The desired file name/path.
            content: The file content (Django File object).

        Returns:
            The final file name used in storage.
        """
        # Handle file overwrite behavior
        if not self.file_overwrite:
            name = self.get_available_name(name)

        params = self._get_write_parameters(name)
        params["Body"] = content

        try:
            self.client.put_object(**params)
        except ClientError as e:
            raise RustFSError(f"Failed to save '{name}' to RustFS: {e}") from e

        return name

    def delete(self, name: str) -> None:
        """
        Delete a file from RustFS storage.

        Args:
            name: The file name/path to delete.
        """
        key = self._normalize_name(name)
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
        except ClientError as e:
            raise RustFSError(f"Failed to delete '{name}' from RustFS: {e}") from e

    def exists(self, name: str) -> bool:
        """
        Check if a file exists in RustFS storage.

        Args:
            name: The file name/path to check.

        Returns:
            True if the file exists, False otherwise.
        """
        key = self._normalize_name(name)
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise RustFSError(f"Failed to check existence of '{name}': {e}") from e

    def size(self, name: str) -> int:
        """
        Get the size of a file in bytes.

        Args:
            name: The file name/path.

        Returns:
            The file size in bytes.
        """
        key = self._normalize_name(name)
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=key)
            return int(response["ContentLength"])
        except ClientError as e:
            raise RustFSError(f"Failed to get size of '{name}': {e}") from e

    def url(self, name: Optional[str]) -> str:
        """
        Get the URL for a file.

        For private buckets, generates a presigned URL.
        For public buckets, returns the direct URL.

        Args:
            name: The file name/path.

        Returns:
            The URL to access the file.
        """
        if name is None:
            return ""
        key = self._normalize_name(name)

        # If custom domain is set, use it for direct URLs
        if self.custom_domain:
            scheme = "https" if self.use_ssl else "http"
            domain = self.custom_domain.rstrip("/")
            return f"{scheme}://{domain}/{filepath_to_uri(key)}"

        # Generate presigned URL for private access
        if self.presign_urls and self.default_acl == "private":
            try:
                return str(
                    self.client.generate_presigned_url(
                        "get_object",
                        Params={"Bucket": self.bucket_name, "Key": key},
                        ExpiresIn=self.url_expiration,
                    )
                )
            except ClientError as e:
                raise RustFSError(f"Failed to generate URL for '{name}': {e}") from e

        # Direct URL via endpoint
        scheme = "https" if self.use_ssl else "http"
        endpoint = self.endpoint_url.rstrip("/")
        return (
            f"{scheme}://{endpoint.split('://', 1)[-1]}/{self.bucket_name}/{filepath_to_uri(key)}"
        )

    def listdir(self, path: str = "") -> tuple:
        """
        List directories and files in the given path.

        Args:
            path: The directory path to list.

        Returns:
            A tuple of (directories, files).
        """
        prefix = self._normalize_name(path)
        if prefix and not prefix.endswith("/"):
            prefix += "/"

        directories = set()
        files = []

        paginator = self.client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.bucket_name,
            Prefix=prefix,
            Delimiter="/",
        )

        for page in page_iterator:
            # Extract common prefixes (directories)
            for common_prefix in page.get("CommonPrefixes", []):
                dir_name = common_prefix["Prefix"][len(prefix) :].rstrip("/")
                if dir_name:
                    directories.add(dir_name)

            # Extract files
            for obj in page.get("Contents", []):
                file_name = obj["Key"][len(prefix) :]
                if file_name:
                    files.append(file_name)

        return list(directories), files

    def get_available_name(self, name: str, max_length: Optional[int] = None) -> str:
        """
        Get an available name for the file, handling duplicates.

        If file_overwrite is False, appends a counter to avoid overwriting.

        Args:
            name: The desired file name.
            max_length: Maximum length of the file name.

        Returns:
            An available file name.
        """
        if self.file_overwrite:
            return name

        # Use Django's default behavior with existence check
        return super().get_available_name(name, max_length)

    def path(self, name: str) -> str:
        """
        Return the local filesystem path.

        Raises NotImplementedError since RustFS is remote storage.
        """
        raise NotImplementedError("RustFS storage does not support local filesystem paths.")

    # ------------------------------------------------------------------
    # RustFS-specific convenience methods
    # ------------------------------------------------------------------

    def get_object_metadata(self, name: str) -> dict:
        """
        Get full metadata for an object from RustFS.

        This provides access to RustFS-specific metadata like ETag,
        LastModified, StorageClass, and custom metadata.

        Args:
            name: The file name/path.

        Returns:
            Dictionary of object metadata from RustFS.
        """
        key = self._normalize_name(name)
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=key)
            return {
                "etag": response.get("ETag", "").strip('"'),
                "last_modified": response.get("LastModified"),
                "content_type": response.get("ContentType", ""),
                "content_length": response.get("ContentLength", 0),
                "storage_class": response.get("StorageClass", "STANDARD"),
                "metadata": response.get("Metadata", {}),
                "version_id": response.get("VersionId", ""),
            }
        except ClientError as e:
            raise RustFSError(f"Failed to get metadata for '{name}': {e}") from e

    def copy_object(self, source_name: str, dest_name: str) -> None:
        """
        Copy an object within RustFS.

        Args:
            source_name: The source file name/path.
            dest_name: The destination file name/path.
        """
        source_key = self._normalize_name(source_name)
        dest_key = self._normalize_name(dest_name)
        copy_source = {
            "Bucket": self.bucket_name,
            "Key": source_key,
        }
        try:
            self.client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key,
            )
        except ClientError as e:
            raise RustFSError(f"Failed to copy '{source_name}' to '{dest_name}': {e}") from e

    def get_presigned_post_url(
        self,
        name: str,
        expires_in: int = 3600,
        fields: Optional[dict] = None,
        conditions: Optional[list] = None,
    ) -> dict:
        """
        Generate a presigned POST URL for direct browser uploads.

        This allows browsers to upload files directly to RustFS without
        going through your Django server - ideal for large files.

        Args:
            name: The object key (file path) to upload to.
            expires_in: URL expiration time in seconds.
            fields: Additional form fields to include.
            conditions: POST policy conditions.

        Returns:
            Dictionary with 'url' and 'fields' for the POST request.
        """
        key = self._normalize_name(name)
        try:
            result = self.client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=key,
                Fields=fields or {},
                Conditions=conditions or [],
                ExpiresIn=expires_in,
            )
            return dict(result)
        except ClientError as e:
            raise RustFSError(f"Failed to generate presigned POST URL for '{name}': {e}") from e

    def is_available(self) -> bool:
        """
        Check if the RustFS server is reachable and healthy.

        Returns:
            True if RustFS is available, False otherwise.
        """
        try:
            # Use head_bucket as a lightweight health check
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except Exception:
            return False


class RustFSStaticStorage(RustFSStorage):
    """
    Storage backend for Django static files on RustFS.

    Uses a separate bucket and public-read ACL by default so that
    static files (CSS, JS, images) are directly accessible via URL.

    Configuration (in settings.py):
        RUSTFS_STATIC_BUCKET_NAME = "django-static"
        RUSTFS_STATIC_LOCATION = "static/"
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize static file storage with static-specific defaults.

        Overrides bucket name, location, and ACL for static files.
        """
        # Set static-specific defaults before calling super
        kwargs.setdefault(
            "bucket_name", self._static_setting("STATIC_BUCKET_NAME", "django-static")
        )
        kwargs.setdefault("location", self._static_setting("STATIC_LOCATION", "static"))
        kwargs.setdefault("default_acl", self._static_setting("STATIC_DEFAULT_ACL", "public-read"))
        kwargs.setdefault("presign_urls", False)  # Static files should be public
        kwargs.setdefault("file_overwrite", True)  # Allow overwrite for collectstatic
        super().__init__(**kwargs)

    def _static_setting(self, name: str, default: Any) -> Any:
        """Get a static-specific setting."""
        return getattr(django_settings, f"RUSTFS_{name}", default)

    def url(self, name: Optional[str]) -> str:
        """
        Return the URL for a static file.

        Static files use public-read ACL and direct URLs (no presigning).
        """
        if name is None:
            return ""
        key = self._normalize_name(name)

        if self.custom_domain:
            scheme = "https" if self.secure_urls else "http"
            domain = self.custom_domain.rstrip("/")
            return f"{scheme}://{domain}/{filepath_to_uri(key)}"

        # Direct URL through endpoint
        endpoint = self.endpoint_url.rstrip("/")
        return f"{endpoint}/{self.bucket_name}/{filepath_to_uri(key)}"
