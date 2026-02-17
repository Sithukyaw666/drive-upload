# drive-upload

CLI tool to upload files and directories to Google Drive.

## Installation

```bash
pip install .
```

Or in editable/development mode:

```bash
pip install -e .
```

### Prerequisites

You need OAuth credentials from the [Google Cloud Console](https://console.cloud.google.com/):

1. Create a project (or use an existing one).
2. Enable the **Google Drive API**.
3. Create **OAuth 2.0 Client ID** credentials (Desktop application).
4. Download the JSON file and save it as `credentials.json`.

**What's in each file:**
- **`credentials.json`** = Your OAuth client credentials (`client_id`, `client_secret`) - like API keys
- **`token.json`** = Your actual access tokens (`access_token`, `refresh_token`) - generated from credentials

## Usage

### Standard Usage (Desktop/Local)

```bash
# Upload a file using an explicit credentials path
upload-drive -s ./my_file.txt -c ./credentials.json

# Upload a directory (it will be zipped automatically)
upload-drive -s ./my_folder -c ./credentials.json

# Use an environment variable for credentials
export GOOGLE_DRIVE_CREDENTIALS=./credentials.json
upload-drive -s ./my_file.txt
```

### Token-based Usage (Headless Servers)

**Step 1: Generate a reusable token**
```bash
# Use your credentials.json to generate token.json (requires browser access)
upload-drive --token generate -c ./credentials.json
# ✅ Token saved to token.json
# This file contains your access token and can be reused on headless servers.
```

**Step 2: Use the token for uploads**
```bash
# Use generated token.json file (contains both OAuth tokens AND client credentials)
upload-drive -s ./my_file.txt -t ./token.json

# Or use token from environment variable  
export GOOGLE_DRIVE_TOKEN='{"access_token":"ya29.a0A...", "refresh_token":"1//0G...", "client_id":"...apps.googleusercontent.com", "client_secret":"..."}'
upload-drive -s ./my_file.txt

# Or pass complete token directly
upload-drive -s ./my_file.txt -t '{"access_token":"ya29.a0A...", "refresh_token":"1//0G...", "client_id":"...", "client_secret":"..."}'
```

**The Process:**
1. `credentials.json` (client_id + client_secret) → OAuth flow → `token.json` (access_token + refresh_token + client credentials)
2. Copy `token.json` to headless servers for standalone authentication

> **Note**: The generated `token.json` includes your OAuth credentials (`client_id`, `client_secret`) and access tokens. Keep this file secure and don't commit it to version control.

### Flags

| Flag              | Description                                                                                                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------------ |
| -s, --source      | Path to the file or directory to upload. Required unless using `--token generate`.                                |
| -c, --credentials | Path to credentials.json. Falls back to GOOGLE_DRIVE_CREDENTIALS env var.                                          |
| -t, --token       | Token handling: `generate` to create token.json, path to token file, or raw JSON. Falls back to GOOGLE_DRIVE_TOKEN env var. |

## How It Works

1. **Authentication** -- On first run, the tool opens a browser for Google OAuth consent. A token.json is cached alongside your credentials file for subsequent runs.
2. **Directory handling** -- If the source is a directory, it is zipped into a temporary archive before uploading. The archive is cleaned up after the upload.
3. **Resumable uploads** -- Large files are uploaded using resumable uploads for reliability.

## Scope

The tool uses the drive.file scope, which only grants access to files created or opened by this application -- the most restrictive scope suitable for uploads.
