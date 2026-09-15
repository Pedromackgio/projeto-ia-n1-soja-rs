# Dataset — Predição da Produtividade de Soja no RS

Este diretório contém as bases capturadas e preparadas para o projeto. Todos os arquivos são derivados de **fontes públicas oficiais** e podem ser reproduzidos executando o notebook `notebooks/01_analise_exploratoria_soja_rs.ipynb`.

## Arquivos

| Arquivo | Descrição | Fonte |
|---|---|---|
| `sidra_1612_soja_rs_bruto.csv` | Resposta bruta da API SIDRA para a tabela 1612 (soja em grão, municípios do RS, 2000-2023). | IBGE/SIDRA — tabela 1612 |
| `sidra_1612_soja_rs_bruto.json` | Mesmo conteúdo em formato JSON (backup do retorno original). | IBGE/SIDRA |
| `sidra_1612_soja_rs_preparado.csv` | Base pivotada em formato `municipio × ano`, com colunas numéricas já limpas. | Derivado |
| `oni_bruto.txt` | Arquivo original do Oceanic Niño Index (formato texto NOAA). | NOAA/CPC |
| `oni_nino34.csv` | ONI convertido para CSV com coluna de fase ENOS (`El Nino`, `La Nina`, `Neutro`). | Derivado |
| `base_soja_rs_N1.csv` | **Base final da N1**: dados PAM + baselines históricas por município + sinal ENOS agregado por safra. | Integrado |

## Fonte principal — IBGE / SIDRA (tabela 1612)

**Endpoint utilizado:** `https://apisidra.ibge.gov.br/values/t/1612/n6/in%20n3%2043/v/<variáveis>/p/<ano>/c81/2713?formato=json`

- `n6` → nível municipal
- `in n3 43` → apenas municípios do estado do Rio Grande do Sul
- `c81/2713` → cultura **Soja (em grão)**
- Período: **2000–2023** (24 safras)

**Variáveis coletadas:**

| Código | Variável | Unidade |
|---|---|---|
| 109 | Área plantada | hectares |
| 216 | Área colhida | hectares |
| 214 | Quantidade produzida | toneladas |
| 112 | Rendimento médio da produção | kg/ha *(variável-alvo)* |
| 215 | Valor da produção | mil reais |

**Volume:** 59 640 registros brutos (5 variáveis × 497 municípios × 24 anos); após pivotar e limpar, 9 692 linhas no nível `município-safra`.

## Fonte auxiliar — NOAA / CPC (ONI)

**URL:** https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt

Série mensal (agrupada em janelas trimestrais móveis) do desvio de temperatura da região Niño 3.4. Para cada safra, foram calculadas a **média**, o **mínimo** e o **máximo** do ANOM entre os trimestres `OND`, `NDJ`, `DJF`, `JFM`, `FMA` — período que cobre o plantio, o florescimento e a colheita da soja no RS. A partir da média foi derivada a **fase dominante da safra**: `El Nino` (≥ +0,5°C), `La Nina` (≤ -0,5°C) e `Neutro`.

## Tratamentos aplicados

1. Renomeação das colunas do retorno SIDRA (`D1C → codigo_municipio`, `D2C → variavel_cod`, `V → valor`, etc.).
2. Substituição dos símbolos SIDRA `-`, `..`, `...`, `x` por `NaN`.
3. Conversão de tipos numéricos (`valor`, `ano`).
4. Pivot para uma linha por `município × ano`.
5. Cálculo, por município, da **média histórica expandida com deslocamento temporal** (`shift(1)`) — a média histórica de cada safra usa **exclusivamente safras anteriores**, evitando vazamento de informação.
6. Cálculo do rendimento da safra anterior (`rendimento_anterior`) sob a mesma lógica.
7. Merge com o ONI (chave: `safra` = ano de colheita).

## Notas de integridade

- A cobertura anual varia de 350 municípios (2000) a 435 (2023), acompanhando o avanço territorial da soja no RS. Ver `figuras/01_cobertura_por_ano.png`.
- 10 979 registros brutos vieram com símbolo `-` (indicando ausência de plantio/colheita); esses valores são preservados como `NaN`.
- A consistência entre `producao_t`, `area_colhida_ha` e `rendimento_kg_ha` é verificada no notebook (seção 4.5).

## Fontes previstas para a N2

| Fonte | Uso | URL |
|---|---|---|
| NASA POWER | Séries meteorológicas diárias (precipitação, temperatura, radiação, umidade) por município. | https://power.larc.nasa.gov/ |
| INMET / BDMEP | Validação das variáveis climáticas com estações observadas do RS. | https://portal.inmet.gov.br/ |
| IBGE (malhas) | Centroide e código IBGE de cada município para integração espacial. | https://portaldemapas.ibge.gov.br/ |
