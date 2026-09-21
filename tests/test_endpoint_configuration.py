"""Regression tests for endpoint, protocol, port, and TLS configuration."""

from unittest.mock import patch

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from django_rustfs.conf import resolve_endpoint
from django_rustfs.storage import RustFSStorage


@pytest.mark.parametrize(
    ("endpoint", "use_ssl", "expected"),
    [
        ("http://localhost:9000", False, "http://localhost:9000"),
        ("https://localhost:9000", True, "https://localhost:9000"),
        ("http://localhost:8080", False, "http://localhost:8080"),
        ("https://localhost:9443", True, "https://localhost:9443"),
        ("localhost:8080", False, "http://localhost:8080"),
        ("localhost:9443", True, "https://localhost:9443"),
    ],
)
def test_resolve_endpoint_protocol_and_ports(endpoint, use_ssl, expected):
    """HTTP/HTTPS schemes and custom ports are preserved or derived."""
    assert resolve_endpoint(endpoint, use_ssl) == expected


@pytest.mark.parametrize(
    ("endpoint", "use_ssl"),
    [
        ("https://localhost:9000", False),
        ("http://localhost:9000", True),
    ],
)
def test_resolve_endpoint_rejects_protocol_disagreement(endpoint, use_ssl):
    """Explicit endpoint schemes cannot silently disagree with USE_SSL."""
    with pytest.raises(
        ImproperlyConfigured, match="RUSTFS_ENDPOINT and RUSTFS_USE_SSL disagree"
    ):
        resolve_endpoint(endpoint, use_ssl)


@pytest.mark.parametrize(
    ("use_ssl", "verify_ssl"),
    [
        (False, True),
        (False, False),
        (True, True),
        (True, False),
    ],
)
def test_client_configuration_matches_canonical_protocol_and_tls(use_ssl, verify_ssl):
    """boto3 receives the canonical endpoint, protocol, and TLS verification."""
    endpoint = "localhost:8080" if not use_ssl else "localhost:9443"

    with patch("django_rustfs.storage.boto3.client") as boto3_client:
        storage = RustFSStorage(
            endpoint_url=endpoint,
            access_key="test",
            secret_key="test",
            use_ssl=use_ssl,
            verify_ssl=verify_ssl,
            auto_create_bucket=False,
        )

        assert storage.client is not None

    boto3_client.assert_called_once()
    kwargs = boto3_client.call_args.kwargs
    expected_endpoint = f"{'https' if use_ssl else 'http'}://{endpoint}"

    assert kwargs["endpoint_url"] == expected_endpoint
    assert kwargs["use_ssl"] is use_ssl
    assert kwargs["verify"] is verify_ssl


@pytest.mark.parametrize(
    ("endpoint", "use_ssl", "verify_ssl", "expected_endpoint"),
    [
        ("http://rustfs.example:8080/", False, True, "http://rustfs.example:8080"),
        ("https://rustfs.example:9443/", True, True, "https://rustfs.example:9443"),
        ("http://rustfs.example:18080/", False, False, "http://rustfs.example:18080"),
        ("https://rustfs.example:19443/", True, False, "https://rustfs.example:19443"),
    ],
)
def test_client_preserves_explicit_ports_and_tls(
    endpoint, use_ssl, verify_ssl, expected_endpoint
):
    """Explicit HTTP/HTTPS ports remain unchanged in boto3 configuration."""
    with patch("django_rustfs.storage.boto3.client") as boto3_client:
        storage = RustFSStorage(
            endpoint_url=endpoint,
            access_key="test",
            secret_key="test",
            use_ssl=use_ssl,
            verify_ssl=verify_ssl,
            auto_create_bucket=False,
        )
        assert storage.client is not None

    kwargs = boto3_client.call_args.kwargs
    assert kwargs["endpoint_url"] == expected_endpoint
    assert kwargs["use_ssl"] is use_ssl
    assert kwargs["verify"] is verify_ssl


@override_settings(
    RUSTFS_ENDPOINT="rustfs.internal:9443",
    RUSTFS_ACCESS_KEY="settings-access",
    RUSTFS_SECRET_KEY="settings-secret",
    RUSTFS_USE_SSL=True,
    RUSTFS_VERIFY_SSL=False,
)
def test_storage_client_uses_canonical_settings_layer():
    """Storage and boto3 configuration are derived from Settings."""
    with patch("django_rustfs.storage.boto3.client") as boto3_client:
        storage = RustFSStorage(auto_create_bucket=False)
        assert storage.client is not None

    assert storage.endpoint_url == "https://rustfs.internal:9443"
    assert storage.use_ssl is True
    assert storage.verify_ssl is False

    kwargs = boto3_client.call_args.kwargs
    assert kwargs["endpoint_url"] == storage.endpoint_url
    assert kwargs["use_ssl"] is storage.use_ssl
    assert kwargs["verify"] is storage.verify_ssl
