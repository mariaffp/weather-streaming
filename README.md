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

Pré-requisitos — **Windows:** WSL2 com Ubuntu + Docker Desktop com integração WSL ativada. **Linux:** Docker Engine com plugin Compose. Ambos: `python3` e `python3-venv` (no Windows, dentro do Ubuntu).

```bash
git clone https://github.com/mariaffp/weather-streaming
cd weather-streaming
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d
```

Guia completo por sistema, teste do producer + consumer e solução de problemas: [docs/setup.md](docs/setup.md).

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
├── notebooks/
│
├── src/
│   ├── config.py
│   ├── producer.py
│   ├── consumer.py
│   ├── streaming.py
│   └── ml.py
│
├── tests/
│
├── docs/
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Status do projeto

Em desenvolvimento.

Etapas iniciais:
- [ ] Análise da base meteorológica.
- [ ] Definição das variáveis e do objetivo do modelo.
- [ ] Preparação dos dados.
- [ ] Configuração do Kafka.
- [ ] Implementação do simulador de dados.
- [ ] Implementação do processamento com Spark.
- [ ] Treinamento do modelo de Machine Learning.
- [ ] Integração do modelo ao fluxo de streaming.
- [ ] Testes e avaliação dos resultados.

## Equipe

Projeto acadêmico desenvolvido em grupo para a disciplina de Sistemas Distribuídos.
