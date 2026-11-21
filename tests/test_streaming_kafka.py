import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import SparkSession

from src import inmet_schema, synthetic_schema
from src.streaming_kafka import diverge, escolher_schema, parse_args


def test_fonte_default():
    assert parse_args([]).fonte == "sintetico"


def test_fonte_inmet():
    assert parse_args(["--fonte", "inmet"]).fonte == "inmet"


def test_escolher_schema_sintetico():
    colunas, tipos, esperada = escolher_schema("sintetico")
    assert colunas == synthetic_schema.COLUNAS
    assert tipos == synthetic_schema.TIPOS
    assert esperada == synthetic_schema.ORIGEM_SINTETICA


def test_escolher_schema_inmet():
    colunas, tipos, esperada = escolher_schema("inmet")
    assert colunas == inmet_schema.COLUNAS
    assert tipos == inmet_schema.TIPOS
    assert esperada == inmet_schema.ORIGEM_INMET


def test_origem_e_ultima_coluna():
    assert synthetic_schema.COLUNAS[-1] == "origem", (
        "a coluna de origem não é a última (sintetico)"
    )
    assert inmet_schema.COLUNAS[-1] == "origem", (
        "a coluna de origem não é a última (inmet)"
    )


def test_diverge():
    assert diverge("sintetico", "sintetico") is False
    assert diverge("inmet", "sintetico") is True
    assert diverge(None, "sintetico") is True


def test_import_nao_inicia_spark():
    assert SparkSession.getActiveSession() is None
