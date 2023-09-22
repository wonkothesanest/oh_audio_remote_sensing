# program1.py
import argparse
import openai
import nltk
import pika

# Initialize OpenAI API key
openai.api_key = ''

def extract_full_sentence(overall_result):
    sentences = nltk.sent_tokenize(overall_result)
    if sentences and len(sentences) > 1:
        return sentences[0]
    return None

def main():
    # Arguments
    parser = argparse.ArgumentParser("Accept command-line input and call ChatGPT")
    parser.add_argument("--text", required=True)
    parser.add_argument("--assistant_prompt", default="You are a helpful assistant.")
    parser.add_argument("--model", default="gpt-3.5-turbo")
    parser.add_argument("--max_tokens", default=250)
    args = parser.parse_args()

    overall_result = ""

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

    for message in response:
        try:
            chunk = message['choices'][0]['delta']["content"]
        except:
            chunk = ""
            pass

        overall_result += chunk

    # Send the result to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='chatgpt_output')
    channel.basic_publish(exchange='', routing_key='chatgpt_output', body=overall_result)
    connection.close()

if __name__ == "__main__":
    main()
