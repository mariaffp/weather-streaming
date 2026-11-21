import argparse
import json
import re
import time
from datetime import datetime, timedelta, timezone

from kafka import KafkaProducer

from src.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC
from src.inmet_reader import ler_registros
from src.synthetic_simulator import gerar_registro


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Envia registros sintéticos ao Kafka.")
    parser.add_argument("--n", type=int, default=10)
    parser.add_argument("--intervalo", type=float, default=1.0)
    parser.add_argument("--aceleracao", type=float, default=1.0)
    parser.add_argument("--fonte", choices=["sintetico", "inmet"], default="sintetico")
    parser.add_argument("--estacao", action="append", default=None)
    parser.add_argument("--inicio", default=None)
    parser.add_argument("--ritmo", choices=["fixo", "real"], default="fixo",
                        help="no modo real, o --intervalo é ignorado")
    parser.add_argument("--verboso", action="store_true")
    args = parser.parse_args(argv)
    if args.aceleracao <= 0:
        parser.error("--aceleracao deve ser maior que zero")
    if args.fonte == "sintetico" and (
        args.estacao or args.inicio is not None or args.ritmo != "fixo"
    ):
        parser.error("--estacao, --inicio e --ritmo exigem --fonte inmet")
    if args.inicio is not None:
        try:
            args.inicio = parsear_inicio(args.inicio)
        except ValueError as erro:
            parser.error(str(erro))
    return args


def parsear_inicio(valor):
    texto = valor.strip()
    try:
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", texto):
            dt = datetime.strptime(texto, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        else:
            dt = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("--inicio inválido: " + valor)
    if dt.tzinfo is None or dt.utcoffset() != timedelta(seconds=0):
        raise ValueError("--inicio deve ser data ou timestamp ISO em UTC: " + valor)
    return dt.isoformat()


def selecionar(registros, estacoes, inicio, n):
    if estacoes:
        conhecidos = sorted({r["estacao_codigo"] for r in registros})
        desconhecidas = [e for e in estacoes if e not in conhecidos]
        if desconhecidas:
            raise ValueError(
                "estação desconhecida: "
                + ", ".join(desconhecidas)
                + " (opções: "
                + ", ".join(conhecidos)
                + ")"
            )
    saida = [
        r
        for r in registros
        if (not estacoes or r["estacao_codigo"] in estacoes)
        and (inicio is None or r["timestamp"] >= inicio)
    ][:n]
    if not saida:
        raise ValueError("filtros não retornaram registros")
    return saida


def espera_real(anterior_iso, atual_iso, aceleracao):
    anterior = datetime.fromisoformat(anterior_iso)
    atual = datetime.fromisoformat(atual_iso)
    return max(0.0, (atual - anterior).total_seconds() / aceleracao)


def serializar(valor):
    return json.dumps(valor, allow_nan=False).encode("utf-8")


def main():
    args = parse_args()
    registros = None
    if args.fonte == "inmet":
        try:
            registros = selecionar(ler_registros(), args.estacao, args.inicio, args.n)
        except ValueError as erro:
            raise SystemExit(str(erro))
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: serializar(v),
    )
    if args.fonte == "inmet":
        for i, registro in enumerate(registros):
            producer.send(KAFKA_TOPIC, registro)
            if i < len(registros) - 1:
                if args.ritmo == "real":
                    time.sleep(
                        espera_real(
                            registro["timestamp"],
                            registros[i + 1]["timestamp"],
                            args.aceleracao,
                        )
                    )
                else:
                    time.sleep(args.intervalo / args.aceleracao)
        total = len(registros)
    else:
        for i in range(args.n):
            producer.send(KAFKA_TOPIC, gerar_registro(i))
            if i < args.n - 1:
                time.sleep(args.intervalo / args.aceleracao)
        total = args.n
    producer.flush()
    if args.verboso:
        print("enviados:", total)


if __name__ == "__main__":
    main()