import random
from datetime import datetime, timedelta, timezone

from src.synthetic_schema import (
    CIDADES,
    COLUNAS,
    FAIXAS,
    ORIGEM_SINTETICA,
    PASSO_SIMULADO_SEGUNDOS,
)

INICIO = datetime.now(timezone.utc).replace(microsecond=0)


def gerar_registro(indice):
    registro = {
        "id_registro": indice,
        "timestamp": (INICIO + timedelta(seconds=indice * PASSO_SIMULADO_SEGUNDOS)).isoformat(),
        "cidade": CIDADES[indice % len(CIDADES)],
        "origem": ORIGEM_SINTETICA,
    }
    for coluna, (minimo, maximo) in FAIXAS.items():
        registro[coluna] = round(random.uniform(minimo, maximo), 1)
    return {coluna: registro[coluna] for coluna in COLUNAS}
