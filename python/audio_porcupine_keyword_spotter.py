#!/usr/bin/env python3

import os
import json
import numpy as np
import pasimple
import threading
import paho.mqtt.client as mqtt
import time
import pvporcupine
import pulsectl
import sounddevice as sd
from datetime import datetime
import configparser

# MQTT broker and topic
mqtt_broker_host = 'master-blaster'
mqtt_topic = 'devices/gregorovich'

# Keywords for Picovoice
keywords = ['picovoice', 'bumblebee', 'porcupine', 'Black Beard', 'gregor', 'marvin']

# Must match keywords defined for model paths
#  Still up for debate but looks like they have to be in the same order as well?
model_paths = [
    '/usr/local/lib/python3.9/dist-packages/pvporcupine/resources/keyword_files/raspberry-pi/picovoice_raspberry-pi.ppn', 
    '/usr/local/lib/python3.9/dist-packages/pvporcupine/resources/keyword_files/raspberry-pi/bumblebee_raspberry-pi.ppn',
    '/usr/local/lib/python3.9/dist-packages/pvporcupine/resources/keyword_files/raspberry-pi/porcupine_raspberry-pi.ppn',
    '/home/pi/oh_audio_remote_sensing/voices/Black-Beard_en_raspberry-pi_v2_2_0.ppn',
    '/home/pi/oh_audio_remote_sensing/voices/gregor_en_raspberry-pi_v2_2_0.ppn',
    '/home/pi/oh_audio_remote_sensing/voices/marvin_en_raspberry-pi_v2_2_0.ppn'
    ]

config = configparser.ConfigParser()
config.read('/etc/secrets.ini')
secret_key = config['pico_voice'].get('secret_key')

if(len(secret_key) < 5):
    raise Exception("Could not get the pico_voice secret")

# These handles will be shared by all threads

# This variable will be shared by all threads
last_keyword_detection_time = 0

# Pulse audio shit
CHANNELS = 1
SAMPLE_RATE = 16000
PACKET_SIZE=1024


def main():
    list_sources()
    start_service()

def make_request(keyword, location):
    d = {"keyword": keyword, "triggering_mic": location, "timestamp": str(datetime.now().timestamp()), "event_time": str(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))}
    d = json.dumps(d)
    # Create an MQTT client
    client = mqtt.Client()

    # Connect to the MQTT broker
    client.connect(mqtt_broker_host)

    # Publish a message to an MQTT topic
    print(d)
    client.publish(mqtt_topic + "/keyword_spotter/keyword", d)
    client.publish(mqtt_topic + "/microphones/" + location, d)

    # Disconnect from the MQTT broker
    client.disconnect()

def process_data(data, handle, source_name):
    int_data = np.frombuffer(data, dtype=np.int16)
    kw = handle.process(int_data)
    if kw >= 0:
        #last_keyword_detection_time = time.time()
        make_request(keywords[kw], source_name)


def listen_to_source(source_name):
    while True:
        try:
            print("Listening to " + source_name, flush=True)
    
            normal_handle = pvporcupine.create(
                access_key=secret_key,
                keywords=keywords,
                keyword_paths=model_paths
            )
            # Create a new PulseAudio client
            with pasimple.PaSimple(pasimple.PA_STREAM_RECORD, pasimple.PA_SAMPLE_S16LE, CHANNELS, SAMPLE_RATE, device_name=source_name) as pa:
                while True:
                    data = pa.read(PACKET_SIZE)
                    # Now 'samples' is a NumPy array containing the audio data
                    handle = normal_handle
                    process_data(data, handle, source_name)
        except Exception as e:
            print(f"Error handling stream {source_name} with error: {e}", flush=True)
            time.sleep(60)
            pass


def start_service():
    # Replace these with your actual sink names
    sink_names = [ "mic_kitchen", "mic_office_esp32", "mic_bedroom", "mic_livingroom"]

    threads = []
    for sink_name in sink_names:
        thread = threading.Thread(target=listen_to_source, args=(sink_name,))
        thread.daemon = True  # Set the thread as a daemon thread
        thread.start()
        threads.append(thread)
    for t in threads:
        t.join()
    #listen_to_source("mic_kitchen")

def list_sources():
    with pulsectl.Pulse('source-list') as pulse:
        for src in pulse.source_list():
            print(f"Device name: {src.name}")
            print("-------------------------")

if __name__ == "__main__":
    main()

