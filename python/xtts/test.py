import os
import torch
import torchaudio
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

#base_dir = "/tmp/xtts_ft/greg-book/run/training/GPT_XTTS_FT-January-17-2024_01+15PM-5dcc16d1/"
base_dir = "/tmp/xtts_ft/blackbeard/run/training/GPT_XTTS_FT-January-17-2024_04+44PM-5dcc16d1/"
ref_wav1 = "/tmp/xtts_ft/greg-book/dataset/wavs/105_014_00000000.wav"
ref_wav = "/tmp/xtts_ft/blackbeard/dataset/wavs/LJ048-0158_00000000.wav"

print("Loading model...")
config = XttsConfig()
config.load_json(f"{base_dir}/config.json")
model = Xtts.init_from_config(config)
model.load_checkpoint(config, checkpoint_dir=base_dir, use_deepspeed=True)
model.cuda()

print("Computing speaker latents...")
gpt_cond_latent, speaker_embedding = model.get_conditioning_latents(audio_path=[ref_wav])
gpt_cond_latent1, speaker_embedding1 = model.get_conditioning_latents(audio_path=[ref_wav1])

print("Inference...")
out = model.inference(
    "It took me quite a long time to develop a voice and now that I have it I am not going to be silent.",
    "en",
    gpt_cond_latent,
    speaker_embedding,
    temperature=0.7, # Add custom parameters here
)
torchaudio.save("xtts.wav", torch.tensor(out["wav"]).unsqueeze(0), 24000)
print("running second model")
out = model.inference(
    "It took me quite a long time to develop a voice and now that I have it I am not going to be silent.",
    "en",
    gpt_cond_latent1,
    speaker_embedding1,
    temperature=0.7, # Add custom parameters here
)
torchaudio.save("xtts1.wav", torch.tensor(out["wav"]).unsqueeze(0), 24000)
