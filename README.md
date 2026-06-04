# YouTube Auto Title Update View Counter

A Python script that automatically updates a YouTube video title every hour using the YouTube Data API.

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **YouTube Data API v3**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Select application type: **Desktop application**
6. Download the JSON credentials file
7. Rename it to `client_secrets.json` and place it in the project directory

### 3. Run the Script

```bash
python update_video_title_hourly.py --video-id YOUR_VIDEO_ID
```

Replace `YOUR_VIDEO_ID` with your actual YouTube video ID (found in the video URL: `youtube.com/watch?v=YOUR_VIDEO_ID`)

### 4. First-Time Authentication

- The script will open your browser and ask you to sign in
- Grant permission to manage your YouTube videos
- The authorization token will be saved automatically for future runs

## Usage

Once running, the script will:
- Update your video title every hour with a timestamp
- Continue running until you press `Ctrl+C`
- You can customize the title format in the `job()` function

## Files

- `update_video_title_hourly.py` - Main script
- `requirements.txt` - Python dependencies
- `client_secrets.json` - OAuth credentials (create from Google Cloud Console)
- `update_video_title_hourly.py-oauth2.json` - Generated after first authentication
