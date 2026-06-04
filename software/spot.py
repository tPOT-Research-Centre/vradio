import logging
import sys
import psutil
import subprocess
import os

from datetime import datetime, timezone

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange




logging.basicConfig(level=logging.INFO)


class SpotifyZeroconf:
    def __init__(self):
        self.device_info = None

    def add_service(self, zeroconf, type, name):
        info = zeroconf.get_service_info(type, name)
        if info:
            addr = ".".join(map(str, info.addresses[0]))
            self.device_info = {
                "name": name,
                "ip": addr,
                "port": info.port,
                "cpath": info.properties.get(b"CPath", b"/").decode("utf-8")
            }

    def remove_service(self, zeroconf, type, name):
        pass

    def update_service(self, zeroconf, type, name):
        pass


class Spot:
    def __init__(self,
                 client_id='8fc500f7e0854d93ba651782de551259',
                 client_secret='44365a61a7a446a2a68144b5f262f646',
                 redirect_uri='http://127.0.0.1:8888/callback',
                 scope='user-library-read user-read-playback-state user-modify-playback-state playlist-read-private',
                 cache_path='.cache'):

        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scope = scope
        self.cache_path = cache_path
        self.playlists = []

        self.current_playlist = None
        self.tracks = None
        self.total_tracks = None
        self.track_index = 0



        self.sp_oauth = SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=self.scope,
            cache_path=self.cache_path
        )
        self.sp = None
        self.actual_device_id = None

    def check_token(self):
        token_info = self.sp_oauth.get_cached_token()

        if not token_info:
            print("No cached token found. Please authenticate on a machine with a browser.")
            return -1

        if not self.sp_oauth.validate_token(token_info):
            print("Token expired or invalid. Please reauthenticate on a browser-enabled device.")
            return -2

        try:
            refreshed = self.sp_oauth.refresh_access_token(token_info['refresh_token'])
            print("Token refreshed successfully.")
            print("New access token:", refreshed['access_token'])

            expires_at_unix = refreshed['expires_at']
            expires_utc = datetime.fromtimestamp(expires_at_unix, tz=timezone.utc)
            print(f"Token expires at: {expires_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}")

            return 1

        except Exception as e:
            print("Failed to refresh token:", e)
            return -3


    def register_raspotify(self):
        zeroconf = Zeroconf()
        listener = SpotifyZeroconf()
        browser = ServiceBrowser(zeroconf, "_spotify-connect._tcp.local.", listener)

        print("Searching for Raspotify device...")
        while listener.device_info is None:
            pass  # wait until discovered

        device = listener.device_info
        zeroconf.close()

        url = f"http://{device['ip']}:{device['port']}{device['cpath']}"

        payload = {
            "action": "addUser",
            "userName": self.client_id,
            "blob": self.sp_oauth,
            "clientKey": ""
        }

        print(f"Registering with {url} ...")
        r = requests.post(url, json=payload)
        r.raise_for_status()

        print("Raspotify registered:", r.text)


    def login(self):
        try:
            self.sp = spotipy.Spotify(auth_manager=self.sp_oauth)
            print("Spotify client initialized.")
        except SpotifyException as e:
            print("Failed to initialize Spotify client:", e)
            self.sp = None

    def select_device(self, name):
        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return -1

        try:
            result = self.sp.devices()
            for d in result['devices']:
#                print(f"\t \t {d['name']} ID: {d['id']}")
                if d['name'] == name:
                    self.actual_device_id = d['id']
                    print("Got actual device id", self.actual_device_id)
                    return 1

        except SpotifyException as e:
            print("Error fetching devices:", e)
            return -1

        print(f"Device {name} not found")
        return -2


    def devices(self):
        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return []

        try:
            result = self.sp.devices()
            for d in result['devices']:
                print(f"\t \t {d['name']} ID: {d['id']}")
            return result['devices']
        except SpotifyException as e:
            print("Error fetching devices:", e)
            return []

    def top_tracks(self):
        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return []

        try:
            result = self.sp.current_user_top_tracks(limit=5, time_range='short_term')
            print(result)
            return result
        except SpotifyException as e:
            print("Error fetching top_tracks:", e)
            return []

    def play(self, track_id):

        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return -1

        if self.actual_device_id == None:
            print("Spotify No device selected. Call `select_device()` first.")
            return -2

        try:
            self.sp.start_playback(device_id=self.actual_device_id, uris=[track_id])
            return 1
        except SpotifyException as e:
            print("Error fetching top_tracks:", e)
            return -1

    def play_list(self, list_id):

        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return -1

        if self.actual_device_id == None:
            print("Spotify No device selected. Call `select_device()` first.")
            return -2

        try:
            self.sp.start_playback(device_id=self.actual_device_id, context_uri=list_id)

            self.current_playlist = self.sp.playlist_tracks(list_id)
            self.tracks = self.current_playlist["items"]
            self.total_tracks = self.current_playlist["total"]

            return 1
        except SpotifyException as e:
            print("Error fetching top_tracks:", e)
            return -1

    def stop(self):
        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return
        try:
            self.sp.pause_playback(device_id=self.actual_device_id)
        except spotipy.SpotifyException as e:
            print(f"Failed to stop device: {e}")


    def next_track(self):
        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return

        try:
            self.sp.next_track(device_id=self.actual_device_id)
            print("Skipped to next track.")
        except spotipy.SpotifyException as e:
            print(f"Failed to skip to next track: {e}")

    def previous_track(self):
        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return


        try:
            self.sp.previous_track(device_id=self.actual_device_id)
            print("Went to previous track.")
        except spotipy.SpotifyException as e:
            print(f"Failed to go to previous track: {e}")


    def next_track_safe(self):
        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return

        try:

            current = self.sp.current_playback()
            current_track_id = current["item"]["id"]

	    # Find its index in the playlist
            self.track_index = next((i for i, item in enumerate(self.tracks) if item["track"]["id"] == current_track_id), None)

            if self.track_index is None or self.track_index >= self.total_tracks - 1:
                 print("end of playlist", self.track_index, self.total_tracks)
                 return;	


            self.sp.next_track(device_id=self.actual_device_id)
            print("Skipped to next track.")
        except spotipy.SpotifyException as e:
            print(f"Failed to skip to next track: {e}")

    def previous_track_safe(self):
        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return


        try:
            self.sp.previous_track(device_id=self.actual_device_id)
            print("Went to previous track.")
        except spotipy.SpotifyException as e:
            print(f"Failed to go to previous track: {e}")

    def get_playlist_completion(self):
        return 100*(self.get_current_track_index()+1)/self.total_tracks

    def get_current_track_index(self):
        if not self.sp:
            print("Spotify client not initialized. Call `login()` first.")
            return 0

        try:

            current = self.sp.current_playback()
            current_track_id = current["item"]["id"]

	    # Find its index in the playlist
            index = next((i for i, item in enumerate(self.tracks) if item["track"]["id"] == current_track_id), None)

            return index

        except spotipy.SpotifyException as e:
            print(f"Failed to skip to next track: {e}")

        return 0


    def play_list_fallback(self, playlist_id):
         # Get the playlist items
        results = self.sp.playlist_items(playlist_id)
        track_uris = [item['track']['uri'] for item in results['items'] if item['track']]

        if not track_uris:
            print("No playable tracks found.")
            return

        # Start playback using track URIs instead of context_uri
        selfsp.start_playback(device_id=self.actual_device_id, uris=track_uris)

    def is_spotifyd_running(self):
        result = subprocess.run(["systemctl", "is-active", "raspotify"],   capture_output=True, text=True  )
        return result.stdout.strip() == "active"



    def is_spotifyd_running_old(self):
        return True
        for proc in psutil.process_iter(attrs=['name']):
            if proc.info['name'] == 'spotifyd':
                return True
        return False

    def start_spotifyd(self):
        print("Starting spotifyd...")
        #subprocess.Popen(['spotifyd'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def ensure_spotifyd_running(self):
        if self.is_spotifyd_running():
            print("raspotify is already running.")
        else:
            print("raspotify not running.")
           # self.start_spotifyd()


    def skip_to_next(self):
        try:
            self.sp.next_track()
            print("Skipped to next track.")
        except spotipy.SpotifyException as e:
            print("Failed to skip track:", e)


    def get_playlist_tracks(self, playlist_id):
        try:
            results = self.sp.playlist_items(playlist_id)
        except spotipy.SpotifyException as e:
            print("Failed to get get_playlist_tracks:", e)

    def get_all_user_playlists(self):
        self.playlists = []
        results = self.sp.current_user_playlists()

        while results:
            for playlist in results['items']:
                self.playlists.append({
                'name': playlist['name'],
                'id': playlist['id'],
                'uri': playlist['uri'],
                'owner': playlist['owner']['display_name'],
                'track_count': playlist['tracks']['total']})

                #print("playlist ", playlist)

            if results['next']:
                results = self.sp.next(results)
            else:
                results = None

        return self.playlists

    
    def currently_playing(self):
    # Check current playback
        playback = self.sp.current_playback()

        if playback is None:
            print("No active playback device or nothing has ever been played.")
            return  0
        elif not playback['is_playing']:
            print("Playback is paused.")
            return 0
        else:
            current_track = playback['item']['name']
            artist = playback['item']['artists'][0]['name']
            print(f"Now playing: {current_track} by {artist}")
            return 1



# Standalone mode
if __name__ == "__main__":
    spot = Spot()
    code = spot.check_token()
    if code == 1:
        spot.login()
        spot.devices()

    print("SpotifyD status ", spot.is_spotifyd_running())
