# =============================================================================
# Projeto : Predicao da Produtividade da Safra de Soja no RS - N2/2026
# Disciplina: Inteligencia Artificial - FCI / Mackenzie
# Professor : Prof. Dr. Leandro Zerbinatti
#
# Integrantes:
#   - Gabriel Bello           - RA 10416808 - 10416808@mackenzista.com.br
#   - Pedro Giovannini Andrade - RA 10425498 - 10425498@mackenzista.com.br
#
# Sintese:
#   Agrega as series diarias do NASA POWER em atributos por municipio-safra
#   (janela 01/out do ano t-1 -> 31/mai do ano t) e integra com a base da N1
#   (PAM/IBGE + ONI/NOAA) para gerar a base final de modelagem (N2).
#
#   Atributos gerados por janela de safra:
#     - pr_acum_safra ........ precipitacao total (mm)
#     - pr_acum_df ........... precipitacao na janela critica (dez-fev)
#     - dias_chuva ........... # dias com precipitacao > 1 mm
#     - max_dias_secos ....... maior sequencia de dias secos (< 1 mm)
#     - tmed_safra ........... temperatura media
#     - tmed_df .............. temperatura media na janela critica
#     - tmax_df_media ........ media da tmax na janela critica
#     - dias_calor_extremo ... # dias com tmax > 32 C
#     - rad_acum ............. radiacao solar acumulada (kWh/m2)
#     - rh_media ............. umidade relativa media (%)
#     - gdd ................. soma de graus-dia (base 10 C, ate 30 C)
#
# Historico:
#   2026-11-16 | Gabriel Bello | Versao inicial (N2).
# =============================================================================

import os, numpy as np, pandas as pd

REPO  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DADOS = os.path.join(REPO, "dados")

power  = pd.read_csv(os.path.join(DADOS, "nasa_power_rs_top50.csv.gz"),
                     compression="gzip", parse_dates=["data"])
basen1 = pd.read_csv(os.path.join(DADOS, "base_soja_rs_N1.csv"))

# ---- define safra: 01/out do ano t-1 ate 31/mai do ano t ----
power["ano"] = power["data"].dt.year
power["mes"] = power["data"].dt.month
power["safra"] = np.where(power["mes"] >= 10,
                          power["ano"] + 1, power["ano"])

# janela critica reprodutiva (dez-fev): meses 12,1,2
power["critico"] = power["mes"].isin([12, 1, 2])
# considera apenas dias dentro da janela out->mai
in_safra = (power["mes"] >= 10) | (power["mes"] <= 5)
pw = power[in_safra].copy()

def max_dias_secos(serie_chuva):
    seq, mx = 0, 0
    for v in serie_chuva.values:
        if pd.isna(v) or v < 1.0:
            seq += 1
            if seq > mx: mx = seq
        else:
            seq = 0
    return mx

def gdd(tmin, tmax, base=10.0, top=30.0):
    tmin = np.clip(tmin, base, top)
    tmax = np.clip(tmax, base, top)
    return ((tmin + tmax) / 2.0 - base).clip(lower=0).sum()

feat_rows = []
for (cod, safra), g in pw.groupby(["codigo_municipio", "safra"]):
    gc = g[g["critico"]]
    feat_rows.append({
        "codigo_municipio":   cod,
        "safra":              safra,
        "pr_acum_safra":      g["PRECTOTCORR"].sum(),
        "pr_acum_df":         gc["PRECTOTCORR"].sum(),
        "dias_chuva":         (g["PRECTOTCORR"] > 1).sum(),
        "max_dias_secos":     max_dias_secos(g["PRECTOTCORR"]),
        "tmed_safra":         g["T2M"].mean(),
        "tmed_df":            gc["T2M"].mean(),
        "tmax_df_media":      gc["T2M_MAX"].mean(),
        "dias_calor_extremo": (gc["T2M_MAX"] > 32).sum(),
        "rad_acum":           g["ALLSKY_SFC_SW_DWN"].sum(),
        "rh_media":           g["RH2M"].mean(),
        "gdd":                gdd(g["T2M_MIN"], g["T2M_MAX"]),
    })
feat = pd.DataFrame(feat_rows)
print(f"[OK] atributos agrometeorologicos: {feat.shape}")

# ---- junta com base N1 (PAM + ONI) ----
base = basen1.merge(feat, on=["codigo_municipio", "safra"], how="inner")
print(f"[OK] base N2 integrada: {base.shape}")

# sanity: alguns resumos
print(base[["pr_acum_safra","tmed_safra","dias_calor_extremo",
            "rendimento_kg_ha"]].describe().round(2))

out = os.path.join(DADOS, "base_soja_rs_N2.csv")
base.to_csv(out, index=False)
print(f"[OK] base final gravada em {out}")
