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

You need a credentials.json file from the [Google Cloud Console](https://console.cloud.google.com/):

1. Create a project (or use an existing one).
2. Enable the **Google Drive API**.
3. Create **OAuth 2.0 Client ID** credentials (Desktop application).
4. Download the JSON file and save it as credentials.json.

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

### Flags

| Flag              | Description                                                                                        |
| ----------------- | -------------------------------------------------------------------------------------------------- |
| -s, --source      | **(required)** Path to the file or directory to upload.                                            |
| -c, --credentials | Path to credentials.json. Falls back to GOOGLE_DRIVE_CREDENTIALS env var.                          |
| -t, --token       | OAuth token JSON. Falls back to GOOGLE_DRIVE_TOKEN env var. If provided, --credentials is ignored. |

## How It Works

1. **Authentication** -- On first run, the tool opens a browser for Google OAuth consent. A token.json is cached alongside your credentials file for subsequent runs.
2. **Directory handling** -- If the source is a directory, it is zipped into a temporary archive before uploading. The archive is cleaned up after the upload.
3. **Resumable uploads** -- Large files are uploaded using resumable uploads for reliability.

## Scope

The tool uses the drive.file scope, which only grants access to files created or opened by this application -- the most restrictive scope suitable for uploads.
