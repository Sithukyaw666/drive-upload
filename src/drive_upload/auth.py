"""OAuth logic and token management for Google Drive API."""

import os
import sys

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Only request access to files created/opened by this app.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

_TOKEN_FILENAME = "token.json"


def _resolve_token_path(credentials_path: str) -> str:
    """Store token.json alongside the credentials file."""
    return os.path.join(os.path.dirname(os.path.abspath(credentials_path)), _TOKEN_FILENAME)


def _is_headless() -> bool:
    """Best-effort detection of a headless (no-display) environment."""
    if sys.platform == "darwin":
        return False
    return not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY")


def authenticate(credentials_path: str) -> Credentials:
    """Return valid Google OAuth2 credentials.

    Loads cached tokens from token.json if available. Falls back to the
    full OAuth consent flow when no valid token exists.

    Args:
        credentials_path: Path to the credentials.json file downloaded
            from the Google Cloud Console.

    Returns:
        An authenticated Credentials object ready for API calls.
    """
    token_path = _resolve_token_path(credentials_path)
    creds: Credentials | None = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if _is_headless():
                print(
                    "WARNING: No display detected. The OAuth flow will attempt "
                    "to open a browser on this machine. If that fails, re-run "
                    "on a machine with a browser or use a remote auth flow.",
                    file=sys.stderr,
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())

    return creds
