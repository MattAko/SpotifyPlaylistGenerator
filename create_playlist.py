"""
Step 1: Log into Youtube
Step 2: Grab Liked Videos
Step 3: Create Spotify Playlist
Step 4: Search Spotify for Song
Step 5: Add this song to Spotify Playlist
"""

import requests
import json
import os

from exceptions import ResponseException
from secrets import spotify_user_id, spotify_token

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import youtube_dl

class CreatePlaylist:
    def __init__(self):
        self.user_id = spotify_user_id
        self.spotify_token = spotify_token
        self.youtube_client = self.get_youtube_client()
        self.all_song_info = {}
        self.playlist_title = ""


    #Step 1: Get the YouTube Client for the User
    #This is how we will be able to extract their liked videos
    def get_youtube_client(self):
        # Log Into Youtube, Copied from Youtube Data API 
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes)
        credentials = flow.run_console()

        # from the Youtube DATA API 
        youtube_client = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)

        return youtube_client

    #Step 2: Get Liked Videos from YouTube Client
    #Store Important Information into a Dictionary 'youtube_client'
    def get_liked_videos(self):
        print("Getting liked videos")

        #Request playlist data

        # playlist_id = "PLzja71NlsinKQMFJlcWyyCqV_0YsdV4gH"

        playlist_id = self.url_check()
        playlist_url = "https://www.youtube.com/playlist?list={}".format(playlist_id)
        request = self.youtube_client.playlists().list(
            part = "snippet,contentDetails",
            id = playlist_id
            )

        #excute to receive a response
        response = request.execute()

        #grab playlist information
        #playlist info includes all information for each video
        playlist_videos = youtube_dl.YoutubeDL({}).extract_info(playlist_url, download=False)
        #print(playlist_videos)
        self.playlist_title = playlist_videos["title"]
        print("Playlist title is: " + self.playlist_title)
        for entry in playlist_videos["entries"]:
            song_name = entry["track"]
            artist = entry["artist"]
            video_title = entry["title"]

            if song_name is not None and artist is not None:
                print("Video Title: " + entry["title"] + " Song: " + entry["track"] + " Arist: " + entry["artist"])
                # save all important info and skip any missing song and artist
                self.all_song_info[video_title] = {
                    "song_name": song_name,
                    "artist": artist,

                    # search spotify for song, save uri of the first song from search
                    "spotify_uri": self.get_spotify_uri(song_name, artist)
                }

    #Step 3: Create a Spotify Playlist
    #Returns the Spotify Playlist ID
    def create_playlist(self):
        print("Creating playlist")
        request_body = json.dumps({
            "name":self.playlist_title,
            "public": False,
            "description":"All liked songs"
        })

        query = "https://api.spotify.com/v1/users/{}/playlists".format(self.user_id)

        response = requests.post(
            query,
            data = request_body,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(self.spotify_token)
            }
        )

        response_json = response.json()

        #playlist id
        return response_json["id"]

    #Step 4: Search Spotify for Song
    #Returns the URI of the first song from search
    def get_spotify_uri(self, song_name, artist):
        print("Getting spotify uri")
        query = "https://api.spotify.com/v1/search?query=track%3A{}+artist%3A{}&type=track&offset=0&limit=20".format(
            song_name,
            artist
        )
        response = requests.get(
            query,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {}".format(spotify_token)
            }
        )
        response_json = response.json()
        songs = response_json["tracks"]["items"]

        # only use the first song
        if response_json["tracks"]["total"] > 0:
            print("Spotify search valid for :" + song_name + " by " + artist)
            return songs[0]["uri"]

        else:
            return "empty"

    #Step 5:
    def add_to_playlist(self):
        print("Add to playlist")
        #populate our songs dictionary
        self.get_liked_videos()

        uris = []
        for song, info in self.all_song_info.items():
            if info["spotify_uri"] != "empty":
                uris.append(info["spotify_uri"])
        print(uris)

        #create a new playlist
        playlist_id = self.create_playlist()

        #add all songs into a new playlist
        request_data = json.dumps(uris)

        query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

        print("Posting songs...")
        response = requests.post(
            query,
            data = request_data,
            headers={
                "Content-Type":"application/json",
                "Authorization":"Bearer {}".format(self.spotify_token)
            }
        )

        response_json = response.json()
        return response_json

    #Check if URL is a valid YouTube Playlist
    #Return the playlist ID
    def url_check(self):
        url = input("Please paste a YouTube playlist URL:")
        if url.startswith("https://www.youtube.com/playlist?list="):
            id = url[len("https://www.youtube.com/playlist?list="):]
            return id
        else:
            pass


if __name__=='__main__':
    cp = CreatePlaylist()
    cp.add_to_playlist()