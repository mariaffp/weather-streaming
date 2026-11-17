from pyspark.sql import SparkSession
from src.synthetic_simulator import gerar_registro
import os
import sys

from pyspark.sql import SparkSession
from src.synthetic_simulator import gerar_registro
from pyspark.sql import functions as F

os.environ["PYSPARK_PYTHON"] = sys.executable

spark = (
    SparkSession.builder
    .appName("MonitoramentoChuvas")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

# Gerar X medições meteorológicas
registros = [gerar_registro(i) for i in range(100)]

# Converter os registros em um DataFrame Spark
df = spark.createDataFrame(registros)

df = df.withColumn(
    "timestamp",
    F.to_timestamp("timestamp")
)

# Visualizar algumas colunas
df.select(
    "cidade",
    "temperatura_c",
    "umidade_pct",
    "precipitacao_mm"
).show(truncate=False)



estatisticas = df.groupBy("cidade").agg(
    F.count("*").alias("total_registros"),

    F.round(
        F.avg("precipitacao_mm"), 2
    ).alias("media_mm"),

    F.percentile_approx(
        "precipitacao_mm", 0.5
    ).alias("mediana_mm"),

    F.max("precipitacao_mm").alias("maximo_mm")
)

estatisticas.show(truncate=False)

registros_invalidos = df.filter(
    F.col("precipitacao_mm").isNull() |
    (F.col("precipitacao_mm") < 0)
)

print("Registros inválidos:", registros_invalidos.count())

distribuicao = df.withColumn(
    "faixa_precipitacao",
    F.when(F.col("precipitacao_mm") <= 10, "0 a 10 mm")
     .when(F.col("precipitacao_mm") <= 20, "10 a 20 mm")
     .when(F.col("precipitacao_mm") <= 30, "20 a 30 mm")
     .when(F.col("precipitacao_mm") <= 40, "30 a 40 mm")
     .otherwise("Acima de 40 mm")
)

distribuicao.groupBy("faixa_precipitacao") \
    .count() \
    .orderBy("faixa_precipitacao") \
    .show(truncate=False)
df.printSchema()

analise_temporal = (
    df.groupBy(
        "cidade",
        F.window("timestamp", "1 hour")
    )
    .agg(
        F.count("*").alias("total_medicoes"),
        F.round(
            F.avg("precipitacao_mm"), 2
        ).alias("media_mm"),
        F.max("precipitacao_mm").alias("maximo_mm")
    )
)

analise_temporal.select(
    "cidade",
    F.col("window.start").alias("inicio"),
    F.col("window.end").alias("fim"),
    "total_medicoes",
    "media_mm",
    "maximo_mm"
).orderBy("inicio", "cidade").show(15, truncate=False)

spark.stop()