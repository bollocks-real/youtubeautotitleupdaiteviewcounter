#!/usr/bin/env python3

import http.client
import httplib2
import os
import sys
import time
import schedule
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Retry settings
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, http.client.NotConnected,
  http.client.IncompleteRead, http.client.ImproperConnectionState,
  http.client.CannotSendRequest, http.client.CannotSendHeader,
  http.client.ResponseNotReady, http.client.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# OAuth configuration
CLIENT_SECRETS_FILE = "client_secrets.json"
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
TOKEN_FILE = "token.json"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console
https://cloud.google.com/console
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

def get_authenticated_service():
  credentials = None
  
  # Load existing token if available
  if os.path.exists(TOKEN_FILE):
    credentials = Credentials.from_authorized_user_file(TOKEN_FILE, YOUTUBE_READ_WRITE_SCOPE)
  
  # If no valid credentials, create new ones
  if not credentials or not credentials.valid:
    if credentials and credentials.expired and credentials.refresh_token:
      credentials.refresh(Request())
    else:
      if not os.path.exists(CLIENT_SECRETS_FILE):
        print(MISSING_CLIENT_SECRETS_MESSAGE)
        sys.exit(1)
      
      flow = InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=[YOUTUBE_READ_WRITE_SCOPE]
      )
      credentials = flow.run_local_server(port=0)
    
    # Save credentials for future runs
    with open(TOKEN_FILE, 'w') as token:
      token.write(credentials.to_json())
  
  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, credentials=credentials)

def update_video_title(youtube, video_id, view_count):
  """Update the title of a video based on its current view count."""
  try:
    # Get the current video details
    videos_response = youtube.videos().list(
      part="snippet",
      id=video_id
    ).execute()

    if not videos_response["items"]:
      print("Video with ID '%s' not found." % video_id)
      return False

    # Get the current snippet
    snippet = videos_response["items"][0]["snippet"]
    
    # Update the title with the view count
    snippet["title"] = "This had %s 1 hour ago" % view_count
    
    # Update the video
    update_response = youtube.videos().update(
      part="snippet",
      body=dict(
        id=video_id,
        snippet=snippet
      )
    ).execute()

    print("Video title updated successfully to: '%s'" % update_response["snippet"]["title"])
    return True

  except HttpError as e:
    print("An HTTP error %d occurred:\n%s" % (e.resp.status, e.content))
    return False

def job(youtube, video_id):
  """Job to run every hour."""
  try:
    stats_response = youtube.videos().list(
      part="statistics",
      id=video_id
    ).execute()

    if not stats_response["items"]:
      print("Video with ID '%s' not found when fetching statistics." % video_id)
      return

    view_count = stats_response["items"][0]["statistics"].get("viewCount", "0")
    new_title = "This had %s 1 hour ago" % view_count
    print("Running scheduled update for video %s with %s views." % (video_id, view_count))
    update_video_title(youtube, video_id, view_count)
  except HttpError as e:
    print("An HTTP error %d occurred while fetching statistics:\n%s" % (e.resp.status, e.content))

if __name__ == "__main__":
  if len(sys.argv) < 3 or sys.argv[1] != "--video-id":
    print("Usage: python update_video_title_hourly.py --video-id VIDEO_ID")
    sys.exit(1)
  
  video_id = sys.argv[2]
  
  youtube = get_authenticated_service()
  
  # Schedule the job to run every hour
  schedule.every(1).hours.do(job, youtube=youtube, video_id=video_id)
  
  print("Starting hourly video title updates for video ID: %s" % video_id)
  print("Press Ctrl+C to stop.")
  
  # Keep the scheduler running
  while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute if a job needs to run
