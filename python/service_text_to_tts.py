#!/usr/bin/env python3

# program2.py
import threading
import pika
import requests
import configparser
import json

RABBIT_URL = 'amqp://nuvihermoth:D0nn1eDarkoisRabbitFrank@rabbit-cluster-external-stage-1443209739.us-east-1.elb.amazonaws.com'
# ROUTING_KEY = 'throttle.compact_social_activity.throttled'
QUEUE_IN_NAME = 'chatgpt_stream'
QUEUE_OUT_NAME = 'coqui_tts_response'
# EXCHANGE = 'events'
THREADS = 5

config = configparser.ConfigParser()
config.read('/etc/secrets.ini')
secret_key = config['coqui'].get('secret_key')

coqui_key = secret_key
class ThreadedConsumer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=QUEUE_IN_NAME)
        threading.Thread(target=self.channel.basic_consume(queue=QUEUE_IN_NAME, on_message_callback=self.call_tts, auto_ack=True))

    def call_tts(self, ch, method, properties, body):
        data_obj = json.loads(body)
        sentence = data_obj["text"]
        voice_id = data_obj["voice_id"]
        #session_id = o["session_id"]
        #order = o["sentance_index"]

        print(f"Processing sentence: {sentence}")
        try:
            request_obj = {"voice_id": voice_id, "text": sentence}
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "authorization": f"Bearer {coqui_key}"
            }
            response = requests.post("https://app.coqui.ai/api/v2/samples", json=request_obj, headers=headers)
            # Handle response here and send to another RabbitMQ queue for the next program
            connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_OUT_NAME)
            d = json.loads(response.content)
            # Update will replace the values in the passed in object
            data_obj.update(d)
            channel.basic_publish(exchange='', routing_key=QUEUE_OUT_NAME, body=json.dumps(data_obj))
        except requests.RequestException as e:
            print(f"Error calling TTS service: {e}")
        finally:
            connection.close()

    def run(self):
        print ('starting thread to consume from rabbitmq...')
        self.channel.start_consuming()
    
if __name__ == "__main__":
    for i in range(THREADS):
        # nifty trick as pika is not naturally thread safe.
        print ('launch thread', i)
        td = ThreadedConsumer()
        td.start()
