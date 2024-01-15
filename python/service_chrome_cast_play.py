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

def write_audio_to_fifo(ch, method, properties, body):
    global pp
    try:
        tts_response = json.loads(body.decode('utf-8'))
        print(f"received wav {tts_response}")
        pp.play_next(tts_response["audio_url"], tts_response["sentance_index"], tts_response["session_id"])
    except:
        pp = ChromecastPlayer()
        pass

if __name__ == "__main__":
    print("starting up chrome player listener")
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='coqui_tts_response')
    channel.basic_consume(queue='coqui_tts_response', on_message_callback=write_audio_to_fifo, auto_ack=True)
    channel.start_consuming()
