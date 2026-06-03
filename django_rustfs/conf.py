"""
Settings configuration for django-rustfs.

All settings are prefixed with RUSTFS_ to avoid conflicts and provide
a clear, RustFS-branded configuration experience.
"""

from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class Settings:
    """
    Lazy settings accessor with validation.

    Mirrors django-storages' pattern but uses RustFS-branded setting names.
    All settings are read from Django's settings module with sensible defaults.
    """

    # Required settings
    ENDPOINT: str = ""  # e.g., "http://localhost:9000"
    ACCESS_KEY: str = ""
    SECRET_KEY: str = ""

    # Bucket settings
    BUCKET_NAME: str = "django-media"
    STATIC_BUCKET_NAME: str = "django-static"
    AUTO_CREATE_BUCKET: bool = True

    # URL generation
    CUSTOM_DOMAIN: str = ""  # e.g., "cdn.example.com"
    SECURE_URLS: bool = True
    URL_EXPIRATION: int = 3600  # 1 hour in seconds

    # File behavior
    DEFAULT_ACL: str = "private"
    PUBLIC_ACL: str = "public-read"
    FILE_OVERWRITE: bool = False
    OBJECT_PARAMETERS: dict = {}
    LOCATION: str = ""  # Prefix path for all uploaded files
    STATIC_LOCATION: str = ""

    # Connection
    REGION: str = "us-east-1"
    USE_SSL: bool = False
    VERIFY_SSL: bool = True
    MAX_POOL_CONNECTIONS: int = 10
    CONNECT_TIMEOUT: int = 5
    READ_TIMEOUT: int = 30

    # Performance
    PRESIGN_URLS: bool = True  # Generate presigned URLs for private objects
    REDUCED_REDUNDANCY: bool = False
    ENCRYPTION: bool = False

    @classmethod
    def check(cls) -> None:
        """
        Validate that required settings are configured.

        Raises:
            ImproperlyConfigured: If required settings are missing.
        """
        endpoint = getattr(settings, "RUSTFS_ENDPOINT", cls.ENDPOINT)
        if not endpoint:
            raise ImproperlyConfigured(
                "django-rustfs: RUSTFS_ENDPOINT is required. "
                "Example: RUSTFS_ENDPOINT = 'http://localhost:9000'"
            )

        access_key = getattr(settings, "RUSTFS_ACCESS_KEY", cls.ACCESS_KEY)
        if not access_key:
            raise ImproperlyConfigured(
                "django-rustfs: RUSTFS_ACCESS_KEY is required. Set it to your RustFS access key."
            )

        secret_key = getattr(settings, "RUSTFS_SECRET_KEY", cls.SECRET_KEY)
        if not secret_key:
            raise ImproperlyConfigured(
                "django-rustfs: RUSTFS_SECRET_KEY is required. Set it to your RustFS secret key."
            )


def get_setting(name: str, default: Any = None) -> Any:
    """
    Get a django-rustfs setting from Django settings.

    Args:
        name: The setting name without the RUSTFS_ prefix.
        default: The default value if the setting is not defined.

    Returns:
        The setting value or the default.
    """
    return getattr(settings, f"RUSTFS_{name}", default)
