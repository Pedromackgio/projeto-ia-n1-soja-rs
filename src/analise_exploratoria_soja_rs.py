# =============================================================================
# Projeto : Predicao da Produtividade da Safra de Soja no Rio Grande do Sul
#           com Aprendizado de Maquina e Dados Agrometeorologicos
# Disciplina: Inteligencia Artificial - N1/2026
# Instituicao: Faculdade de Computacao e Informatica (FCI)
#              Universidade Presbiteriana Mackenzie
# Professor : Prof. Dr. Leandro Zerbinatti
#
# Integrantes:
#   - Gabriel Bello           - RA 10416808 - 10416808@mackenzista.com.br
#   - Pedro Giovannini Andrade - RA 10425498 - 10425498@mackenzista.com.br
#
# Sintese do conteudo:
#   Script equivalente ao notebook 01_analise_exploratoria_soja_rs.ipynb.
#   Realiza captura via API SIDRA (tabela 1612 - Soja em grao - municipios do RS),
#   preparacao dos dados (tratamento de simbolos SIDRA, pivot, tipagem),
#   analise exploratoria (cobertura, estatisticas, distribuicoes, evolucao,
#   correlacoes e valores extremos) e integracao com o Oceanic Nino Index (NOAA).
#
# Historico de alteracoes:
#   Data        | Autor                     | Descricao
#   ------------|---------------------------|--------------------------------------
#   2026-09-14  | Pedro Giovannini Andrade  | Versao inicial do script.
#   2026-09-14  | Gabriel Bello             | Revisao dos graficos e do tratamento
#                                             de valores ausentes.
# =============================================================================

import os
import io
import json
import time
import warnings

import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


warnings.filterwarnings("ignore")
sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.dpi"] = 100
pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 160)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "dados")
FIG_DIR = os.path.join(BASE_DIR, "figuras")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)


def baixar_sidra_1612(destino_csv: str) -> None:
    """Baixa a tabela 1612 (soja em grao) do SIDRA para todos os municipios do RS,
    ano a ano, entre 2000 e 2023, e concatena em um unico CSV."""
    if os.path.exists(destino_csv):
        print(f"[SIDRA] Arquivo ja existe: {destino_csv}")
        return

    variaveis = ["109", "216", "214", "112", "215"]
    anos = list(range(2000, 2024))
    header = None
    linhas = []

    for ano in anos:
        url = (
            "https://apisidra.ibge.gov.br/values/t/1612/n6/in%20n3%2043"
            f"/v/{','.join(variaveis)}/p/{ano}/c81/2713?formato=json"
        )
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        if header is None:
            header = data[0]
        linhas.extend(data[1:])
        print(f"[SIDRA] {ano}: {len(data)-1} registros | acumulado {len(linhas)}")
        time.sleep(0.4)

    pd.DataFrame(linhas).to_csv(destino_csv, index=False)
    print(f"[SIDRA] Salvo em: {destino_csv}")


def preparar_base_sidra(bruto_csv: str, saida_csv: str) -> pd.DataFrame:
    """Le o CSV bruto do SIDRA e devolve uma base pivotada municipio x ano."""
    df_raw = pd.read_csv(bruto_csv, dtype=str)

    renome = {
        "D1C": "codigo_municipio",
        "D1N": "municipio",
        "D2C": "variavel_cod",
        "D2N": "variavel_nome",
        "D3C": "ano",
        "V": "valor",
        "MN": "unidade",
    }
    df = df_raw.rename(columns=renome)[list(renome.values())]

    mapa_var = {
        "109": "area_plantada_ha",
        "216": "area_colhida_ha",
        "214": "producao_t",
        "112": "rendimento_kg_ha",
        "215": "valor_producao_mil_reais",
    }
    df["variavel"] = df["variavel_cod"].map(mapa_var)
    df["valor"] = df["valor"].replace(
        {"-": np.nan, "..": np.nan, "...": np.nan, "x": np.nan, "X": np.nan}
    )
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["ano"] = df["ano"].astype(int)

    base = (
        df.pivot_table(
            index=["codigo_municipio", "municipio", "ano"],
            columns="variavel",
            values="valor",
            aggfunc="first",
        )
        .reset_index()
    )
    base.columns.name = None
    base["municipio_nome"] = base["municipio"].str.replace(" - RS", "", regex=False)

    col_order = [
        "codigo_municipio", "municipio_nome", "ano",
        "area_plantada_ha", "area_colhida_ha", "producao_t",
        "rendimento_kg_ha", "valor_producao_mil_reais",
    ]
    base = base[col_order]
    base.to_csv(saida_csv, index=False)
    print(f"[PREP] Base preparada salva em: {saida_csv}  shape={base.shape}")
    return base


def baixar_e_preparar_oni(destino_csv: str) -> pd.DataFrame:
    """Baixa o Oceanic Nino Index (NOAA/CPC) e adiciona a coluna de fase ENOS."""
    if os.path.exists(destino_csv):
        return pd.read_csv(destino_csv)

    url = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text), sep=r"\s+")
    df = df[df["YR"] >= 1999].reset_index(drop=True)

    def fase(v):
        if v >= 0.5:
            return "El Nino"
        if v <= -0.5:
            return "La Nina"
        return "Neutro"

    df["fase_enso"] = df["ANOM"].apply(fase)
    df.to_csv(destino_csv, index=False)
    print(f"[ONI] Salvo em: {destino_csv}")
    return df


def gerar_analises(base: pd.DataFrame, oni: pd.DataFrame) -> pd.DataFrame:
    """Gera todos os graficos e agregacoes da EDA e devolve a base final da N1."""

    # 4.1 Cobertura
    cobertura = (
        base.groupby("ano")["rendimento_kg_ha"]
        .apply(lambda s: s.notna().sum())
        .rename("municipios_com_dado")
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    sns.barplot(data=cobertura, x="ano", y="municipios_com_dado", color="#2b8a3e", ax=ax)
    ax.set_title("Cobertura de municipios do RS com rendimento de soja informado")
    ax.set_xlabel("Ano da safra")
    ax.set_ylabel("Numero de municipios")
    ax.tick_params(axis="x", rotation=45)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "01_cobertura_por_ano.png"), dpi=120)
    plt.close(fig)

    # 4.3 Distribuicao do rendimento
    rend = base["rendimento_kg_ha"].dropna()
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    sns.histplot(rend, bins=50, color="#2b8a3e", ax=axes[0])
    axes[0].set_title("Distribuicao do rendimento (kg/ha) - RS 2000-2023")
    axes[0].axvline(rend.median(), color="red", linestyle="--", label=f"Mediana: {rend.median():.0f}")
    axes[0].axvline(rend.mean(), color="blue", linestyle="--", label=f"Media: {rend.mean():.0f}")
    axes[0].legend()
    sns.boxplot(x=rend, color="#8ce99a", ax=axes[1])
    axes[1].set_title("Boxplot do rendimento (kg/ha)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "02_distribuicao_rendimento.png"), dpi=120)
    plt.close(fig)

    # 4.4 Evolucao temporal
    evol = (
        base.groupby("ano")["rendimento_kg_ha"]
        .agg(["mean", "median", "std", "count"])
        .rename(columns={"mean": "media", "median": "mediana", "std": "desvio", "count": "n"})
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(evol["ano"], evol["media"], marker="o", color="#2b8a3e", label="Media entre municipios")
    ax.plot(evol["ano"], evol["mediana"], marker="s", color="#1c7ed6", label="Mediana entre municipios")
    ax.fill_between(evol["ano"], evol["media"] - evol["desvio"], evol["media"] + evol["desvio"],
                    alpha=0.15, color="#2b8a3e", label="+/-1 desvio padrao")
    ax.set_title("Evolucao do rendimento medio de soja nos municipios do RS")
    ax.set_xlabel("Ano da safra")
    ax.set_ylabel("Rendimento (kg/ha)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "03_evolucao_rendimento.png"), dpi=120)
    plt.close(fig)

    # 4.6 Ranking dos maiores produtores
    top = (
        base.groupby("municipio_nome")["producao_t"]
        .sum(min_count=1)
        .sort_values(ascending=False)
        .head(20)
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(9, 6))
    sns.barplot(data=top, y="municipio_nome", x="producao_t", color="#2b8a3e", ax=ax)
    ax.set_title("Top 20 municipios do RS por producao acumulada (2000-2023)")
    ax.set_xlabel("Producao acumulada (t)")
    ax.set_ylabel("Municipio")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "04_top20_produtores.png"), dpi=120)
    plt.close(fig)

    # 4.7 Correlacoes
    corr = base[[
        "area_plantada_ha", "area_colhida_ha", "producao_t",
        "rendimento_kg_ha", "valor_producao_mil_reais",
    ]].corr()
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, ax=ax)
    ax.set_title("Matriz de correlacao - variaveis PAM/IBGE (soja RS)")
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "05_correlacoes.png"), dpi=120)
    plt.close(fig)

    # 4.9 Baselines historicos
    base_ord = base.sort_values(["codigo_municipio", "ano"]).copy()
    base_ord["media_hist_mun"] = (
        base_ord.groupby("codigo_municipio")["rendimento_kg_ha"]
        .transform(lambda s: s.shift(1).expanding().mean())
    )
    base_ord["rendimento_anterior"] = (
        base_ord.groupby("codigo_municipio")["rendimento_kg_ha"].shift(1)
    )

    # 5. Sinal ENOS agregado por safra
    trimestres_safra = ["OND", "NDJ", "DJF", "JFM", "FMA"]
    oni_saf = oni[oni["SEAS"].isin(trimestres_safra)].copy()
    oni_saf["safra"] = np.where(
        oni_saf["SEAS"].isin(["OND", "NDJ"]), oni_saf["YR"] + 1, oni_saf["YR"]
    )
    oni_agg = (
        oni_saf.groupby("safra")["ANOM"]
        .agg(["mean", "min", "max"])
        .rename(columns={"mean": "oni_medio_safra",
                         "min": "oni_min_safra",
                         "max": "oni_max_safra"})
        .reset_index()
    )

    def fase(v):
        if v >= 0.5:
            return "El Nino"
        if v <= -0.5:
            return "La Nina"
        return "Neutro"

    oni_agg["fase_dominante_safra"] = oni_agg["oni_medio_safra"].apply(fase)

    base_enos = base_ord.merge(oni_agg, left_on="ano", right_on="safra", how="left")

    resumo_enso = (
        base_enos.dropna(subset=["rendimento_kg_ha", "fase_dominante_safra"])
        .groupby(["ano", "fase_dominante_safra"])["rendimento_kg_ha"]
        .mean()
        .reset_index()
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    for fase_lbl, cor in [("La Nina", "#d6336c"), ("Neutro", "#868e96"), ("El Nino", "#1c7ed6")]:
        sub = resumo_enso[resumo_enso["fase_dominante_safra"] == fase_lbl]
        ax.scatter(sub["ano"], sub["rendimento_kg_ha"], color=cor, label=fase_lbl, s=80)
    ax.plot(evol["ano"], evol["media"], color="k", alpha=0.4, linewidth=1, label="Media estadual")
    ax.set_title("Rendimento medio anual vs. fase ENOS dominante (ONI)")
    ax.set_xlabel("Ano da safra")
    ax.set_ylabel("Rendimento (kg/ha)")
    ax.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, "06_enso_vs_rendimento.png"), dpi=120)
    plt.close(fig)

    print("[EDA] Rendimento medio por fase ENOS (todas as safras do RS):")
    print(
        base_enos.groupby("fase_dominante_safra")["rendimento_kg_ha"]
        .agg(["mean", "median", "count"]).round(1)
    )

    saida = os.path.join(DATA_DIR, "base_soja_rs_N1.csv")
    base_enos.to_csv(saida, index=False)
    print(f"[EDA] Base final N1 salva em: {saida}  shape={base_enos.shape}")
    return base_enos


def main():
    bruto_csv = os.path.join(DATA_DIR, "sidra_1612_soja_rs_bruto.csv")
    prep_csv = os.path.join(DATA_DIR, "sidra_1612_soja_rs_preparado.csv")
    oni_csv = os.path.join(DATA_DIR, "oni_nino34.csv")

    baixar_sidra_1612(bruto_csv)
    base = preparar_base_sidra(bruto_csv, prep_csv)
    oni = baixar_e_preparar_oni(oni_csv)
    gerar_analises(base, oni)


if __name__ == "__main__":
    main()
