#!/usr/bin/env python3

import datetime
import os
from flask import Flask, Response, request
import time
import io
import pika
import requests
import wave
import threading
import json
from pydub import AudioSegment
import pydub
import os
import io
from pydub import AudioSegment
from typing import Dict, Tuple
import http.server
import socketserver
import threading
import time


app = Flask(__name__)
MAXIMUM_CONNECTION_MINUTES = 5
TTS_READY_QUEUE_NAME = 'coqui_tts_response'
AUDIO_DESIRED_QUEUE = 'audio_stream_wanted'
AUDIO_READY_QUEUE = 'audio_stream'
AUDIO_BASE_DIR = "/home/orangepi5b/audio"
PORT = 2525
HOST_NAME = f"http://orangepi5b:{PORT}"
Handler = http.server.SimpleHTTPRequestHandler

known_sessions_lock = threading.Lock()
known_sessions = {}

class AudioStreamSession(object):
    def __init__(self, session_id: str) -> None:
        self._cache = {}  # Cache to store audio data segments
        self.session_id = session_id
        self.is_done = False
        self._current_file_index = 0
        self._current_session_index = 0
        self._last_index = -1
        self._stored_files = []

    def set_in_cache(self, session_index: int, data: bytes, is_last: bool = False):
        # Store the audio data in the cache with its session index
        self._cache[session_index] = data

        # If this is the last segment, set the last_index
        if is_last:
            self._last_index = session_index


    def write_to_file(self):
        with self.audio_lock:
            # Check for the next contiguous segment
            if self._current_session_index not in self._cache:
                return None  # Stop if there's a gap

            # Initialize an empty AudioSegment for combining segments
            combined_audio = AudioSegment.empty()

            # Find the end of the contiguous sequence
            end_index = self._current_session_index
            while end_index in self._cache:
                end_index += 1
            # Combine segments in the contiguous sequence
            for index in range(self._current_session_index, end_index):
                combined_audio += AudioSegment.from_file(io.BytesIO(self._cache[index]), format='wav')
                del self._cache[index]  # Remove segment from cache after adding

            # Write the combined audio to a file
            base_dir = AUDIO_BASE_DIR
            os.makedirs(base_dir, exist_ok=True)
            file_name = f"{self.session_id}-{self._current_file_index}.wav"
            file_path = os.path.join(base_dir, file_name)
            combined_audio.export(file_path, format="wav")
            self._stored_files.append(file_name)
            self._current_file_index += 1
            # Update the current_session_index
            self._current_session_index = end_index
            
        if(self._current_session_index == self._last_index):
            self.is_done = True
        return file_name


class ThreadedConsumer(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        print("initiing thread", flush=True)
        # Set up a connection to RabbitMQ
        credentials=pika.PlainCredentials("dusty", "Ninja")
        parameters = pika.ConnectionParameters('192.168.0.42', 5672, '/', credentials)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.audio_lock = threading.Lock()
        self.channel.queue_declare(queue=TTS_READY_QUEUE_NAME)
        self.channel.basic_consume(queue=TTS_READY_QUEUE_NAME, on_message_callback=self.tts_audio_ready_callback, auto_ack=True)
        self.channel.queue_declare(queue=AUDIO_DESIRED_QUEUE)
        self.channel.basic_consume(queue=AUDIO_DESIRED_QUEUE, on_message_callback=self.audio_desired_callback, auto_ack=True)

        # Declare the queue


    def tts_audio_ready_callback(self, ch, method, properties, body):
        global known_sessions
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

            if(session_id not in known_sessions.keys()):
                with known_sessions_lock:
                    a = AudioStreamSession(session_id)
                    known_sessions[session_id] = a
            known_sessions[session_id].set_in_cache(sentence_index, data=audio_data, is_last=is_last)

            if(sentence_index == 0):
                self._write_and_publish(known_sessions[session_id], message)
        except Exception as e:
            print(f"Something went wrong with recieving audio chunk {e}")
            pass
    

    def audio_desired_callback(self, ch, method, properties, body):
        # when we want an audio bit, we take what we have and write it to a file
        # Then we emit an audio ready message with its location (served by http.server)
        message = json.loads(body)

        print(body, flush=True)
        # Extract needed data
        session_id = message['session_id']
        if(session_id not in known_sessions.keys()):
            return
        self._write_and_publish(known_sessions[session_id], message)
        
    def _write_and_publish(self, session: AudioStreamSession, message: json):
        file_name = session.write_to_file()
        message["filename"] = file_name
        message["audio_url"] = f"{HOST_NAME}/{file_name}"
        self.channel.basic_publish('', AUDIO_READY_QUEUE, json.dumps(message))



    def run(self):
        try:
            print ('starting thread to consume from rabbitmq...')
            self.channel.start_consuming()
        finally:
            self.connection.close()

# {"audio_url": "http://wonko:5005/api/tts?text=going%20on%20a%20walk&speaker_id=gregorovich", "session_id": "1", "sentance_index": 0}
def run_server(directory):
    while True:
        try:
            os.chdir(directory)  # Change the working directory to the specified directory
            with socketserver.TCPServer(("", PORT), Handler) as httpd:
                print(f"HTTP server is serving at port {PORT} in directory {directory}")
                httpd.serve_forever()
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            time.sleep(5*60)
            pass


def start_server(directory):
    server_thread = threading.Thread(target=run_server, args=(directory,))
    server_thread.daemon = True
    server_thread.start()
    return server_thread

if __name__ == "__main__":
    # Set up the consumer
    tc = ThreadedConsumer()
    tc.start()
    start_server(AUDIO_BASE_DIR)
    tc.join()

