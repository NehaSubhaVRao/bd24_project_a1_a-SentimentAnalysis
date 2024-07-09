import json
import os
from confluent_kafka import SerializingProducer, KafkaError


def read_json_file(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            yield json.loads(line)


def delivery_report(err, msg):
    if err is not None:
        print(f'Message delivery failed: {err}')
    else:
        print(f"Message delivered to {msg.topic} [{msg.partition()}]")


def main():
    topic = 'sender'
    producer = SerializingProducer({
        'bootstrap.servers': 'localhost:9092'
    })

    # Directory containing the JSON files
    directory = r"\Sentiment_Analysis\Federated_Sentiment_Analysis\Streaming_Data"

    # Initialize the chunk count
    chunk_count = 0

    # Loop through the files in the directory
    while True:
        # Construct the file name
        file_name = f"data_{chunk_count}.json"
        file_path = os.path.join(directory, file_name)

        # Check if the file exists
        if not os.path.exists(file_path):
            break

        # Read messages from the JSON file
        messages = read_json_file(file_path)

        for message in messages:
            try:
                producer.produce(topic,
                                 key=str(message.get('id')),  # Ensure the key is a string
                                 value=json.dumps(message),
                                 on_delivery=delivery_report)
                # Serve delivery reports and manage internal queue
                producer.poll(0)
                print(f"Sent: {message}")
            except BufferError as e:
                print(f"BufferError: {e}, waiting for free space in the queue")
                producer.flush()

        chunk_count += 1
        # #training with 2 chunks to train in less time(for demo)
        # if(chunk_count==2):
        #     break

    # Wait for all messages to be delivered
    producer.flush()


if __name__ == "__main__":
    main()