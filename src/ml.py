"""Treino e avaliação do modelo de chuva (offline).

    python -m src.ml                 # treina, avalia e salva em models/

Fluxo: lê o INMET 2025 -> atributos (src/ml_features.py) -> divisão
temporal treino / validação / teste -> compara baseline e modelos na
validação -> escolhe limiar na validação -> mede no teste (dados nunca
vistos) -> reajusta o melhor em treino+validação e salva o artefato
(models/modelo_chuva.joblib) que a etapa de streaming vai carregar.

Contrato do artefato (dict via joblib): modelo (tem predict_proba), features
(colunas, na ordem), limiar, horizonte_h, limiar_mm, nome_modelo, treinado_ate.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.inmet_reader import ler_registros
from src.ml_features import (
    FEATURES,
    HORIZONTE_H,
    LIMIAR_MM,
    calcular_features,
    registros_para_df,
)

DIR_MODELOS = Path("models")
ARQUIVO_MODELO = DIR_MODELOS / "modelo_chuva.joblib"
ARQUIVO_METRICAS = DIR_MODELOS / "metricas.json"
DIR_FIGURAS = Path("docs/img")

CORTE_VALIDACAO = "2025-09-01"
CORTE_TESTE = "2025-11-01"
SEMENTE = 0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Treina o modelo de chuva.")
    parser.add_argument("--corte-validacao", default=CORTE_VALIDACAO)
    parser.add_argument("--corte-teste", default=CORTE_TESTE)
    parser.add_argument("--beta", type=float, default=1.0,
                        help="peso do recall no F-beta usado para escolher o limiar")
    parser.add_argument("--sem-figuras", action="store_true")
    parser.add_argument("--saida", default=str(ARQUIVO_MODELO))
    return parser.parse_args(argv)


def carregar_base(diretorio="data/raw/inmet"):
    return calcular_features(registros_para_df(ler_registros(diretorio)), com_alvo=True)


def dividir(base, corte_validacao, corte_teste):
    """Divisão temporal. Os últimos HORIZONTE_H horas antes de cada corte
    são descartados (purge): o alvo dessas linhas olha para dentro do
    período seguinte e vazaria informação."""
    base = base[base["y"].notna()]
    purge = pd.Timedelta(hours=HORIZONTE_H)
    cv = pd.Timestamp(corte_validacao, tz="UTC")
    ct = pd.Timestamp(corte_teste, tz="UTC")
    ts = base["timestamp"]
    treino = base[ts < cv - purge]
    validacao = base[(ts >= cv) & (ts < ct - purge)]
    teste = base[ts >= ct]
    return treino, validacao, teste


def construir_modelos():
    return {
        "regressao_logistica": make_pipeline(
            SimpleImputer(strategy="median"),
            StandardScaler(),
            LogisticRegression(class_weight="balanced", max_iter=2000),
        ),
        "random_forest": make_pipeline(
            SimpleImputer(strategy="median"),
            RandomForestClassifier(
                n_estimators=200,
                min_samples_leaf=10,
                max_depth=14,
                class_weight="balanced_subsample",
                n_jobs=-1,
                random_state=SEMENTE,
            ),
        ),
        "gradient_boosting": HistGradientBoostingClassifier(
            max_depth=4,
            learning_rate=0.05,
            max_iter=200,
            class_weight="balanced",
            random_state=SEMENTE,
        ),
    }


def score_persistencia(df):
    """Baseline sem aprendizado: 'se está chovendo agora, vai chover'
    (desempata pela quantidade de chuva)."""
    chuva = df["precipitacao_mm"].fillna(0.0)
    return (chuva > 0).astype(float) + chuva / 1000.0


def escolher_limiar(y, prob, beta=1.0):
    """Limiar que maximiza o F-beta nas probabilidades dadas."""
    precisao, recall, limiares = precision_recall_curve(y, prob)
    precisao, recall = precisao[:-1], recall[:-1]
    b2 = beta**2
    denom = b2 * precisao + recall
    f = np.divide((1 + b2) * precisao * recall, denom,
                  out=np.zeros_like(denom), where=denom > 0)
    return float(limiares[int(np.argmax(f))])


def metricas(y, prob, limiar):
    """Métricas de ranking (independem do limiar) e de alerta (no limiar)."""
    y = np.asarray(y).astype(int)
    pred = (np.asarray(prob) >= limiar).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    precisao = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precisao * recall / (precisao + recall) if precisao + recall else 0.0
    return {
        "n": int(len(y)),
        "positivos": int(y.sum()),
        "prevalencia": float(y.mean()) if len(y) else 0.0,
        "pr_auc": float(average_precision_score(y, prob)) if y.sum() else None,
        "roc_auc": float(roc_auc_score(y, prob)) if 0 < y.sum() < len(y) else None,
        "limiar": float(limiar),
        "precisao": float(precisao),
        "recall": float(recall),
        "f1": float(f1),
        "vp": int(tp), "fp": int(fp), "fn": int(fn), "vn": int(tn),
    }


def treinar(base, corte_validacao=CORTE_VALIDACAO, corte_teste=CORTE_TESTE,
            beta=1.0, figuras=True, saida=ARQUIVO_MODELO):
    treino, validacao, teste = dividir(base, corte_validacao, corte_teste)
    for nome, parte in (("treino", treino), ("validação", validacao), ("teste", teste)):
        if parte["y"].sum() == 0 or parte["y"].sum() == len(parte):
            raise ValueError(f"{nome} sem as duas classes; ajuste os cortes")

    # 1) comparar na validação (modelos treinados só no treino)
    ajustados, auc_validacao = {}, {}
    for nome, modelo in construir_modelos().items():
        modelo.fit(treino[FEATURES], treino["y"])
        prob = modelo.predict_proba(validacao[FEATURES])[:, 1]
        ajustados[nome] = modelo
        auc_validacao[nome] = float(average_precision_score(validacao["y"], prob))
    melhor = max(auc_validacao, key=auc_validacao.get)

    # 2) limiar escolhido na validação, nunca no teste
    prob_val = ajustados[melhor].predict_proba(validacao[FEATURES])[:, 1]
    limiar = escolher_limiar(validacao["y"], prob_val, beta)

    # 3) teste: dados que nenhuma etapa anterior viu
    resultado = {}
    prob_teste = {}
    for nome, modelo in ajustados.items():
        prob_teste[nome] = modelo.predict_proba(teste[FEATURES])[:, 1]
        lim = limiar if nome == melhor else escolher_limiar(
            validacao["y"], modelo.predict_proba(validacao[FEATURES])[:, 1], beta
        )
        resultado[nome] = metricas(teste["y"], prob_teste[nome], lim)
    prob_teste["persistencia"] = score_persistencia(teste).to_numpy()
    resultado["persistencia"] = metricas(teste["y"], prob_teste["persistencia"], 1.0)
    por_estacao = {}
    for codigo, g in teste.groupby("estacao_codigo"):
        idx = g.index
        pos = teste.index.get_indexer(idx)
        por_estacao[codigo] = metricas(g["y"], prob_teste[melhor][pos], limiar)

    importancia = permutation_importance(
        ajustados[melhor], teste[FEATURES], teste["y"],
        scoring="average_precision", n_repeats=5, random_state=SEMENTE, n_jobs=-1,
    )
    ranking = sorted(
        zip(FEATURES, importancia.importances_mean, importancia.importances_std),
        key=lambda t: -t[1],
    )

    # 4) reajuste final em treino+validação (tudo antes do teste)
    final = construir_modelos()[melhor]
    antes_do_teste = pd.concat([treino, validacao])
    final.fit(antes_do_teste[FEATURES], antes_do_teste["y"])

    ate = (antes_do_teste["timestamp"].max() + pd.Timedelta(hours=HORIZONTE_H))
    artefato = {
        "modelo": final,
        "nome_modelo": melhor,
        "features": FEATURES,
        "limiar": limiar,
        "horizonte_h": HORIZONTE_H,
        "limiar_mm": LIMIAR_MM,
        "treinado_ate": ate.isoformat(),
        "treinado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artefato, saida, compress=3)

    relatorio = {
        "alvo": f"precipitação acumulada >= {LIMIAR_MM} mm nas próximas {HORIZONTE_H} h",
        "cortes": {"validacao": corte_validacao, "teste": corte_teste},
        "tamanhos": {
            "treino": int(len(treino)), "validacao": int(len(validacao)),
            "teste": int(len(teste)),
        },
        "prevalencia": {
            "treino": float(treino["y"].mean()),
            "validacao": float(validacao["y"].mean()),
            "teste": float(teste["y"].mean()),
        },
        "pr_auc_validacao": auc_validacao,
        "modelo_escolhido": melhor,
        "limiar": limiar,
        "teste": resultado,
        "teste_por_estacao": por_estacao,
        "importancia_permutacao": [
            {"feature": f, "media": float(m), "desvio": float(s)} for f, m, s in ranking
        ],
        "treinado_ate": ate.isoformat(),
    }
    ARQUIVO_METRICAS.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_METRICAS.write_text(json.dumps(relatorio, indent=2, ensure_ascii=False))
    if figuras:
        try:
            gerar_figuras(teste["y"].to_numpy(), prob_teste, ranking, melhor)
        except ImportError:
            print("matplotlib ausente; figuras ignoradas")
    return artefato, relatorio


def gerar_figuras(y, prob_por_modelo, ranking, melhor):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    DIR_FIGURAS.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for nome, prob in prob_por_modelo.items():
        p, r, _ = precision_recall_curve(y, prob)
        ap = average_precision_score(y, prob)
        ax.plot(r, p, label=f"{nome} (PR-AUC {ap:.2f})",
                lw=2.5 if nome == melhor else 1.2)
    ax.axhline(np.mean(y), color="gray", ls=":", label="aleatório")
    ax.set(xlabel="Recall", ylabel="Precisão", title="Curva precisão-recall (teste: nov–dez/2025)",
           xlim=(0, 1), ylim=(0, 1))
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(DIR_FIGURAS / "ml_pr_curve.png", dpi=150)
    plt.close(fig)

    top = ranking[:10][::-1]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.barh([t[0] for t in top], [t[1] for t in top], xerr=[t[2] for t in top])
    ax.set(xlabel="Queda média da PR-AUC ao embaralhar", title="Importância por permutação (teste)")
    fig.tight_layout()
    fig.savefig(DIR_FIGURAS / "ml_importancia.png", dpi=150)
    plt.close(fig)


def carregar_modelo(caminho=ARQUIVO_MODELO):
    return joblib.load(caminho)


def main():
    args = parse_args()
    base = carregar_base()
    artefato, rel = treinar(base, args.corte_validacao, args.corte_teste,
                            args.beta, not args.sem_figuras, args.saida)
    print("Alvo:", rel["alvo"])
    print("Tamanhos:", rel["tamanhos"])
    print("PR-AUC validação:", {k: round(v, 3) for k, v in rel["pr_auc_validacao"].items()})
    print("Modelo escolhido:", rel["modelo_escolhido"], "| limiar:", round(rel["limiar"], 3))
    print(f"{'modelo':22s} {'PR-AUC':>7s} {'ROC':>6s} {'prec':>6s} {'recall':>7s} {'F1':>6s}")
    for nome, m in rel["teste"].items():
        print(f"{nome:22s} {m['pr_auc']:7.3f} {m['roc_auc']:6.3f} "
              f"{m['precisao']:6.3f} {m['recall']:7.3f} {m['f1']:6.3f}")
    print("Salvo em", args.saida, "e", ARQUIVO_METRICAS)


if __name__ == "__main__":
    main()
