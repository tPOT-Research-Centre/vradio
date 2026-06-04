# vradio
Vintage Radio Python Framework for comment/feedback. 

The idea is that as channels are added the user will create new classes from a template in the channels folder. These will all have a similar format. 

A yaml file is used (config.yaml) to configure the radio and link the various channels to buttons and encoder functions etc. 

Requires python 3.11 and greater, need to consider using poetry to manage python dependencies. 

Now tested on a PI4 and Pi5, can be started from dp@raspberrypi:~/vradio $ python main.py
The libraries are not system-wide installation, instead, on virtual environment. Before launching main.py, activate venv using: `source env/bin/activate`. Ensure you are in vradio folder when you activate venv.

Uses FFMPEG to play the audio from python, so FFMPEG must be installed. 

This version requires raspotify installed on the system along with an associated configuration file, see
https://linuxaudiofoundation.org/category/librespot/

Run spot_auth.py before running this player. spot_auth will give a URL to be pasted into a browser, the response an then be pased into spot_auth, this will set the token in the local cache which should be valid for 30 days. 




To register raspotify with the back end and get the token
1. set up a port forward from 5588 -> localhost:5588 on putty
2. stop the raspotify service
3. librespot --cache /home/pi/.cache/librespot -j
           Past the URL into the browser with spotify logged in
           (this should pull down a token)... 
   
4. sudo cp /home/pi/.cache/librespot/credentials.json /var/cache/raspotify/

You can start it manually to check it's working by going:- 
sudo /usr/bin/librespot --name "VradioPlayer" --cache /var/cache/raspotify --backend alsa --initial-volume 80 --verbose


When running as a service use the following file (/etc/systemd/system/vradio.service):- 


[Unit]
Description=VRadio Startup Script
After=network-online.target sound.target
Wants=network-online.target sound.target

[Service]
Type=simple
User=pi
Group=pi
ExecStart=/home/pi/vradio/start.sh
WorkingDirectory=/home/pi/vradio
Restart=always
RestartSec=5
PrivateTmp=false
Environment="XDG_RUNTIME_DIR=/run/user/1000"
Environment="PULSE_SERVER=unix:/run/user/1000/pulse/native"

[Install]
WantedBy=multi-user.target











