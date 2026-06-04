# channels/internet_radio.py

import asyncio

"""

	This class requires spotifyd installed on the system (Version 0.4.0) along with an associated configuration file... 

	You need to run spot_auth.py before running this player. spot_auth will give a URL to be pasted into a browser, the response
        can then be pased into spot_auth, this will set the token in the local cache which should be valid for 30 days. 
"""

import asyncio
import time
import subprocess

from spot import Spot



from base_channel import BaseChannel

class spotify_demo(BaseChannel):
    def __init__(self, config):
        super().__init__(config)
        self.play_lock = asyncio.Lock()
        self.ch_index = 0
        self.process=0

        self.allowed_playlists = config.get("play_lists")

        self.play_back_device_name = config.get("playback_device")
        
        print(f"[{self.name}] Going to use {self.play_back_device_name} for playback, if available")


        self.vradio_spot = Spot()
      #  self.vradio_spot.ensure_spotifyd_running()
        time.sleep(2)  # Give spotifyd time to register its up and running


        if self.vradio_spot.check_token() > 0:
            print("Spotify Token refreshed")
            self.vradio_spot.login()
            self.vradio_spot.devices()
            self.vradio_spot.select_device(self.play_back_device_name)
            self.vradio_spot.stop()

            self.playlists = self.vradio_spot.get_all_user_playlists()

            keep_names_lower = [name.lower() for name in self.allowed_playlists]
            self.playlists[:] = [p for p in self.playlists if p['name'].lower().strip() in keep_names_lower]


            print(f"[{self.name}] Found {len(self.playlists)} playlists")
            for p in self.playlists:
                print(p, "track count", p["track_count"])

            self.track_count = 0
            self.track_index = 0

            self.play_list_count = len(self.playlists)
            self.play_list_index = 0

        else:
            print(f"[{self.name}] Unable to refresh token, run spot_auth.py and get a new token")





    async def play(self):
       

        if self.process == 0 and self.allowed_playlists != None:
            if self.magic_eye != None:
                print(f"[{self.name}] Setting magic eye", 100)
                self.magic_eye.send(self.magic_colour, 100)

            self.process = 1

            self.vradio_spot.play_list(self.playlists[0]['uri'])
            self.track_count=self.playlists[0]['track_count']
            print(f"[{self.name}] Starting stream:")
           
       
        
    async def on_encoder_B_input(self, value: int):
         
        if value > 0 and self.play_list_index < self.play_list_count - 1:
            self.play_list_index = self.play_list_index + 1
            print(self.play_list_index, " URI ", self.playlists[self.play_list_index]['uri'])
            self.vradio_spot.stop()
            self.vradio_spot.play_list(self.playlists[self.play_list_index]['uri'])
            self.track_count=self.playlists[self.play_list_index]['track_count']


        if value < 0 and self.play_list_index > 0:
            self.play_list_index = self.play_list_index -1

            self.vradio_spot.stop()
            self.vradio_spot.play_list(self.playlists[self.play_list_index]['uri'])
            self.track_count=self.playlists[self.play_list_index]['track_count']




        

    async def on_encoder_A_input(self, value: int):
         track = self.vradio_spot.get_current_track_index()
         print("Stats ",  track, self.vradio_spot.get_playlist_completion())

         if self.magic_eye != None:
             #print("Setting magic eye", self.enc_actual)
             self.magic_eye.send(self.magic_colour, self.vradio_spot.get_playlist_completion())


         if value > 0 and track < self.track_count -1:
                    self.vradio_spot.next_track()


         if value < 0 and track > 0:
             self.vradio_spot.previous_track()



    async def stop(self):
#        print(f"[{self.name}] Stop Requested")
        if self.process != 0:
            self.vradio_spot.stop()
            print("process finished")

            if self.magic_eye != None:
                print(f"[{self.name}] Setting magic eye", 0)
                self.magic_eye.send(self.magic_colour, 0)


        self.process = 0




