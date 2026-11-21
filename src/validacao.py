FAIXAS = {
    "temperatura_c": (-10.0, 50.0),
    "umidade_pct": (0.0, 100.0),
    "pressao_hpa": (900.0, 1050.0),
    "precipitacao_mm": (0.0, 500.0),
    "vento_ms": (0.0, 60.0),
    "vento_kmh": (0.0, 250.0),
}

AGREGACOES = {
    "temperatura_c": "media",
    "umidade_pct": "media",
    "pressao_hpa": "media",
    "precipitacao_mm": "soma",
    "vento_ms": "maximo",
    "vento_kmh": "maximo",
}

AGRUPAR_POR = {
    "sintetico": "cidade",
    "inmet": "estacao_codigo",
}


def coluna_timestamp(colunas, tipos):
    for coluna in colunas:
        if tipos[coluna] == "string":
            return coluna
    raise ValueError("schema sem coluna de texto para timestamp")


def coluna_origem(colunas):
    return colunas[-1]


def classificar(registro, colunas, tipos, origem_esperada):
    if registro is None:
        return "malformado"
    if registro.get(coluna_timestamp(colunas, tipos)) is None:
        return "malformado"
    if registro.get(coluna_origem(colunas)) != origem_esperada:
        return "malformado"
    for coluna in colunas:
        if tipos[coluna] != "double":
            continue
        valor = registro.get(coluna)
        if valor is None:
            continue
        minimo, maximo = FAIXAS[coluna]
        if valor < minimo or valor > maximo:
            return "invalido"
    return "valido"
