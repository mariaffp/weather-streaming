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

**Teste producer INMET.** Com o Kafka zerado (`docker compose down && docker compose up -d`, 10–15 s). Terminal 2:

```bash
python -m src.consumer
```

Terminal 3:

```bash
python -m src.producer --fonte inmet --n 8
```

Esperado: 8 linhas, horas `2025-01-01T00:00` e `01:00`, 4 estações em ordem de código; ausente aparece como `=None`.

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

**Testes unitários.** Na raiz, com o `.venv` ativo:

```bash
python -m pytest tests/ -q
```

Esperado: `53 passed`. O `requirements.txt` está congelado com `pip freeze`.

## Arquitetura proposta

O fluxo previsto para a aplicação é:

1. Base de dados meteorológicos.
2. Simulação da chegada dos registros.
3. Envio dos eventos ao Kafka.
4. Consumo e pré-processamento pelo Spark.
5. Aplicação de um modelo de Machine Learning.
6. Análise e apresentação dos resultados.

## Dados

Dados reais do INMET: 4 estações (A607 Campos dos Goytacazes, A608 Macaé, A620 Campos - São Tomé, A627 Niterói), ano de 2025, 1 registro por hora (8.760 por estação, 35.040 no total). Formato: Latin-1, separador `;`, decimal com vírgula. Detalhes em [docs/dados-inmet.md](docs/dados-inmet.md).

Nenhuma estação é de Rio das Ostras nem de Cabo Frio; Macaé (A608) é a mais próxima citada nos arquivos.

Os 4 CSVs estão versionados em `data/raw/inmet/`: o clone já os traz. Outros arquivos do INMET colocados em `data/raw/` continuam ignorados pelo Git.

## Estrutura prevista

```text
weather-streaming/
│
├── data/
│   ├── raw/
│   │   └── inmet/ (4 CSVs do INMET, versionados)
│   └── processed/
│
├── src/
│   ├── config.py
│   ├── synthetic_schema.py
│   ├── synthetic_simulator.py
│   ├── inmet_schema.py
│   ├── inmet_reader.py
│   ├── validacao.py
│   ├── producer.py
│   ├── consumer.py
│   ├── streaming_kafka.py
│   ├── streaming_kafka_processado.py
│   ├── consultar_processados.py
│   ├── streaming.py
│   ├── streaming_arquivos.py
│   ├── gerar_lote.py
│   ├── consultar_estatisticas.py
│   └── ml.py
│
├── tests/
│   ├── test_config.py
│   ├── test_synthetic.py
│   ├── test_inmet.py
│   ├── test_producer.py
│   ├── test_streaming_kafka.py
│   └── test_validacao.py
│
├── docs/
│   ├── arquitetura.md
│   ├── setup.md
│   ├── dados-inmet.md
│   └── amostras/
│
├── docker-compose.yml
├── requirements.txt
├── status_projeto.md
├── .gitignore
└── README.md
```

`src/streaming.py` faz processamento em lote (exploração de 100 registros gerados em memória).

## Estado atual

Já funciona: Kafka em container via Docker Compose; `src/producer.py` envia registros sintéticos ou reais (INMET) em JSON; `src/consumer.py` imprime os registros recebidos; `src/streaming_kafka.py` lê o tópico com `--fonte` e acusa fonte trocada numa segunda tabela; `src/streaming_kafka_processado.py` classifica, agrega por dia/estação e grava Parquet em `data/processed`. Fluxo validado manualmente de ponta a ponta; 53 testes passam com `python -m pytest tests/ -q`. Regra prática: producer e Spark precisam usar a mesma fonte.

A base real do INMET está analisada ([docs/dados-inmet.md](docs/dados-inmet.md)). Ainda NÃO estão feitos: o modelo de ML e sua integração, e a ligação com a lógica do grupo (decisão: manter os dois caminhos; ponte Kafka→arquivos + variáveis novas; convergência depois). Nada no pipeline classifica "chuva intensa" ou "instabilidade": isso é a etapa de ML, do grupo, ainda pendente.

## Status do projeto

Em desenvolvimento.

Etapas iniciais:
- [x] Análise da base meteorológica (INMET 2025, ver docs/dados-inmet.md).
- [ ] Definição das variáveis e do objetivo do modelo.
- [ ] Preparação dos dados.
- [x] Configuração do Kafka.
- [x] Implementação do simulador de dados (parcial: dados sintéticos provisórios).
- [x] Implementação do processamento com Spark (lê com --fonte e proteção; Parquet pronto; ligação com o grupo pendente).
- [x] Leitor dos dados reais (validado nas 4 estações).
- [x] Producer com fonte real.
- [x] Spark com dados reais (validado manualmente).
- [x] Pré-processamento em fluxo (Parquet, validado manualmente).
- [ ] Ligação com a lógica do grupo (decisão: manter os dois caminhos; ponte Kafka→`data/entrada/` + variáveis novas no fluxo dela; `streaming_arquivos.py` segue intocado).
- [ ] Treinamento do modelo de Machine Learning.
- [ ] Integração do modelo ao fluxo de streaming.
- [ ] Testes e avaliação dos resultados.

## Equipe

Projeto acadêmico desenvolvido em grupo para a disciplina de Sistemas Distribuídos.
