#!/bin/bash

# Define the project root directory
ROOT_DIR=$(dirname $(dirname $(realpath $0)))

echo "[Unit]
Description=Starts Flask server on 5002 to serve a tts service locally using coqui

[Service]
ExecStart=${ROOT_DIR}/scripts/wonko_start_server.sh
User=dusty
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/service_tts_server.service
sudo chmod +x ${ROOT_DIR}/scripts/wonko_start_server.sh

sudo systemctl enable service_tts_server

sudo systemctl start service_tts_server

