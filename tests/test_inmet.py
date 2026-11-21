import sys
import tempfile
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inmet_reader import (
    analisar_nome_arquivo,
    conferir_nome_arquivo,
    ler_registros,
    montar_timestamp,
    normalizar_nome,
    numero,
)
from src.inmet_schema import COLUNAS, ORIGEM_INMET

AMOSTRAS = str(Path(__file__).resolve().parents[1] / "docs" / "amostras")

VARIAVEIS = ["temperatura_c", "umidade_pct", "pressao_hpa", "precipitacao_mm", "vento_ms"]


def buscar(registros, codigo, timestamp):
    for registro in registros:
        if registro["estacao_codigo"] == codigo and registro["timestamp"] == timestamp:
            return registro
    assert False


def test_numero():
    assert numero("") is None
    assert numero("  ") is None
    assert numero("1011,3") == 1011.3
    assert numero(",8") == 0.8
    assert numero("0") == 0.0


def test_montar_timestamp():
    assert montar_timestamp("2025/01/01", "0100 UTC") == "2025-01-01T01:00:00+00:00"
    assert montar_timestamp("2025/12/31", "2300 UTC") == "2025-12-31T23:00:00+00:00"


def test_normalizar_nome():
    assert normalizar_nome("SÃO-TOMÉ  X") == "sao tome x"
    assert normalizar_nome("MACAE") == "macae"


def test_analisar_nome_arquivo():
    assert analisar_nome_arquivo(
        "INMET_SE_RJ_A608_MACAE_01-01-2025_A_31-12-2025.CSV"
    ) == ("A608", "MACAE")
    assert analisar_nome_arquivo(
        "INMET_SE_RJ_A620_CAMPOS DOS GOYTACAZES - SAO TOME_01-01-2025_A_31-12-2025.CSV"
    ) == ("A620", "CAMPOS DOS GOYTACAZES - SAO TOME")
    assert analisar_nome_arquivo("A607.CSV") is None


def test_conferir_avisa_divergencia_codigo():
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        conferir_nome_arquivo(
            "INMET_SE_RJ_A608_MACAE_01-01-2025_A_31-12-2025.CSV", "A999", "MACAE"
        )
    assert len(avisos) == 1


def test_conferir_aceita_nome_normalizado():
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        conferir_nome_arquivo(
            "INMET_SE_RJ_A620_CAMPOS DOS GOYTACAZES - SAO TOME_01-01-2025_A_31-12-2025.CSV",
            "A620",
            "campos dos goytacazes-são  tomé",
        )
    assert avisos == []


def test_conferir_pula_nome_curto():
    with warnings.catch_warnings(record=True) as avisos:
        warnings.simplefilter("always")
        conferir_nome_arquivo("A607.CSV", "A999", "XXX")
    assert avisos == []


def test_registros_tem_chaves_do_schema():
    registros = list(ler_registros(AMOSTRAS))
    assert len(registros) == 12
    for registro in registros:
        assert list(registro.keys()) == COLUNAS


def test_timestamp_iso_utc():
    registros = list(ler_registros(AMOSTRAS))
    registro = buscar(registros, "A608", "2025-01-01T01:00:00+00:00")
    assert registro["timestamp"] == "2025-01-01T01:00:00+00:00"


def test_parse_virgula_inicial():
    registros = list(ler_registros(AMOSTRAS))
    assert buscar(registros, "A608", "2025-01-01T01:00:00+00:00")["vento_ms"] == 0.8
    assert buscar(registros, "A607", "2025-01-01T23:00:00+00:00")["precipitacao_mm"] == 0.2


def test_vazio_vira_none():
    registros = list(ler_registros(AMOSTRAS))
    registro = buscar(registros, "A608", "2025-07-03T21:00:00+00:00")
    for variavel in VARIAVEIS:
        assert registro[variavel] is None
    assert registro["estacao_codigo"] == "A608"
    assert registro["origem"] == ORIGEM_INMET


def test_ordem_timestamp_estacao():
    registros = list(ler_registros(AMOSTRAS))
    chaves = [(r["timestamp"], r["estacao_codigo"]) for r in registros]
    assert chaves == sorted(chaves)
    mesma_hora = [r["estacao_codigo"] for r in registros if r["timestamp"] == "2025-01-01T01:00:00+00:00"]
    assert mesma_hora == ["A608", "A627"]


def test_estacao_vem_dos_metadados():
    registros = list(ler_registros(AMOSTRAS))
    registro = buscar(registros, "A620", "2025-01-21T12:00:00+00:00")
    assert registro["estacao_nome"] == "CAMPOS DOS GOYTACAZES - SAO TOME"
    assert registro["origem"] == "inmet"


def test_cabecalho_latin1():
    bruto = Path(AMOSTRAS, "A608.CSV").read_bytes()
    try:
        bruto.decode("utf-8")
        decodifica = True
    except UnicodeDecodeError:
        decodifica = False
    assert not decodifica
    assert "PRECIPITAÇÃO TOTAL, HORÁRIO (mm)" in bruto.decode("latin-1").splitlines()[8]


def test_diretorio_inexistente():
    try:
        ler_registros("nao/existe")
    except FileNotFoundError:
        return
    assert False


def test_diretorio_sem_csv():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            ler_registros(tmp)
        except ValueError:
            return
    assert False


def test_chave_meta_ausente():
    linhas = ["OUTRA:;x"] * 8 + ["Data;Hora UTC;X;"] + ["2025/01/01;0000 UTC;1;"]
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "T.CSV").write_text("\n".join(linhas) + "\n", encoding="latin-1")
        try:
            list(ler_registros(tmp))
        except ValueError:
            return
    assert False
