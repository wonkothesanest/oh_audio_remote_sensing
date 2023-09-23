# program1.py
import argparse
import uuid
import openai
import nltk
import pika
import configparser
import json

config = configparser.ConfigParser()
config.read('/etc/secrets.ini')
secret_key = config['openai'].get('secret_key')

# Initialize OpenAI API key
openai.api_key = secret_key

def extract_full_sentence(overall_result):
    # Use NLTK to tokenize the text into sentences
    sentences = nltk.sent_tokenize(overall_result)
    if sentences and len(sentences) > 1:
        return sentences[0]
    return None

def main():
    global voice_id
    # Arguments
    parser = argparse.ArgumentParser("Accept command-line input and call ChatGPT")
    parser.add_argument("--text", required=True)
    parser.add_argument("--assistant_prompt", default="You are a helpful assistant.")
    parser.add_argument("--model", default="gpt-3.5-turbo")
    parser.add_argument("--max_tokens", default=250)
    parser.add_argument("--voice", default=None)
    args = parser.parse_args()

    voice_id = args.voice_id
    overall_result = ""
    full_result = ""
    sentence_order = 0

    # Send the result to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='chatgpt_stream')
    channel.queue_declare(queue='chatgpt_response')

    # Connect to ChatGPT API in streaming mode
    response = openai.ChatCompletion.create(
        model=args.model,
        messages=[
            {"role": "system", "content": args.assistant_prompt},
            {"role": "user", "content": args.text}
        ],
        max_tokens=args.max_tokens,
        stream=True
    )

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
            channel.basic_publish(exchange='', routing_key='chatgpt_stream', body={"voice_id": voice_id, "text": sentence, "sentance_index": sentence_order, "session_id":session_id})
            sentence_order += 1
            sentence = extract_full_sentence(overall_result)
    if(overall_result != None and overall_result != ""):
        channel.basic_publish(exchange='', routing_key='chatgpt_stream', body=json.dumps({"voice_id": voice_id, "text": sentence, "sentance_index": sentence_order, "session_id":session_id}))
        sentence_order += 1

    print(f"Fully processed this text: {full_result}")
    
    channel.basic_publish(exchange='', routing_key='chatgpt_response', body=full_result)

    connection.close()

if __name__ == "__main__":
    main()
