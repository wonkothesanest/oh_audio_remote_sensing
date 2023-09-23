# program3.py
import pika
import os
import json
import pulse_player

FIFO_PATH = "/tmp/audio_fifo"

response_map = {}
pp = pulse_player.PulsePlayer()

# if not os.path.exists(FIFO_PATH):
#     os.mkfifo(FIFO_PATH)

def write_audio_to_fifo(ch, method, properties, body):
    # audio_data = body
    # with open(FIFO_PATH, 'wb') as fifo:
    #     fifo.write(audio_data)
    tts_response = json.loads(body.decode('utf-8'))
    #print(f"Audio Data has been processed. {tts_response}")
    #print(f",{tts_response}")
    pp.play_next(tts_response["audio_url"], tts_response["sentance_index"], tts_response["session_id"])

if __name__ == "__main__":
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='tts_output')
    channel.basic_consume(queue='tts_output', on_message_callback=write_audio_to_fifo, auto_ack=True)
    
    channel.start_consuming()
