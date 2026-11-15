CIDADES = ["Rio das Ostras", "Macaé", "Cabo Frio"]

COLUNAS = [
    "id_registro",
    "timestamp",
    "cidade",
    "temperatura_c",
    "umidade_pct",
    "pressao_hpa",
    "precipitacao_mm",
    "vento_kmh",
    "origem",
]

FAIXAS = {
    "temperatura_c": (15.0, 40.0),
    "umidade_pct": (20.0, 100.0),
    "pressao_hpa": (990.0, 1030.0),
    "precipitacao_mm": (0.0, 50.0),
    "vento_kmh": (0.0, 80.0),
}

ORIGEM_SINTETICA = "sintetico"

PASSO_SIMULADO_SEGUNDOS = 600
