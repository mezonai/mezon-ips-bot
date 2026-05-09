"""S3-compatible storage upload service."""

import os
from typing import Optional

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError


class S3UploadService:
    """Service for uploading files to S3-compatible storage."""

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str = "auto",
        public_url_base: Optional[str] = None,
    ):
        """Initialize S3 upload service.

        Args:
            endpoint_url: S3-compatible endpoint URL (e.g., https://s3.amazonaws.com)
            access_key: Access key ID
            secret_key: Secret access key
            bucket_name: Bucket name
            region: Region name (default: "auto" for Cloudflare R2)
            public_url_base: Public URL base for uploaded files (e.g., https://cdn.example.com)
        """
        self.bucket_name = bucket_name
        self.public_url_base = public_url_base

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        content_type: Optional[str] = None,
        expires_in: int = 604800,  # 7 days default
    ) -> str:
        """Upload a file to S3-compatible storage.

        Args:
            file_path: Local file path
            object_name: S3 object name (defaults to basename of file_path)
            content_type: MIME type (optional)
            expires_in: Presigned URL expiration in seconds (default: 7 days)

        Returns:
            Presigned URL of the uploaded file (valid for expires_in seconds)

        Raises:
            FileNotFoundError: If file_path does not exist
            ClientError: If upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if object_name is None:
            object_name = os.path.basename(file_path)

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        # Upload file
        self.s3_client.upload_file(
            file_path, self.bucket_name, object_name, ExtraArgs=extra_args
        )

        # Generate presigned URL for download (7 days expiry)
        presigned_url = self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": object_name},
            ExpiresIn=expires_in,
        )

        return presigned_url

    def delete_file(self, object_name: str) -> bool:
        """Delete a file from S3-compatible storage.

        Args:
            object_name: S3 object name

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError:
            return False
