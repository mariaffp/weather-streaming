"""Engenharia de atributos para o modelo de chuva (pandas puro, sem Spark).

A mesma função é usada no treino (histórico inteiro) e no streaming (buffer
das últimas horas de cada estação), para que o modelo veja no streaming
exatamente os mesmos atributos que viu no treino.

Problema: dado o que foi observado até a hora t (inclusive), prever se vai
chover pelo menos LIMIAR_MM mm acumulados nas próximas HORIZONTE_H horas
(t+1 .. t+H). Os atributos usam só t e o passado; o alvo usa só o futuro.
"""
import numpy as np
import pandas as pd

HORIZONTE_H = 3
LIMIAR_MM = 1.0

VARIAVEIS = ["temperatura_c", "umidade_pct", "pressao_hpa", "vento_ms"]
COLUNAS_BASE = VARIAVEIS + ["precipitacao_mm"]
JANELAS_CHUVA_H = (3, 6, 24)

FEATURES = (
    COLUNAS_BASE
    + [f"chuva_{w}h" for w in JANELAS_CHUVA_H]
    + [f"d{k}_{v}" for v in VARIAVEIS for k in (1, 3)]
    + ["vento_max3", "hora_sin", "hora_cos"]
)

HISTORICO_MINIMO_H = max(JANELAS_CHUVA_H) + 1


def _serie_estacao(d):
    """Uma estação, 1 linha por hora (horas ausentes viram linhas vazias)."""
    d = d.sort_values("timestamp").drop_duplicates("timestamp", keep="last")
    return d.set_index("timestamp").asfreq("h")


def _atributos_estacao(d, com_alvo):
    p = d["precipitacao_mm"]
    for w in JANELAS_CHUVA_H:
        d[f"chuva_{w}h"] = p.rolling(w, min_periods=1).sum()
    for v in VARIAVEIS:
        d[f"d1_{v}"] = d[v] - d[v].shift(1)
        d[f"d3_{v}"] = d[v] - d[v].shift(3)
    d["vento_max3"] = d["vento_ms"].rolling(3, min_periods=1).max()
    hora = d.index.hour
    d["hora_sin"] = np.sin(2 * np.pi * hora / 24)
    d["hora_cos"] = np.cos(2 * np.pi * hora / 24)
    if com_alvo:
        futuro = pd.concat(
            [p.shift(-k) for k in range(1, HORIZONTE_H + 1)], axis=1
        )
        completo = futuro.notna().all(axis=1)
        d["y"] = np.where(
            completo, (futuro.sum(axis=1) >= LIMIAR_MM).astype(float), np.nan
        )
    return d


def calcular_features(df, com_alvo=False):
    """Recebe registros (timestamp UTC, estacao_codigo e as 5 variáveis) e
    devolve uma linha por registro útil com FEATURES (e `y` se com_alvo).

    Registro útil = pelo menos uma das 5 variáveis presente. Horas que não
    existem no histórico entram como lacunas (NaN) nas janelas, nunca são
    preenchidas. Sem alvo, `y` não existe; com alvo, `y` é NaN quando alguma
    das próximas HORIZONTE_H horas é desconhecida.
    """
    partes = []
    for codigo, d in df.groupby("estacao_codigo"):
        d = _serie_estacao(d[["timestamp"] + COLUNAS_BASE])
        d["estacao_codigo"] = codigo
        partes.append(_atributos_estacao(d, com_alvo).reset_index())
    if not partes:
        colunas = ["timestamp", "estacao_codigo"] + FEATURES + (["y"] if com_alvo else [])
        return pd.DataFrame(columns=colunas)
    saida = pd.concat(partes, ignore_index=True)
    saida = saida[saida[COLUNAS_BASE].notna().any(axis=1)]
    colunas = ["timestamp", "estacao_codigo"] + FEATURES + (["y"] if com_alvo else [])
    return saida[colunas].reset_index(drop=True)


def registros_para_df(registros):
    """Lista de dicts (formato do producer/leitor INMET) -> DataFrame com
    timestamp tz-aware em UTC."""
    df = pd.DataFrame(list(registros))
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df
