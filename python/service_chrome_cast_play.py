#!/usr/bin/env python3
# program3.py
import pika
import os
import json
import sys
from modules.chromecast_player import ChromecastPlayer
pp = ChromecastPlayer()

response_map = {}
pp = ChromecastPlayer()

queue_name = 'audio_stream'

def queue_up_audio(ch, method, properties, body):
    global pp
    try:
        tts_response = json.loads(body.decode('utf-8'))
        print(f"received wav {tts_response}", flush=True)
        pp.play_next(tts_response["audio_url"], tts_response["sentance_index"], tts_response["session_id"])
    except:
        pp = ChromecastPlayer()
        pass

if __name__ == "__main__":
    print("trying to call function directly")
    queue_up_audio(None, None, None, '{"session_id": "3ba87a5a-e90e-40be-8c0a-7e49a08235be", "audio_url": "http://192.168.0.42:5099/api/stream?session_id=720b2317-34e5-413c-8034-4ead6bc8463a", "sentance_index": 0}')
    print("starting up chrome player listener")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    #channel.basic_consume(queue=queue_name, on_message_callback=queue_up_audio, auto_ack=True)
    #channel.start_consuming()
