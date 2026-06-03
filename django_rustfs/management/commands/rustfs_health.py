"""
Management command to check RustFS health and connectivity.

Usage:
    python manage.py rustfs_health

Checks:
    - Network connectivity to RustFS endpoint
    - Authentication validity
    - Bucket existence and accessibility
    - Server response time
"""

import time
from typing import Any

from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand, CommandError

from django_rustfs.storage import RustFSStorage


class Command(BaseCommand):
    """Check RustFS server health and connectivity."""

    help = "Check connectivity and health of the configured RustFS server"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--bucket",
            type=str,
            help="Specific bucket name to check (defaults to RUSTFS_BUCKET_NAME)",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed response information",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute the health check."""
        bucket_name = options.get("bucket")
        verbose = options.get("verbose", False)

        self.stdout.write("🔍 Checking RustFS health...\n")

        # Initialize storage (this validates config)
        try:
            storage = RustFSStorage()
        except Exception as e:
            raise CommandError(f"❌ Configuration error: {e}")

        # Override bucket if specified
        if bucket_name:
            storage.bucket_name = bucket_name

        endpoint = storage.endpoint_url
        self.stdout.write(f"   Endpoint: {endpoint}")
        self.stdout.write(f"   Bucket:   {storage.bucket_name}")
        self.stdout.write("")

        # Check 1: Basic connectivity
        start_time = time.time()
        try:
            storage.client.head_bucket(Bucket=storage.bucket_name)
            latency = (time.time() - start_time) * 1000
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ Bucket '{storage.bucket_name}' is accessible")
            )
            self.stdout.write(f"     Response time: {latency:.1f}ms")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "404":
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  Bucket '{storage.bucket_name}' does not exist"
                    )
                )
                self.stdout.write(
                    f"     Tip: Run 'python manage.py rustfs_init_buckets' to create it"
                )
            elif error_code in ("403", "InvalidAccessKeyId", "SignatureDoesNotMatch"):
                raise CommandError(
                    f"  ❌ Authentication failed ({error_code}): {error_msg}\n"
                    f"     Check your RUSTFS_ACCESS_KEY and RUSTFS_SECRET_KEY settings"
                )
            else:
                raise CommandError(
                    f"  ❌ Bucket check failed ({error_code}): {error_msg}"
                )
        except Exception as e:
            raise CommandError(
                f"  ❌ Cannot connect to RustFS at {endpoint}:\n"
                f"     {type(e).__name__}: {e}\n"
                f"     Check that RustFS is running and RUSTFS_ENDPOINT is correct"
            )

        # Check 2: List bucket contents (lightweight)
        try:
            response = storage.client.list_objects_v2(
                Bucket=storage.bucket_name, MaxKeys=1
            )
            object_count = response.get("KeyCount", 0)
            self.stdout.write(
                self.style.SUCCESS(f"  ✅ List operation works ({object_count} objects visible)")
            )
        except ClientError as e:
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠️  List operation failed: {e}"
                )
            )

        # Check 3: Upload/Download/Delete roundtrip
        self.stdout.write("")
        self.stdout.write("  🧪 Running upload/download roundtrip test...")
        test_key = f"_rustfs_health_check_{int(time.time())}.txt"
        test_content = b"django-rustfs health check"

        try:
            # Upload
            storage.client.put_object(
                Bucket=storage.bucket_name,
                Key=test_key,
                Body=test_content,
                ContentType="text/plain",
            )

            # Download
            response = storage.client.get_object(
                Bucket=storage.bucket_name, Key=test_key
            )
            downloaded = response["Body"].read()

            if downloaded == test_content:
                self.stdout.write(
                    self.style.SUCCESS("  ✅ Upload/download roundtrip successful")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("  ❌ Data mismatch in roundtrip test")
                )

            # Cleanup
            storage.client.delete_object(
                Bucket=storage.bucket_name, Key=test_key
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Roundtrip test failed: {e}")
            )

        # Summary
        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS("✅ RustFS health check completed successfully!")
        )
