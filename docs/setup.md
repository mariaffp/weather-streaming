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

Todos os comandos deste guia partem da raiz do projeto (a pasta com o `docker-compose.yml`). No Windows, clone dentro do filesystem do Linux (por exemplo, na sua home `~`), não em `/mnt/c`.

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

## 7. Teste: Spark

Com o Kafka no ar (se o teste anterior foi rodado, recrie com `docker compose down && docker compose up -d` e espere uns 10 a 15 segundos, senão o Spark mostra as mensagens antigas por causa do `startingOffsets=earliest`). Terminal 2:

```bash
python3 -m src.producer --n 5 --intervalo 0.2
```

Terminal 3, em uma linha só:

```bash
PYTHONPATH=. spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.3.0 src/streaming_kafka.py
```

Esperado: um `Batch: 0` com tabela de 9 colunas e 5 linhas; `Ctrl+C` encerra. O primeiro run demora alguns minutos e gera muito log. O producer deve rodar antes do Spark, para o tópico existir.

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
