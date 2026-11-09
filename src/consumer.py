import json

from kafka import KafkaConsumer

from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC


def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    for message in consumer:
        print(message.topic, message.partition, message.offset, message.value)


if __name__ == "__main__":
    main()
