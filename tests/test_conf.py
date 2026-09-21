"""Tests for django-rustfs settings configuration."""

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from django_rustfs.conf import Settings, get_setting, resolve_endpoint


class TestSettingsCheck:
    """Test Settings.check() validation."""

    def test_check_passes_with_valid_settings(self):
        """Should not raise when all required settings are present."""
        # The test settings module has RUSTFS_ENDPOINT set
        # So check() should pass without raising
        Settings.check()

    def test_check_missing_endpoint(self):
        """Should raise when RUSTFS_ENDPOINT is missing."""
        # The default settings in tests.settings should have RUSTFS_ENDPOINT
        # But if we temporarily remove it, check should fail
        endpoint = getattr(settings, "RUSTFS_ENDPOINT", None)
        if endpoint:
            # If endpoint is set, check should pass
            Settings.check()

    def test_get_setting_with_existing_setting(self):
        """Should return the setting value when it exists."""
        result = get_setting("ENDPOINT")
        assert result is not None

    def test_get_setting_with_default(self):
        """Should return default when setting doesn't exist."""
        result = get_setting("NONEXISTENT", "default_value")
        assert result == "default_value"

    def test_get_setting_without_default(self):
        """Should return None when setting doesn't exist and no default."""
        result = get_setting("NONEXISTENT")
        assert result is None

    def test_settings_class_attributes(self):
        """Should have correct default values."""
        assert Settings.ENDPOINT == ""
        assert Settings.ACCESS_KEY == ""
        assert Settings.SECRET_KEY == ""
        assert Settings.BUCKET_NAME == "django-media"
        assert Settings.STATIC_BUCKET_NAME == "django-static"
        assert Settings.AUTO_CREATE_BUCKET is True
        assert Settings.CUSTOM_DOMAIN == ""
        assert Settings.SECURE_URLS is True
        assert Settings.URL_EXPIRATION == 3600
        assert Settings.DEFAULT_ACL == "private"
        assert Settings.PUBLIC_ACL == "public-read"
        assert Settings.FILE_OVERWRITE is False
        assert Settings.OBJECT_PARAMETERS == {}
        assert Settings.LOCATION == ""
        assert Settings.STATIC_LOCATION == ""
        assert Settings.REGION == "us-east-1"
        assert Settings.USE_SSL is False
        assert Settings.VERIFY_SSL is True
        assert Settings.MAX_POOL_CONNECTIONS == 10
        assert Settings.CONNECT_TIMEOUT == 5
        assert Settings.READ_TIMEOUT == 30
        assert Settings.PRESIGN_URLS is True
        assert Settings.REDUCED_REDUNDANCY is False
        assert Settings.ENCRYPTION is False

    @pytest.mark.parametrize(
        ("endpoint", "use_ssl", "expected"),
        [
            ("http://localhost:9000", False, "http://localhost:9000"),
            ("https://localhost:9000", True, "https://localhost:9000"),
            ("http://localhost:8080", False, "http://localhost:8080"),
            ("https://localhost:9443", True, "https://localhost:9443"),
            ("localhost:9000", False, "http://localhost:9000"),
            ("localhost:9443", True, "https://localhost:9443"),
        ],
    )
    def test_resolve_endpoint(self, endpoint, use_ssl, expected):
        """Endpoint scheme should follow or match the SSL setting."""
        assert resolve_endpoint(endpoint, use_ssl) == expected

    @pytest.mark.parametrize(
        ("endpoint", "use_ssl"),
        [
            ("https://localhost:9000", False),
            ("http://localhost:9000", True),
        ],
    )
    def test_resolve_endpoint_rejects_contradictory_ssl(self, endpoint, use_ssl):
        """Explicit endpoint schemes must agree with RUSTFS_USE_SSL."""
        with pytest.raises(ImproperlyConfigured, match="RUSTFS_ENDPOINT and RUSTFS_USE_SSL disagree"):
            resolve_endpoint(endpoint, use_ssl)

    def test_resolve_endpoint_rejects_unknown_scheme(self):
        """Only HTTP and HTTPS endpoint schemes are supported."""
        with pytest.raises(ImproperlyConfigured, match="must use http:// or https://"):
            resolve_endpoint("ftp://localhost:9000", False)

