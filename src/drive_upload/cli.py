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
        default=None,
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
    parser.add_argument(
        "-t",
        "--token",
        default=None,
        help=(
            "Token handling: 'generate' to create token.json, "
            "path to token.json file, or raw JSON string. "
            "Falls back to the GOOGLE_DRIVE_TOKEN environment variable. "
            "If provided, --credentials is ignored (except for 'generate')."
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

    # Handle token generation mode
    if args.token == "generate":
        if not args.credentials:
            credentials_path = _resolve_credentials(None)
        else:
            credentials_path = args.credentials
        
        if not os.path.isfile(credentials_path):
            print(f"Error: credentials file not found: {credentials_path}", file=sys.stderr)
            raise SystemExit(1)
        
        print("Generating OAuth token...", file=sys.stderr)
        creds = authenticate(credentials_path)
        
        # Read client info from credentials.json
        import json
        with open(credentials_path, "r") as f:
            client_config = json.load(f)
        
        client_info = client_config.get("installed") or client_config.get("web")
        if not client_info:
            print("Error: Invalid credentials.json format", file=sys.stderr)
            raise SystemExit(1)
        
        # Get the raw OAuth token data and add client credentials
        token_data = json.loads(creds.to_json())
        
        # Ensure we have the client credentials required by from_authorized_user_info
        token_data.update({
            "client_id": client_info["client_id"],
            "client_secret": client_info["client_secret"],
        })
        
        # Save complete token.json in current directory
        token_file = "token.json"
        with open(token_file, "w") as f:
            json.dump(token_data, f, indent=2)
        
        print(f"\n✅ Token saved to {token_file}", file=sys.stderr)
        print(f"This file contains your access token and can be reused on headless servers.", file=sys.stderr)
        print(f"Usage: upload-drive -s <file> -t {token_file}", file=sys.stderr)
        return

    # Validate source is provided for upload operations
    if not args.source:
        print("Error: --source is required for upload operations.", file=sys.stderr)
        print("Use --token generate to create a token.json file.", file=sys.stderr)
        raise SystemExit(1)

    # Handle token file or direct token
    if args.token:
        if os.path.isfile(args.token):
            # Read token from file
            print(f"Using token from file: {args.token}", file=sys.stderr)
            with open(args.token, "r") as f:
                os.environ["GOOGLE_DRIVE_TOKEN"] = f.read().strip()
        else:
            # Direct token JSON string
            os.environ["GOOGLE_DRIVE_TOKEN"] = args.token
        
        # Use dummy credentials path since authenticate() will use the token
        creds = authenticate("/dev/null")
    else:
        # Standard credentials-based flow
        credentials_path = _resolve_credentials(args.credentials)
        if not os.path.isfile(credentials_path):
            print(f"Error: credentials file not found: {credentials_path}", file=sys.stderr)
            raise SystemExit(1)
        creds = authenticate(credentials_path)

    upload(args.source, creds)
