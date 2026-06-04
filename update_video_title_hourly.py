#!/usr/bin/python

import httplib
import httplib2
import os
import sys
import time
import schedule
from datetime import datetime

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow

# Retry settings
httplib2.RETRIES = 1
MAX_RETRIES = 10
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# OAuth configuration
CLIENT_SECRETS_FILE = "client_secrets.json"
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console
https://cloud.google.com/console
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

def get_authenticated_service(args):
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
    scope=YOUTUBE_READ_WRITE_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))

def update_video_title(youtube, video_id, new_title):
  """Update the title of a video."""
  try:
    # Get the current video details
    videos_response = youtube.videos().list(
      part="snippet",
      id=video_id
    ).execute()

    if not videos_response["items"]:
      print "Video with ID '%s' not found." % video_id
      return False

    # Get the current snippet
    snippet = videos_response["items"][0]["snippet"]
    
    # Update the title
    snippet["title"] = new_title
    
    # Update the video
    update_response = youtube.videos().update(
      part="snippet",
      body=dict(
        id=video_id,
        snippet=snippet
      )
    ).execute()

    print "Video title updated successfully to: '%s'" % update_response["snippet"]["title"]
    return True

  except HttpError, e:
    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
    return False

def job(youtube, video_id):
  """Job to run every hour."""
  timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  new_title = "Updated Title - %s" % timestamp
  print "Running scheduled update at %s" % timestamp
  update_video_title(youtube, video_id, new_title)

if __name__ == "__main__":
  argparser.add_argument("--video-id", required=True,
    help="The ID of the video to update.")
  args = argparser.parse_args()

  youtube = get_authenticated_service(args)
  
  # Schedule the job to run every hour
  schedule.every(1).hours.do(job, youtube=youtube, video_id=args.video_id)
  
  print "Starting hourly video title updates for video ID: %s" % args.video_id
  print "Press Ctrl+C to stop."
  
  # Keep the scheduler running
  while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute if a job needs to run
