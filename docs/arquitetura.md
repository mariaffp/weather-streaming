# Arquitetura

Projeto acadêmico experimental de Sistemas Distribuídos para monitoramento de dados meteorológicos da Região dos Lagos (RJ), com foco em Rio das Ostras. Não é um sistema oficial de previsão.

## Fluxo previsto

Base meteorológica -> simulador (producer) -> Kafka -> Spark Structured Streaming -> pré-processamento -> análise -> ML.

## Já implementado

- `docker-compose.yml`: Kafka em modo KRaft, um broker para ambiente de estudante.
- `src/config.py`: endereço do Kafka e nome do tópico, fonte única para producer, consumer e Spark.
- `src/synthetic_schema.py`: schema provisório dos registros de teste, definido num único lugar (colunas, tipos em `TIPOS`, faixas de sorteio e cidades).
- `src/synthetic_simulator.py`: gera registros sintéticos a partir do schema provisório, só para validar o fluxo.
- `src/producer.py`: envia N registros sintéticos em JSON com `--n`, `--intervalo` e `--aceleracao` configuráveis por linha de comando.
- `src/consumer.py`: exibe uma linha por registro (tópico, partição, offset e pares `chave=valor`), sem conhecer as colunas.
- `src/streaming_kafka.py`: lê o tópico com Spark Structured Streaming e mostra os registros no console, com o schema derivado de `TIPOS` (`startingOffsets=earliest`, sem checkpoint).
- Arquivos do grupo com fonte de arquivos: `src/streaming.py` (exploração em lote de 100 registros gerados em memória) e `src/streaming_arquivos.py` (Structured Streaming lendo JSON de `data/entrada/`, com validação, janelas de 1h, sinks Parquet e checkpoints), com `src/gerar_lote.py` e `src/consultar_estatisticas.py` de apoio. O `status_projeto.md` está em revisão pelo grupo.
- `tests/test_config.py`: verifica que as configurações do Kafka existem e são strings não vazias.
- `tests/test_synthetic.py`: verifica que o registro gerado segue o schema, que vem marcado como sintético e que a formatação do consumer funciona.

O schema provisório foi escolhido para teste do fluxo e não tem relação com a base real, ainda não analisada. As cinco colunas numéricas espelham as variáveis que o README declara como escopo do projeto (temperatura, umidade, pressão, precipitação e vento); os valores são sorteados sem nenhum significado meteorológico. Os tipos Spark de cada coluna estão em `TIPOS`, sem importar PySpark.

## Ainda não existe

Com os dados sintéticos atuais:

- Ligação do Kafka à lógica de validação, agregação e Parquet do grupo (`streaming_arquivos.py` hoje só lê arquivos de `data/entrada/`).
- Timestamp como tipo de tempo com watermark no caminho Kafka (hoje chega como string no console).
- Tratamento de JSON inválido no caminho Kafka (mensagem malformada hoje gera linha nula silenciosa).
- Checkpoint da fonte Kafka (hoje, com `earliest` e sem checkpoint, cada restart relê o tópico inteiro).
- Correção dos bloqueios no código do grupo: schema DDL hardcoded divergente de `TIPOS`, variável inexistente em `streaming_arquivos.py:136` e `gerar_lote.py` escrevendo fora de `data/entrada/`.
- Testes da integração Kafka-Spark (consistência `TIPOS`↔`COLUNAS`, leitura do tópico).

Dependendo dos dados reais do INMET:

- Análise da base meteorológica e definição do schema real (o schema atual é provisório e será substituído).
- Simulador real lendo registros da base.
- Modelo de ML (`src/ml.py` está vazio).
