# Arquitetura

Projeto acadêmico experimental de Sistemas Distribuídos para monitoramento de dados meteorológicos da Região dos Lagos (RJ), com foco em Rio das Ostras. Não é um sistema oficial de previsão.

## Fluxo previsto

Base meteorológica -> simulador (producer) -> Kafka -> Spark Structured Streaming -> pré-processamento -> análise -> ML.

## Já implementado

- `docker-compose.yml`: Kafka em modo KRaft, um broker para ambiente de estudante.
- `src/config.py`: endereço do Kafka e nome do tópico, fonte única para producer, consumer e Spark.
- `src/synthetic_schema.py`: schema provisório dos registros de teste, definido num único lugar (colunas, tipos em `TIPOS`, faixas de sorteio e cidades).
- `src/synthetic_simulator.py`: gera registros sintéticos a partir do schema provisório, só para validar o fluxo.
- `src/inmet_schema.py`: schema dos registros reais (colunas, tipos em `TIPOS`, mapeamento dos cabeçalhos do CSV).
- `src/inmet_reader.py`: lê os CSVs do INMET em Latin-1 e devolve registros ordenados por timestamp e estação, com valor vazio virando nulo.
- `src/validacao.py`: regras puras (faixas, agregações, chave de agrupamento por fonte) e classificação em malformado/inválido/válido, sem PySpark.
- `src/streaming_kafka_processado.py`: lê o tópico com `--fonte`, converte o timestamp, classifica, agrega por dia/estação e grava Parquet em `data/processed`, com checkpoints próprios.
- `src/consultar_processados.py`: mostra contagem, schema e amostra das três saídas, sem escrever nada.
- `src/producer.py`: envia registros sintéticos ou reais (INMET) em JSON, com `--n`, `--intervalo`, `--aceleracao`, `--fonte`, `--estacao`, `--inicio`, `--ritmo` e `--verboso`.
- `src/consumer.py`: exibe uma linha por registro (tópico, partição, offset e pares `chave=valor`), sem conhecer as colunas.
- `src/streaming_kafka.py`: lê o tópico com Spark Structured Streaming e mostra os registros no console, com o schema derivado de `TIPOS` (`startingOffsets=earliest`, sem checkpoint). Aceita `--fonte` e imprime uma segunda tabela só com linhas de origem divergente (o nome `origem_divergente` aparece só nos logs e na interface web).
- Arquivos do grupo com fonte de arquivos: `src/streaming.py` (exploração em lote de 100 registros gerados em memória) e `src/streaming_arquivos.py` (Structured Streaming lendo JSON de `data/entrada/`, com validação, janelas de 1h, sinks Parquet e checkpoints), com `src/gerar_lote.py` e `src/consultar_estatisticas.py` de apoio. O `status_projeto.md` está em revisão pelo grupo.
- `tests/test_config.py`: verifica que as configurações do Kafka existem e são strings não vazias.
- `tests/test_synthetic.py`: verifica que o registro gerado segue o schema, que vem marcado como sintético e que a formatação do consumer funciona.
- `tests/test_inmet.py`: cobre o leitor com as amostras de `docs/amostras`, sem depender de `data/raw`.
- `tests/test_producer.py`, `tests/test_streaming_kafka.py`, `tests/test_validacao.py`: cobrem flags/filtros do producer, escolha de schema e regras de validação. Total: 53 testes via `python -m pytest tests/ -q`.

O schema provisório foi escolhido para teste do fluxo e não tem relação com a base real do INMET, analisada em `docs/dados-inmet.md`. As cinco colunas numéricas espelham as variáveis que o README declara como escopo do projeto (temperatura, umidade, pressão, precipitação e vento); os valores são sorteados sem nenhum significado meteorológico. Os tipos Spark de cada coluna estão em `TIPOS`, sem importar PySpark.

## Tratamento em fluxo

Cada registro é classificado sem imputar nada: **malformado** (JSON que não parseia, timestamp/`origem` nulos ou origem divergente da fonte), **inválido** (valor presente fora da faixa) ou **válido** (o resto, mesmo com nulos — ausente não é inválido). Faixas (limites inclusivos):

| Variável | Faixa |
|---|---|
| temperatura_c | [-10, 50] |
| umidade_pct | [0, 100] |
| pressao_hpa | [900, 1050] |
| precipitacao_mm | [0, 500] |
| vento_ms | [0, 60] |
| vento_kmh | [0, 250] |

Princípio: impossibilidade física ou falha de sensor, nunca "valores observados" — chuva forte passa (houve 62,2 mm/h na A627).

O timestamp vira tipo timestamp, com watermark de 10 minutos; janelas diárias tumbling por estação, alinhadas à meia-noite UTC. Agregados sobre válidos: média de temperatura/umidade/pressão, soma de precipitação, máximo do vento, contagem de registros e nulos por variável (nulos ignorados, nunca preenchidos). Saídas append em `data/processed/validos`, `data/processed/invalidos` (malformados junto, `categoria` distingue) e `data/processed/agregados`, com checkpoints em `data/checkpoints/processado_*`. Como o modo é append, cada janela diária só é emitida depois que o watermark passa seu fim: a última janela de um lote pequeno fica pendente.

## Interface para o ML (só descrição)

- `data/processed/validos`: 9 colunas do schema + `categoria`, com `timestamp` em tipo timestamp.
- `data/processed/agregados`: chave da estação, `inicio`/`fim` da janela, `{variável}_{media,soma,maximo}`, `total_registros`, `nulos_{variável}`.
- O dia é UTC (UTC-3 em Brasília); a soma diária de chuva com horas nulas é um limite inferior, sempre acompanhada de `nulos_precipitacao_mm`.
- Nada no pipeline classifica "chuva intensa" ou "instabilidade": isso é a etapa de ML, do grupo, ainda pendente.

## Ainda não existe

- Modelo de ML (`src/ml.py` está vazio) e sua integração ao fluxo de streaming.
- Ligação com a lógica do grupo (`streaming_arquivos.py`, independente e intocado), incluindo os bloqueios conhecidos: schema DDL hardcoded, variável inexistente em `streaming_arquivos.py:136` e `gerar_lote.py` escrevendo fora de `data/entrada/`.
