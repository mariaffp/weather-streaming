import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from src.ml_features import (
    COLUNAS_BASE,
    FEATURES,
    HORIZONTE_H,
    LIMIAR_MM,
    calcular_features,
)


def serie(n=40, estacao="A1", chuva=None, inicio="2025-01-01"):
    ts = pd.date_range(inicio, periods=n, freq="h", tz="UTC")
    df = pd.DataFrame(
        {
            "timestamp": ts,
            "estacao_codigo": estacao,
            "temperatura_c": np.linspace(20, 30, n),
            "umidade_pct": 70.0,
            "pressao_hpa": 1010.0,
            "precipitacao_mm": 0.0 if chuva is None else chuva,
            "vento_ms": 2.0,
        }
    )
    return df


def test_features_completas_e_sem_alvo():
    f = calcular_features(serie())
    assert list(f.columns) == ["timestamp", "estacao_codigo"] + FEATURES
    assert len(f) == 40


def test_chuva_acumulada_e_delta():
    chuva = np.zeros(40)
    chuva[10] = 2.0
    chuva[11] = 1.0
    f = calcular_features(serie(chuva=chuva)).set_index("timestamp")
    t = pd.Timestamp("2025-01-01 11:00", tz="UTC")
    assert f.loc[t, "chuva_3h"] == 3.0
    assert f.loc[t, "chuva_24h"] == 3.0
    assert f.loc[pd.Timestamp("2025-01-01 14:00", tz="UTC"), "chuva_3h"] == 0.0
    d1 = f.loc[t, "d1_temperatura_c"]
    assert abs(d1 - 10 / 39) < 1e-9


def test_alvo_olha_so_para_o_futuro():
    chuva = np.zeros(40)
    chuva[20] = LIMIAR_MM
    f = calcular_features(serie(chuva=chuva), com_alvo=True).set_index("timestamp")
    for h in range(20 - HORIZONTE_H, 20):
        assert f.loc[pd.Timestamp(f"2025-01-01 {h:02d}:00", tz="UTC"), "y"] == 1.0
    assert f.loc[pd.Timestamp("2025-01-01 20:00", tz="UTC"), "y"] == 0.0
    assert f.loc[pd.Timestamp("2025-01-01 16:00", tz="UTC"), "y"] == 0.0
    # sem futuro conhecido -> NaN
    assert f["y"].iloc[-1:].isna().all()
    assert f["y"].iloc[-HORIZONTE_H:].isna().all()


def test_atributos_nao_dependem_do_futuro():
    base = serie(chuva=np.r_[np.zeros(30), np.ones(10)])
    alterada = base.copy()
    alterada.loc[alterada.index[25:], ["precipitacao_mm", "temperatura_c"]] = 99.0
    a = calcular_features(base).iloc[:25][FEATURES]
    b = calcular_features(alterada).iloc[:25][FEATURES]
    pd.testing.assert_frame_equal(a, b)


def test_hora_ausente_vira_lacuna_nao_preenchimento():
    df = serie(n=10)
    df = df.drop(index=5)  # some a hora 05:00
    f = calcular_features(df).set_index("timestamp")
    assert len(f) == 9
    # delta de 1h na hora 06 compara com 05 (ausente) -> NaN
    assert np.isnan(f.loc[pd.Timestamp("2025-01-01 06:00", tz="UTC"), "d1_temperatura_c"])


def test_alvo_nan_se_hora_futura_ausente():
    df = serie(n=12).drop(index=8)
    f = calcular_features(df, com_alvo=True).set_index("timestamp")
    assert np.isnan(f.loc[pd.Timestamp("2025-01-01 06:00", tz="UTC"), "y"])
    assert not np.isnan(f.loc[pd.Timestamp("2025-01-01 04:00", tz="UTC"), "y"])


def test_registro_todo_vazio_e_descartado():
    df = serie(n=6)
    df.loc[2, COLUNAS_BASE] = np.nan
    f = calcular_features(df)
    assert len(f) == 5


def test_estacoes_nao_se_misturam():
    a = serie(estacao="A1", chuva=np.r_[np.zeros(20), np.full(20, 5.0)])
    b = serie(estacao="A2")
    f = calcular_features(pd.concat([a, b])).set_index(["estacao_codigo", "timestamp"])
    t = pd.Timestamp("2025-01-02 06:00", tz="UTC")
    assert f.loc[("A1", t), "chuva_3h"] == 15.0
    assert f.loc[("A2", t), "chuva_3h"] == 0.0


def test_vazio():
    f = calcular_features(serie().iloc[0:0])
    assert f.empty
