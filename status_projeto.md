# Weather Streaming — Resumo da implementação e próximos passos

**Projeto:** `weather-streaming`  
**Etapa concluída:** Apache Spark / Structured Streaming com arquivos JSON  
**Último commit:** `23661f2` — `feat(spark): implementar pipeline meteorologico com structured streaming`  
**Próxima etapa:** Integração Kafka → Spark

## 1. Objetivo do projeto

O projeto tem como objetivo construir um pipeline de processamento de dados meteorológicos, capaz de receber medições, validar os registros, processá-los continuamente e gerar estatísticas que possam ser utilizadas posteriormente em análises e modelos de Machine Learning.

A arquitetura pretendida é:

**Simulador meteorológico → Kafka → Apache Spark → Armazenamento de dados processados → Análises / Machine Learning**

O projeto está sendo desenvolvido por etapas, para que cada componente possa ser testado individualmente antes da integração completa.

## 2. O que já foi implementado

### 2.1. Simulador de dados meteorológicos

O projeto já possui um simulador Python que gera medições sintéticas para três cidades:

- Macaé
- Rio das Ostras
- Cabo Frio

Cada registro contém:

| Campo | Descrição |
|---|---|
| `id_registro` | Identificador da medição |
| `timestamp` | Data e hora simuladas |
| `cidade` | Cidade da medição |
| `temperatura_c` | Temperatura |
| `umidade_pct` | Umidade relativa |
| `pressao_hpa` | Pressão atmosférica |
| `precipitacao_mm` | Precipitação |
| `vento_kmh` | Velocidade do vento |
| `origem` | Origem do registro |

O simulador utiliza intervalos de 10 minutos entre registros consecutivos, alternando as cidades. Assim, cada cidade recebe uma nova medição simulada a cada 30 minutos.

**Observação:** os valores são sintéticos, gerados a partir de faixas predefinidas. São adequados para testar o pipeline, mas ainda não representam uma série meteorológica realista para treinamento de modelos preditivos.

### 2.2. Processamento inicial com Spark

**Arquivo:** `src/streaming.py`

Implementamos uma primeira etapa de exploração de dados com PySpark, trabalhando com um DataFrame contendo 100 medições sintéticas.

As operações incluem:

- Cálculo de média, mediana e máximo da precipitação.
- Contagem de registros por cidade.
- Identificação de valores negativos ou ausentes.
- Distribuição de precipitação por faixas.
- Agrupamento de medições em janelas temporais de uma hora.

Essa etapa utiliza processamento em lote (*batch processing*), não streaming contínuo.

Sua finalidade foi validar as transformações e compreender as operações do Spark antes de passar ao Structured Streaming.

### 2.3. Ingestão contínua com Structured Streaming

**Arquivo:** `src/streaming_arquivos.py`

Implementamos um pipeline com o Spark Structured Streaming.

Nessa versão, o Spark monitora a pasta `data/entrada/`. Quando novos arquivos JSON são disponibilizados, o mecanismo de streaming pode processá-los em microbatches.

O processamento executa:

1. Leitura de arquivos JSON com esquema explícito.
2. Conversão do campo `timestamp` para o tipo temporal do Spark.
3. Validação dos registros.
4. Separação dos dados válidos e inválidos.
5. Agregações por cidade e por janela de uma hora.
6. Persistência dos resultados em formato Parquet.

A validação atualmente verifica principalmente se cidade, timestamp e precipitação estão preenchidos e se a precipitação não é negativa.

As informações são armazenadas em três destinos:

| Destino | Conteúdo |
|---|---|
| `data/processados/validos/` | Registros aprovados |
| `data/processados/invalidos/` | Registros reprovados |
| `data/processados/estatisticas/` | Estatísticas agregadas |

### 2.4. Estatísticas temporais

O pipeline calcula, por cidade e por janela de uma hora:

- Quantidade de medições.
- Precipitação média.
- Precipitação máxima.

As agregações utilizam o modo `update` do Structured Streaming.

Quando uma medição pertence a uma janela já existente, o Spark atualiza o resultado agregado daquela janela.

Utilizamos `foreachBatch` para salvar as atualizações em diretórios Parquet separados por identificador de microbatch.

### 2.5. Consulta dos resultados consolidados

**Arquivo:** `src/consultar_estatisticas.py`

Foi criado um script para consultar os arquivos Parquet de estatísticas.

Como uma mesma janela pode aparecer em diferentes microbatches, o script identifica a versão mais recente de cada combinação de cidade, início e fim da janela.

Isso permite obter uma visão consolidada das estatísticas, sem simplesmente somar resultados de atualizações anteriores.

### 2.6. Checkpoints e recuperação

Configuramos checkpoints independentes para as três consultas de streaming.

Os checkpoints ficam em `data/checkpoints/`.

Eles permitem que o Spark acompanhe o progresso do processamento e retome a leitura após uma interrupção, respeitando o estado registrado anteriormente.

**Esse mecanismo foi testado com a fonte de arquivos, mas ainda não foi validado em uma integração com Kafka.**

## 3. Testes realizados e resultados

Utilizamos arquivos JSON com registros sintéticos, incluindo um registro propositalmente inválido.

| Verificação | Resultado |
|---|---|
| Registros de entrada | 15 |
| Registros válidos | 14 |
| Registros inválidos | 1 |
| Agregações temporais | Funcionando |
| Persistência em Parquet | Funcionando |
| Consulta consolidada | Funcionando |
| Retomada utilizando checkpoints | Validada no teste local |

Também foi realizado um teste com um registro pertencente a uma janela temporal previamente processada, para verificar a atualização das estatísticas.

Ao reiniciar o processamento mantendo os checkpoints, os registros de entrada já processados não foram duplicados no teste realizado.

Esses resultados confirmam o funcionamento do protótipo com arquivos. Não representam ainda uma garantia de processamento exatamente uma vez para todas as futuras integrações e saídas.

## 4. Ambiente de execução

O desenvolvimento do módulo Spark foi realizado em Ubuntu, utilizando WSL2 no Windows.

Componentes utilizados:

- Apache Spark via PySpark 4.3.0.
- Java 21.
- Python no ambiente virtual do Ubuntu.
- Arquivos JSON como entrada.
- Parquet como formato de armazenamento.

O diretório do projeto no WSL2 é:

`/mnt/c/dev/git/weather-streaming`

Para iniciar o pipeline atual:

```bash
cd /mnt/c/dev/git/weather-streaming
~/venvs/weather-streaming/bin/python -m src.streaming_arquivos
```

Para consultar as estatísticas persistidas:

```bash
~/venvs/weather-streaming/bin/python -m src.consultar_estatisticas
```

Os diretórios de dados e checkpoints foram configurados para não serem versionados no Git.

Portanto, quem clonar o projeto precisará preparar os dados de teste e a estrutura de diretórios necessária.

## 5. Onde paramos no fluxo

**O módulo Spark está funcional com entrada via arquivos JSON, mas ainda não recebe eventos diretamente do Kafka.**

Fluxo implementado:

```text
Simulador Python
       |
       v
Arquivos JSON
       |
       v
data/entrada/
       |
       v
Spark Structured Streaming
       |
       +--> Validação dos registros
       |          |
       |          +--> Parquet: válidos
       |          |
       |          +--> Parquet: inválidos
       |
       +--> Janelas temporais de 1 hora
                  |
                  v
            Estatísticas Parquet
                  |
                  v
        Consulta e consolidação
```

**Fluxo que ainda precisamos integrar:**

```text
Simulador Python
       |
       v
Kafka Producer
       |
       v
     Kafka
       |
       v
Spark Structured Streaming
       |
       v
Validação e agregações
       |
       v
       Parquet
       |
       v
Análises / Machine Learning
```

A parte de Kafka possui arquivos próprios no repositório, incluindo `producer.py`, `consumer.py` e `docker-compose.yml`, mas suas alterações estão separadas do commit Spark.

Ainda precisamos conferir seu estado e validar a execução conjunta dos componentes.

## 6. Próximas atividades para a integrante do grupo

### Etapa A — Verificar a infraestrutura Kafka

Revisar os arquivos existentes:

- `docker-compose.yml`
- `src/producer.py`
- `src/consumer.py`
- `src/config.py`

Confirmar o endereço do broker, nome do tópico, formato das mensagens, configuração do produtor e funcionamento do consumidor de teste.

**Resultado esperado:** comprovar que o produtor publica registros meteorológicos no Kafka e que o consumidor consegue recebê-los.

### Etapa B — Conectar o Spark ao Kafka

Adaptar o pipeline para utilizar o Kafka como fonte de eventos.

O Spark deverá realizar a leitura com `readStream.format("kafka")`, utilizando o conector Kafka compatível com a versão do Spark.

Depois será necessário:

1. Converter o conteúdo recebido em `value` para texto.
2. Interpretar o JSON com o esquema meteorológico existente.
3. Recuperar os campos necessários.
4. Reutilizar as regras de validação e agregação.
5. Configurar checkpoints próprios para a nova fonte de streaming.

**Resultado esperado:** o Spark processar registros publicados no tópico Kafka sem depender da criação de novos arquivos na pasta `data/entrada/`.

### Etapa C — Executar um teste de ponta a ponta

Iniciar a infraestrutura Kafka, executar o produtor e iniciar o processamento Spark.

Validar:

- Publicação e recebimento das mensagens.
- Quantidade de registros processados.
- Separação entre dados válidos e inválidos.
- Atualização das estatísticas temporais.
- Armazenamento Parquet.
- Recuperação após reiniciar o processamento.
- Tratamento de mensagens inválidas.

**Resultado esperado:** demonstrar o funcionamento integrado de Kafka e Spark.

### Etapa D — Preparar a continuidade para Machine Learning

Após validar a integração:

- Definir quais variáveis e estatísticas serão utilizadas pelo modelo.
- Revisar a qualidade e a representatividade dos dados sintéticos.
- Estabelecer o objetivo do modelo preditivo.
- Preparar o conjunto de dados para treinamento e avaliação.

Essa etapa ainda não foi implementada.

## 7. Observações importantes para o trabalho em grupo

O último commit específico do Spark é:

`23661f2 — feat(spark): implementar pipeline meteorologico com structured streaming`

Ele contém os arquivos de processamento desenvolvidos e as alterações necessárias em `.gitignore` e `requirements.txt`.

Outras modificações relacionadas a Kafka, Docker, simulador, testes e documentação permanecem no diretório de trabalho e **não foram incluídas nesse commit**.

É importante conferir essas alterações antes de realizar novos commits, para evitar misturar o trabalho de diferentes integrantes.

Também é recomendável preservar a versão que lê arquivos JSON. Ela será útil como referência e para testes de regressão enquanto desenvolvemos a integração Kafka.

---

## Resumo para continuidade

**Concluído:** pipeline de processamento meteorológico em Spark Structured Streaming com entrada por arquivos JSON, validação, agregações temporais, persistência em Parquet e checkpoints.

**Ponto atual:** implementação Spark registrada no Git e validada localmente.

**Próxima tarefa prioritária:** verificar a infraestrutura Kafka existente e conectar seu tópico ao Spark Structured Streaming.

**Meta da próxima entrega:** executar um fluxo completo no qual o simulador publica dados no Kafka e o Spark os recebe, valida, agrega e persiste automaticamente.
