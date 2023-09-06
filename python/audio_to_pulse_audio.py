#!/usr/bin/env python3

import pulsectl
import socket
import os
import threading

print("starting Script") 
# UDP server configuration
UDP_IP = ""  # Replace with the IP address of the machine sending the UDP data

# Audio configuration
SAMPLE_RATE = 44100
CHANNELS = 1
FORMAT = 's16le'  # PulseAudio format for 16-bit signed little-endian data
PACKET_SIZE = 512

def start_udp_audio_stream(port, stream_name):
    with pulsectl.Pulse('UDP-Audio-Stream') as pulse:
        # Prereq, fifo file must be setup and working to be writen to, Pulse audio in python is giving me a fucking hell of a time.
        # File name for the FIFO file
        fifo_file = f'/tmp/{stream_name}_fifo'
    
        # Create the FIFO file if it doesn't already exist
        if not os.path.exists(fifo_file):
            os.mkfifo(fifo_file)
    
        # Load the pipe-source module to create a new source
        # pulse.module_load('module-null-sink', f'sink_name=udp_audio_sink sink_properties=device.description="{stream_name}"')
        #aggs = "source_name=mystream file=/tmp/mystream_fifo format=s16le rate=44100 channels=1"
        #aggs =  str(f"source_name=" + stream_name + " file=" + fifo_file+ " format=" + FORMAT + " rate=" + str(SAMPLE_RATE) + " channels=" + str(CHANNELS) + "")
        #print(aggs)
        #pulse.module_load('module-pipe-source', f'source_name={stream_name} file={fifo_file} format={FORMAT} rate={SAMPLE_RATE} channels={CHANNELS}')
        #pulse.module_load('module-pipe-source', aggs)
        #pulse.module_load('module-pipe-source', aggs)
        #pulse.module_load('module-pipe-source', str(f'source_name={stream_name} file={fifo_file} format=s16le rate=44100 channels=1'))
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((UDP_IP, port))
    
        print(f"Listening for audio data from UDP on port {port}...")
    
        # Open the FIFO file for writing
        with open(fifo_file, 'wb') as fifo:
            while True:
                try:
                    data, addr = udp_socket.recvfrom(PACKET_SIZE)
                    if len(data) == PACKET_SIZE:
                        # Write the data to the FIFO file
                        fifo.write(data)
                except Exception as e:
                    print(f"An error occurred: {e}")
                    print("Continuing with the audio streaming...")
    
        # Unload the pipe-source module when we're done
        # pulse.module_unload('module-pipe-source')
        print(f"Finished audio streaming on port {port}, goodbye")
    
if __name__ == "__main__":
    # Start multiple audio streams by calling the function with different ports and stream names
    threads = []
    threads.append(threading.Thread(target=start_udp_audio_stream, args=(60555, "mic_office_esp32")))
    #start_udp_audio_stream(60555, "mic_office_esp32")
    threads.append(threading.Thread(target=start_udp_audio_stream, args=(60556, "mic_kitchen")))

    for thread in threads:
        thread.daemon = True
        thread.start()

    for thread in threads:
        thread.join()

