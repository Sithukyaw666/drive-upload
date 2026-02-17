"""OAuth logic and token management for Google Drive API."""

import json
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
    # Check for common headless indicators
    if os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_CLIENT"):
        return True
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
    # Check if token is provided directly via environment variable
    direct_token = os.environ.get("GOOGLE_DRIVE_TOKEN")
    if direct_token:
        print("Using provided token.", file=sys.stderr)
        try:
            token_data = json.loads(direct_token)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in token: {e}", file=sys.stderr)
            raise SystemExit(1)

        # Build Credentials directly from the token fields
        access_token = token_data.get("access_token") or token_data.get("token")
        if not access_token:
            print("Token must contain 'access_token' or 'token' field.", file=sys.stderr)
            raise SystemExit(1)

        creds = Credentials(
            token=access_token,
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=SCOPES,
        )

        # If token has client credentials and is expired, try refreshing
        if not creds.valid and creds.expired and creds.refresh_token and creds.client_id:
            print("Token expired, refreshing...", file=sys.stderr)
            creds.refresh(Request())

        return creds

    token_path = _resolve_token_path(credentials_path)
    creds: Credentials | None = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            
            if _is_headless():
                print(
                    "\n=== HEADLESS AUTHENTICATION ===",
                    file=sys.stderr,
                )
                print(
                    "Running on a server without browser access."
                    "\nThe authorization server will start on port 8080."
                    "\n\nIf this server is not directly accessible:"
                    "\n  1. Run: ssh -L 8080:localhost:8080 <your-server>"
                    "\n  2. Keep the SSH session open during authentication"
                    "\n\nOtherwise, just copy the URL below and open it in any browser:",
                    file=sys.stderr,
                )
                
                try:
                    creds = flow.run_local_server(
                        port=8080,
                        open_browser=False,
                        authorization_prompt_message=(
                            "\n\n🔗 COPY THIS URL TO YOUR BROWSER:\n{url}\n\n"
                            "After authorization, return to this terminal.\n"
                        ),
                    )
                except Exception as e:
                    print(f"\nAuthentication failed: {e}", file=sys.stderr)
                    print(
                        "\nTroubleshooting:"
                        "\n- Ensure port 8080 is not blocked"
                        "\n- Check your SSH tunnel if using one"
                        "\n- Verify the credentials.json file is valid",
                        file=sys.stderr,
                    )
                    raise
            else:
                # Desktop environment - open browser automatically
                try:
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    print(f"\nBrowser-based auth failed: {e}", file=sys.stderr)
                    print(
                        "\nFalling back to manual mode...",
                        file=sys.stderr,
                    )
                    # Fallback to headless mode
                    creds = flow.run_local_server(
                        port=8080,
                        open_browser=False,
                        authorization_prompt_message=(
                            "\n\n🔗 COPY THIS URL TO YOUR BROWSER:\n{url}\n\n"
                            "After authorization, return to this terminal.\n"
                        ),
                    )

        with open(token_path, "w") as token_file:
            token_file.write(creds.to_json())
        
        # Display the token for manual use in headless environments
        if _is_headless():
            print(
                "\n" + "="*50,
                file=sys.stderr,
            )
            print(
                "✅ AUTHENTICATION SUCCESSFUL!"
                "\n\nFor future use on headless servers, set this environment variable:"
                "\nexport GOOGLE_DRIVE_TOKEN='" + creds.to_json().replace("'", "'\"'\"'") + "'"
                "\n\nOr save it to a file and source it:"
                "\necho \"export GOOGLE_DRIVE_TOKEN='" + creds.to_json().replace("'", "'\"'\"'") + "'\" > ~/drive_token.env"
                "\nsource ~/drive_token.env"
                "\n" + "="*50,
                file=sys.stderr,
            )

    return creds
