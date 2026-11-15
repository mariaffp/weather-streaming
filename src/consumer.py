import json

from kafka import KafkaConsumer

from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC


def formatar_mensagem(topico, particao, offset, valor):
    campos = " ".join(f"{chave}={valor[chave]}" for chave in valor)
    return f"{topico} {particao} {offset} {campos}"


def main():
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        auto_offset_reset="earliest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    for message in consumer:
        print(formatar_mensagem(message.topic, message.partition, message.offset, message.value))


if __name__ == "__main__":
    main()
