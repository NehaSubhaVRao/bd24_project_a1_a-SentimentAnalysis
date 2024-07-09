from confluent_kafka import Consumer, KafkaException
import json
import time
from model import *  # Assuming model.py is in the same directory

FILE_PATH = r'\Sentiment_Analysis\Federated_Sentiment_Analysis\Streaming_Data'
def create_consumer(broker, group_id, topics):
    consumer_config = {
        'bootstrap.servers': broker,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(consumer_config)
    consumer.subscribe(topics)
    try:
        with open(FILE_PATH, 'a') as file:
            while True:
                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        raise KafkaException(msg.error())
                record = msg.value().decode('utf-8')
                file.write(record + '\n')
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

    return consumer

if __name__ == "__main__":
    broker = 'localhost:9092'
    group_id = 'your_group'
    topics = ['processed-sender']
    batch_size = 10

    try:
        consumer = create_consumer(broker, group_id, topics)
    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()