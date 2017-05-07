import httplib2
import os
import sys
import argparse

import json
import sys
import requests
from urlparse import urlparse, parse_qs

base_url = 'https://www.googleapis.com/youtube/v3/'
comment_threads_url = 'commentThreads'
videos_url = 'videos'

from apiclient.discovery import build_from_document
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# The client_secrets_file variable specifies the name of a file that contains

# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
youtube_read_write_ssl_scope = "https://www.googleapis.com/auth/youtube.force-ssl"
youtube_api_service_name = "youtube"
youtube_api_version = "v3"


class YouTubeApi:
    def __init__(self, client_secrets_file=None):
        
        self.client_secrets_file = "client_secrets.json" if not client_secrets_file \
            else client_secrets_file

    # Authorize the request and store authorization credentials.
    def get_authenticated_service(self, args):
        # This variable defines a message to display if the client_secrets_file is
        # missing.
        missing_client_secrets_message = """
        WARNING: Please configure OAuth 2.0
        
        To make this sample run you will need to populate the client_secrets.json file
        found at:
           %s
        with information from the APIs Console
        https://console.developers.google.com
        
        For more information about the client_secrets.json file format, please visit:
        https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
        """ % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           self.client_secrets_file))
                                   
        flow = flow_from_clientsecrets(self.client_secrets_file, scope=youtube_read_write_ssl_scope,
            message=missing_client_secrets_message)

        storage = Storage("%s-oauth2.json" % 'tuber.py')
        credentials = storage.get()

        if credentials is None or credentials.invalid:
            credentials = run_flow(flow, storage, args)

        # Trusted testers can download this discovery document from the developers page
        # and it should be in the same directory with the code
        # https://www.googleapis.com/discovery/v1/apis/youtube/v3/rest
        with open("youtube-v3-discoverydocument.json", "r") as f:
            doc = f.read()
            return build_from_document(doc, http=credentials.authorize(httplib2.Http()))
    
    def get_my_parser(self):
        ### this is here to override default parameters set by google's
        # argparser https://github.com/google/oauth2client/blob/master/oauth2client/tools.py
        parser = argparse.ArgumentParser(add_help=False, conflict_handler='resolve')
        parser.add_argument('--auth_host_name', default='localhost',
                            help='Hostname when running a local web server.')
        parser.add_argument('--noauth_local_webserver', action='store_true',
                            default=True, help='Do not run a local web server.')
        parser.add_argument('--auth_host_port', default=[8080, 8090], type=int,
                            nargs='*', help='Port web server should listen on.')
        parser.add_argument(
            '--logging_level', default='ERROR',
            choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
            help='Set the logging level of detail.')
        return parser

    def post_comment(self, video_url, comment_text):
        response = self.get_video_params(video_url)
        
        response = self.get_video_params(video_url)
        if response['success']:
            video_id, channel_id = (response['video_id'], response['channel_id'])
        else:
            return response

        parser = self.get_my_parser()
        parser.add_argument("--channelid", default=channel_id)
        parser.add_argument("--videoid", default=video_id)
        parser.add_argument("--text",  default=comment_text)
        
        args = parser.parse_args()
        
        youtube = self.get_authenticated_service(args)

        try:
            insert_result = youtube.commentThreads().insert(
              part="snippet",
              body=dict(
                snippet=dict(
                  channelId=channel_id,
                  videoId=video_id,
                  topLevelComment=dict(
                    snippet=dict(
                      textOriginal=comment_text
                    )
                  )
                )
              )
            ).execute()
        except:
            response = {'success': False, 'text': 'Some request error'}
            return response

        comment = insert_result["snippet"]["topLevelComment"]
        author = comment["snippet"]["authorDisplayName"]
        text = comment["snippet"]["textDisplay"]

        response = {'success': True, 'text': 'Your comment has been posted'}
        return response


    def get_video_params(self, video_url):
        try:
            if 'youtu.be' in video_url:
                video_id = video_url.split('youtu.be/')[-1]
            else:
                video_url_dict = urlparse(str(video_url))
                q = parse_qs(video_url_dict.query)
                video_id = q["v"][0]
        except:
            response = {'success': False, 'text': 'Invalid YouTube URL'}
            return response

        parser = self.get_my_parser()
        parser.add_argument("--videoid", default=video_id)
        
        args = parser.parse_args()
        
        youtube = self.get_authenticated_service(args)

        results = youtube.videos().list(
            part="snippet",
            id=video_id
          ).execute()

        if results['items']:
            channel_id = results['items'][0]['snippet']['channelId']
            response = {'success': True, 'video_id': video_id, 'channel_id': channel_id}
            
        else:
            response = {'success': False, 'text': 'Such URL does not exist'}

        return response
