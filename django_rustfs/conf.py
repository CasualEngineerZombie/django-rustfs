"""
Settings configuration for django-rustfs.

All settings are prefixed with RUSTFS_ to avoid conflicts and provide
a clear, RustFS-branded configuration experience.
"""

from typing import Any

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


# Canonical defaults for all django-rustfs settings.
# Keep configuration defaults here rather than duplicating them in consumers.
DEFAULTS: dict[str, Any] = {
    # Required settings
    "ENDPOINT": "",
    "ACCESS_KEY": "",
    "SECRET_KEY": "",
    # Bucket settings
    "BUCKET_NAME": "django-media",
    "STATIC_BUCKET_NAME": "django-static",
    "AUTO_CREATE_BUCKET": True,
    # URL generation
    "CUSTOM_DOMAIN": "",
    "SECURE_URLS": True,
    "URL_EXPIRATION": 3600,
    # File behavior
    "DEFAULT_ACL": "private",
    "PUBLIC_ACL": "public-read",
    "FILE_OVERWRITE": False,
    "OBJECT_PARAMETERS": {},
    "LOCATION": "",
    "STATIC_LOCATION": "",
    # Connection
    "REGION": "us-east-1",
    "USE_SSL": False,
    "VERIFY_SSL": True,
    "MAX_POOL_CONNECTIONS": 10,
    "CONNECT_TIMEOUT": 5,
    "READ_TIMEOUT": 30,
    # Performance
    "PRESIGN_URLS": True,
    "REDUCED_REDUNDANCY": False,
    "ENCRYPTION": False,
}


class Settings:
    """
    Lazy settings accessor with validation.

    Django settings override the canonical defaults defined in this module.
    """

    # Preserve the public Settings attributes while deriving their defaults
    # from the single DEFAULTS mapping above.
    ENDPOINT: str = DEFAULTS["ENDPOINT"]
    ACCESS_KEY: str = DEFAULTS["ACCESS_KEY"]
    SECRET_KEY: str = DEFAULTS["SECRET_KEY"]
    BUCKET_NAME: str = DEFAULTS["BUCKET_NAME"]
    STATIC_BUCKET_NAME: str = DEFAULTS["STATIC_BUCKET_NAME"]
    AUTO_CREATE_BUCKET: bool = DEFAULTS["AUTO_CREATE_BUCKET"]
    CUSTOM_DOMAIN: str = DEFAULTS["CUSTOM_DOMAIN"]
    SECURE_URLS: bool = DEFAULTS["SECURE_URLS"]
    URL_EXPIRATION: int = DEFAULTS["URL_EXPIRATION"]
    DEFAULT_ACL: str = DEFAULTS["DEFAULT_ACL"]
    PUBLIC_ACL: str = DEFAULTS["PUBLIC_ACL"]
    FILE_OVERWRITE: bool = DEFAULTS["FILE_OVERWRITE"]
    OBJECT_PARAMETERS: dict = DEFAULTS["OBJECT_PARAMETERS"]
    LOCATION: str = DEFAULTS["LOCATION"]
    STATIC_LOCATION: str = DEFAULTS["STATIC_LOCATION"]
    REGION: str = DEFAULTS["REGION"]
    USE_SSL: bool = DEFAULTS["USE_SSL"]
    VERIFY_SSL: bool = DEFAULTS["VERIFY_SSL"]
    MAX_POOL_CONNECTIONS: int = DEFAULTS["MAX_POOL_CONNECTIONS"]
    CONNECT_TIMEOUT: int = DEFAULTS["CONNECT_TIMEOUT"]
    READ_TIMEOUT: int = DEFAULTS["READ_TIMEOUT"]
    PRESIGN_URLS: bool = DEFAULTS["PRESIGN_URLS"]
    REDUCED_REDUNDANCY: bool = DEFAULTS["REDUCED_REDUNDANCY"]
    ENCRYPTION: bool = DEFAULTS["ENCRYPTION"]

    @classmethod
    def get(cls, name: str) -> Any:
        """Get a setting using Django settings with the canonical default."""
        return getattr(settings, f"RUSTFS_{name}", DEFAULTS[name])

    @classmethod
    def check(cls) -> None:
        """
        Validate that required settings are configured.

        Raises:
            ImproperlyConfigured: If required settings are missing.
        """
        if not cls.get("ENDPOINT"):
            raise ImproperlyConfigured(
                "django-rustfs: RUSTFS_ENDPOINT is required. "
                "Example: RUSTFS_ENDPOINT = 'http://localhost:9000'"
            )

        if not cls.get("ACCESS_KEY"):
            raise ImproperlyConfigured(
                "django-rustfs: RUSTFS_ACCESS_KEY is required. Set it to your RustFS access key."
            )

        if not cls.get("SECRET_KEY"):
            raise ImproperlyConfigured(
                "django-rustfs: RUSTFS_SECRET_KEY is required. Set it to your RustFS secret key."
            )


def get_setting(name: str, default: Any = None) -> Any:
    """
    Get a django-rustfs setting from Django settings.

    Args:
        name: The setting name without the RUSTFS_ prefix.
        default: Optional fallback. If omitted, the canonical default is used.

    Returns:
        The setting value or the configured/default value.
    """
    if default is None and name in DEFAULTS:
        default = DEFAULTS[name]
    return getattr(settings, f"RUSTFS_{name}", default)
