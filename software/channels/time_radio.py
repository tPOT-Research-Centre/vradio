# channels/internet_radio.py

import asyncio

"""

	This class requires raspotify installed on the system along with an associated configuration file... 

	You need to run spot_auth.py before running this player. spot_auth will give a URL to be pasted into a browser, the response
        can then be pased into spot_auth, this will set the token in the local cache which should be valid for 30 days. 
"""

import asyncio
import time
import subprocess
import re
import random
from collections import defaultdict

from spot import Spot



from base_channel import BaseChannel

class time_demo(BaseChannel):
    def __init__(self, config):
        super().__init__(config)
        self.play_lock = asyncio.Lock()
        self.ch_index = 0
        self.process=0

        self.play_back_device_name = config.get("playback_device")
        self.allowed_playlists = config.get("play_lists")
        
        print(f"[{self.name}] Got the following lists {self.allowed_playlists} ")

        print(f"[{self.name}] Going to use {self.play_back_device_name} for playback, if available")


        self.vradio_spot = Spot()
      #  self.vradio_spot.ensure_spotifyd_running()
        time.sleep(2)  # Give spotifyd time to register its up and running


        if self.vradio_spot.check_token() > 0:
            print("Spotify Token refreshed")
            self.vradio_spot.login()
            #self.vradio_spot.register_raspotify()
            self.vradio_spot.devices()
            self.vradio_spot.select_device(self.play_back_device_name)
            self.vradio_spot.stop()

            self.playlists = self.vradio_spot.get_all_user_playlists()
            print(f"[{self.name}] Found {len(self.playlists)} playlists, Type {type(self.playlists)}")
            for p in self.playlists:
                print(f"[{self.name}] {p}")

            #keep_names_lower = [name.lower() for name in self.allowed_playlists]
            #self.playlists[:] = [p for p in self.playlists if p['name'].lower().strip() in keep_names_lower]

#            print("final lists...")
#            for p in self.playlists:
#                print(p)



            self.track_count = 0
            self.track_index = 0

            self.play_list_count = len(self.playlists)
            self.play_list_index = 0
            self.playlist_index = 0

            print(f"[{self.name}] Processing playlists")

             # Regex to find 4-digit years between 1900–2099
            year_pattern = re.compile(r"(19\d0|20\d0)")

             # Group playlists by decade
            self.decades = defaultdict(list)

            for pl in self.playlists:
                match = year_pattern.search(pl['name'])
                if match:
                    year = int(match.group(0))
                    decade = (year // 10) * 10  # e.g. 1992 -> 1990
                    self.decades[decade].append(pl)
                else:
                    print(f"[{self.name}] No Match found for:- {pl['name']}")

            # Print grouped playlists
            for decade, pls in sorted(self.decades.items()):
                print(f"[{self.name}] Playlists from the {decade}s:")
                for pl in pls:
                    print(f"[{self.name}]  - {pl['name']} ({pl['track_count']} tracks). URI {pl['uri']}")






        else:
            print(f"[{self.name}] Unable to refresh token, run spot_auth.py and get a new token")

        self.min_decade = min(self.decades)
        self.max_decade = max(self.decades)
        print(f"[{self.name}] Min decade: {self.min_decade}")
        print(f"[{self.name}] Max decade: {self.max_decade}")

        self.sorted_decades = sorted(self.decades.keys())
        print(f"[{self.name}] Sorted decades: {self.sorted_decades}")
        self.decade_index = 0


    async def play(self):
       

        if self.process == 0:

            if self.magic_eye != None:
                print(f"[{self.name}] Setting magic eye", 100)
                self.magic_eye.send(self.magic_colour, 100)


            self.process = 1

            self.vradio_spot.play_list(self.playlists[0]['uri'])
            self.track_count=self.playlists[0]['track_count']
            print(f"[{self.name}] Starting stream:")
           
       
        
    async def on_encoder_B_input(self, value: int):
         if value > 0 and self.decade_index < len(self.sorted_decades) - 1:
            self.decade_index = self.decade_index + 1

            #select a play list at random from this decade... 

            self.playlist_index = random.randint(0, len(self.decades[self.sorted_decades[self.decade_index]])-1)

            print(f"[{self.name}] playing:", self.decade_index, self.sorted_decades[self.decade_index], self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["name"])
         

            self.vradio_spot.stop()
            self.vradio_spot.play_list(self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["uri"])
            self.track_count=self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["track_count"]


         if value < 0 and self.decade_index > 0:
            self.decade_index = self.decade_index -1
            #print("playing:", self.sorted_decades[self.decade_index])

            self.playlist_index = random.randint(0, len(self.decades[self.sorted_decades[self.decade_index]])-1)

            print(f"[{self.name}] playing:", self.decade_index, self.sorted_decades[self.decade_index], self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["name"])

            
            #self.vradio_spot.play_list(self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["uri"])


            self.vradio_spot.stop()
            self.vradio_spot.play_list(self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["uri"])
            self.track_count=self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["track_count"]



    async def on_encoder_A_input(self, value: int):
        
        if value > 0 and self.playlist_index < len(self.decades[self.sorted_decades[self.decade_index]]) -1:
            self.playlist_index=self.playlist_index+1

            print(f"[{self.name}] playing:", self.decade_index, self.sorted_decades[self.decade_index], self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["name"])
            self.vradio_spot.stop()
            self.vradio_spot.play_list(self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["uri"])
            self.track_count=self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["track_count"]

            
	    #if self.magic_eye != None:
            #    self.magic_eye.send(self.magic_colour, self.vradio_spot.get_playlist_completion())


        if value < 0 and self.playlist_index > 0:
            self.playlist_index=self.playlist_index-1
            print(f"[{self.name}] playing:", self.decade_index, self.sorted_decades[self.decade_index], self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["name"])
            self.vradio_spot.stop()
            self.vradio_spot.play_list(self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["uri"])
            self.track_count=self.decades[self.sorted_decades[self.decade_index]][self.playlist_index]["track_count"]

            #if self.magic_eye != None:
            #    self.magic_eye.send(self.magic_colour, self.vradio_spot.get_playlist_completion())




    async def on_encoder_A_input_old(self, value: int):
        track = self.vradio_spot.get_current_track_index()
        print("Stats ",  track, self.vradio_spot.get_playlist_completion())



        if value > 0 and track < self.track_count -1:
            self.vradio_spot.next_track()
            if self.magic_eye != None:
                self.magic_eye.send(self.magic_colour, self.vradio_spot.get_playlist_completion())


        if value < 0 and track > 0:
            self.vradio_spot.previous_track()

            if self.magic_eye != None:
                self.magic_eye.send(self.magic_colour, self.vradio_spot.get_playlist_completion())


    async def stop(self):
#        print(f"[{self.name}] Stop Requested")
        if self.process != 0:
            self.vradio_spot.stop()
            print(f"[{self.name}] process finished")
            if self.magic_eye != None:
                print(f"[{self.name}] Setting magic eye", 0)
                self.magic_eye.send(self.magic_colour, 0)


        self.process = 0


