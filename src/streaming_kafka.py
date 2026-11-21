import argparse
import os
import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

TIPOS_SPARK = {
    "double": DoubleType(),
    "long": LongType(),
    "string": StringType(),
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Lê o tópico do Kafka com Spark.")
    parser.add_argument("--fonte", choices=["sintetico", "inmet"], default="sintetico")
    return parser.parse_args(argv)


def escolher_schema(fonte):
    if fonte == "inmet":
        from src.inmet_schema import COLUNAS, ORIGEM_INMET, TIPOS
        return COLUNAS, TIPOS, ORIGEM_INMET
    from src.synthetic_schema import COLUNAS, ORIGEM_SINTETICA, TIPOS
    return COLUNAS, TIPOS, ORIGEM_SINTETICA


def diverge(recebida, esperada):
    return recebida is None or recebida != esperada


def main():
    args = parse_args()
    colunas, tipos, esperada = escolher_schema(args.fonte)
    os.environ["PYSPARK_PYTHON"] = sys.executable
    esquema = StructType(
        [StructField(coluna, TIPOS_SPARK[tipos[coluna]]) for coluna in colunas]
    )
    spark = (
        SparkSession.builder
        .appName("LeituraKafkaMeteorologia")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    bruto = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", "earliest")
        .load()
    )
    registros = bruto.select(
        F.from_json(F.col("value").cast("string"), esquema).alias("registro")
    ).select("registro.*")
    consulta = (
        registros.writeStream
        .format("console")
        .option("truncate", "false")
        .outputMode("append")
        .start()
    )
    divergentes = (
        registros.filter(
            F.col(colunas[-1]).isNull() | (F.col(colunas[-1]) != esperada)
        )
        .writeStream
        .queryName("origem_divergente")
        .format("console")
        .option("truncate", "false")
        .outputMode("append")
        .start()
    )
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
