# program3.py
import pika
import os

FIFO_PATH = "/tmp/audio_fifo"

# if not os.path.exists(FIFO_PATH):
#     os.mkfifo(FIFO_PATH)

def write_audio_to_fifo(ch, method, properties, body):
    # audio_data = body
    # with open(FIFO_PATH, 'wb') as fifo:
    #     fifo.write(audio_data)
    print(f"Audio Data has been processed. {body}")

if __name__ == "__main__":
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='tts_output')
    channel.basic_consume(queue='tts_output', on_message_callback=write_audio_to_fifo, auto_ack=True)
    channel.start_consuming()
