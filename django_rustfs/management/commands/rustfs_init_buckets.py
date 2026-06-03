"""
Management command to initialize RustFS buckets.

Usage:
    python manage.py rustfs_init_buckets
    python manage.py rustfs_init_buckets --bucket=my-custom-bucket

Creates buckets if they don't exist and sets appropriate access policies.
"""

from typing import Any

from botocore.exceptions import ClientError
from django.core.management.base import BaseCommand, CommandError

from django_rustfs.storage import RustFSStaticStorage, RustFSStorage


class Command(BaseCommand):
    """Initialize RustFS buckets for Django media and static files."""

    help = "Create and configure RustFS buckets for Django"

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--bucket",
            type=str,
            help="Create only this specific bucket",
        )
        parser.add_argument(
            "--skip-static",
            action="store_true",
            help="Skip creating the static files bucket",
        )
        parser.add_argument(
            "--public",
            action="store_true",
            help="Make the bucket public-readable (useful for media serving)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute bucket initialization."""
        specific_bucket = options.get("bucket")
        skip_static = options.get("skip_static", False)
        make_public = options.get("public", False)
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN — no changes will be made\n")
            )

        self.stdout.write("🪣 Initializing RustFS buckets...\n")

        # Track results
        created_buckets = []
        existing_buckets = []
        errors = []

        try:
            storage = RustFSStorage()
        except Exception as e:
            raise CommandError(f"❌ Configuration error: {e}") from e

        buckets_to_create = []

        # Determine which buckets to create
        if specific_bucket:
            buckets_to_create.append(
                (specific_bucket, make_public or storage.default_acl == "public-read")
            )
        else:
            # Media bucket (default storage)
            buckets_to_create.append(
                (storage.bucket_name, make_public or storage.default_acl == "public-read")
            )

            # Static bucket (if not skipped)
            if not skip_static:
                try:
                    static_storage = RustFSStaticStorage()
                    if static_storage.bucket_name != storage.bucket_name:
                        buckets_to_create.append(
                            (static_storage.bucket_name, True)  # Static is always public
                        )
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️  Could not configure static storage: {e}"
                        )
                    )

        # Create each bucket
        for bucket_name, is_public in buckets_to_create:
            result = self._create_bucket(
                storage, bucket_name, is_public, dry_run
            )
            if result == "created":
                created_buckets.append(bucket_name)
            elif result == "exists":
                existing_buckets.append(bucket_name)
            elif result.startswith("error:"):
                errors.append((bucket_name, result[6:]))

        # Summary
        self.stdout.write("")
        self.stdout.write("=" * 50)
        if dry_run:
            self.stdout.write("DRY RUN SUMMARY")
        else:
            self.stdout.write("RESULTS")
        self.stdout.write("=" * 50)

        if created_buckets:
            for name in created_buckets:
                self.stdout.write(
                    self.style.SUCCESS(f"  ✅ Created:   {name}")
                )

        if existing_buckets:
            for name in existing_buckets:
                self.stdout.write(
                    self.style.NOTICE(f"  ℹ️  Existing:  {name}")
                )

        if errors:
            for name, error in errors:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ Failed:    {name} — {error}")
                )

        total = len(created_buckets) + len(existing_buckets)
        self.stdout.write("")
        if errors:
            self.stdout.write(
                self.style.WARNING(
                    f"Done: {total} bucket(s) OK, {len(errors)} error(s)"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ All done: {total} bucket(s) ready to use"
                )
            )

    def _create_bucket(
        self,
        storage: RustFSStorage,
        bucket_name: str,
        is_public: bool,
        dry_run: bool,
    ) -> str:
        """
        Create a single bucket and optionally set its policy.

        Returns:
            "created" — bucket was created
            "exists" — bucket already exists
            "error:<msg>" — an error occurred
        """
        self.stdout.write(f"\n  📦 Bucket: {bucket_name}")

        # Check if bucket exists
        try:
            storage.client.head_bucket(Bucket=bucket_name)
            self.stdout.write("     Status: Already exists ✓")
            return "exists"
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code != "404":
                return f"error:head_bucket failed: {e}"

        # Create bucket
        if dry_run:
            self.stdout.write("     Would create bucket (dry run)")
            if is_public:
                self.stdout.write("     Would set public-read policy (dry run)")
            return "created"

        try:
            storage.client.create_bucket(Bucket=bucket_name)
            self.stdout.write(
                self.style.SUCCESS("     Status: Created ✓")
            )
        except ClientError as e:
            return f"error:create_bucket failed: {e}"

        # Set bucket policy for public access if requested
        if is_public:
            policy = self._public_bucket_policy(bucket_name)
            try:
                storage.client.put_bucket_policy(
                    Bucket=bucket_name, Policy=policy
                )
                self.stdout.write("     Policy: public-read ✓")
            except ClientError as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"     Policy: Could not set public-read ({e})"
                    )
                )

        return "created"

    def _public_bucket_policy(self, bucket_name: str) -> str:
        """Generate a public-read bucket policy."""
        import json

        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{bucket_name}/*"],
                }
            ],
        }
        return json.dumps(policy)
