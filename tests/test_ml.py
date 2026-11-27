import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest

from src.ml import dividir, escolher_limiar, metricas, parse_args, score_persistencia, treinar
from src.ml_features import FEATURES, HORIZONTE_H


def base_sintetica(n=24 * 120, semente=0):
    rng = np.random.default_rng(semente)
    ts = pd.date_range("2025-01-01", periods=n, freq="h", tz="UTC")
    df = pd.DataFrame({"timestamp": ts, "estacao_codigo": "A1"})
    for f in FEATURES:
        df[f] = rng.normal(size=n)
    df["precipitacao_mm"] = np.abs(df["precipitacao_mm"])
    df["y"] = (df["umidade_pct"] + rng.normal(scale=0.5, size=n) > 1.0).astype(float)
    return df


def test_dividir_e_temporal_sem_sobreposicao():
    base = base_sintetica()
    tr, va, te = dividir(base, "2025-03-01", "2025-04-01")
    assert tr["timestamp"].max() < va["timestamp"].min() < va["timestamp"].max() < te["timestamp"].min()
    # purge: o alvo da última linha de treino não invade a validação
    corte = pd.Timestamp("2025-03-01", tz="UTC")
    assert tr["timestamp"].max() + pd.Timedelta(hours=HORIZONTE_H) < corte
    assert len(tr) + len(va) + len(te) == len(base) - 2 * HORIZONTE_H


def test_dividir_ignora_alvo_desconhecido():
    base = base_sintetica()
    base.loc[base.index[-5:], "y"] = np.nan
    _, _, te = dividir(base, "2025-03-01", "2025-04-01")
    assert te["y"].notna().all()


def test_escolher_limiar_separa_classes():
    y = np.array([0, 0, 0, 0, 1, 1, 1, 1])
    p = np.array([0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9])
    assert 0.4 < escolher_limiar(y, p) <= 0.6


def test_metricas_matriz_de_confusao():
    m = metricas([0, 0, 1, 1], [0.1, 0.8, 0.4, 0.9], 0.5)
    assert (m["vp"], m["fp"], m["fn"], m["vn"]) == (1, 1, 1, 1)
    assert m["precisao"] == 0.5 and m["recall"] == 0.5 and m["f1"] == 0.5
    assert m["prevalencia"] == 0.5


def test_metricas_sem_alertas_nao_divide_por_zero():
    m = metricas([0, 1, 1], [0.1, 0.1, 0.2], 0.9)
    assert m["precisao"] == 0.0 and m["recall"] == 0.0 and m["f1"] == 0.0


def test_persistencia_ordena_por_chuva_atual():
    df = pd.DataFrame({"precipitacao_mm": [0.0, np.nan, 0.4, 3.0]})
    s = score_persistencia(df).tolist()
    assert s[0] == s[1] == 0.0 and s[2] > 0.0 and s[3] > s[2]
    assert s[2] >= 1.0  # qualquer chuva passa do limiar 1.0 da persistência


def test_treinar_salva_artefato_e_aprende(tmp_path, monkeypatch):
    import src.ml as ml
    monkeypatch.setattr(ml, "ARQUIVO_METRICAS", tmp_path / "metricas.json")
    base = base_sintetica()
    saida = tmp_path / "m.joblib"
    artefato, rel = treinar(base, "2025-03-01", "2025-04-01", figuras=False, saida=saida)
    assert saida.exists() and (tmp_path / "metricas.json").exists()
    assert artefato["features"] == FEATURES
    assert 0.0 < artefato["limiar"] < 1.0
    recarregado = ml.carregar_modelo(saida)
    prob = recarregado["modelo"].predict_proba(base[FEATURES].iloc[:10])[:, 1]
    assert prob.shape == (10,) and ((prob >= 0) & (prob <= 1)).all()
    # sinal sintético forte em umidade_pct: o modelo precisa superar o acaso
    assert rel["teste"][rel["modelo_escolhido"]]["pr_auc"] > rel["prevalencia"]["teste"] * 2
    assert "persistencia" in rel["teste"]


def test_treinar_recusa_particao_sem_duas_classes(tmp_path):
    base = base_sintetica()
    base["y"] = 0.0
    with pytest.raises(ValueError):
        treinar(base, "2025-03-01", "2025-04-01", figuras=False, saida=tmp_path / "x.joblib")


def test_parse_args_padroes():
    a = parse_args([])
    assert a.beta == 1.0 and a.corte_teste > a.corte_validacao
