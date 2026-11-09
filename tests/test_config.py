import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC


def test_kafka_bootstrap_servers():
    assert isinstance(KAFKA_BOOTSTRAP_SERVERS, str)
    assert KAFKA_BOOTSTRAP_SERVERS != ""


def test_kafka_topic():
    assert isinstance(KAFKA_TOPIC, str)
    assert KAFKA_TOPIC != ""
