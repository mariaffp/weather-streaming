COLUNAS = [
    "timestamp",
    "estacao_codigo",
    "estacao_nome",
    "temperatura_c",
    "umidade_pct",
    "pressao_hpa",
    "precipitacao_mm",
    "vento_ms",
    "origem",
]

TIPOS = {
    "timestamp": "string",
    "estacao_codigo": "string",
    "estacao_nome": "string",
    "temperatura_c": "double",
    "umidade_pct": "double",
    "pressao_hpa": "double",
    "precipitacao_mm": "double",
    "vento_ms": "double",
    "origem": "string",
}

MAPEAMENTO = {
    "TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)": "temperatura_c",
    "UMIDADE RELATIVA DO AR, HORARIA (%)": "umidade_pct",
    "PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)": "pressao_hpa",
    "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)": "precipitacao_mm",
    "VENTO, VELOCIDADE HORARIA (m/s)": "vento_ms",
}

ORIGEM_INMET = "inmet"
