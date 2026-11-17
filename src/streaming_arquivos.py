import os
import sys
from pyspark.sql import functions as F
from pyspark.sql import SparkSession

os.environ["PYSPARK_PYTHON"] = sys.executable

spark = (
    SparkSession.builder
    .appName("MonitoramentoChuvasStreaming")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

esquema = """
    id_registro BIGINT,
    timestamp STRING,
    cidade STRING,
    temperatura_c DOUBLE,
    umidade_pct DOUBLE,
    pressao_hpa DOUBLE,
    precipitacao_mm DOUBLE,
    vento_kmh DOUBLE,
    origem STRING
"""

df_stream = (
    spark.readStream
    .schema(esquema)
    .json("data/entrada")
)

df_validado = (
    df_stream
    .withColumn(
        "timestamp",
        F.to_timestamp("timestamp")
    )
    .withColumn(
        "registro_valido",
        F.col("cidade").isNotNull()
        & F.col("timestamp").isNotNull()
        & F.col("precipitacao_mm").isNotNull()
        & (F.col("precipitacao_mm") >= 0)
    )
)

df_validos = df_validado.filter(
    F.col("registro_valido") == True
)

df_invalidos = df_validado.filter(
    F.col("registro_valido") == False
)

analise_temporal = (
    df_validos
    .groupBy(
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
    .select(
        "cidade",
        F.col("window.start").alias("inicio"),
        F.col("window.end").alias("fim"),
        "total_medicoes",
        "media_mm",
        "maximo_mm"
    )
)

def salvar_estatisticas(df_batch, batch_id):
    destino = f"data/processados/estatisticas/lote_{batch_id:05d}"

    df_batch.write \
        .mode("overwrite") \
        .parquet(destino)

    print(f"Estatísticas salvas: microbatch {batch_id}")


consulta_validos = (
    analise_temporal.writeStream
    .queryName("estatisticas_parquet")
    .outputMode("update")
    .foreachBatch(salvar_estatisticas)
    .option(
        "checkpointLocation",
        "data/checkpoints/estatisticas_parquet"
    )
    .trigger(processingTime="5 seconds")
    .start()
)


consulta_invalidos = (
    df_invalidos.writeStream
    .queryName("invalidos_parquet")
    .format("parquet")
    .outputMode("append")
    .option("path", "data/processados/invalidos")
    .option(
        "checkpointLocation",
        "data/checkpoints/invalidos_parquet"
    )
    .trigger(processingTime="5 seconds")
    .start()
)


consulta_validos_parquet = (
    df_validos.writeStream
    .queryName("validos_parquet")
    .format("parquet")
    .outputMode("append")
    .option("path", "data/processados/validos")
    .option(
        "checkpointLocation",
        "data/checkpoints/validos_parquet"
    )
    .trigger(processingTime="5 seconds")
    .start()
)

spark.streams.awaitAnyTermination()

consulta.awaitTermination()

spark.stop()