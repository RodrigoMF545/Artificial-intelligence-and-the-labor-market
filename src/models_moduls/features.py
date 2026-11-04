"""Construção de variáveis para os modelos do Dia 4."""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

PARQUET = "data/processed/survey_clean.parquet"
OTHER_ROLE = "Other (please specify):"
ORDEM_EXP = ["0-1 anos", "2-4 anos", "5-9 anos", "10-19 anos", "20+ anos"]


def load_clean(path: str = PARQUET) -> pd.DataFrame:
    return pd.read_parquet(path)


def exp_band(years: pd.Series) -> pd.Series:
    """Mesmas faixas do SQL (limite superior exclusivo): <2, <5, <10, <20, 20+."""
    return pd.cut(years, bins=[-np.inf, 2, 5, 10, 20, np.inf], labels=ORDEM_EXP, right=False)


def safe(name: str) -> str:
    """XGBoost não aceita [, ] ou < nos nomes das colunas."""
    return re.sub(r"[\[\]<>]", "_", str(name))


# --- multi-valor ('A;B;C') ------------------------------------------------------
def _tokens(s: pd.Series) -> pd.Series:
    return s.fillna("").astype(str).str.split(";").map(lambda L: {x.strip() for x in L if x.strip()})


def top_tokens(s: pd.Series, top_n: int, exclude=()) -> list[str]:
    counts = _tokens(s).map(list).explode().value_counts()
    return [t for t in counts.index if t not in exclude][:top_n]


def multi_hot(s: pd.Series, items: list[str], prefix: str) -> pd.DataFrame:
    tok = _tokens(s)
    return pd.DataFrame(
        {f"{prefix}__{it}": tok.map(lambda t, it=it: it in t).astype("int8") for it in items},
        index=s.index,
    )


# --- categóricas -----------------------------------------------------------------
def group_rare(s: pd.Series, min_share: float = 0.02, other: str = "Other") -> pd.Series:
    vc = s.value_counts(normalize=True)
    keep = vc.index[vc >= min_share]
    return s.where(s.isin(keep), other)


def dummies(s: pd.Series, prefix: str, drop_first: bool, ref: str) -> pd.DataFrame:
    out = pd.get_dummies(s, prefix=prefix, dtype="int8")
    if drop_first:
        ref_col = f"{prefix}_{ref}"
        out = out.drop(columns=ref_col) if ref_col in out.columns else out.iloc[:, 1:]
    return out


# --- matriz de variáveis ------------------------------------------------------------
def build_features(
    df: pd.DataFrame,
    target: str = "log_comp",
    require_ai: bool = True,
    min_n_country: int = 100,
    top_roles: int = 10,
    top_langs: int = 20,
    drop_first: bool = True,
    min_share: float = 0.02,
):
    """Devolve (X, y, groups, d).

    groups: {coluna: grupo}, com grupos 'ia', 'ano', 'experiencia', 'pais', 'funcao',
            'linguagem', 'educacao', 'org', 'remoto'.
    d: as linhas usadas (índice 0..n-1, alinhado com X e y).
    """
    d = df[df[target].notna()]
    if require_ai:
        d = d[d["uses_ai"].notna()]
    d = d.reset_index(drop=True)

    blocks: list[tuple[pd.DataFrame, str]] = []
    if require_ai:
        blocks.append((pd.DataFrame({"uses_ai": d["uses_ai"].astype(float)}), "ia"))
    blocks.append((pd.DataFrame({"year_2025": (d["year"] == 2025).astype(int)}), "ano"))
    blocks.append((pd.DataFrame({"years_pro": d["years_pro"].astype(float),
                                 "years_pro_sq": d["years_pro"].astype(float) ** 2 / 100}), "experiencia"))

    # país: só os que têm n >= min_n_country em cada ano; os outros -> 'Other'
    cnt = d.groupby(["country", "year"]).size().unstack(fill_value=0)
    valid = cnt.index[cnt.min(axis=1) >= min_n_country]
    pais = d["country"].astype("string").where(d["country"].isin(valid), "Other")
    blocks.append((dummies(pais, "pais", drop_first, "Other"), "pais"))

    roles = top_tokens(d["dev_type"], top_roles, exclude=(OTHER_ROLE,))
    blocks.append((multi_hot(d["dev_type"], roles, "funcao"), "funcao"))
    langs = top_tokens(d["languages"], top_langs)
    blocks.append((multi_hot(d["languages"], langs, "lang"), "linguagem"))

    for col, prefix, group in (("ed_level", "edu", "educacao"), ("org_size", "org", "org"),
                               ("remote_work", "remoto", "remoto")):
        if col in d.columns:
            cat = group_rare(d[col].astype("string").fillna("Unknown"), min_share)
            blocks.append((dummies(cat, prefix, drop_first, "Unknown"), group))

    X = pd.concat([b for b, _ in blocks], axis=1)
    groups = {c: g for b, g in blocks for c in b.columns}
    rename = {c: safe(c) for c in X.columns}
    X = X.rename(columns=rename)
    groups = {rename[c]: g for c, g in groups.items()}
    return X, d[target].astype(float), groups, d


def cols_of(groups: dict[str, str], *names: str) -> list[str]:
    return [c for c, g in groups.items() if g in names]
