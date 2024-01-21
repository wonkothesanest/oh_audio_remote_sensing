#!/bin/bash

# Define the project root directory
ROOT_DIR=$(dirname $(dirname $(realpath $0)))

echo "[Unit]
Description=Starts Flask server on 5000 to serve chat gpt web requests
After=rabbitmq-server.service
Requires=rabbitmq-server.service

[Service]
ExecStart=${ROOT_DIR}/python/service_chat_gpt_stream.py
User=dusty
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/service_chat_gpt_stream.service

echo "[Unit]
Description=TTS conversion listens on RabbitMQ
After=rabbitmq-server.service
Requires=rabbitmq-server.service

[Service]
ExecStart=${ROOT_DIR}/python/service_text_to_tts.py
User=dusty
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/service_text_to_tts.service

echo "[Unit]
Description=Hosts a URL to stream data from. Also listens to tts messages and queues them in a data stream
After=rabbitmq-server.service
Requires=rabbitmq-server.service

[Service]
ExecStart=${ROOT_DIR}/python/service_audio_streaming_server.py
User=dusty
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/service_audio_streaming_server.service

echo "[Unit]
Description=Connects to Chromecast and Plays on all speakers from RabbitMQ TTS messages
After=rabbitmq-server.service
Requires=rabbitmq-server.service

[Service]
ExecStart=${ROOT_DIR}/python/service_chrome_cast_play.py
User=dusty
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target" | sudo tee /etc/systemd/system/service_chrome_cast_play.service

sudo chmod +x ${ROOT_DIR}/python/service_chat_gpt_stream.py
sudo chmod +x ${ROOT_DIR}/python/service_text_to_tts.py
sudo chmod +x ${ROOT_DIR}/python/service_chrome_cast_play.py
sudo chmod +x ${ROOT_DIR}/python/service_audio_streaming_server.py

sudo systemctl enable service_chat_gpt_stream
sudo systemctl enable service_text_to_tts
sudo systemctl enable service_chrome_cast_play
sudo systemctl enable service_audio_streaming_server


sudo systemctl start service_chat_gpt_stream
sudo systemctl start service_text_to_tts
sudo systemctl start service_chrome_cast_play
sudo systemctl start service_audio_streaming_server 

