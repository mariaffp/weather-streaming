# Arquitetura

Projeto acadêmico experimental de Sistemas Distribuídos para monitoramento de dados meteorológicos da Região dos Lagos (RJ), com foco em Rio das Ostras. Não é um sistema oficial de previsão.

## Fluxo previsto

Base meteorológica -> simulador (producer) -> Kafka -> Spark Structured Streaming -> pré-processamento -> análise -> ML.

## Já implementado

- `docker-compose.yml`: Kafka em modo KRaft, um broker para ambiente de estudante.
- `src/config.py`: endereço do Kafka e nome do tópico, fonte única para producer e consumer.
- `src/synthetic_schema.py`: schema provisório dos registros de teste, definido num único lugar (colunas, faixas de sorteio e cidades).
- `src/synthetic_simulator.py`: gera registros sintéticos a partir do schema provisório, só para validar o fluxo.
- `src/producer.py`: envia N registros sintéticos com intervalo e aceleração configuráveis por linha de comando.
- `src/consumer.py`: exibe uma linha por registro (tópico, partição, offset e pares `chave=valor`), sem conhecer as colunas.
- `tests/test_config.py`: verifica que as configurações do Kafka existem e são strings não vazias.
- `tests/test_synthetic.py`: verifica que o registro gerado segue o schema, que vem marcado como sintético e que a formatação do consumer funciona.

O schema provisório foi escolhido para teste do fluxo e não tem relação com a base real, ainda não analisada. As cinco colunas numéricas espelham as variáveis que o README declara como escopo do projeto (temperatura, umidade, pressão, precipitação e vento); os valores são sorteados sem nenhum significado meteorológico.

## Ainda não existe

- Análise da base meteorológica e definição do schema real (o schema atual é provisório e será substituído).
- Simulador real lendo registros da base.
- Spark Structured Streaming (`src/streaming.py` está vazio).
- Pré-processamento e análise.
- Modelo de ML (`src/ml.py` está vazio).
