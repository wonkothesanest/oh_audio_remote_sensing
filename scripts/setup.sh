#!/bin/bash

# Define the project root directory
ROOT_DIR=$(dirname $(dirname $(realpath $0)))

# Create a systemd service file for audio_porcupine_keyword_spotter.py
echo "[Unit]
Description=Audio Porcupine Keyword Spotter
After=pulseaudio.service

[Service]
ExecStart=${ROOT_DIR}/python/audio_porcupine_keyword_spotter.py
User=pulse

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/audio_porcupine_keyword_spotter.service

# Create a systemd service file for audio_to_pulse_audio.py
echo "[Unit]
Description=Audio to Pulse Audio
After=pulseaudio.service

[Service]
ExecStart=${ROOT_DIR}/python/audio_to_pulse_audio.py
User=pulse

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/audio_to_pulse_audio.service

echo "[Unit]
Description=PulseAudio system server

[Service]
Type=simple
ExecStart=/usr/bin/pulseaudio --system --disallow-exit --disable-shm --exit-idle-time=-1

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/pulseaudio.service

# Make the scripts executable
sudo chmod +x ${ROOT_DIR}/python/audio_porcupine_keyword_spotter.py
sudo chmod +x ${ROOT_DIR}/python/audio_to_pulse_audio.py

# Enable the services to start on boot
sudo systemctl enable pulseaudio
sudo systemctl enable audio_porcupine_keyword_spotter
sudo systemctl enable audio_to_pulse_audio


# Start the services immediately
sudo systemctl start pulseaudio
sudo systemctl start audio_porcupine_keyword_spotter
sudo systemctl start audio_to_pulse_audio

