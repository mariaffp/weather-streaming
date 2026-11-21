import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import inmet_schema, synthetic_schema
from src.synthetic_schema import FAIXAS as FAIXAS_SINTETICAS
from src.validacao import (
    AGRUPAR_POR,
    AGREGACOES,
    FAIXAS,
    classificar,
    coluna_origem,
    coluna_timestamp,
)


def base_inmet():
    return {
        "timestamp": "2025-01-01T00:00:00+00:00",
        "estacao_codigo": "A608",
        "estacao_nome": "MACAE",
        "temperatura_c": 25.0,
        "umidade_pct": 80.0,
        "pressao_hpa": 1012.0,
        "precipitacao_mm": 0.0,
        "vento_ms": 3.0,
        "origem": "inmet",
    }


def val(colunas, tipos, esperada, **mudancas):
    registro = base_inmet()
    registro.update(mudancas)
    return classificar(registro, colunas, tipos, esperada)


def test_faixas_sinteticas_cabem_na_validade():
    for coluna, (minimo, maximo) in FAIXAS_SINTETICAS.items():
        valido_min, valido_max = FAIXAS[coluna]
        assert valido_min <= minimo
        assert maximo <= valido_max


def test_valido_com_nulos():
    colunas = inmet_schema.COLUNAS
    tipos = inmet_schema.TIPOS
    assert val(colunas, tipos, "inmet") == "valido"
    assert (
        val(
            colunas,
            tipos,
            "inmet",
            temperatura_c=None,
            umidade_pct=None,
            pressao_hpa=None,
            precipitacao_mm=None,
            vento_ms=None,
        )
        == "valido"
    )


def test_limites_inclusivos():
    colunas = inmet_schema.COLUNAS
    tipos = inmet_schema.TIPOS
    assert val(colunas, tipos, "inmet", precipitacao_mm=500.0) == "valido"
    assert val(colunas, tipos, "inmet", precipitacao_mm=500.1) == "invalido"
    assert val(colunas, tipos, "inmet", precipitacao_mm=62.2) == "valido"
    assert val(colunas, tipos, "inmet", umidade_pct=100.0) == "valido"
    assert val(colunas, tipos, "inmet", umidade_pct=100.1) == "invalido"


def test_invalido_por_variavel():
    colunas = inmet_schema.COLUNAS
    tipos = inmet_schema.TIPOS
    assert val(colunas, tipos, "inmet", temperatura_c=80.0) == "invalido"
    assert val(colunas, tipos, "inmet", umidade_pct=-1.0) == "invalido"
    assert val(colunas, tipos, "inmet", pressao_hpa=800.0) == "invalido"
    assert val(colunas, tipos, "inmet", precipitacao_mm=-0.5) == "invalido"
    assert val(colunas, tipos, "inmet", vento_ms=100.0) == "invalido"


def test_malformado():
    colunas = inmet_schema.COLUNAS
    tipos = inmet_schema.TIPOS
    assert classificar(None, colunas, tipos, "inmet") == "malformado"
    assert val(colunas, tipos, "inmet", timestamp=None) == "malformado"
    assert val(colunas, tipos, "inmet", origem=None) == "malformado"
    assert val(colunas, tipos, "inmet", origem="sintetico") == "malformado"


def test_localizadores():
    assert (
        coluna_timestamp(inmet_schema.COLUNAS, inmet_schema.TIPOS) == "timestamp"
    )
    assert (
        coluna_timestamp(synthetic_schema.COLUNAS, synthetic_schema.TIPOS)
        == "timestamp"
    )
    assert coluna_origem(inmet_schema.COLUNAS) == "origem"
    assert coluna_origem(synthetic_schema.COLUNAS) == "origem"


def test_completude_regras():
    for modulo in (inmet_schema, synthetic_schema):
        for coluna in modulo.COLUNAS:
            if modulo.TIPOS[coluna] == "double":
                assert coluna in FAIXAS
                assert coluna in AGREGACOES
    assert set(AGRUPAR_POR) == {"sintetico", "inmet"}
    assert AGRUPAR_POR["sintetico"] in synthetic_schema.COLUNAS
    assert AGRUPAR_POR["inmet"] in inmet_schema.COLUNAS


def test_agregacoes():
    assert AGREGACOES["temperatura_c"] == "media"
    assert AGREGACOES["umidade_pct"] == "media"
    assert AGREGACOES["pressao_hpa"] == "media"
    assert AGREGACOES["precipitacao_mm"] == "soma"
    assert AGREGACOES["vento_ms"] == "maximo"
    assert AGREGACOES["vento_kmh"] == "maximo"
