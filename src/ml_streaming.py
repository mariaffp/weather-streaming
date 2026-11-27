from pathlib import Path

import joblib
import pandas as pd
from pyspark.sql import functions as F

from src.ml_features import HISTORICO_MINIMO_H, FEATURES, calcular_features


ARQUIVO_MODELO = Path("models/modelo_chuva.joblib")
SAIDA_PREVISOES = "data/processed/previsoes_ml"


def criar_processador_ml(spark, caminho_modelo=ARQUIVO_MODELO):
    artefato = joblib.load(caminho_modelo)
    modelo = artefato["modelo"]
    features_modelo = artefato["features"]
    limiar = float(artefato["limiar"])
    horizonte = int(artefato["horizonte_h"])
    historico = {}

    def processar(batch_df, batch_id):
        registros = [linha.asDict(recursive=True) for linha in batch_df.collect()]
        if not registros:
            return
        df_lote = pd.DataFrame(registros)
        df_lote["timestamp"] = pd.to_datetime(df_lote["timestamp"], utc=True)
        chaves_lote = set(
            (str(linha["estacao_codigo"]), linha["timestamp"])
            for linha in df_lote[["estacao_codigo", "timestamp"]].to_dict("records")
        )
        novos = []
        for codigo, grupo in df_lote.groupby("estacao_codigo"):
            codigo = str(codigo)
            anteriores = historico.get(codigo, [])
            combinados = pd.concat([pd.DataFrame(anteriores), grupo], ignore_index=True)
            combinados["timestamp"] = pd.to_datetime(combinados["timestamp"], utc=True)
            combinados = combinados.drop_duplicates("timestamp", keep="last")
            combinados = combinados.sort_values("timestamp")
            features = calcular_features(combinados, com_alvo=False)
            if not features.empty:
                features["estacao_codigo"] = features["estacao_codigo"].astype(str)
                features["timestamp"] = pd.to_datetime(features["timestamp"], utc=True)
                for _, linha in features.iterrows():
                    chave = (codigo, linha["timestamp"])
                    if chave in chaves_lote:
                        valores = linha[features_modelo].to_frame().T
                        probabilidade = float(modelo.predict_proba(valores)[:, 1][0])
                        novos.append({
                            "timestamp": linha["timestamp"].to_pydatetime(),
                            "estacao_codigo": codigo,
                            "probabilidade_chuva": probabilidade,
                            "limiar": limiar,
                            "alerta_chuva": bool(probabilidade >= limiar),
                            "horizonte_h": horizonte,
                            "batch_id": int(batch_id),
                        })
            limite = combinados["timestamp"].max() - pd.Timedelta(hours=HISTORICO_MINIMO_H)
            historico[codigo] = combinados[combinados["timestamp"] >= limite].to_dict("records")
        if novos:
            previsoes = spark.createDataFrame(novos).withColumn(
                "probabilidade_chuva_pct", F.round(F.col("probabilidade_chuva") * 100, 2)
            )
            (previsoes.write.mode("append").parquet(SAIDA_PREVISOES))

    return processar
