import io
import sys
from contextlib import redirect_stderr
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.inmet_reader import ler_registros
from src.producer import (
    espera_real,
    parse_args,
    parsear_inicio,
    selecionar,
    serializar,
)

AMOSTRAS = str(Path(__file__).resolve().parents[1] / "docs" / "amostras")


def base():
    return [
        {"timestamp": "2025-01-01T00:00:00+00:00", "estacao_codigo": "A607"},
        {"timestamp": "2025-01-01T00:00:00+00:00", "estacao_codigo": "A608"},
        {"timestamp": "2025-01-01T01:00:00+00:00", "estacao_codigo": "A607"},
    ]


def parse_falha(argv):
    with redirect_stderr(io.StringIO()):
        try:
            parse_args(argv)
        except SystemExit:
            return
    assert False


def test_defaults_novos():
    args = parse_args([])
    assert args.fonte == "sintetico"
    assert args.estacao is None
    assert args.inicio is None
    assert args.ritmo == "fixo"
    assert args.verboso is False


def test_fonte_inmet():
    args = parse_args(["--fonte", "inmet"])
    assert args.fonte == "inmet"


def test_flags_inmet_exigem_fonte():
    parse_falha(["--estacao", "A608"])
    parse_falha(["--inicio", "2025-01-01"])
    parse_falha(["--ritmo", "real"])


def test_inicio_convertido():
    args = parse_args(["--fonte", "inmet", "--inicio", "2025-03-01"])
    assert args.inicio == "2025-03-01T00:00:00+00:00"


def test_inicio_invalido():
    parse_falha(["--fonte", "inmet", "--inicio", "32/01"])


def test_parsear_inicio():
    assert parsear_inicio("2025-03-01") == "2025-03-01T00:00:00+00:00"
    assert parsear_inicio("2025-03-01T10:00:00Z") == "2025-03-01T10:00:00+00:00"
    assert parsear_inicio("2025-03-01T10:00:00+00:00") == "2025-03-01T10:00:00+00:00"
    for invalido in ["32/01", "2025-03-01T10:00", "2025-03-01T10:00:00+01:00"]:
        try:
            parsear_inicio(invalido)
        except ValueError:
            continue
        assert False


def test_selecionar_estacao():
    registros = selecionar(base(), ["A608"], None, 10)
    assert [r["estacao_codigo"] for r in registros] == ["A608"]
    registros = selecionar(base(), ["A607", "A608"], None, 2)
    assert len(registros) == 2


def test_selecionar_inicio_e_n():
    registros = selecionar(base(), None, "2025-01-01T01:00:00+00:00", 10)
    assert len(registros) == 1
    registros = selecionar(base(), None, None, 2)
    assert len(registros) == 2


def test_selecionar_erros():
    try:
        selecionar(base(), ["AXXX"], None, 10)
    except ValueError as erro:
        assert "AXXX" in str(erro) and "A607" in str(erro)
    else:
        assert False
    try:
        selecionar(base(), None, "2026-01-01T00:00:00+00:00", 10)
    except ValueError:
        pass
    else:
        assert False
    try:
        selecionar(base(), None, None, 0)
    except ValueError:
        pass
    else:
        assert False


def test_espera_real():
    assert espera_real("2025-01-01T00:00:00+00:00", "2025-01-01T00:00:00+00:00", 3600) == 0.0
    assert espera_real("2025-01-01T00:00:00+00:00", "2025-01-01T01:00:00+00:00", 3600) == 1.0
    assert espera_real("2025-01-01T01:00:00+00:00", "2025-01-01T00:00:00+00:00", 3600) == 0.0


def test_serializar():
    assert serializar({"a": None}) == b'{"a": null}'
    assert serializar({"a": 1.5}) == b'{"a": 1.5}'
    try:
        serializar({"a": float("nan")})
    except ValueError:
        pass
    else:
        assert False


def test_amostras_primeiros_registros():
    registros = selecionar(list(ler_registros(AMOSTRAS)), None, None, 8)
    assert len(registros) == 8
    assert registros[0]["timestamp"] == registros[1]["timestamp"] == "2025-01-01T01:00:00+00:00"
    assert [registros[0]["estacao_codigo"], registros[1]["estacao_codigo"]] == ["A608", "A627"]


def test_amostras_filtros():
    todos = list(ler_registros(AMOSTRAS))
    assert len(selecionar(todos, ["A608"], None, 100)) == 3
    assert len(selecionar(todos, None, "2025-07-01T00:00:00+00:00", 100)) == 6


def test_filtro_estacao_a608_com_iterador():
    registros = selecionar(ler_registros(AMOSTRAS), ["A608"], None, 100)
    assert len(registros) == 3


def test_filtro_estacao_a607_com_iterador():
    registros = selecionar(ler_registros(AMOSTRAS), ["A607"], None, 100)
    assert len(registros) == 3
