#!/bin/bash

source /home/dusty/workspace/py-envs/coqui/bin/activate

python /home/dusty/workspace/external-repos/TTS/TTS/server/server.py  --speakers_file_path '/home/dusty/workspace/runs/all_characters/YourTTS-EN-cast of characters-October-15-2023_08+37PM-0000000/speakers.pth' --model_path '/home/dusty/workspace/runs/all_characters/YourTTS-EN-cast of characters-October-15-2023_08+37PM-0000000/best_model.pth' --config_path '/home/dusty/workspace/runs/all_characters/YourTTS-EN-cast of characters-October-15-2023_08+37PM-0000000/config.json'
