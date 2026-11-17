# Predição da Produtividade da Safra de Soja no Rio Grande do Sul

Projeto de **Inteligência Artificial (2026)** — Faculdade de Computação e
Informática (FCI) · Universidade Presbiteriana Mackenzie.

**Professor:** Prof. Dr. Leandro Zerbinatti

## Integrantes

| Nome | RA | E-mail |
|---|---|---|
| Gabriel Bello | 10416808 | 10416808@mackenzista.com.br |
| Pedro Giovannini Andrade | 10425498 | 10425498@mackenzista.com.br |

## Objetivo

Desenvolver e avaliar uma abordagem de aprendizado de máquina capaz de prever
antecipadamente a produtividade municipal da soja no Rio Grande do Sul e
sinalizar o risco de o rendimento ficar abaixo da referência histórica de cada
município. **Opção: Framework** (Python + pandas/NumPy + Matplotlib + scikit-learn).

## Resultados principais (N2)

Validação temporal — treino ≤ 2018, teste 2019–2023 (250 obs.).

| Modelo | MAE (kg/ha) | RMSE (kg/ha) | R² |
|---|---|---|---|
| Baseline — média histórica | 907,6 | 1.004,0 | 0,10 |
| Baseline — safra anterior | 1.195,9 | 1.476,4 | −0,96 |
| Ridge | 758,0 | 893,7 | 0,28 |
| Random Forest | 650,9 | 850,7 | 0,35 |
| **Gradient Boosting** | **598,2** | **771,0** | **0,47** |

- Atributo mais importante (RF): **precipitação acumulada na janela
  reprodutiva dez–fev** (≈ 51% da importância).
- Indicador de risco de quebra (rendimento < média histórica):
  **acurácia 77,6%** e **recall 97%** na classe "risco".

## Estrutura do repositório

```
.
├── README.md
├── relatorio/
│   ├── Relatorio_IA_N1_Soja_RS.docx       Relatório da N1
│   └── Relatorio_IA_N2_Soja_RS.docx       Relatório da N2 (entrega 2º bim.)
├── notebooks/
│   ├── 01_analise_exploratoria_soja_rs.ipynb
│   └── 02_modelagem_soja_rs.ipynb
├── src/
│   ├── analise_exploratoria_soja_rs.py    Script N1
│   ├── 02_build_features.py               Atributos agrometeorológicos N2
│   └── 03_train_models.py                 Treino + avaliação + gráficos N2
├── dados/
│   ├── README.md
│   ├── sidra_1612_soja_rs_bruto.csv
│   ├── sidra_1612_soja_rs_preparado.csv
│   ├── oni_nino34.csv
│   ├── base_soja_rs_N1.csv                Base N1 (PAM + ONI)
│   ├── centroides_rs_top50.csv            50 municípios selecionados
│   ├── nasa_power_rs_top50.csv.gz         NASA POWER diário 2000-2023
│   ├── base_soja_rs_N2.csv                Base final com features climáticas
│   ├── metricas_modelos.csv               Métricas em teste
│   └── relatorio_risco.txt                Matriz de confusão do indicador
└── figuras/
    ├── 01_cobertura_por_ano.png  ... 06_enso_vs_rendimento.png   (N1)
    ├── 07_comparacao_modelos.png
    ├── 08_obs_vs_previsto.png
    ├── 09_mae_por_safra.png
    ├── 10_importancia_rf.png
    └── 11_matriz_risco.png
```

## Como reproduzir

1. Dependências (Python 3.9+):
   ```bash
   pip install pandas numpy matplotlib seaborn requests jupyter scikit-learn
   ```
2. Pipeline completo:
   ```bash
   # N1 — EDA
   python src/analise_exploratoria_soja_rs.py

   # N2 — integração climática + modelagem
   python src/02_build_features.py
   python src/03_train_models.py
   ```
3. O arquivo `dados/nasa_power_rs_top50.csv.gz` já está versionado; para
   regerá-lo do zero, rodar o download descrito na seção 5 do relatório N2.

## Bases de dados

- **PAM/IBGE — Tabela 1612** (SIDRA via API): rendimento, área e produção
  da soja por município do RS, 2000-2023.
- **NOAA/CPC — Oceanic Niño Index (ONI)**: sinal ENOS trimestral.
- **NASA POWER** (ponto diário): precipitação (PRECTOTCORR), temperatura
  (T2M, T2M_MIN, T2M_MAX), radiação (ALLSKY_SFC_SW_DWN) e umidade (RH2M)
  nos centroides dos 50 maiores produtores — 2000-2023.
- **IBGE / centroides municipais** (agregador `kelvins/Municipios-Brasileiros`):
  chave espacial para consulta ao NASA POWER.
- **INMET / BDMEP**: verificação cruzada qualitativa das variáveis climáticas
  (seção 5.3 do relatório).

Descrição detalhada em [`dados/README.md`](dados/README.md).

## Aspectos éticos

O projeto utiliza **exclusivamente dados públicos e agregados em nível
municipal**, sem dados pessoais. O indicador de risco de quebra de safra
**não deve ser interpretado como recomendação automática** de plantio,
crédito, seguro ou comercialização — decisões com impacto econômico devem
manter avaliação humana e informações agronômicas locais. Todo o pipeline
(bases, tratamento e parâmetros dos modelos) é mantido neste repositório
para permitir auditoria e reprodução.

## Licença dos dados

Os dados originais permanecem sob as licenças e termos de uso das respectivas
fontes públicas (IBGE, NOAA, NASA, INMET). Este repositório apenas redistribui
uma cópia estática para fins acadêmicos, com citação das fontes.
