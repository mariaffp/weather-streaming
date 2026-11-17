import json
from pathlib import Path

from src.synthetic_simulator import gerar_registro

destino = Path("data/lote_002.json")

with destino.open("w", encoding="utf-8") as arquivo:
    for indice in range(6, 12):
        registro = gerar_registro(indice)
        arquivo.write(json.dumps(registro) + "\n")

print("Lote gerado:", destino)