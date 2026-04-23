"""
S3 Client - Handles file storage operations with S3-compatible services.
Supports AWS S3, Supabase Storage, MinIO, and other S3-compatible services.
"""

import os
import logging
from typing import Optional, BinaryIO, Dict, Any
from datetime import datetime
import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from botocore.config import Config

from config import settings

logger = logging.getLogger(__name__)

# Global S3 client instance
_s3_client_instance: Optional["S3Client"] = None


class S3Client:
    """
    S3-compatible storage client for file operations.

    Supports:
    - AWS S3
    - Supabase Storage
    - MinIO
    - Any S3-compatible service

    Usage:
        client = S3Client()
        # Upload a file
        path = await client.upload_file(file_bytes, "my_file.xlsx", user_id)
        # Download a file
        file_bytes = await client.download_file(path)
        # Get a presigned URL
        url = client.get_presigned_url(path)
    """

    def __init__(self):
        """Initialize the S3 client with settings from config."""
        self._client = None
        self._bucket_name = settings.storage.bucket_name
        self._is_configured = settings.storage.is_configured

    def _get_client(self):
        """Get or create the boto3 S3 client."""
        if self._client is None:
            if not self._is_configured:
                logger.warning("S3 storage is not configured. Using local fallback.")
                return None

            config = Config(
                region_name=settings.storage.region,
                signature_version="s3v4",
                retries={"max_attempts": 3, "mode": "standard"},
            )

            client_kwargs = {
                "aws_access_key_id": settings.storage.access_key,
                "aws_secret_access_key": settings.storage.secret_key,
                "config": config,
            }

            # Add endpoint URL for non-AWS S3 services (Supabase, MinIO, etc.)
            if settings.storage.endpoint_url:
                client_kwargs["endpoint_url"] = settings.storage.endpoint_url

            # Use SSL if configured
            if not settings.storage.use_ssl:
                os.environ["AWS_HTTPS"] = "false"

            self._client = boto3.client("s3", **client_kwargs)

        return self._client

    @property
    def is_available(self) -> bool:
        """Check if S3 storage is available."""
        return self._is_configured and self._get_client() is not None

    def generate_storage_path(self, filename: str, user_id: str) -> str:
        """
        Generate a unique storage path for a file.

        Args:
            filename: Original filename
            user_id: User ID for organization

        Returns:
            Unique storage path in the format: files/{user_id}/{uuid}_{filename}
        """
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = self._sanitize_filename(filename)
        return f"{settings.storage.files_prefix}/{user_id}/{unique_id}_{safe_filename}"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Replace spaces and special characters
        safe_name = filename.replace(" ", "_")
        # Keep only alphanumeric, dots, underscores, and hyphens
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._-")
        return safe_name

    def upload_file(
        self,
        file_data: BinaryIO | bytes,
        filename: str,
        user_id: str,
        content_type: str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ) -> str:
        """
        Upload a file to S3 storage.

        Args:
            file_data: File data as bytes or file-like object
            filename: Original filename
            user_id: User ID for organization
            content_type: MIME type of the file

        Returns:
            Storage path of the uploaded file

        Raises:
            RuntimeError: If S3 is not configured or upload fails
        """
        client = self._get_client()

        if client is None:
            # Fallback to local storage
            return self._local_fallback_upload(file_data, filename, user_id)

        storage_path = self.generate_storage_path(filename, user_id)

        try:
            # Handle both bytes and file-like objects
            if isinstance(file_data, bytes):
                client.put_object(
                    Bucket=self._bucket_name,
                    Key=storage_path,
                    Body=file_data,
                    ContentType=content_type,
                    Metadata={
                        "original-filename": filename,
                        "user-id": user_id,
                        "uploaded-at": datetime.utcnow().isoformat(),
                    },
                )
            else:
                client.upload_fileobj(
                    file_data,
                    self._bucket_name,
                    storage_path,
                    ExtraArgs={
                        "ContentType": content_type,
                        "Metadata": {
                            "original-filename": filename,
                            "user-id": user_id,
                            "uploaded-at": datetime.utcnow().isoformat(),
                        },
                    },
                )

            logger.info(f"Uploaded file to S3: {storage_path}")
            return storage_path

        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise RuntimeError(f"Failed to upload file: {e}")
        except NoCredentialsError:
            logger.error("S3 credentials not found")
            raise RuntimeError("S3 credentials not configured")

    def download_file(self, storage_path: str) -> bytes:
        """
        Download a file from S3 storage.

        Args:
            storage_path: Path to the file in S3

        Returns:
            File content as bytes

        Raises:
            RuntimeError: If S3 is not configured or download fails
        """
        client = self._get_client()

        if client is None:
            # Fallback to local storage
            return self._local_fallback_download(storage_path)

        try:
            response = client.get_object(Bucket=self._bucket_name, Key=storage_path)
            return response["Body"].read()

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "NoSuchKey":
                raise FileNotFoundError(f"File not found: {storage_path}")
            logger.error(f"S3 download error: {e}")
            raise RuntimeError(f"Failed to download file: {e}")

    def delete_file(self, storage_path: str) -> bool:
        """
        Delete a file from S3 storage.

        Args:
            storage_path: Path to the file in S3

        Returns:
            True if deletion was successful

        Raises:
            RuntimeError: If S3 is not configured or deletion fails
        """
        client = self._get_client()

        if client is None:
            # Fallback to local storage
            return self._local_fallback_delete(storage_path)

        try:
            client.delete_object(Bucket=self._bucket_name, Key=storage_path)
            logger.info(f"Deleted file from S3: {storage_path}")
            return True

        except ClientError as e:
            logger.error(f"S3 delete error: {e}")
            raise RuntimeError(f"Failed to delete file: {e}")

    def get_presigned_url(self, storage_path: str, expiration: int = None) -> str:
        """
        Generate a presigned URL for direct file access.

        Args:
            storage_path: Path to the file in S3
            expiration: URL expiration time in seconds (default from settings)

        Returns:
            Presigned URL for the file

        Raises:
            RuntimeError: If S3 is not configured
        """
        client = self._get_client()

        if client is None:
            raise RuntimeError("S3 storage is not configured")

        if expiration is None:
            expiration = settings.storage.presigned_url_expiration

        try:
            url = client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket_name, "Key": storage_path},
                ExpiresIn=expiration,
            )
            return url

        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise RuntimeError(f"Failed to generate presigned URL: {e}")

    def file_exists(self, storage_path: str) -> bool:
        """
        Check if a file exists in S3 storage.

        Args:
            storage_path: Path to the file in S3

        Returns:
            True if file exists, False otherwise
        """
        client = self._get_client()

        if client is None:
            # Fallback to local storage
            return self._local_fallback_exists(storage_path)

        try:
            client.head_object(Bucket=self._bucket_name, Key=storage_path)
            return True

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                return False
            logger.error(f"S3 head object error: {e}")
            return False

    def get_file_metadata(self, storage_path: str) -> Dict[str, Any]:
        """
        Get metadata for a file in S3.

        Args:
            storage_path: Path to the file in S3

        Returns:
            Dictionary with file metadata
        """
        client = self._get_client()

        if client is None:
            return {}

        try:
            response = client.head_object(Bucket=self._bucket_name, Key=storage_path)
            return {
                "content_length": response.get("ContentLength", 0),
                "content_type": response.get("ContentType", ""),
                "last_modified": response.get("LastModified"),
                "metadata": response.get("Metadata", {}),
            }

        except ClientError as e:
            logger.error(f"S3 head object error: {e}")
            return {}

    # Local fallback methods for development/testing
    def _local_fallback_upload(self, file_data, filename: str, user_id: str) -> str:
        """Fallback to local filesystem storage."""
        import tempfile
        from pathlib import Path

        # Create local storage directory
        local_dir = Path(tempfile.gettempdir()) / "smartxl_files" / user_id
        local_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        unique_id = str(uuid.uuid4())[:8]
        safe_filename = self._sanitize_filename(filename)
        storage_path = f"local://{user_id}/{unique_id}_{safe_filename}"
        local_path = local_dir / f"{unique_id}_{safe_filename}"

        # Write file
        if isinstance(file_data, bytes):
            local_path.write_bytes(file_data)
        else:
            with open(local_path, "wb") as f:
                f.write(file_data.read())

        logger.warning(f"Using local fallback storage: {local_path}")
        return storage_path

    def _local_fallback_download(self, storage_path: str) -> bytes:
        """Download from local fallback storage."""
        import tempfile
        from pathlib import Path

        if not storage_path.startswith("local://"):
            raise FileNotFoundError(f"File not found: {storage_path}")

        # Parse local path
        relative_path = storage_path[8:]  # Remove "local://"
        local_path = Path(tempfile.gettempdir()) / "smartxl_files" / relative_path

        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {local_path}")

        return local_path.read_bytes()

    def _local_fallback_delete(self, storage_path: str) -> bool:
        """Delete from local fallback storage."""
        from pathlib import Path

        if not storage_path.startswith("local://"):
            return True  # S3 file, ignore

        relative_path = storage_path[8:]
        local_path = Path(tempfile.gettempdir()) / "smartxl_files" / relative_path

        if local_path.exists():
            local_path.unlink()

        return True

    def _local_fallback_exists(self, storage_path: str) -> bool:
        """Check existence in local fallback storage."""
        from pathlib import Path

        if not storage_path.startswith("local://"):
            return False  # S3 file, not in local storage

        relative_path = storage_path[8:]
        local_path = Path(tempfile.gettempdir()) / "smartxl_files" / relative_path

        return local_path.exists()


def get_s3_client() -> S3Client:
    """
    Get the global S3 client instance.
    Creates a new instance if none exists.

    Returns:
        S3Client instance
    """
    global _s3_client_instance
    if _s3_client_instance is None:
        _s3_client_instance = S3Client()
    return _s3_client_instance


def reset_s3_client() -> None:
    """
    Reset the global S3 client instance.
    Used for testing purposes.
    """
    global _s3_client_instance
    _s3_client_instance = None
