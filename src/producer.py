import argparse
import json
import time

from kafka import KafkaProducer

from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from src.synthetic_simulator import gerar_registro


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Envia registros sintéticos ao Kafka.")
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--intervalo", type=float, default=1.0)
    parser.add_argument("--aceleracao", type=float, default=1.0)
    args = parser.parse_args(argv)
    if args.aceleracao <= 0:
        parser.error("--aceleracao deve ser maior que zero")
    return args


def main():
    args = parse_args()
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    for i in range(args.n):
        producer.send(KAFKA_TOPIC, gerar_registro(i))
        if i < args.n - 1:
            time.sleep(args.intervalo / args.aceleracao)
    producer.flush()


if __name__ == "__main__":
    main()