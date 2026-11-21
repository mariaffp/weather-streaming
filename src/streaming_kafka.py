import os
import sys

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType, LongType, StringType, StructField, StructType

from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from src.synthetic_schema import COLUNAS, TIPOS

TIPOS_SPARK = {
    "double": DoubleType(),
    "long": LongType(),
    "string": StringType(),
}


def main():
    os.environ["PYSPARK_PYTHON"] = sys.executable
    esquema = StructType(
        [StructField(coluna, TIPOS_SPARK[TIPOS[coluna]]) for coluna in COLUNAS]
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
    consulta.awaitTermination()


if __name__ == "__main__":
    main()
