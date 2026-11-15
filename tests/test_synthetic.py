import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.consumer import formatar_mensagem
from src.producer import parse_args
from src.synthetic_schema import COLUNAS, ORIGEM_SINTETICA
from src.synthetic_simulator import gerar_registro


def test_registro_tem_colunas_do_schema_em_ordem():
    assert list(gerar_registro(0).keys()) == COLUNAS


def test_registro_marcado_como_sintetico():
    assert gerar_registro(3)["origem"] == ORIGEM_SINTETICA


def test_parse_args_defaults():
    args = parse_args([])
    assert args.n == 10
    assert args.intervalo == 1.0
    assert args.aceleracao == 1.0


def test_formatar_mensagem():
    linha = formatar_mensagem("meteorologia", 0, 7, {"a": 1, "b": "x"})
    assert linha == "meteorologia 0 7 a=1 b=x"
