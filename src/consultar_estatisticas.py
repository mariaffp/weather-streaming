import os
import sys

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

os.environ["PYSPARK_PYTHON"] = sys.executable

spark = (
    SparkSession.builder
    .appName("ConsultaEstatisticas")
    .master("local[4]")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

historico = (
    spark.read
    .option("recursiveFileLookup", "true")
    .parquet("data/processados/estatisticas")
)

historico = historico.withColumn(
    "batch_id",
    F.regexp_extract(
        F.input_file_name(), r"lote_(\d+)", 1
    ).cast("long")
)

janela = (
    Window
    .partitionBy("cidade", "inicio", "fim")
    .orderBy(F.col("batch_id").desc())
)

estatisticas_atuais = (
    historico
    .withColumn("versao", F.row_number().over(janela))
    .filter(F.col("versao") == 1)
    .drop("versao", "batch_id")
)

estatisticas_atuais.orderBy(
    "inicio", "cidade"
).show(20, truncate=False)

spark.stop()