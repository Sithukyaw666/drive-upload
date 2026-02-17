"""Zipping directories and uploading files to Google Drive."""

from __future__ import annotations

import mimetypes
import os
import shutil
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


def _zip_directory(source_dir: str) -> str:
    """Zip a directory and return the path to the resulting archive."""
    base_name = os.path.normpath(source_dir)
    archive_path = shutil.make_archive(base_name, "zip", source_dir)
    return archive_path


def _guess_mimetype(file_path: str) -> str:
    """Return a MIME type for *file_path*, defaulting to octet-stream."""
    mime, _ = mimetypes.guess_type(file_path)
    return mime or "application/octet-stream"


def upload_file(
    file_path: str,
    creds: Credentials,
    *,
    mimetype: str | None = None,
) -> str:
    """Upload a file to Google Drive and return the new file ID.

    Uses resumable uploads with a chunked progress display so large
    files are handled reliably and the user can see progress.
    """
    service = build("drive", "v3", credentials=creds)

    resolved_mime = mimetype or _guess_mimetype(file_path)
    file_metadata = {"name": os.path.basename(file_path)}
    media = MediaFileUpload(file_path, mimetype=resolved_mime, resumable=True)

    print(f"Uploading {file_path} ({resolved_mime})...")
    request = service.files().create(
        body=file_metadata, media_body=media, fields="id",
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"\r  Progress: {pct}%", end="", flush=True)

    print()  # newline after progress
    file_id: str = response["id"]
    print(f"Upload complete - File ID: {file_id}")
    return file_id


def upload(source_path: str, creds: Credentials) -> None:
    """Upload a file or directory to Google Drive.

    If source_path is a directory it will be zipped first. The temporary
    zip is cleaned up after the upload regardless of success or failure.
    """
    if not os.path.exists(source_path):
        print(f"Error: source path does not exist: {source_path}", file=sys.stderr)
        raise SystemExit(1)

    path_to_upload = source_path
    temp_zip: str | None = None

    if os.path.isdir(source_path):
        print(f"Directory detected. Zipping {source_path}...")
        temp_zip = _zip_directory(source_path)
        path_to_upload = temp_zip

    try:
        mime = "application/zip" if temp_zip else None
        upload_file(path_to_upload, creds, mimetype=mime)
    finally:
        if temp_zip and os.path.exists(temp_zip):
            os.remove(temp_zip)
            print(f"Cleaned up temporary zip: {temp_zip}")
