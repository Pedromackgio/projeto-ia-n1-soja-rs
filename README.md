# Predição da Produtividade da Safra de Soja no Rio Grande do Sul

Projeto de **Inteligência Artificial (N1 · 2026)** — Faculdade de Computação e Informática (FCI) · Universidade Presbiteriana Mackenzie.

**Professor:** Prof. Dr. Leandro Zerbinatti

## Integrantes

| Nome | RA | E-mail |
|---|---|---|
| Gabriel Bello | 10416808 | 10416808@mackenzista.com.br |
| Pedro Giovannini Andrade | 10425498 | 10425498@mackenzista.com.br |

## Objetivo

Desenvolver e avaliar uma abordagem de aprendizado de máquina capaz de prever antecipadamente a produtividade municipal da soja no Rio Grande do Sul e sinalizar o risco de o rendimento ficar abaixo da referência histórica de cada município.

A **opção do projeto é Framework**: Python + pandas/NumPy + Matplotlib + scikit-learn.

## Estrutura do repositório

```
.
├── README.md                        Este arquivo
├── relatorio/
│   └── Relatorio_IA_N1_Soja_RS.docx  Relatório do projeto (template preenchido)
├── notebooks/
│   └── 01_analise_exploratoria_soja_rs.ipynb   Notebook completo da EDA
├── src/
│   └── analise_exploratoria_soja_rs.py  Fonte da análise (script com cabeçalho)
├── dados/
│   ├── README.md                    Descrição das bases utilizadas
│   ├── sidra_1612_soja_rs_bruto.csv Dados brutos da API SIDRA
│   ├── sidra_1612_soja_rs_preparado.csv  Dados PAM já preparados
│   ├── oni_nino34.csv               Índice ONI (NOAA) já formatado
│   └── base_soja_rs_N1.csv          Base final integrada da N1
└── figuras/                         Gráficos gerados pelo notebook
```

## Como reproduzir a análise

1. Requisitos (recomenda-se Python 3.9+):
   ```bash
   pip install pandas numpy matplotlib seaborn requests jupyter
   ```
2. Executar o notebook:
   ```bash
   jupyter notebook notebooks/01_analise_exploratoria_soja_rs.ipynb
   ```
   Alternativamente, o script equivalente pode ser executado com:
   ```bash
   python src/analise_exploratoria_soja_rs.py
   ```
3. Todos os arquivos gerados são salvos em `dados/` e `figuras/`.

## Dataset

Descrição detalhada em [`dados/README.md`](dados/README.md).

- **PAM/IBGE — Tabela 1612:** rendimento, área e produção da soja por município do RS entre 2000 e 2023 (fonte: SIDRA/IBGE via API).
- **NOAA/CPC — Oceanic Niño Index (ONI):** sinal ENOS trimestral, usado como atributo climático de grande escala.
- **Previstas para a N2:** NASA POWER (variáveis agrometeorológicas diárias por município), INMET (validação com estações observadas), IBGE (malhas municipais).

## Aspectos éticos

O projeto utiliza **exclusivamente dados públicos e agregados em nível municipal**, sem dados pessoais. Ainda assim, o indicador de risco de quebra de safra **não deve ser interpretado como recomendação automática de plantio, crédito, seguro ou comercialização** — decisões com impacto econômico devem manter avaliação humana e informações agronômicas locais. Todo o pipeline (bases, tratamento e parâmetros dos modelos) é mantido neste repositório para permitir auditoria e reprodução.

## Licença dos dados

Os dados originais permanecem sob as licenças e termos de uso das respectivas fontes públicas (IBGE, NOAA, NASA, INMET). Este repositório apenas redistribui uma cópia estática para fins acadêmicos, com citação das fontes.
