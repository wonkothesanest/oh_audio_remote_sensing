# oh_audio_remote_sensing
Collection of home automation scripts to run for monitoring the home and reporting back to the mother ship.
Now with chat gpt and tts streaming!!

# Chat GPT deps.
pip install openai nltk pika
python -m nltk.downloader punkt


run the setup script from the main directory for it to install both services.


Don't forget to restart the services after you make a change.

ugh so frustrating trying to get system scrpts to start.  Need to make sure they are the right users and the services are booting in the right order.
I think we finally have it all sorted out and defined in the setup script.

For loading xtts server to create models, make sure the lib cuda installed in the python directories is exported to LD_LIBRARY_PATH
LD_LIBRARY_PATH=/home/dusty/workspace/py-envs/coqui/lib/python3.11/site-packages/nvidia/cudnn/lib/
export LD_LIBRARY_PATH

