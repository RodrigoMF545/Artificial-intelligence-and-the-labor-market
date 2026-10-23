
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.column_mapping import MAPPING

PROCESSED = Path("data/processed")
OUTPUT = PROCESSED / "survey_clean.parquet"

# --- Parâmetros (ajustar depois de correr as validações no notebook) --------
# Filtro de profissionais. CONFIRMAR com src.validations.check_employment:
# os valores de `Employment` podem diferir entre 2024 e 2025.
EMPLOYMENT_PATTERN = r"Employed, full-time"
MIN_COMP_USD = 1_000
COMP_QUANTILES = (0.01, 0.99)
MAX_YEARS_PRO = 50

# --- Escalas ordinais (1 = mais negativo, 5 = mais positivo) ----------------
AISENT_SCORE = {
    "very unfavorable": 1, "unfavorable": 2, "indifferent": 3,
    "favorable": 4, "very favorable": 5,           # "unsure" -> NaN
}
AIACC_SCORE = {
    "highly distrust": 1, "somewhat distrust": 2, "neither trust nor distrust": 3,
    "somewhat trust": 4, "highly trust": 5,
}
AICOMPLEX_SCORE = {
    "very poor at handling complex tasks": 1,
    "bad at handling complex tasks": 2,
    "neither good or bad at handling complex tasks": 3,
    "good, but not great at handling complex tasks": 4,
    "very well at handling complex tasks": 5,      # "I don't use ... / I don't know" -> NaN
}


def _norm(s: pd.Series) -> pd.Series:
    """Texto em minúsculas, sem espaços nas pontas e com apóstrofo reto."""
    return (
        s.astype("string")
        .str.replace("\u2019", "'", regex=False)
        .str.strip()
        .str.lower()
    )


def parse_years(x) -> float:
    """Converte 'Less than 1 year', 'More than 50 years' ou '12' em número."""
    if pd.isna(x):
        return np.nan
    s = str(x).strip().lower()
    if s.startswith("less than 1"):
        return 0.5
    if s.startswith("more than 50"):
        return 50.0
    try:
        return float(s)
    except ValueError:
        return np.nan


def _score(raw: pd.Series, table: dict[str, int]) -> pd.Series:
    return pd.to_numeric(_norm(raw).map(table), errors="coerce")


# ---------------------------------------------------------------------------
#  Canonic Names
# ---------------------------------------------------------------------------
def harmonize_columns(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Renomeia as colunas do ano para os nomes canónicos do MAPPING."""
    rename = {
        per_year[year]: canon
        for canon, per_year in MAPPING.items()
        if per_year.get(year) and per_year[year] in df.columns
    }
    out = df[list(rename)].rename(columns=rename).copy()
    out["year"] = year
    return out


# ---------------------------------------------------------------------------
# Filter and Cleaning
# ---------------------------------------------------------------------------
def filter_professionals(df: pd.DataFrame, pattern: str = EMPLOYMENT_PATTERN) -> pd.DataFrame:
    mask = df["employment"].astype("string").str.contains(pattern, case=False, na=False, regex=True)
    return df[mask].copy()


def add_experience(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["years_pro"] = pd.to_numeric(df["years_pro"], errors="coerce")
    if "years_code" in df.columns:
        df["years_code"] = df["years_code"].map(parse_years)
    return df


def clean_compensation(
    df: pd.DataFrame,
    min_comp: float = MIN_COMP_USD,
    quantiles: tuple[float, float] = COMP_QUANTILES,
) -> pd.DataFrame:
    """Remove nulos, valores abaixo do mínimo e outliers (percentis por ano)."""
    df = df.copy()
    df["comp_yearly"] = pd.to_numeric(df["comp_yearly"], errors="coerce")
    df = df[df["comp_yearly"].notna() & (df["comp_yearly"] >= min_comp)].copy()
    q_lo, q_hi = quantiles
    lo = df.groupby("year")["comp_yearly"].transform(lambda s: s.quantile(q_lo))
    hi = df.groupby("year")["comp_yearly"].transform(lambda s: s.quantile(q_hi))
    df = df[(df["comp_yearly"] >= lo) & (df["comp_yearly"] <= hi)].copy()
    df["log_comp"] = np.log(df["comp_yearly"])
    return df


# ---------------------------------------------------------------------------
# IA Variables
# ---------------------------------------------------------------------------
def ai_use_group(raw: pd.Series) -> pd.Series:
    """'uses' | 'plans' | 'no' | <NA>. Compatível com as escalas de 2024 e 2025."""
    u = _norm(raw)
    out = pd.Series(pd.NA, index=raw.index, dtype="string")
    out[u.str.startswith("yes", na=False)] = "uses"
    out[u.str.contains("plan to soon", na=False)] = "plans"
    out[u.str.contains("don't plan", na=False)] = "no"
    return out


def add_ai_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Uso de IA: nunca tratar NaN como "No"
    group = ai_use_group(df["ai_use"])
    df["ai_use_group"] = group
    df["uses_ai"] = group.map({"uses": True, "plans": False, "no": False}).astype("boolean")

    # Frequência: só existe em 2025
    u = _norm(df["ai_use"])
    freq = pd.Series(pd.NA, index=df.index, dtype="string")
    freq[u.str.contains("daily", na=False)] = "daily"
    freq[u.str.contains("weekly", na=False)] = "weekly"
    freq[u.str.contains("monthly", na=False)] = "monthly_or_less"
    df["ai_use_frequency"] = freq

    # Escalas ordinais (1-5); categorias sem ordem (Unsure, "don't know") -> NaN
    df["ai_sentiment_score"] = _score(df["ai_sentiment"], AISENT_SCORE)
    df["ai_accuracy_score"] = _score(df["ai_accuracy"], AIACC_SCORE)
    df["ai_complexity_score"] = _score(df["ai_complexity"], AICOMPLEX_SCORE)

    # Ameaça percebida
    t = _norm(df["ai_threat"])
    threat = pd.Series(pd.NA, index=df.index, dtype="string")
    threat[t == "yes"] = "yes"
    threat[t == "no"] = "no"
    threat[t.str.contains("not sure", na=False)] = "not_sure"
    df["ai_threat_group"] = threat
    return df


# ---------------------------------------------------------------------------
# Step 4
# ---------------------------------------------------------------------------
def multi_hot(df: pd.DataFrame, col: str, top_n: int = 15, sep: str = ";") -> pd.DataFrame:
    dummies = df[col].fillna("").astype(str).str.get_dummies(sep=sep)
    dummies = dummies.drop(columns=[c for c in dummies.columns if c.strip() == ""], errors="ignore")
    top = dummies.sum().sort_values(ascending=False).head(top_n).index
    out = dummies[top].astype("int8")
    out.columns = [f"{col}__{c}" for c in out.columns]
    return out


def _log(steps: list[dict], name: str, df: pd.DataFrame) -> None:
    counts = df["year"].value_counts().to_dict()
    steps.append({"step": name, "total": len(df), **{str(y): n for y, n in sorted(counts.items())}})


def build_clean_dataset(
    frames: dict[int, pd.DataFrame] | None = None,
    save: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devolve (dataset limpo, tabela com as linhas que restam após cada passo)."""
    if frames is None:
        from src.data_loading import YEARS, load_year
        frames = {y: load_year(y) for y in YEARS}

    steps: list[dict] = []
    df = pd.concat([harmonize_columns(f, y) for y, f in frames.items()], ignore_index=True)
    _log(steps, "0. brutos (colunas mapeadas)", df)

    df = df.drop_duplicates(subset=["year", "response_id"])
    _log(steps, "1. sem ResponseId duplicado", df)

    df = filter_professionals(df)
    _log(steps, "2. profissionais a tempo inteiro", df)

    df = add_experience(df)
    df = df[df["years_pro"].notna() & (df["years_pro"] <= MAX_YEARS_PRO)].copy()
    _log(steps, "3. experiência válida (WorkExp)", df)

    df = df[df["country"].notna()].copy()
    _log(steps, "4. país conhecido", df)

    df = clean_compensation(df)
    _log(steps, "5. remuneração válida, sem outliers", df)

    df = add_ai_features(df)
    df = df.reset_index(drop=True)

    if save:
        PROCESSED.mkdir(parents=True, exist_ok=True)
        df.to_parquet(OUTPUT, index=False)
    return df, pd.DataFrame(steps)
