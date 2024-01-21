#!/usr/bin/env python3

import datetime
from flask import Flask, Response, request
import time
import io
import pika
import requests
import wave
import threading
import json


app = Flask(__name__)
MAXIMUM_CONNECTION_MINUTES = 5
QUEUE_NAME = 'coqui_tts_response'

class StreamingServer(object):
    def __init__(self) -> None:
        self.semaphore = threading.Semaphore()
        self.semaphore.acquire()
        self.cache = dict()
        self.semaphore.release()


    def generate(self, session_id: str):
        is_first_frame = True
        is_last_frame = False
        current_index = 0
        # Adding a timer just in case we get errant connections, we want to close them.
        start_time = datetime.datetime.now()
        while True:
            cache_key = (session_id, current_index)
            self.semaphore.acquire()
            print(f"these cache key {cache_key} in {self.cache.keys()}", flush=True)
            self.semaphore.release()
            if(is_last_frame):
            #    for k in self.cache.keys():
            #        if(k[0] == session_id):
            #            del self.cache[k]
                return

            if cache_key in self.cache:
                # Stream the current audio part
                self.semaphore.acquire()
                if(is_first_frame):
                    yield self.cache[cache_key]["data"]
                else:
                    buffer = io.BytesIO()
                    buffer.write(self.cache[cache_key]["data"])
                    buffer.seek(0)
                    with wave.open(buffer, 'rb') as wave_file:
                        yield wave_file.readframes(wave_file.getnframes())
                time.sleep(2)
                if("is_last" in self.cache[cache_key].keys() and self.cache[cache_key]["is_last"]):
                    is_last_frame = True
                #del self.cache[cache_key]
                self.semaphore.release()

                if(datetime.datetime.now() - start_time >= datetime.timedelta(minutes=MAXIMUM_CONNECTION_MINUTES)):
                    is_last_frame = True
                current_index += 1
            else:
                # Return silence for 1 second and check again
                yield create_silence(first=is_first_frame)
                time.sleep(1)
            is_first_frame = False


@app.route('/api/stream')
def stream_audio():
    session_id = request.args.get('session_id')
    print(f"we have a consumer of the stream {session_id}", flush=True)
    #response = Response(stream.generate(session_id=session_id), mimetype="audio/wav")
    response = Response(stream.generate(session_id=session_id), mimetype="audio/wav")
    response.headers['Content-Type'] = 'audio/wav'
    response.headers['Content-Disposition'] = 'attachment; filename=sound.wav'
    
    return response

def create_silence(duration=.5, sample_rate=24000, channels=1, first=False):
    try:
        # Number of frames = sample rate * duration
        n_frames = int(sample_rate * duration)

        # Create a buffer with a WAV file
        buffer = io.BytesIO()
        silence = bytearray(n_frames * channels * 2)  # 2 bytes per sample for 16-bit audio
        if(first):
            with wave.open(buffer, 'wb') as wave_file:
                wave_file.setnchannels(channels)
                wave_file.setsampwidth(2)  # sample width in bytes, 2 for 16-bit audio
                wave_file.setframerate(sample_rate)
                
                # Add silence (zero-valued bytes)
                wave_file.writeframes(silence)
        else:
            buffer.write(silence)
        
        # Get the content of the buffer
        buffer.seek(0)
        return buffer.read()
    finally:
        buffer.close()




class ThreadedConsumer(threading.Thread):
    def __init__(self, streamer:StreamingServer):
        threading.Thread.__init__(self)
        print("initiing thread", flush=True)
        # Set up a connection to RabbitMQ
        credentials=pika.PlainCredentials("dusty", "Ninja")
        parameters = pika.ConnectionParameters('192.168.0.42', 5672, '/', credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.stream = streamer
        self.channel.queue_declare(queue=QUEUE_NAME)
        self.channel.basic_consume(queue=QUEUE_NAME, on_message_callback=self.callback, auto_ack=True)

        # Declare the queue


    def callback(self, ch, method, properties, body):
        # Decode the message
        try:
            message = json.loads(body)
    
            print(body, flush=True)
            # Extract needed data
            audio_url = message['audio_url']
            session_id = message['session_id']
            sentence_index = message['sentance_index']
            is_last = False
            if("is_last" in message.keys()):
                is_last = message['is_last']
    
            # Download the audio data
            response = requests.get(audio_url)
            audio_data = response.content
    
            # Store in cache
            self.stream.semaphore.acquire()
            self.stream.cache[(session_id, sentence_index)] = { "data": audio_data, "is_last": is_last}
            print(f"Stored audio for session {session_id}, sentence {sentence_index} new keys {self.stream.cache.keys()} thread {threading.current_thread()}", flush=True)
            self.stream.semaphore.release()
        except:
            print("Something went wrong")
            pass
    


    def run(self):
        try:
            print ('starting thread to consume from rabbitmq...')
            self.channel.start_consuming()
        finally:
            self.connection.close()

# {"audio_url": "http://wonko:5005/api/tts?text=going%20on%20a%20walk&speaker_id=gregorovich", "session_id": "1", "sentence_index": 0}
stream = StreamingServer()

if __name__ == "__main__":
    # Set up the consumer
    tc = ThreadedConsumer(stream)
    tc.start()

    app.run(debug=False, host="0.0.0.0", port=5099)

