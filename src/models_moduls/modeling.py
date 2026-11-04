"""Modelos e testes do Dia 4 (Q1 a Q5)."""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, silhouette_score
from sklearn.model_selection import train_test_split
from xgboost import XGBRegressor

from src.models_moduls.features import (OTHER_ROLE, cols_of, exp_band, multi_hot, ORDEM_EXP,
                          top_tokens)

SEED = 42


def pct(b):
    """Coeficiente de um modelo em log -> variação percentual."""
    return 100 * (np.exp(b) - 1)


# =============================== Q2: OLS ===========================================
def fit_ols(X: pd.DataFrame, y: pd.Series, cols: list[str]):
    keep = [c for c in cols if X[c].nunique() > 1]          # remove colunas constantes
    Xc = sm.add_constant(X[keep].astype(float), has_constant="add")
    return sm.OLS(y, Xc).fit(cov_type="HC1")                 # erros-padrão robustos


def effect(res, name: str) -> dict:
    """Efeito percentual de uma variável e intervalo de confiança a 95%."""
    if name not in res.params.index:
        return {"pct": np.nan, "lo": np.nan, "hi": np.nan}
    lo, hi = res.conf_int().loc[name]
    return {"pct": pct(res.params[name]), "lo": pct(lo), "hi": pct(hi)}


def ols_specs(X, y, groups) -> pd.DataFrame:
    """Coeficientes de 'uses_ai' e de 'year_2025' à medida que se acrescentam controlos."""
    specs = [
        ("1. só IA + ano",                       ["ia", "ano"]),
        ("2. + experiência",                     ["ia", "ano", "experiencia"]),
        ("3. + país",                            ["ia", "ano", "experiencia", "pais"]),
        ("4. + função, linguagens, educação...", ["ia", "ano", "experiencia", "pais", "funcao",
                                                   "linguagem", "educacao", "org", "remoto"]),
    ]
    rows = []
    for name, gs in specs:
        res = fit_ols(X, y, cols_of(groups, *gs))
        ia, yr = effect(res, "uses_ai"), effect(res, "year_2025")
        rows.append({"modelo": name, "n": int(res.nobs), "r2": round(res.rsquared, 3),
                     "ia_pct": ia["pct"], "ia_lo": ia["lo"], "ia_hi": ia["hi"],
                     "ano_pct": yr["pct"], "ano_lo": yr["lo"], "ano_hi": yr["hi"]})
    return pd.DataFrame(rows).round(1)


def effect_by_band(X, y, groups, d) -> pd.DataFrame:
    """Efeito ajustado de 'uses_ai' dentro de cada faixa de experiência (modelo completo)."""
    band = exp_band(d["years_pro"])
    cols = cols_of(groups, "ia", "ano", "experiencia", "pais", "funcao", "linguagem",
                   "educacao", "org", "remoto")
    rows = []
    for b in ORDEM_EXP:
        m = (band == b).to_numpy()
        with warnings.catch_warnings():        # faixas pequenas podem ter colunas colineares
            warnings.simplefilter("ignore")
            res = fit_ols(X[m], y[m], cols)
        e = effect(res, "uses_ai")
        rows.append({"faixa": b, "n": int(m.sum()), **{k: round(v, 1) for k, v in e.items()}})
    return pd.DataFrame(rows)


# =============================== Q1: logística =====================================
def adoption_adjusted(X, groups, d) -> dict:
    """Mudança de adoção 2024->2025: bruta vs ajustada por experiência, país, função..."""
    cols = cols_of(groups, "ano", "experiencia", "pais", "funcao", "educacao", "org", "remoto")
    cols = [c for c in cols if X[c].nunique() > 1]
    Xc = sm.add_constant(X[cols].astype(float), has_constant="add")
    yb = X["uses_ai"]
    res = sm.Logit(yb, Xc).fit(disp=0, maxiter=300)
    X1, X0 = Xc.copy(), Xc.copy()
    X1["year_2025"], X0["year_2025"] = 1.0, 0.0
    adj_pp = 100 * (res.predict(X1) - res.predict(X0)).mean()
    raw = yb.groupby(d["year"]).mean()
    lo, hi = res.conf_int().loc["year_2025"]
    return {"bruta_pp": 100 * (raw[2025] - raw[2024]), "ajustada_pp": adj_pp,
            "odds_ratio": float(np.exp(res.params["year_2025"])),
            "or_lo": float(np.exp(lo)), "or_hi": float(np.exp(hi)), "n": int(res.nobs)}


# =============================== Q3: XGBoost + SHAP ================================
def make_xgb(**kw) -> XGBRegressor:
    params = dict(n_estimators=1000, learning_rate=0.05, max_depth=5, subsample=0.8,
                  colsample_bytree=0.8, min_child_weight=5, early_stopping_rounds=40,
                  random_state=SEED, n_jobs=-1)
    params.update(kw)
    return XGBRegressor(**params)


def metrics(y_true, y_pred) -> dict:
    mdape = np.median(np.abs(np.exp(y_pred) - np.exp(y_true)) / np.exp(y_true)) * 100
    return {"r2": round(r2_score(y_true, y_pred), 3),
            "mae_log": round(mean_absolute_error(y_true, y_pred), 3),
            "erro_mediano_%": round(float(mdape), 1)}


def train_and_compare(X, y):
    """Baseline, regressão linear e XGBoost, avaliados no mesmo conjunto de teste."""
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=SEED)
    X_fit, X_val, y_fit, y_val = train_test_split(X_tr, y_tr, test_size=0.15, random_state=SEED)

    base = DummyRegressor(strategy="median").fit(X_tr, y_tr)
    lin = LinearRegression().fit(X_tr, y_tr)
    xgb = make_xgb()
    xgb.fit(X_fit, y_fit, eval_set=[(X_val, y_val)], verbose=False)

    table = pd.DataFrame({
        "baseline (mediana)": metrics(y_te, base.predict(X_te)),
        "regressão linear": metrics(y_te, lin.predict(X_te)),
        "XGBoost": metrics(y_te, xgb.predict(X_te)),
    }).T
    return xgb, table, (X_tr, X_te, y_tr, y_te)


def temporal_check(X, y, d) -> dict:
    """Treina com 2024, testa em 2025 (sem a variável 'ano'): a diferença média é a
    mudança salarial de 2025 que o modelo não explica pelas outras variáveis."""
    cols = [c for c in X.columns if c != "year_2025"]
    m24, m25 = (d["year"] == 2024).to_numpy(), (d["year"] == 2025).to_numpy()
    X_tr, X_val, y_tr, y_val = train_test_split(X.loc[m24, cols], y[m24], test_size=0.15, random_state=SEED)
    model = make_xgb()
    model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
    pred = model.predict(X.loc[m25, cols])
    resid = y[m25].to_numpy() - pred
    return {**metrics(y[m25].to_numpy(), pred), "vies_medio_%": round(float(pct(resid.mean())), 1)}


def shap_values(model, X_sample: pd.DataFrame) -> pd.DataFrame:
    """SHAP exatos para árvores, via XGBoost (pred_contribs). Colunas = variáveis."""
    import xgboost as xgb
    contrib = model.get_booster().predict(xgb.DMatrix(X_sample), pred_contribs=True)
    return pd.DataFrame(contrib[:, :-1], columns=X_sample.columns, index=X_sample.index)


def shap_by_group(sv: pd.DataFrame, groups: dict) -> pd.DataFrame:
    imp = sv.abs().mean()
    out = imp.groupby(imp.index.map(groups)).sum().sort_values(ascending=False)
    return (100 * out / out.sum()).round(1).rename("importancia_%").to_frame()


def shap_binary_effect(sv: pd.DataFrame, X_sample: pd.DataFrame, prefix: str) -> pd.DataFrame:
    """Efeito médio (em %) de ter a tecnologia/função, segundo o modelo."""
    rows = []
    for c in [c for c in sv.columns if c.startswith(prefix)]:
        on = X_sample[c] == 1
        if on.sum() >= 30:
            rows.append({"variavel": c.split("__", 1)[1], "n": int(on.sum()),
                         "efeito_%": round(float(pct(sv.loc[on, c].mean())), 1)})
    return pd.DataFrame(rows).sort_values("efeito_%", ascending=False).reset_index(drop=True)


# =============================== Q4: testes ========================================
def compare_years(d_users: pd.DataFrame, score: str) -> dict:
    """Mann-Whitney 2025 vs 2024 e tamanho de efeito (delta de Cliff)."""
    a = d_users.loc[d_users["year"] == 2024, score].dropna().to_numpy()
    b = d_users.loc[d_users["year"] == 2025, score].dropna().to_numpy()
    u, p = stats.mannwhitneyu(b, a, alternative="two-sided")
    delta = 2 * u / (len(a) * len(b)) - 1
    size = ("desprezável" if abs(delta) < 0.147 else "pequeno" if abs(delta) < 0.33
            else "médio" if abs(delta) < 0.474 else "grande")
    return {"n_2024": len(a), "n_2025": len(b), "media_2024": round(a.mean(), 2),
            "media_2025": round(b.mean(), 2), "p_valor": float(p),
            "cliff_delta": round(float(delta), 3), "efeito": size}


def adjusted_year_effect(d_users: pd.DataFrame, score: str) -> dict:
    """Efeito de 2025 na pontuação (pontos de escala), controlando experiência e país."""
    from src.models_moduls.features import build_features
    X, y, groups, _ = build_features(d_users, target=score, require_ai=False, top_roles=0, top_langs=0)
    res = fit_ols(X, y, cols_of(groups, "ano", "experiencia", "pais"))
    lo, hi = res.conf_int().loc["year_2025"]
    return {"ajustado": round(float(res.params["year_2025"]), 3),
            "ic_lo": round(float(lo), 3), "ic_hi": round(float(hi), 3)}


# =============================== Q5: clustering ====================================
def cluster_matrix(df: pd.DataFrame, top_langs: int = 15, top_roles: int = 8):
    d = df[df["uses_ai"].notna()].reset_index(drop=True)
    L = multi_hot(d["languages"], top_tokens(d["languages"], top_langs), "lang")
    R = multi_hot(d["dev_type"], top_tokens(d["dev_type"], top_roles, exclude=(OTHER_ROLE,)), "funcao")
    exp = np.log1p(d["years_pro"].astype(float))
    exp = (exp - exp.min()) / (exp.max() - exp.min())
    Xc = pd.concat([exp.rename("experiencia"), d["uses_ai"].astype(float), L, R], axis=1)
    return d, Xc, L, R


def choose_k(Xc: pd.DataFrame, ks=range(3, 8), sample: int = 5000) -> pd.DataFrame:
    rows = []
    for k in ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(Xc)
        sil = silhouette_score(Xc, km.labels_, sample_size=min(sample, len(Xc)), random_state=SEED)
        rows.append({"k": k, "inercia": round(km.inertia_, 0), "silhouette": round(sil, 3)})
    return pd.DataFrame(rows)


def describe_clusters(d, labels, L, R) -> pd.DataFrame:
    rows = []
    for k in sorted(set(labels)):
        m = labels == k
        lift = (L[m].mean() / L.mean().replace(0, np.nan)).sort_values(ascending=False)
        langs = ", ".join(f"{c.split('__', 1)[1]} ({L.loc[m, c].mean():.0%})" for c in lift.index[:4])
        roles = ", ".join(f"{c.split('__', 1)[1]} ({R.loc[m, c].mean():.0%})"
                          for c in R[m].mean().sort_values(ascending=False).index[:3])
        rows.append({"cluster": k, "n": int(m.sum()), "pct_amostra": round(100 * m.mean(), 1),
                     "exp_mediana": float(d.loc[m, "years_pro"].median()),
                     "pct_usa_ia": round(100 * d.loc[m, "uses_ai"].astype(float).mean(), 1),
                     "salario_mediano": float(d.loc[m, "comp_yearly"].median()),
                     "linguagens_distintivas": langs, "funcoes_principais": roles})
    return pd.DataFrame(rows)


def pca_2d(Xc: pd.DataFrame, labels, sample: int = 5000) -> pd.DataFrame:
    idx = np.random.default_rng(SEED).choice(len(Xc), size=min(sample, len(Xc)), replace=False)
    pcs = PCA(n_components=2, random_state=SEED).fit_transform(Xc.iloc[idx])
    return pd.DataFrame({"pc1": pcs[:, 0], "pc2": pcs[:, 1], "cluster": np.asarray(labels)[idx].astype(str)})
