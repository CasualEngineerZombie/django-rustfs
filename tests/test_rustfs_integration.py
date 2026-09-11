"""Integration tests against a real RustFS S3-compatible service."""

import os
import urllib.request
import uuid
from contextlib import closing

import boto3
import pytest
from django.core.files.base import ContentFile
from django.core.files.storage import StorageHandler
from django.test import override_settings

from django_rustfs.storage import RustFSStaticStorage, RustFSStorage

pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def rustfs_config():
    """Return RustFS connection settings used by the integration environment."""
    return {
        "endpoint_url": os.getenv("RUSTFS_ENDPOINT", "http://127.0.0.1:9000"),
        "access_key": os.getenv("RUSTFS_ACCESS_KEY", "test-access-key"),
        "secret_key": os.getenv("RUSTFS_SECRET_KEY", "test-secret-key"),
        "region": os.getenv("RUSTFS_REGION", "us-east-1"),
    }


@pytest.fixture
def rustfs_bucket(rustfs_config):
    """Create an isolated bucket and remove it after the test."""
    client = boto3.client(
        "s3",
        endpoint_url=rustfs_config["endpoint_url"],
        aws_access_key_id=rustfs_config["access_key"],
        aws_secret_access_key=rustfs_config["secret_key"],
        region_name=rustfs_config["region"],
    )
    bucket = f"django-rustfs-test-{uuid.uuid4().hex[:12]}"
    client.create_bucket(Bucket=bucket)

    try:
        yield bucket
    finally:
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=bucket):
            objects = [{"Key": obj["Key"]} for obj in page.get("Contents", [])]
            if objects:
                client.delete_objects(Bucket=bucket, Delete={"Objects": objects})
        client.delete_bucket(Bucket=bucket)


@pytest.fixture
def storage(rustfs_config, rustfs_bucket):
    """Create a RustFSStorage instance connected to the isolated bucket."""
    return RustFSStorage(
        **rustfs_config,
        bucket_name=rustfs_bucket,
        auto_create_bucket=False,
        file_overwrite=False,
        presign_urls=True,
        default_acl="private",
    )


def test_bucket_is_reachable(storage, rustfs_bucket):
    """The storage backend can reach the real RustFS bucket."""
    assert storage.is_available() is True
    response = storage.client.head_bucket(Bucket=rustfs_bucket)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_save_open_exists_size_and_delete(storage):
    """Core Django storage operations work against RustFS."""
    name = storage.save("documents/readme.txt", ContentFile(b"hello RustFS"))

    assert name == "documents/readme.txt"
    assert storage.exists(name) is True
    assert storage.size(name) == len(b"hello RustFS")

    with storage.open(name, "rb") as uploaded:
        assert uploaded.read() == b"hello RustFS"

    storage.delete(name)
    assert storage.exists(name) is False


def test_binary_and_empty_files(storage):
    """Binary payloads and zero-byte objects round-trip unchanged."""
    binary = bytes(range(256))
    binary_name = storage.save("binary/data.bin", ContentFile(binary))
    empty_name = storage.save("binary/empty.bin", ContentFile(b""))

    with storage.open(binary_name, "rb") as uploaded:
        assert uploaded.read() == binary
    assert storage.size(binary_name) == 256

    with storage.open(empty_name, "rb") as uploaded:
        assert uploaded.read() == b""
    assert storage.size(empty_name) == 0


def test_nested_paths_and_listdir(storage):
    """Nested object keys are stored and listed using Django semantics."""
    storage.save("media/images/photo.jpg", ContentFile(b"image"))
    storage.save("media/images/icon.svg", ContentFile(b"svg"))
    storage.save("media/docs/readme.txt", ContentFile(b"docs"))
    storage.save("media/root.txt", ContentFile(b"root"))

    directories, files = storage.listdir("media")
    assert set(directories) == {"images", "docs"}
    assert files == ["root.txt"]

    directories, files = storage.listdir("media/images")
    assert directories == []
    assert set(files) == {"photo.jpg", "icon.svg"}


def test_location_prefix(storage):
    """The configured location is reflected in the actual S3 object key."""
    storage.location = "uploads/prefix"
    name = storage.save("photo.jpg", ContentFile(b"content"))

    assert name == "photo.jpg"
    assert storage.exists(name) is True
    response = storage.client.head_object(
        Bucket=storage.bucket_name,
        Key="uploads/prefix/photo.jpg",
    )
    assert response["ContentLength"] == len(b"content")


def test_unicode_filename_and_path(storage):
    """Unicode object names survive a complete upload/download round trip."""
    name = "uploads/日本語/файл résumé.txt"
    saved_name = storage.save(name, ContentFile("こんにちは RustFS".encode()))

    assert saved_name == name
    assert storage.exists(name) is True
    with storage.open(name, "rb") as uploaded:
        assert uploaded.read().decode("utf-8") == "こんにちは RustFS"


def test_non_overwrite_behavior(storage):
    """Saving the same name twice produces distinct objects when overwrite is disabled."""
    first = storage.save("documents/report.txt", ContentFile(b"first"))
    second = storage.save("documents/report.txt", ContentFile(b"second"))

    assert first == "documents/report.txt"
    assert second != first
    assert storage.exists(first) is True
    assert storage.exists(second) is True


def test_overwrite_behavior(rustfs_config, rustfs_bucket):
    """Overwrite mode replaces the existing object at the requested key."""
    storage = RustFSStorage(
        **rustfs_config,
        bucket_name=rustfs_bucket,
        auto_create_bucket=False,
        file_overwrite=True,
        default_acl="private",
    )

    assert storage.save("documents/report.txt", ContentFile(b"first")) == "documents/report.txt"
    assert storage.save("documents/report.txt", ContentFile(b"second")) == "documents/report.txt"

    with storage.open("documents/report.txt", "rb") as uploaded:
        assert uploaded.read() == b"second"


def test_object_metadata_and_copy(storage):
    """Metadata retrieval and server-side object copy work against RustFS."""
    storage.object_parameters = {"Metadata": {"source": "integration-test"}}
    storage.save("source/object.txt", ContentFile(b"copy me"))

    metadata = storage.get_object_metadata("source/object.txt")
    assert metadata["content_length"] == len(b"copy me")
    assert metadata["content_type"] == "text/plain"
    assert metadata["metadata"]["source"] == "integration-test"
    assert metadata["etag"]

    storage.copy_object("source/object.txt", "copies/object.txt")
    assert storage.exists("copies/object.txt") is True
    with storage.open("copies/object.txt", "rb") as copied:
        assert copied.read() == b"copy me"


def test_private_presigned_url(storage):
    """Private objects can be downloaded through a generated presigned URL."""
    name = storage.save("private/file.txt", ContentFile(b"private content"))
    url = storage.url(name)

    assert "X-Amz-Signature" in url
    with closing(urllib.request.urlopen(url, timeout=10)) as response:
        assert response.status == 200
        assert response.read() == b"private content"


def test_public_direct_url(rustfs_config, rustfs_bucket):
    """Public ACL configuration produces a direct object URL."""
    storage = RustFSStorage(
        **rustfs_config,
        bucket_name=rustfs_bucket,
        auto_create_bucket=False,
        default_acl="public-read",
        presign_urls=False,
        secure_urls=False,
    )
    name = storage.save("public/file.txt", ContentFile(b"public content"))
    url = storage.url(name)

    assert url.endswith(f"/{rustfs_bucket}/public/file.txt")
    with closing(urllib.request.urlopen(url, timeout=10)) as response:
        assert response.status == 200
        assert response.read() == b"public content"


def test_presigned_post_url(storage):
    """RustFS accepts boto3-generated presigned POST data."""
    result = storage.get_presigned_post_url("uploads/direct.txt")

    assert result["url"].startswith(storage.endpoint_url)
    assert result["fields"]["key"] == "uploads/direct.txt"


def test_missing_object_raises_storage_error(storage):
    """Opening a missing object surfaces the backend's storage exception."""
    from django_rustfs.storage import RustFSError

    with pytest.raises(RustFSError):
        storage.open("does-not-exist.txt")


def test_static_storage(rustfs_config, rustfs_bucket):
    """RustFSStaticStorage works against the same S3-compatible service."""
    storage = RustFSStaticStorage(
        **rustfs_config,
        bucket_name=rustfs_bucket,
        auto_create_bucket=False,
        secure_urls=False,
    )
    name = storage.save("css/app.css", ContentFile(b"body { display: block; }"))

    assert name == "css/app.css"
    assert storage.exists(name) is True
    assert storage.file_overwrite is True
    assert storage.presign_urls is False
    assert storage.url(name).endswith(f"/{rustfs_bucket}/static/css/app.css")

    with storage.open(name, "rb") as uploaded:
        assert uploaded.read() == b"body { display: block; }"


def test_storages_configuration(rustfs_config, rustfs_bucket):
    """The Django STORAGES configuration can instantiate RustFSStorage."""
    storages = StorageHandler(
        {
            "default": {
                "BACKEND": "django_rustfs.storage.RustFSStorage",
                "OPTIONS": {
                    **rustfs_config,
                    "bucket_name": rustfs_bucket,
                    "auto_create_bucket": False,
                    "presign_urls": False,
                },
            }
        }
    )

    storage = storages["default"]
    name = storage.save("configured/file.txt", ContentFile(b"configured"))

    assert name == "configured/file.txt"
    with storage.open(name, "rb") as uploaded:
        assert uploaded.read() == b"configured"


def test_storage_location_from_django_settings(rustfs_config, rustfs_bucket):
    """STORAGES options and Django settings can configure a location prefix."""
    with override_settings(
        RUSTFS_LOCATION="configured-prefix",
        RUSTFS_ENDPOINT=rustfs_config["endpoint_url"],
        RUSTFS_ACCESS_KEY=rustfs_config["access_key"],
        RUSTFS_SECRET_KEY=rustfs_config["secret_key"],
        RUSTFS_REGION=rustfs_config["region"],
        RUSTFS_BUCKET_NAME=rustfs_bucket,
        RUSTFS_AUTO_CREATE_BUCKET=False,
    ):
        storage = RustFSStorage()
        storage.save("settings.txt", ContentFile(b"settings"))
        assert storage.exists("settings.txt") is True

        response = storage.client.get_object(
            Bucket=rustfs_bucket,
            Key="configured-prefix/settings.txt",
        )
        assert response["Body"].read() == b"settings"
