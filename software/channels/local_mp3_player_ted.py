# channels/local_mp3_player.py
import asyncio
import subprocess
import os
import random
import time

from base_channel import BaseChannel

class LocalMP3Channel(BaseChannel):
    def __init__(self, config):
        super().__init__(config)
        self.play_lock = asyncio.Lock()

        self.volume = 50
        self.process = None

        # Get the directory where the current script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Relative folder "audio" inside the script directory
        self.audio_dir = os.path.join(script_dir, 'audio')

        supported_exts = {'.mp3', '.mp4'}
        self.media_files = []

        for filename in os.listdir(self.audio_dir):
            if os.path.splitext(filename)[1].lower() in supported_exts:
                self.media_files.append(os.path.join(self.audio_dir, filename))
        print("Media Files", self.media_files)

        self.file_path = None
        self.dir = 0
        self.eye_val = 0
        self.offset = 0  # in seconds
        self.start_time = None


        name  = config.get("filename")
        self.fname = os.path.join(self.audio_dir, name )

        print("File To Play", self.fname)





    async def play(self):
        #run magic eye test if it's available on this model

        if self.magic_eye != None:
           if self.dir == 0:
               self.eye_val=self.eye_val+10
               if self.eye_val>99:
                   self.dir = 1
                   self.eye_val=99
           else:
               self.eye_val=self.eye_val-10
               if self.eye_val <= 0:
                   self.dir = 0
                   self.eye_val=0


           self.magic_eye.send(self.magic_colour, self.eye_val)


        async with self.play_lock:
            if self.process is None:
                await self.playNewAudio()
            else:
                if self.process.returncode is not None:
                    print(f"[{self.name}] Stopped at eof, reseeting offset")
                    self.offset = 0
                    await self.playNewAudio()


 

    async def stop(self):
        async with self.play_lock:

            if self.process and self.process.returncode is None:
                elapsed = time.time() - self.start_time
                self.offset += elapsed

                print(f"[{self.name}] Stopping playback. Saving offset {self.offset}s")
                self.process.terminate()
                await self.process.wait()
        

                if self.magic_eye != None:
                    self.magic_eye.send(0xF000, 0)

            self.process = None


    async def playNewAudio(self):
        # select a new autio file. 
        self.file_path = self.fname

        # stop the audio playing, if it is playing
        if self.process and self.process.returncode is None:
            print(f"[{self.name}] Stopping playback.")
            self.process.terminate()
            await self.process.wait()
        self.process = None

        self.start_time = time.time()
        seconds_into_hour = int(self.start_time % 3600)


        print(f"[{self.name}] Starting playback of: {self.file_path} from time {seconds_into_hour}")
        self.process = await asyncio.create_subprocess_exec("ffplay", "-nodisp", "-autoexit", "-ss", str(seconds_into_hour), self.file_path,stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)


    async def on_encoder_A_input(self, value: int):
         await self.playNewAudio()

    async def on_encoder_B_input(self, value: int):
         print(f"[{self.name}] Encoder B not implemented")


  







