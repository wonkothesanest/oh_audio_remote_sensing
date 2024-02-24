import argparse
import io

import json
import os
import sys
from pathlib import Path
from threading import Lock
from typing import Union
from urllib.parse import parse_qs

from flask import Flask, render_template, render_template_string, request, send_file, make_response, abort
import os
import torch
import torchaudio
from TTS.utils.audio.numpy_transforms import save_wav
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts
import glob

base_dir = "/home/dusty/workspace/runs/gregorovich-book/run/training/GPT_XTTS_FT-January-23-2024_06+28PM-5dcc16d1"
#base_dir = "/tmp/xtts_ft/blackbeard/run/training/GPT_XTTS_FT-January-17-2024_04+44PM-5dcc16d1/"
voices = ["gregorovich", "blackbeard", "marvin"]
configs = {
            "gregorovich":{"ref_wavs": glob.glob("/home/dusty/workspace/runs/gregorovich-book/dataset/wavs/*.wav")},
            "marvin":{"ref_wavs": glob.glob("/home/dusty/workspace/runs/marvin/dataset/wavs/*.wav")},
            "blackbeard":{"ref_wavs": glob.glob("/home/dusty/workspace/runs/blackbeard/dataset/wavs/*.wav")}
        }

print("Loading model...")
config = XttsConfig()
config.load_json(f"{base_dir}/config.json")
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir=base_dir, use_deepspeed=False)
model.cuda()

print("Computing speaker latents...")
for v in voices:
    print(f"Creating conditioning latents for {v}")
    gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=configs[v]['ref_wavs'])
    configs[v]['gpt_cond_latent'] = gpt_cond_latent
    configs[v]['speaker_embedding'] = speaker_embedding


app = Flask(__name__)
from threading import Lock
lock = Lock()

@app.route("/api/tts", methods=["GET", "POST"])
def tts():
    print("processing request")
    with lock:
        text = request.headers.get("text") or request.values.get("text", "")
        speaker_idx = request.headers.get("speaker-id") or request.values.get("speaker_id", "")
        print(f"Speaker {speaker_idx} to speak: {text}")
        if(speaker_idx not in voices):
            print(speaker_idx)
            abort(404)

        #language_idx = request.headers.get("language-id") or request.values.get("language_id", "")
        #style_wav = request.headers.get("style-wav") or request.values.get("style_wav", "")
        #style_wav = style_wav_uri_to_dict(style_wav)

        #print(f" > Model input: {text}")
        #print(f" > Speaker Idx: {speaker_idx}")
        #print(f" > Language Idx: {language_idx}")
        out = model.inference(
            text,
            "en",
            configs[speaker_idx]['gpt_cond_latent'],
            configs[speaker_idx]['speaker_embedding'],
            temperature=0.7, # Add custom parameters here
        )
        out_stream = io.BytesIO()
        print("finished")
        torchaudio.save(out_stream, torch.tensor(out["wav"]).unsqueeze(0), 24000, format="wav")

    out_stream.seek(0)
    response = make_response(out_stream.read())
    response.headers.set('Content-Type', 'audio/wav')
    response.headers.set(
        'Content-Disposition', 'attachment', filename='output.wav')
    return response


app.run(debug=False, host="::", port=5005)
