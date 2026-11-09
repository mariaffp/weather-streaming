# Arquitetura

Projeto acadêmico experimental de Sistemas Distribuídos para monitoramento de dados meteorológicos da Região dos Lagos (RJ), com foco em Rio das Ostras. Não é um sistema oficial de previsão.

## Fluxo previsto

Base meteorológica -> simulador (producer) -> Kafka -> Spark Structured Streaming -> pré-processamento -> análise -> ML.

## Já implementado

- `docker-compose.yml`: Kafka em modo KRaft, um broker para ambiente de estudante.
- `src/config.py`: endereço do Kafka e nome do tópico, fonte única para producer e consumer.
- `src/producer.py`: envia uma mensagem de teste ao tópico.
- `src/consumer.py`: lê o tópico e imprime as mensagens, para validar que o envio funciona.
- `tests/test_config.py`: verifica que as configurações do Kafka existem e são strings não vazias.

## Ainda não existe

- Análise da base meteorológica e definição do schema.
- Simulador real lendo registros da base.
- Spark Structured Streaming (`src/streaming.py` está vazio).
- Pré-processamento e análise.
- Modelo de ML (`src/ml.py` está vazio).
