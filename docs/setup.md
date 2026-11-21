# Instalação e execução

Guia detalhado para rodar o projeto do zero. A seção 1 é separada por sistema; da seção 2 em diante, os passos são iguais no Windows (dentro do terminal do Ubuntu/WSL) e no Linux.

No Windows, rode todos os comandos no terminal do Ubuntu, não no PowerShell nem no CMD.

## 1. Pré-requisitos

### Windows

1. WSL2 com Ubuntu instalado (pela Microsoft Store).
2. Docker Desktop com a integração WSL ativada: Settings → Resources → WSL Integration → marcar o Ubuntu.
3. No terminal do Ubuntu, instale Python, git e Java 17:

```bash
sudo apt update
sudo apt install -y python3 python3-venv git openjdk-17-jdk
```

4. Confirme que está tudo disponível (ainda no terminal do Ubuntu):

```bash
python3 --version
docker --version
docker compose version
java -version
```

### Linux

1. Docker Engine com o plugin Compose, instalado pelo repositório oficial do Docker da sua distribuição. Depois ative o serviço:

```bash
sudo systemctl enable --now docker
```

Para rodar `docker` sem `sudo`, adicione seu usuário ao grupo `docker` e saia/entre de novo:

```bash
sudo usermod -aG docker $USER
```

2. Python, git e Java 17 (Debian/Ubuntu; em outras distribuições use o gerenciador de pacotes correspondente):

```bash
sudo apt update
sudo apt install -y python3 python3-venv git openjdk-17-jdk
```

3. Confirme que está tudo disponível:

```bash
python3 --version
docker --version
docker compose version
java -version
```

## 2. Clonar o repositório

```bash
git clone https://github.com/mariaffp/weather-streaming
cd weather-streaming
```

Todos os comandos deste guia partem da raiz do projeto (a pasta com o `docker-compose.yml`). No Windows, clone dentro do filesystem do Linux (por exemplo, na sua home `~`), não em `/mnt/c`. O clone já traz os 4 CSVs em `data/raw/inmet`, sem precisar copiar nada.

## 3. Criar e ativar o ambiente virtual

O nome precisa ser exatamente `.venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Com o ambiente ativo, o prompt mostra `(.venv)` no início da linha. Repita o `source` em cada terminal novo que for usar.

## 4. Instalar as dependências

```bash
pip install -r requirements.txt
```

Isso traz o `pyspark==4.3.0` e as demais dependências, incluindo o `pytest` para os testes.

## 5. Subir o Kafka

```bash
docker compose up -d
docker ps
```

O `docker ps` deve listar o container `kafka` com status `Up`. Espere uns 10 a 15 segundos antes de usar, para o broker ficar pronto. Para parar depois: `docker compose down`.

## 6. Teste: producer + consumer

Antes do teste, derrube e suba o Kafka para limpar a mensagem antiga. Sem isso, o consumer mostra `{'mensagem': 'teste'}` antes dos registros novos.

```bash
docker compose down && docker compose up -d
```

Espere uns 10 a 15 segundos o broker ficar pronto. Use 3 terminais, todos na raiz do projeto e com o `.venv` ativado.

**Terminal 1 — Kafka:** confirma que o broker está no ar.

```bash
docker ps
```

Deve aparecer uma linha com o container `kafka`, status `Up` e a porta `9092`.

**Terminal 2 — consumer:** abre o consumidor e deixa rodando, aguardando mensagens.

```bash
python3 -m src.consumer
```

Nada aparece de imediato: o comando fica bloqueado esperando. Depois que o producer enviar (passo seguinte), aparece uma linha por registro, assim:

```text
meteorologia 0 0 id_registro=0 timestamp=2026-11-15T12:00:00+00:00 cidade=Rio das Ostras temperatura_c=27.3 umidade_pct=68.2 pressao_hpa=1012.4 precipitacao_mm=3.1 vento_kmh=22.5 origem=sintetico
```

Os números variam a cada execução, pois são sorteados. Encerre com `Ctrl+C` quando quiser.

**Terminal 3 — producer:** envia N registros sintéticos e termina.

```bash
python3 -m src.producer --n 10 --intervalo 1 --aceleracao 1
```

Sem argumentos, usa os mesmos valores (10 registros, intervalo de 1s, aceleração 1). Não imprime nada em caso de sucesso, só devolve o prompt. Os registros aparecem no Terminal 2.

## 7. Producer com fonte INMET

Flags do producer (conferidas em `src/producer.py`): `--n` (default 10), `--intervalo` (1.0), `--aceleracao` (1.0), `--fonte` (`sintetico` ou `inmet`, default `sintetico`), `--estacao` (código, repetível), `--inicio` (data `AAAA-MM-DD` ou timestamp ISO em UTC), `--ritmo` (`fixo` ou `real`), `--verboso` (imprime `enviados: N` no fim). `--estacao`, `--inicio` e `--ritmo` exigem `--fonte inmet` e dão erro claro sem ela. No ritmo real, a espera entre envios é a diferença real entre timestamps dividida por `--aceleracao` (com 3600, 1h de dados dura 1s) e o `--intervalo` é ignorado.

Com o Kafka zerado e o consumer ligado:

```bash
python3 -m src.producer --fonte inmet --n 8
```

Esperado: 8 linhas, horas `2025-01-01T00:00` e `01:00`, 4 estações em ordem de código; ausente aparece como `=None` (no fio vai `null`).

Ritmo real acelerado, 2 estações, 100 registros:

```bash
python3 -m src.producer --fonte inmet --estacao A607 --estacao A608 --n 100 --ritmo real --aceleracao 3600
```

Esperado: 100 linhas em cerca de 50 segundos.

## 8. Teste: Spark

Com o Kafka no ar (se o teste anterior foi rodado, recrie com `docker compose down && docker compose up -d` e espere uns 10 a 15 segundos, senão o Spark mostra as mensagens antigas por causa do `startingOffsets=earliest`). Terminal 2:

```bash
python3 -m src.producer --n 5 --intervalo 0.2
```

Terminal 3, em uma linha só:

```bash
PYTHONPATH=. spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.3.0 src/streaming_kafka.py
```

Esperado: um `Batch: 0` com tabela de 9 colunas e 5 linhas; `Ctrl+C` encerra. O primeiro run demora alguns minutos e gera muito log. O producer deve rodar antes do Spark, para o tópico existir.

O Spark aceita `--fonte inmet` no fim do comando (`... src/streaming_kafka.py --fonte inmet`). Regra prática: producer e Spark precisam usar a mesma fonte. Se a fonte estiver trocada, o console imprime uma segunda tabela idêntica, só com as linhas de origem divergente; com a fonte certa, essa segunda tabela sai vazia. O nome da consulta (`origem_divergente`) não aparece no console: só nos logs e na interface web do Spark.

Validado manualmente: (a) producer `--fonte inmet --n 8` com Spark `--fonte inmet` — 9 colunas reais, `vento_ms` nulo nas A607, segunda tabela vazia; (b) sintético dos dois lados — igual a hoje, segunda tabela vazia. Observado: (c) producer inmet com Spark sem `--fonte` — tabela principal com `id_registro`, `cidade` e `vento_kmh` nulos (as colunas de mesmo nome nos dois schemas saem preenchidas, com `origem=inmet`) mais a segunda tabela com as mesmas linhas.

## 9. Demo de ponta a ponta (fluxo com Parquet)

Ordem, com Kafka e saídas zerados (o reset abaixo também é obrigatório antes de cada reexecução):

1. Kafka limpo: `docker compose down && docker compose up -d`, esperar 10 a 15 segundos.
2. Reset das saídas (rode a partir da raiz do projeto; apaga só o gerado por este job):

```bash
rm -rf data/processed/validos data/processed/invalidos data/processed/agregados data/checkpoints/processado_validos data/checkpoints/processado_invalidos data/checkpoints/processado_agregados
```

3. Producer: `python3 -m src.producer --fonte inmet --estacao A607 --estacao A608 --n 100 --ritmo real --aceleracao 3600` (cerca de 50 segundos).
4. Spark, em uma linha só:

```bash
PYTHONPATH=. spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.3.0 src/streaming_kafka_processado.py --fonte inmet
```

5. Esperar ~30 s após o producer terminar, encerrar com `Ctrl+C` e conferir:

```bash
PYTHONPATH=. spark-submit src/consultar_processados.py
```

Esperado: `validos=100`, `invalidos` vazio (a mensagem de falha de leitura é normal aqui), `agregados=4` (2 dias × 2 estações, 24 registros cada). A janela parcial do dia 3 não aparece: com `append` + watermark, cada janela diária só é emitida depois que o watermark passa seu fim, então a última janela de um lote pequeno fica pendente. Reexecutar sem o reset duplica linhas no `append`; depois de `docker compose down`, o checkpoint antigo fica fora de sincronia e precisa ser apagado junto. `data/processados` e `data/checkpoints/*_parquet` pertencem ao código do grupo — não apague.

## Problemas comuns

**`python: command not found`** — o comando é `python3`, não `python`. Use `python3 -m venv .venv`, `python3 -m src.producer` etc. No Windows, confira também que você está no terminal do Ubuntu, não no PowerShell.

**venv criado com nome errado** — se a pasta foi criada como `venv`, `env` ou outro nome, ela não está coberta pelo `.gitignore` e pode acabar indo para o git. O nome deve ser `.venv`. Para corrigir: `rm -rf venv` (ou o nome errado) e refazer o passo 3.

**`docker: command not found`** — no Windows, a integração WSL não está ativa: no Docker Desktop, abra Settings → Resources → WSL Integration e marque o Ubuntu; depois feche e reabra o terminal do Ubuntu. No Linux, o Docker Engine (ou o plugin Compose, se o erro for só no `docker compose`) não está instalado.

**`permission denied` ao rodar `docker` (Linux)** — seu usuário não está no grupo `docker`. Rode `sudo usermod -aG docker $USER`, saia e entre de novo, ou use `sudo` antes dos comandos `docker`.

**Erro `ModuleNotFoundError: No module named 'src'`** — o comando foi rodado fora da raiz do projeto. Volte para a pasta clonada (`cd weather-streaming`, onde está o `docker-compose.yml`) e rode de novo.

**Consumer sem receber nada** — verifique nesta ordem: o container `kafka` está `Up` no `docker ps`? O producer rodou sem erro no Terminal 3? O consumer foi iniciado da raiz do projeto com o `.venv` ativado? Aguarde alguns segundos após enviar. Se ainda assim não chegar, pare o consumer com `Ctrl+C` e rode de novo: ele lê desde o início do tópico.

**Producer falha com `ValueError: Invalid file object`** — costuma indicar que o broker ainda está iniciando; espere uns segundos e tente de novo.

**`java: command not found`** — o Java 17 não está instalado. Rode `sudo apt install openjdk-17-jdk` e confira com `java -version`.

**Falha ao baixar o conector no `spark-submit`** — o primeiro run precisa de internet para buscar o pacote `spark-sql-kafka-0-10_2.13:4.3.0` no Maven. Confira a conexão e rode de novo; o erro aparece no log do Spark.

**Parquet com linhas duplicadas** — o job foi reexecutado sem o reset do passo 2 da seção 9. O sink `append` soma; apague saídas e checkpoints e rode de novo.

**Spark falha com erro de offsets após recriar o Kafka** — o `docker compose down` zera o tópico mas o checkpoint lembra offsets antigos. Apague os checkpoints deste job (mesmo comando do passo 2) e rode de novo.

**Timestamps exibidos deslocados** — esperado, ainda não observado: o fuso da sessão Spark não é fixado, então a exibição pode seguir o fuso da máquina, embora a janela diária seja alinhada ao dia UTC.
