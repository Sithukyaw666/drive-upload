"""CLI argument parsing for upload-drive."""

from __future__ import annotations

import argparse
import os
import sys

from drive_upload.auth import authenticate
from drive_upload.uploader import upload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="upload-drive",
        description="Upload a file or directory to Google Drive.",
    )
    parser.add_argument(
        "-s",
        "--source",
        required=True,
        help="Path to the file or directory to upload.",
    )
    parser.add_argument(
        "-c",
        "--credentials",
        default=None,
        help=(
            "Path to the Google OAuth credentials.json file. "
            "Falls back to the GOOGLE_DRIVE_CREDENTIALS environment variable."
        ),
    )
    return parser


def _resolve_credentials(cli_value: str | None) -> str:
    """Return the credentials path, checking the CLI flag first, then the env var."""
    if cli_value:
        return cli_value

    env_value = os.environ.get("GOOGLE_DRIVE_CREDENTIALS")
    if env_value:
        return env_value

    print(
        "Error: No credentials provided.\n"
        "Supply --credentials / -c or set the GOOGLE_DRIVE_CREDENTIALS "
        "environment variable.",
        file=sys.stderr,
    )
    raise SystemExit(1)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the upload-drive command."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    credentials_path = _resolve_credentials(args.credentials)

    if not os.path.isfile(credentials_path):
        print(f"Error: credentials file not found: {credentials_path}", file=sys.stderr)
        raise SystemExit(1)

    creds = authenticate(credentials_path)
    upload(args.source, creds)
