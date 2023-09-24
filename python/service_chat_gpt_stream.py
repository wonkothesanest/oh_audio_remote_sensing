#!/usr/bin/env python3

from flask import Flask, request, jsonify
import uuid
import openai
import nltk
import pika
import configparser
import json

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('/etc/secrets.ini')
secret_key = config['openai'].get('secret_key')

# Initialize OpenAI API key
openai.api_key = secret_key

cache = {}
cache_semaphore = threading.Semaphore()

def extract_full_sentence(overall_result):
    # Use NLTK to tokenize the text into sentences
    sentences = nltk.sent_tokenize(overall_result)
    if sentences and len(sentences) > 1:
        return sentences[0]
    return None

def __add_to_cache(user: str, voice_id: str, value: str)->None:
    cache_semaphore.acquire()
    cache[voice_id] = cache[voice_id] if cache[voice_id] else []
    cache[voice_id].append(text)
    cache_semaphore.release()


@app.route('/chatgpt/stream-to-audio', methods=['POST'])
def chatgpt():
    data = request.json
    text = data.get('text')
    assistant_prompt = data.get('assistant_prompt', "You are a helpful assistant.")
    model = data.get('model', "gpt-4")
    max_tokens = data.get('max_tokens', 250)
    voice_id = data.get('voice_id', '774437df-2959-4a01-8a44-a93097f8e8d5')
    __add_to_cache("user", voice_id, text)

    overall_result = ""
    full_result = ""
    sentence_order = 0

    # Send the result to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='chatgpt_stream')
    channel.queue_declare(queue='chatgpt_response')

    # Connect to ChatGPT API in streaming mode
    additional_prompt = f"\n keep your response to less than {max_tokens} tokens"
    messages = [
            {"role": "system", "content": assistant_prompt + additional_prompt},
            {"role": "user", "content": text}
        ]
    print(messages)
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        max_tokens=max_tokens,
        stream=True
    )
    print("processed response")

    session_id = str(uuid.uuid4())

    for message in response:
        try:
            chunk = message['choices'][0]['delta']["content"]
        except:
            chunk = ""
            pass

        overall_result += chunk
        full_result += chunk

        sentence = extract_full_sentence(overall_result)
        while sentence:
            overall_result = overall_result[len(sentence):]
            data = {"voice_id": voice_id, "text": sentence, "sentance_index": sentence_order, "session_id":session_id}
            channel.basic_publish(exchange='', routing_key='chatgpt_stream', body=json.dumps(data))
            sentence_order += 1
            sentence = extract_full_sentence(overall_result)
    if(overall_result != None and overall_result != ""):
        data = {"voice_id": voice_id, "text": overall_result, "sentance_index": sentence_order, "session_id":session_id}
        channel.basic_publish(exchange='', routing_key='chatgpt_stream', body=json.dumps(data))
        sentence_order += 1

    channel.basic_publish(exchange='', routing_key='chatgpt_response', body=full_result)
    __add_to_cache("assistant", voice_id, full_result)

    connection.close()

    return jsonify({"message": "Processed", "result": full_result})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
