import argparse
import os
import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructField, StructType

from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from src.streaming_kafka import TIPOS_SPARK, escolher_schema
from src.validacao import (
    AGRUPAR_POR,
    AGREGACOES,
    FAIXAS,
    coluna_origem,
    coluna_timestamp,
)

AGREGADORES = {
    "media": F.avg,
    "soma": F.sum,
    "maximo": F.max,
}

SAIDAS = {
    "validos": "data/processed/validos",
    "invalidos": "data/processed/invalidos",
    "agregados": "data/processed/agregados",
}

CHECKPOINTS = {
    "validos": "data/checkpoints/processado_validos",
    "invalidos": "data/checkpoints/processado_invalidos",
    "agregados": "data/checkpoints/processado_agregados",
}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Processa o tópico do Kafka com Spark.")
    parser.add_argument("--fonte", choices=["sintetico", "inmet"], default="sintetico")
    return parser.parse_args(argv)


def main():
    args = parse_args()
    colunas, tipos, esperada = escolher_schema(args.fonte)
    ts = coluna_timestamp(colunas, tipos)
    origem = coluna_origem(colunas)
    os.environ["PYSPARK_PYTHON"] = sys.executable
    esquema = StructType(
        [StructField(coluna, TIPOS_SPARK[tipos[coluna]]) for coluna in colunas]
    )
    spark = (
        SparkSession.builder
        .appName("LeituraKafkaProcessado")
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
    parsed = bruto.select(
        F.from_json(F.col("value").cast("string"), esquema).alias("registro")
    )
    base = parsed.select(
        "registro.*", F.col("registro").isNull().alias("registro_nulo")
    )
    com_ts = base.withColumn(ts, F.to_timestamp(F.col(ts)))
    mal = (
        F.col("registro_nulo")
        | F.col(ts).isNull()
        | F.col(origem).isNull()
        | (F.col(origem) != esperada)
    )
    invalido = F.lit(False)
    for coluna in colunas:
        if tipos[coluna] != "double":
            continue
        minimo, maximo = FAIXAS[coluna]
        invalido = invalido | (
            F.col(coluna).isNotNull()
            & ((F.col(coluna) < minimo) | (F.col(coluna) > maximo))
        )
    com_cat = com_ts.withColumn(
        "categoria",
        F.when(mal, "malformado").when(invalido, "invalido").otherwise("valido"),
    )
    validos = com_cat.filter(F.col("categoria") == "valido").drop("registro_nulo")
    invalidos = com_cat.filter(F.col("categoria") != "valido").drop("registro_nulo")
    chave = AGRUPAR_POR[args.fonte]
    agregacoes = [F.count("*").alias("total_registros")]
    nomes = ["total_registros"]
    for coluna in colunas:
        if tipos[coluna] != "double":
            continue
        nome = coluna + "_" + AGREGACOES[coluna]
        agregacoes.append(AGREGADORES[AGREGACOES[coluna]](F.col(coluna)).alias(nome))
        agregacoes.append((F.count("*") - F.count(coluna)).alias("nulos_" + coluna))
        nomes.extend([nome, "nulos_" + coluna])
    agregados = (
        validos
        .withWatermark(ts, "10 minutes")
        .groupBy(F.col(chave), F.window(F.col(ts), "1 day"))
        .agg(*agregacoes)
        .select(
            F.col(chave),
            F.col("window.start").alias("inicio"),
            F.col("window.end").alias("fim"),
            *[F.col(nome) for nome in nomes],
        )
    )
    consultas = []
    consultas.append(
        validos.writeStream
        .queryName("processado_validos")
        .format("parquet")
        .outputMode("append")
        .option("path", SAIDAS["validos"])
        .option("checkpointLocation", CHECKPOINTS["validos"])
        .start()
    )
    consultas.append(
        invalidos.writeStream
        .queryName("processado_invalidos")
        .format("parquet")
        .outputMode("append")
        .option("path", SAIDAS["invalidos"])
        .option("checkpointLocation", CHECKPOINTS["invalidos"])
        .start()
    )
    consultas.append(
        agregados.writeStream
        .queryName("processado_agregados")
        .format("parquet")
        .outputMode("append")
        .option("path", SAIDAS["agregados"])
        .option("checkpointLocation", CHECKPOINTS["agregados"])
        .start()
    )
    spark.streams.awaitAnyTermination()


if __name__ == "__main__":
    main()
