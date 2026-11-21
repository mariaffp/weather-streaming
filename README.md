# Weather Streaming

Sistema de monitoramento e análise de dados meteorológicos da Região dos Lagos (RJ), utilizando processamento de dados em fluxo e Machine Learning.

## Sobre o projeto

Este projeto é desenvolvido como parte da disciplina de Sistemas Distribuídos.

A proposta é construir uma aplicação capaz de processar dados meteorológicos continuamente, analisando variáveis como temperatura, umidade, pressão atmosférica, precipitação e velocidade do vento.

O foco é identificar padrões e condições meteorológicas associadas a chuvas intensas, tempestades e instabilidades na Região dos Lagos, com atenção especial a Rio das Ostras e municípios próximos.

## Objetivos

- Trabalhar com dados meteorológicos históricos.
- Simular a chegada contínua de registros meteorológicos.
- Utilizar Apache Kafka para ingestão e distribuição dos dados.
- Utilizar Apache Spark para processamento em streaming.
- Aplicar técnicas de Machine Learning para análise e identificação de padrões meteorológicos.
- Avaliar os resultados do processamento.

## Tecnologias

| Tecnologia | Finalidade |
|---|---|
| Python | Desenvolvimento da aplicação |
| Apache Kafka | Ingestão e distribuição de eventos |
| Apache Spark | Processamento distribuído e streaming |
| PySpark | Integração entre Python e Spark |
| Machine Learning | Análise e classificação de padrões |
| Git/GitHub | Versionamento e colaboração |

## Como executar

Pré-requisitos — **Windows:** WSL2 com Ubuntu + Docker Desktop com integração WSL ativada. **Linux:** Docker Engine com plugin Compose. Ambos: `python3` e `python3-venv` (no Windows, dentro do Ubuntu) e Java 17 (`sudo apt install openjdk-17-jdk`). O `pip install -r requirements.txt` traz o `pyspark==4.3.0`.

```bash
git clone https://github.com/mariaffp/weather-streaming
cd weather-streaming
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d
```

Guia completo por sistema, teste do producer + consumer e solução de problemas: [docs/setup.md](docs/setup.md).

## Colinha de testes

Em todos os terminais: estar na raiz do projeto e rodar `source .venv/bin/activate` antes.

**Teste Kafka (producer + consumer).** Terminal 1:

```bash
docker compose down && docker compose up -d
```

Esperar uns 10 a 15 segundos o broker ficar pronto. Terminal 2:

```bash
python -m src.consumer
```

Terminal 3:

```bash
python -m src.producer --n 5 --intervalo 0.2
```

Esperado: 5 linhas no consumer, com `id_registro` de 0 a 4 e `origem=sintetico`.

**Teste Spark.** Com o Kafka no ar — se o teste do Kafka foi rodado antes, recrie primeiro com `docker compose down && docker compose up -d` e espere uns 10 a 15 segundos, senão o Spark também mostra as mensagens do teste anterior por causa do `startingOffsets=earliest`. Terminal 2:

```bash
python -m src.producer --n 5 --intervalo 0.2
```

Terminal 3, em uma linha só:

```bash
PYTHONPATH=. spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.3.0 src/streaming_kafka.py
```

Esperado: um `Batch: 0` com tabela de 9 colunas e 5 linhas; `Ctrl+C` encerra. O primeiro run demora alguns minutos e gera muito log. O producer deve rodar antes do Spark, para o tópico existir.

Para derrubar tudo: `docker compose down`.

## Arquitetura proposta

O fluxo previsto para a aplicação é:

1. Base de dados meteorológicos.
2. Simulação da chegada dos registros.
3. Envio dos eventos ao Kafka.
4. Consumo e pré-processamento pelo Spark.
5. Aplicação de um modelo de Machine Learning.
6. Análise e apresentação dos resultados.

## Dados

A base meteorológica utilizada será documentada após a análise de sua origem, período, variáveis disponíveis e qualidade dos registros.

## Estrutura prevista

```text
weather-streaming/
│
├── data/
│   ├── raw/
│   └── processed/
│
├── src/
│   ├── config.py
│   ├── synthetic_schema.py
│   ├── synthetic_simulator.py
│   ├── producer.py
│   ├── consumer.py
│   ├── streaming_kafka.py
│   ├── streaming.py
│   ├── streaming_arquivos.py
│   ├── gerar_lote.py
│   ├── consultar_estatisticas.py
│   └── ml.py
│
├── tests/
│   ├── test_config.py
│   └── test_synthetic.py
│
├── docs/
│   ├── arquitetura.md
│   └── setup.md
│
├── docker-compose.yml
├── requirements.txt
├── status_projeto.md
├── .gitignore
└── README.md
```

`src/streaming.py` faz processamento em lote (exploração de 100 registros gerados em memória).

## Estado atual

Já funciona: Kafka em container via Docker Compose; `src/producer.py` envia registros sintéticos em JSON com `--n`, `--intervalo` e `--aceleracao`; `src/consumer.py` imprime os registros recebidos; `src/streaming_kafka.py` lê o tópico com Spark Structured Streaming e mostra os registros no console, com o schema derivado de `src/synthetic_schema.py` (`TIPOS`).

Os dados são sintéticos e provisórios, gerados por sorteio sem significado meteorológico. Ainda NÃO estão feitos: a análise da base real, a ligação do Kafka à lógica de validação/agregação/Parquet do grupo (`streaming_arquivos.py`), o pré-processamento definitivo e o ML.

## Status do projeto

Em desenvolvimento.

Etapas iniciais:
- [ ] Análise da base meteorológica.
- [ ] Definição das variáveis e do objetivo do modelo.
- [ ] Preparação dos dados.
- [x] Configuração do Kafka.
- [x] Implementação do simulador de dados (parcial: dados sintéticos provisórios).
- [x] Implementação do processamento com Spark (parcial: lê o tópico, ainda sem ligar à lógica do grupo).
- [ ] Treinamento do modelo de Machine Learning.
- [ ] Integração do modelo ao fluxo de streaming.
- [ ] Testes e avaliação dos resultados.

## Equipe

Projeto acadêmico desenvolvido em grupo para a disciplina de Sistemas Distribuídos.
