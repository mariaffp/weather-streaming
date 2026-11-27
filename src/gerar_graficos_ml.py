
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


# ==========================================
# CONFIGURAÇÕES
# ==========================================

PASTA_DADOS = Path("data/processed/previsoes_ml")
PASTA_GRAFICOS = Path("data/processed/graficos_ml")

PASTA_GRAFICOS.mkdir(parents=True, exist_ok=True)

# Identificação das cidades
nomes_estacoes = {
    "A607": "Campos dos Goytacazes",
    "A608": "Macaé",
    "A620": "Campos dos Goytacazes - São Tomé",
    "A627": "Niterói"
}


# ==========================================
# CARREGAMENTO DAS PREVISÕES
# ==========================================

arquivos = list(PASTA_DADOS.glob("*.parquet"))

if not arquivos:
    raise FileNotFoundError(
        "Nenhum arquivo Parquet encontrado na pasta de previsões."
    )

df = pd.concat(
    [pd.read_parquet(arquivo) for arquivo in arquivos],
    ignore_index=True
)

df["timestamp"] = pd.to_datetime(df["timestamp"])

df["probabilidade_chuva_pct"] = (
    df["probabilidade_chuva"] * 100
)

df["cidade_estacao"] = (
    df["estacao_codigo"].astype(str).map(nomes_estacoes)
)

df["cidade_estacao"] = df["cidade_estacao"].fillna(
    df["estacao_codigo"].astype(str)
)

df = df.sort_values("timestamp")

# Limiar utilizado pelo modelo
limiar_pct = float(df["limiar"].iloc[0]) * 100


# ==========================================
# GRÁFICO 1: PROBABILIDADE POR CIDADE
# ==========================================

medias = (
    df.groupby("cidade_estacao")["probabilidade_chuva_pct"]
    .mean()
    .sort_values(ascending=False)
)

plt.figure(figsize=(10, 6))

medias.plot(kind="bar")

plt.title("Probabilidade média de chuva por cidade")
plt.xlabel("Cidade da estação meteorológica")
plt.ylabel("Probabilidade média de chuva (%)")
plt.xticks(rotation=25, ha="right")
plt.ylim(0, 100)
plt.tight_layout()

plt.savefig(
    PASTA_GRAFICOS / "01_probabilidade_por_cidade.png",
    dpi=300
)

plt.close()


# ==========================================
# GRÁFICO 2: EVOLUÇÃO DA PROBABILIDADE
# ==========================================

plt.figure(figsize=(12, 6))

for cidade, grupo in df.groupby("cidade_estacao"):
    grupo = grupo.sort_values("timestamp")

    plt.plot(
        grupo["timestamp"],
        grupo["probabilidade_chuva_pct"],
        marker="o",
        label=cidade
    )

plt.title("Evolução da probabilidade de chuva por cidade")
plt.xlabel("Data e horário")
plt.ylabel("Probabilidade de chuva (%)")
plt.ylim(0, 100)
plt.legend(title="Cidade")
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    PASTA_GRAFICOS / "02_evolucao_probabilidade.png",
    dpi=300
)

plt.close()


# ==========================================
# GRÁFICO 3: DISTRIBUIÇÃO DAS PROBABILIDADES
# ==========================================

plt.figure(figsize=(10, 6))

plt.hist(
    df["probabilidade_chuva_pct"],
    bins=10,
    edgecolor="black"
)

plt.title("Distribuição das probabilidades de chuva")
plt.xlabel("Probabilidade de chuva (%)")
plt.ylabel("Quantidade de previsões")
plt.tight_layout()

plt.savefig(
    PASTA_GRAFICOS / "03_distribuicao_probabilidades.png",
    dpi=300
)

plt.close()


# ==========================================
# GRÁFICO 4: PREVISÃO E ALERTA DE CHUVA
# ==========================================

plt.figure(figsize=(12, 6))

for cidade, grupo in df.groupby("cidade_estacao"):
    grupo = grupo.sort_values("timestamp")

    plt.plot(
        grupo["timestamp"],
        grupo["probabilidade_chuva_pct"],
        marker="o",
        label=cidade
    )

    # Destacar previsões classificadas como alerta
    alertas = grupo[grupo["alerta_chuva"]]

    if not alertas.empty:
        plt.scatter(
            alertas["timestamp"],
            alertas["probabilidade_chuva_pct"],
            marker="X",
            s=100,
            label=f"Alerta: {cidade}"
        )

# Limiar de decisão do modelo
plt.axhline(
    y=limiar_pct,
    linestyle="--",
    label=f"Limiar de alerta ({limiar_pct:.2f}%)"
)

plt.title("Previsão e alertas de chuva por cidade")
plt.xlabel("Data e horário")
plt.ylabel("Probabilidade estimada de chuva (%)")
plt.ylim(0, 100)
plt.legend(title="Localidade")
plt.xticks(rotation=30)
plt.tight_layout()

plt.savefig(
    PASTA_GRAFICOS / "04_previsao_alerta_chuva.png",
    dpi=300
)

plt.close()


# ==========================================
# RESUMO
# ==========================================

print("\n======================================")
print("   GRAFICOS GERADOS COM SUCESSO!")
print("======================================")

print("Total de previsões:", len(df))
print("Limiar de alerta:", round(limiar_pct, 2), "%")

print("\nPrevisões por cidade:")
print(df.groupby("cidade_estacao").size())

print("\nQuantidade de alertas:", int(df["alerta_chuva"].sum()))

print("\nArquivos gerados:")

for arquivo in sorted(PASTA_GRAFICOS.glob("*.png")):
    print("-", arquivo.name)

print("\nPasta:", PASTA_GRAFICOS.resolve())
