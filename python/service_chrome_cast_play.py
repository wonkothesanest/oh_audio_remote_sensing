# program3.py
import pika
import os
import json
import chromecast_player

FIFO_PATH = "/tmp/audio_fifo"

response_map = {}
pp = chromecast_player.ChromecastPlayer()

def write_audio_to_fifo(ch, method, properties, body):
    tts_response = json.loads(body.decode('utf-8'))
    pp.play_next(tts_response["audio_url"], tts_response["sentance_index"], tts_response["session_id"])

if __name__ == "__main__":
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='coqui_tts_response')
    channel.basic_consume(queue='coqui_tts_response', on_message_callback=write_audio_to_fifo, auto_ack=True)
    
    channel.start_consuming()
