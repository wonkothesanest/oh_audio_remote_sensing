# program2.py
import pika
import requests
import configparser

config = configparser.ConfigParser()
config.read('/etc/secrets.ini')
secret_key = config['coqui'].get('secret_key')

coqui_key = secret_key
voice_id = None

def call_tts(ch, method, properties, body):
    sentence = body.decode('utf-8')
    print(f"Processing sentence: {sentence}")
    try:
        request_obj = {"voice_id": voice_id, "text": sentence}
        headers = {
            "accept": "audio/wav",
            "content-type": "application/json",
            "authorization": f"Bearer {coqui_key}"
        }
        response = requests.post("https://app.coqui.ai/api/v2/samples", json=request_obj, headers=headers)
        # Handle response here and send to another RabbitMQ queue for the next program
        connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='tts_output')
        channel.basic_publish(exchange='', routing_key='tts_output', body=response.content)
        connection.close()
    except requests.RequestException as e:
        print(f"Error calling TTS service: {e}")

if __name__ == "__main__":
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='chatgpt_output')
    channel.basic_consume(queue='chatgpt_output', on_message_callback=call_tts, auto_ack=True)
    channel.start_consuming()
