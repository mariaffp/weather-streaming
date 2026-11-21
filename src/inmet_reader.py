import csv
import unicodedata
import warnings
from datetime import datetime, timezone
from pathlib import Path

from src.inmet_schema import COLUNAS, MAPEAMENTO, ORIGEM_INMET


def normalizar_nome(valor):
    base = unicodedata.normalize("NFD", valor)
    sem_acento = "".join(c for c in base if unicodedata.category(c) != "Mn")
    return " ".join(sem_acento.lower().replace("-", " ").split())


def analisar_nome_arquivo(nome):
    partes = Path(nome).name.split("_")
    if len(partes) < 6 or partes[0] != "INMET":
        return None
    return partes[3], partes[4]


def conferir_nome_arquivo(caminho, codigo_meta, nome_meta):
    achado = analisar_nome_arquivo(str(caminho))
    if achado is None:
        return
    codigo_arquivo, nome_arquivo = achado
    if codigo_arquivo != codigo_meta:
        warnings.warn("codigo divergente no arquivo " + str(caminho))
    if normalizar_nome(nome_arquivo) != normalizar_nome(nome_meta):
        warnings.warn("estacao divergente no arquivo " + str(caminho))


def numero(valor):
    texto = valor.strip()
    if texto == "":
        return None
    return float(texto.replace(",", "."))


def montar_timestamp(data, hora):
    return datetime.strptime(
        data.strip() + hora.strip()[:4], "%Y/%m/%d%H%M"
    ).replace(tzinfo=timezone.utc).isoformat()


def ler_arquivo(caminho):
    with open(caminho, encoding="latin-1", newline="") as f:
        leitor = csv.reader(f, delimiter=";")
        meta = {}
        for _ in range(8):
            linha = next(leitor)
            meta[linha[0].strip().rstrip(":")] = linha[1].strip() if len(linha) > 1 else ""
        if "CODIGO (WMO)" not in meta:
            raise ValueError("chave CODIGO (WMO) ausente em " + str(caminho))
        if "ESTACAO" not in meta:
            raise ValueError("chave ESTACAO ausente em " + str(caminho))
        codigo = meta["CODIGO (WMO)"]
        estacao = meta["ESTACAO"]
        conferir_nome_arquivo(caminho, codigo, estacao)
        cabecalho = next(leitor)
        i_data = cabecalho.index("Data")
        i_hora = cabecalho.index("Hora UTC")
        indices = {norm: cabecalho.index(orig) for orig, norm in MAPEAMENTO.items()}
        registros = []
        for linha in leitor:
            if "".join(linha).strip() == "":
                continue
            registro = {
                "timestamp": montar_timestamp(linha[i_data], linha[i_hora]),
                "estacao_codigo": codigo,
                "estacao_nome": estacao,
                "origem": ORIGEM_INMET,
            }
            for norm, i in indices.items():
                registro[norm] = numero(linha[i])
            registros.append({col: registro[col] for col in COLUNAS})
    return registros


def ler_registros(diretorio="data/raw/inmet"):
    base = Path(diretorio)
    if not base.is_dir():
        raise FileNotFoundError("diretório de dados não encontrado: " + str(diretorio))
    arquivos = sorted(
        p for p in base.iterdir() if p.is_file() and p.suffix.lower() == ".csv"
    )
    if not arquivos:
        raise ValueError("nenhum CSV em: " + str(diretorio))
    todos = []
    for caminho in arquivos:
        todos.extend(ler_arquivo(caminho))
    todos.sort(key=lambda r: (r["timestamp"], r["estacao_codigo"]))
    return iter(todos)
