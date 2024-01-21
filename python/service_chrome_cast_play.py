#!/usr/bin/env python3
# program3.py
import pika
import os
import json
import sys

import pychromecast
from modules.chromecast_player import ChromecastPlayer



def media_status_listener(media_status):
    print(f"Media Status: {media_status}")
    if(not pp.cast.media_controller.player_is_playing() and pp.current_session_id is not None):
        channel.basic_publish('', AUDIO_DESIRED_QUEUE, json.dumps({"session_id": pp.current_session_id}))


pp = ChromecastPlayer(media_status_listener)

AUDIO_STREAM_QUEUE = 'audio_stream'
AUDIO_DESIRED_QUEUE = 'audio_stream_wanted'

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

def queue_up_audio(ch, method, properties, body):
    global pp
    try:
        tts_response = json.loads(body.decode('utf-8'))
        print(f"received wav {tts_response}", flush=True)
        pp.play_next(tts_response["audio_url"], tts_response["session_id"])
    except:
        pp = ChromecastPlayer(media_status_listener)
        pp.play_next(tts_response["audio_url"], tts_response["session_id"])
        pass
def request_more_audio(session_id:str):
    msg = {}
    msg['session_id'] = session_id
    channel.basic_publish('', AUDIO_DESIRED_QUEUE, json.dumps(msg))


if __name__ == "__main__":
    print("starting up chrome player listener")
    channel.queue_declare(queue=AUDIO_STREAM_QUEUE)
    channel.basic_consume(queue=AUDIO_STREAM_QUEUE, on_message_callback=queue_up_audio, auto_ack=True)
    channel.queue_declare(queue=AUDIO_DESIRED_QUEUE)
    channel.start_consuming()
