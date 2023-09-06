import pyaudio
import socket

# UDP server configuration
UDP_IP = ""  # Replace with the IP address of the machine sending the UDP data
UDP_PORT = 60555
PACKET_SIZE = 1024

# Audio configuration
SAMPLE_RATE = 44100 
CHANNELS = 1
FORMAT = pyaudio.paInt16

def main():
    p = pyaudio.PyAudio()

    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        output=True
    )

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind((UDP_IP, UDP_PORT))

    print("Listening for audio data from UDP...")

    try:
        while True:
            data, addr = udp_socket.recvfrom(PACKET_SIZE)
            if len(data) == PACKET_SIZE:
                stream.write(data)
    except KeyboardInterrupt:
        print("\nStopping the audio streaming.")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Finished script, goodbye")

if __name__ == "__main__":
    main()


