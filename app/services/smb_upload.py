"""SMB-compatible local directory upload/copy service."""

import os
import shutil
from pathlib import Path
from typing import Optional


class SMBUploadService:
    """Service for copying files to a local SMB share folder."""

    def __init__(
        self, share_path: Optional[str], public_url_base: Optional[str] = None
    ):
        """Initialize SMB upload service.

        Args:
            share_path: Local filesystem path representing the mounted SMB share
            public_url_base: Public HTTP URL base mapping to the share_path (optional)
        """
        self.share_path = share_path
        self.public_url_base = public_url_base

        if self.share_path:
            try:
                os.makedirs(self.share_path, exist_ok=True)
            except Exception:
                # Share might not be writable yet, handle gracefully at init
                pass

    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        content_type: Optional[str] = None,
        expires_in: int = 604800,
    ) -> str:
        """Copy a file to the SMB share folder.

        Args:
            file_path: Local file path to upload
            object_name: Destination filename (defaults to basename of file_path)
            content_type: MIME type (ignored)
            expires_in: Expiration parameter (ignored)

        Returns:
            The HTTP URL if public_url_base is configured, else a file:// URL.

        Raises:
            ValueError: If share_path is not configured
            FileNotFoundError: If file_path does not exist
        """
        if not self.share_path:
            raise ValueError("SMB share path (SMB_SHARE_PATH) is not configured.")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if object_name is None:
            object_name = os.path.basename(file_path)

        dest_path = os.path.join(self.share_path, object_name)

        # Ensure parent directory exists (e.g. if share_path has subfolders)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Copy the file to the SMB share directory
        shutil.copy2(file_path, dest_path)

        # Return public URL if configured
        if self.public_url_base:
            if "\\" in self.public_url_base:
                base = self.public_url_base.rstrip("\\")
                return f"{base}\\{object_name}"
            else:
                base = self.public_url_base.rstrip("/")
                return f"{base}/{object_name}"

        # Otherwise, return local file:// URI or smb:// URI for UNC paths
        uri = Path(dest_path).absolute().as_uri()
        if uri.startswith("file://") and not uri.startswith("file:///"):
            # UNC path: file://server/share/file -> smb://server/share/file
            uri = "smb:" + uri[5:]
        return uri

    def delete_file(self, object_name: str) -> bool:
        """Delete a file from the SMB share folder.

        Args:
            object_name: Filename to delete

        Returns:
            True if successful, False otherwise
        """
        if not self.share_path:
            return False

        dest_path = os.path.join(self.share_path, object_name)
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)
                return True
        except Exception:
            pass
        return False
