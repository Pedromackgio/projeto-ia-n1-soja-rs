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
#   Treina e avalia tres algoritmos supervisionados sobre a base N2
#   (PAM/IBGE + ONI/NOAA + NASA POWER) com validacao TEMPORAL - safras ate
#   2018 para treino, 2019-2023 para teste, sem embaralhar. Compara com
#   linhas de base (media historica municipal e rendimento da safra anterior).
#   Gera metricas (MAE, RMSE, R2), erro por safra, importancia de atributos
#   (RF) e matriz de classificacao para o indicador de risco de quebra
#   (rendimento < media historica do municipio).
#
# Historico:
#   2026-11-16 | Pedro Giovannini Andrade | Versao inicial (N2).
# =============================================================================

import os, json, warnings
import numpy as np, pandas as pd
import matplotlib.pyplot as plt

from sklearn.compose           import ColumnTransformer
from sklearn.preprocessing     import StandardScaler, OneHotEncoder
from sklearn.impute            import SimpleImputer
from sklearn.pipeline          import Pipeline
from sklearn.linear_model      import Ridge
from sklearn.ensemble          import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics           import (mean_absolute_error, mean_squared_error,
                                       r2_score, confusion_matrix,
                                       classification_report)

warnings.filterwarnings("ignore")

REPO  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DADOS = os.path.join(REPO, "dados")
FIG   = os.path.join(REPO, "figuras")
os.makedirs(FIG, exist_ok=True)

base = pd.read_csv(os.path.join(DADOS, "base_soja_rs_N2.csv"))
base = base.dropna(subset=["rendimento_kg_ha"])
print(f"[OK] base carregada: {base.shape}")

FEAT_NUM = [
    "media_hist_mun", "rendimento_anterior",
    "oni_medio_safra", "oni_min_safra", "oni_max_safra",
    "pr_acum_safra", "pr_acum_df", "dias_chuva", "max_dias_secos",
    "tmed_safra", "tmed_df", "tmax_df_media", "dias_calor_extremo",
    "rad_acum", "rh_media", "gdd",
]
FEAT_CAT = ["fase_dominante_safra"]
TARGET   = "rendimento_kg_ha"

# ---------- divisao temporal ----------
CORTE_TR = 2018
train = base[base["safra"] <= CORTE_TR].dropna(subset=FEAT_NUM + [TARGET])
test  = base[base["safra"] >  CORTE_TR].dropna(subset=FEAT_NUM + [TARGET])
print(f"treino: {len(train):5d}  (ate {CORTE_TR})")
print(f"teste : {len(test):5d}  ({CORTE_TR+1}+)")

Xtr, ytr = train[FEAT_NUM + FEAT_CAT], train[TARGET]
Xte, yte = test [FEAT_NUM + FEAT_CAT], test [TARGET]

prep = ColumnTransformer([
    ("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                       ("sc",  StandardScaler())]), FEAT_NUM),
    ("cat", OneHotEncoder(handle_unknown="ignore"), FEAT_CAT),
])

MODELOS = {
    "Ridge":            Ridge(alpha=1.0, random_state=0),
    "RandomForest":     RandomForestRegressor(n_estimators=400, max_depth=14,
                                              min_samples_leaf=3, n_jobs=-1,
                                              random_state=0),
    "GradientBoosting": GradientBoostingRegressor(n_estimators=400, max_depth=3,
                                                  learning_rate=0.05,
                                                  random_state=0),
}

def metricas(y, yhat):
    rmse = float(np.sqrt(mean_squared_error(y, yhat)))
    return dict(MAE=float(mean_absolute_error(y, yhat)),
                RMSE=rmse,
                R2=float(r2_score(y, yhat)))

# ---------- baselines ----------
res = {}
res["baseline_media_hist"]     = metricas(yte, test["media_hist_mun"]
                                          .fillna(train[TARGET].mean()))
res["baseline_ano_anterior"]   = metricas(yte, test["rendimento_anterior"]
                                          .fillna(train[TARGET].mean()))

pred_cols = {}
for nome, mdl in MODELOS.items():
    pipe = Pipeline([("prep", prep), ("mdl", mdl)])
    pipe.fit(Xtr, ytr)
    yhat = pipe.predict(Xte)
    res[nome] = metricas(yte, yhat)
    pred_cols[nome] = yhat
    print(f"[{nome:17s}] MAE={res[nome]['MAE']:7.1f}  "
          f"RMSE={res[nome]['RMSE']:7.1f}  R2={res[nome]['R2']:6.3f}")

# importancia de atributos (Random Forest)
pipe_rf = Pipeline([("prep", prep),
                    ("mdl",  MODELOS["RandomForest"])]).fit(Xtr, ytr)
rf = pipe_rf.named_steps["mdl"]
ohe = pipe_rf.named_steps["prep"].named_transformers_["cat"]
nomes = FEAT_NUM + list(ohe.get_feature_names_out(FEAT_CAT))
imp = pd.Series(rf.feature_importances_, index=nomes).sort_values(ascending=True)

# ---------- indicador de risco de quebra ----------
# risco observado: rendimento < media historica do municipio
risco_obs   = (test[TARGET]            < test["media_hist_mun"]).astype(int)
risco_pred  = (pred_cols["GradientBoosting"] < test["media_hist_mun"]).astype(int)
cm = confusion_matrix(risco_obs, risco_pred)
cr = classification_report(risco_obs, risco_pred, digits=3,
                           target_names=["ok","risco"], output_dict=False)
print("\nMatriz de confusao (risco de quebra):\n", cm)
print(cr)

# ---------- salvar metricas ----------
pd.DataFrame(res).T.round(3).to_csv(os.path.join(DADOS,"metricas_modelos.csv"))
print("\nMetricas gerais (N2):")
print(pd.DataFrame(res).T.round(2))

# ---------- graficos ----------
# 1) barras MAE e R2
mdf = pd.DataFrame(res).T.reset_index().rename(columns={"index":"modelo"})
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
ax[0].barh(mdf["modelo"], mdf["MAE"], color="#1f77b4")
ax[0].set_title("MAE (kg/ha) - teste 2019-2023")
ax[0].invert_yaxis(); ax[0].grid(axis="x", alpha=.4)
for i,v in enumerate(mdf["MAE"]):
    ax[0].text(v, i, f"  {v:.0f}", va="center")
ax[1].barh(mdf["modelo"], mdf["R2"], color="#2ca02c")
ax[1].set_title("R2 - teste 2019-2023")
ax[1].invert_yaxis(); ax[1].grid(axis="x", alpha=.4)
for i,v in enumerate(mdf["R2"]):
    ax[1].text(v, i, f"  {v:.2f}", va="center")
plt.tight_layout()
plt.savefig(os.path.join(FIG, "07_comparacao_modelos.png"), dpi=130)
plt.close()

# 2) scatter observado x previsto (melhor modelo)
melhor = min([m for m in pred_cols], key=lambda m: res[m]["MAE"])
plt.figure(figsize=(6.5, 6))
plt.scatter(yte, pred_cols[melhor], alpha=.4, s=18)
mn, mx = yte.min(), yte.max()
plt.plot([mn,mx],[mn,mx], "k--", lw=1)
plt.xlabel("Rendimento observado (kg/ha)")
plt.ylabel("Rendimento previsto (kg/ha)")
plt.title(f"Observado vs. previsto - {melhor} (MAE={res[melhor]['MAE']:.0f})")
plt.grid(alpha=.3); plt.tight_layout()
plt.savefig(os.path.join(FIG, "08_obs_vs_previsto.png"), dpi=130)
plt.close()

# 3) MAE por safra
erro = (test.assign(abs_err=np.abs(pred_cols[melhor] - yte))
             .groupby("safra")["abs_err"].mean())
plt.figure(figsize=(8, 4.5))
plt.bar(erro.index.astype(str), erro.values, color="#ff7f0e")
plt.title(f"Erro medio absoluto por safra - {melhor}")
plt.ylabel("MAE (kg/ha)")
for i,(s,v) in enumerate(erro.items()):
    plt.text(i, v, f"{v:.0f}", ha="center", va="bottom", fontsize=9)
plt.grid(axis="y", alpha=.3); plt.tight_layout()
plt.savefig(os.path.join(FIG, "09_mae_por_safra.png"), dpi=130)
plt.close()

# 4) importancia de atributos - RF
plt.figure(figsize=(8, 7))
imp.plot.barh(color="#17becf")
plt.title("Importancia de atributos - Random Forest")
plt.tight_layout()
plt.savefig(os.path.join(FIG, "10_importancia_rf.png"), dpi=130)
plt.close()

# 5) matriz de confusao risco
fig, ax = plt.subplots(figsize=(4.8, 4.2))
im = ax.imshow(cm, cmap="Blues")
ax.set_xticks([0,1], ["ok","risco"]); ax.set_yticks([0,1], ["ok","risco"])
ax.set_xlabel("previsto"); ax.set_ylabel("observado")
ax.set_title("Indicador de risco de quebra")
for i in range(2):
    for j in range(2):
        ax.text(j, i, f"{cm[i,j]:d}", ha="center", va="center",
                color="white" if cm[i,j] > cm.max()/2 else "black",
                fontweight="bold", fontsize=14)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "11_matriz_risco.png"), dpi=130)
plt.close()

# salva report de risco
with open(os.path.join(DADOS, "relatorio_risco.txt"), "w") as f:
    f.write("Matriz de confusao (risco de quebra):\n")
    f.write(np.array2string(cm) + "\n\n")
    f.write(cr)

print("\n[OK] graficos e metricas gravados em", FIG)
