# Dados reais do INMET

Resumo verificado dos arquivos em `data/raw/inmet/` (versionados no Git). Período: 2025. Nada aqui foi corrigido nem convertido.

## Arquivos

| Código | Estação | Tamanho | Lat, Lon | Alt |
|---|---|---|---|---|
| A607 | CAMPOS DOS GOYTACAZES | 792.402 B | -21,71, -41,34 | 17 |
| A608 | MACAE | 817.278 B | -22,38, -41,81 | 28 |
| A620 | CAMPOS DOS GOYTACAZES - SAO TOME | 811.537 B | -22,04, -41,05 | 7 |
| A627 | NITEROI | 838.953 B | -22,87, -43,10 | 6 |

Todas REGIAO SE, UF RJ. Fundações como escritas: 25/09/06, 22/09/06, 13/06/08, 13/07/18. Cada arquivo tem 8.769 linhas: 8 de metadados + 1 cabeçalho + 8.760 dados.

## Formato

- 8 linhas `CHAVE:;valor`, depois 1 linha de cabeçalho (idêntico nos 4 arquivos).
- Separador `;`, decimal `,`, quebra LF, sem BOM.
- Codificação original Latin-1 (ISO-8859): UTF-8 falha no Ç. O leitor precisa abrir com Latin-1.
- Data `AAAA/MM/DD`, hora `HHMM UTC`. Fuso "UTC" escrito na coluna.
- Cabeçalho e linhas terminam com `;` sobrando: 20º campo sempre vazio, descartar no parse.
- Decimais às vezes sem zero à esquerda (`PRECIPITAÇÃO ...,2`, `VENTO ...,8`).
- Ausente = campo vazio. Sem `-9999`, `NULL` ou `NA` como valor.

## Colunas

`Data`, `Hora UTC`, `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)`, `PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)`, `PRESSÃO ATMOSFERICA MAX.NA HORA ANT. (AUT) (mB)`, `PRESSÃO ATMOSFERICA MIN. NA HORA ANT. (AUT) (mB)`, `RADIACAO GLOBAL (Kj/m²)`, `TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)`, `TEMPERATURA DO PONTO DE ORVALHO (°C)`, `TEMPERATURA MÁXIMA NA HORA ANT. (AUT) (°C)`, `TEMPERATURA MÍNIMA NA HORA ANT. (AUT) (°C)`, `TEMPERATURA ORVALHO MAX. NA HORA ANT. (AUT) (°C)`, `TEMPERATURA ORVALHO MIN. NA HORA ANT. (AUT) (°C)`, `UMIDADE REL. MAX. NA HORA ANT. (AUT) (%)`, `UMIDADE REL. MIN. NA HORA ANT. (AUT) (%)`, `UMIDADE RELATIVA DO AR, HORARIA (%)`, `VENTO, DIREÇÃO HORARIA (gr) (° (gr))`, `VENTO, RAJADA MAXIMA (m/s)`, `VENTO, VELOCIDADE HORARIA (m/s)`.

Peculiaridades: `PRESSAO` sem acento numa coluna e `PRESSÃO` nas outras; pressão em `mB`; vento em `m/s`; direção com unidade duplicada no nome.

## Período e cobertura

1 registro/hora, 01/01/2025 00h → 31/12/2025 23h UTC, sem timestamps duplicados nem horários faltantes.

## Ausentes por arquivo

- A607: ~0,06% na maioria; radiação 46,29% (vazia de madrugada); vento 71,44% (vazio de 01/01 até 18/09 15h, normal depois).
- A608: ~4,8% na maioria, com bloco de 411h vazio (25/10 16h → 11/11 18h); radiação 49,24% (vazia de madrugada).
- A620: ~4,9% na maioria, com bloco de 392h vazio (03/10 16h → 19/10 23h); orvalho ~10,7%; umidade 16–23%; radiação só 4,86% (registra a noite inteira, mínimo 0,0).
- A627: ~0,4% na maioria, em falhas isoladas de 1h e um bloco de 7h; radiação 46,43% (vazia de madrugada).
- 22/12 20h e 23/12 09h estão totalmente vazias nas 4 estações ao mesmo tempo.

## Suspeitos (observação, sem corrigir)

- A620: ponto de orvalho acima do bulbo seco em 843 linhas (9,6%); umidade cravada em 100,0.
- A627: orvalho até −4,2 °C, máxima até 42,2 °C, umidade mínima 10%, chuva de 62,2 mm/h.
- Máximas de chuva: 31,6 (A607), 25,8 (A608), 33,6 (A620), 62,2 (A627) mm/h.
- Nenhum negativo, pressão fora de 900–1050, rajada abaixo da velocidade ou direção fora de 0–360.

## Cobertura da Região dos Lagos

Fato: nenhuma estação é de Rio das Ostras nem de Cabo Frio. Macaé (A608) é a mais próxima citada nos arquivos. As 4 estações entram no projeto, com código e nome da estação como campos do registro.

## Colunas escolhidas (uma por variável, as horárias)

- Temperatura: `TEMPERATURA DO AR - BULBO SECO, HORARIA (°C)`
- Umidade: `UMIDADE RELATIVA DO AR, HORARIA (%)`
- Pressão: `PRESSAO ATMOSFERICA AO NIVEL DA ESTACAO, HORARIA (mB)`
- Precipitação: `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)`
- Vento: `VENTO, VELOCIDADE HORARIA (m/s)`

Sem conversão de valores: mB e hPa são numericamente iguais e o vento fica em m/s. Nomes normalizados ficam para a Etapa 2.

## Amostras

`docs/amostras/` tem 1 arquivo por estação (`A607.CSV`, `A608.CSV`, `A620.CSV`, `A627.CSV`), cada um com as 8 linhas de metadados + cabeçalho + 3 linhas de dados, mantidos na codificação original Latin-1 para os testes exercitarem o formato real (~4,3 KB no total):

- A607: 01/01 2300 (precipitação `,2`), 18/09 1300 (linha vazia), 18/09 1800 (completa).
- A608: 01/01 0100 (vento `,8`), 01/07 1000 (completa), 03/07 2100 (linha vazia).
- A620: 01/01 0300 (vento `,5`), 21/01 1200 (linha vazia), 01/07 1300 (completa).
- A627: 01/01 0100 (vento `,7`), 21/01 1200 (linha vazia), 01/07 1000 (completa).
