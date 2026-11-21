import os
import sys

from pyspark.sql import SparkSession

CAMINHOS = [
    ("validos", "data/processed/validos"),
    ("invalidos", "data/processed/invalidos"),
    ("agregados", "data/processed/agregados"),
]


def main():
    os.environ["PYSPARK_PYTHON"] = sys.executable
    spark = (
        SparkSession.builder
        .appName("ConsultarProcessados")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    for nome, caminho in CAMINHOS:
        print("=" * 60)
        print(nome, caminho)
        try:
            df = spark.read.parquet(caminho)
        except Exception as erro:
            print("leitura falhou:", erro)
            continue
        print("registros:", df.count())
        df.printSchema()
        df.show(20, truncate=False)
    spark.stop()


if __name__ == "__main__":
    main()
