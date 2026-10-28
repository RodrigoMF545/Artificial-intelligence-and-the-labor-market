from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.column_mapping import MAPPING

PROCESSED = Path("data/processed")
OUTPUT = PROCESSED / "survey_clean.parquet"

# Professional filter. In 2024, `Employment` distinguishes "Employed, full-time" and
# "Employed, part-time"; in 2025, only "Employed" exists. To make the years comparable,
# the filter matches any token that is "Employed" (with or without details), and does NOT
# match "Not employed" or "Independent contractor...".
EMPLOYMENT_PATTERN = r"(?:^|;)\s*Employed(?:,|;|$)"

FILL_YEARS_PRO_FROM_ALT = True
MIN_COMP_USD = 1_000
COMP_QUANTILES = (0.01, 0.99)
MAX_YEARS_PRO = 50

# --- Ordinal scales (1 = most negative, 5 = most positive) ----------------
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


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------
def _norm(s: pd.Series) -> pd.Series:
    """Text in lowercase, trimmed, and using straight apostrophes."""
    return (
        s.astype("string")
        .str.replace("\u2019", "'", regex=False)
        .str.strip()
        .str.lower()
    )


def parse_years(x) -> float:
    """Converts 'Less than 1 year', 'More than 50 years', or '12' to a number."""
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
# Step 1: canonical names
# ---------------------------------------------------------------------------
def harmonize_columns(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Renames that year's columns to the canonical names in MAPPING."""
    rename = {
        per_year[year]: canon
        for canon, per_year in MAPPING.items()
        if per_year.get(year) and per_year[year] in df.columns
    }
    out = df[list(rename)].rename(columns=rename).copy()
    out["year"] = year
    return out


# ---------------------------------------------------------------------------
# Steps 2–4: filtering and cleaning
# ---------------------------------------------------------------------------
def filter_professionals(df: pd.DataFrame, pattern: str = EMPLOYMENT_PATTERN) -> pd.DataFrame:
    mask = df["employment"].astype("string").str.contains(pattern, case=False, na=False, regex=True)
    return df[mask].copy()


def add_experience(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["years_pro"] = pd.to_numeric(df["years_pro"], errors="coerce")
    if FILL_YEARS_PRO_FROM_ALT and "years_pro_alt" in df.columns:
        df["years_pro"] = df["years_pro"].fillna(df["years_pro_alt"].map(parse_years))
    if "years_code" in df.columns:
        df["years_code"] = df["years_code"].map(parse_years)
    return df


def clean_compensation(
    df: pd.DataFrame,
    min_comp: float = MIN_COMP_USD,
    quantiles: tuple[float, float] = COMP_QUANTILES,
) -> pd.DataFrame:
    """Removes nulls, values below the minimum, and outliers (year-specific percentiles)."""
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
# Step 5: AI features (preserving NaN)
# ---------------------------------------------------------------------------
def ai_use_group(raw: pd.Series) -> pd.Series:
    """'uses' | 'plans' | 'no' | <NA>. Compatible with the 2024 and 2025 scales."""
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

    # Frequency: available only in 2025
    u = _norm(df["ai_use"])
    freq = pd.Series(pd.NA, index=df.index, dtype="string")
    freq[u.str.contains("daily", na=False)] = "daily"
    freq[u.str.contains("weekly", na=False)] = "weekly"
    freq[u.str.contains("monthly", na=False)] = "monthly_or_less"
    df["ai_use_frequency"] = freq

    # Ordinal scales (1–5); unordered categories (Unsure, "don't know") -> NaN
    df["ai_sentiment_score"] = _score(df["ai_sentiment"], AISENT_SCORE)
    df["ai_accuracy_score"] = _score(df["ai_accuracy"], AIACC_SCORE)
    df["ai_complexity_score"] = _score(df["ai_complexity"], AICOMPLEX_SCORE)

    # Perceived threat
    t = _norm(df["ai_threat"])
    threat = pd.Series(pd.NA, index=df.index, dtype="string")
    threat[t == "yes"] = "yes"
    threat[t == "no"] = "no"
    threat[t.str.contains("not sure", na=False)] = "not_sure"
    df["ai_threat_group"] = threat
    return df


# ---------------------------------------------------------------------------
# Modeling helper (Day 4): multi-value fields -> 0/1 columns
# ---------------------------------------------------------------------------
def multi_hot(df: pd.DataFrame, col: str, top_n: int = 15, sep: str = ";") -> pd.DataFrame:
    dummies = df[col].fillna("").astype(str).str.get_dummies(sep=sep)
    dummies = dummies.drop(columns=[c for c in dummies.columns if c.strip() == ""], errors="ignore")
    top = dummies.sum().sort_values(ascending=False).head(top_n).index
    out = dummies[top].astype("int8")
    out.columns = [f"{col}__{c}" for c in out.columns]
    return out


# ---------------------------------------------------------------------------
# Pipeline completo
# ---------------------------------------------------------------------------
def _log(steps: list[dict], name: str, df: pd.DataFrame, years) -> None:
    """Records rows by year; raises an error if any year disappears completely."""
    counts = df["year"].value_counts().to_dict()
    row = {"step": name, "total": len(df)}
    for y in sorted(years):
        row[str(y)] = int(counts.get(y, 0))
    steps.append(row)
    empty = [y for y in years if counts.get(y, 0) == 0]
    if empty:
        raise ValueError(
            f"Year(s) {empty} have no rows after step '{name}'. "
            "Verifica os filtros (por exemplo EMPLOYMENT_PATTERN)."
        )


def build_clean_dataset(
    frames: dict[int, pd.DataFrame] | None = None,
    save: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (clean dataset, table with the rows remaining after each step)."""
    if frames is None:
        from src.data_loading import YEARS, load_year
        frames = {y: load_year(y) for y in YEARS}

    steps: list[dict] = []
    years = list(frames)
    df = pd.concat([harmonize_columns(f, y) for y, f in frames.items()], ignore_index=True)
    _log(steps, "0. raw (mapped columns)", df, years)

    df = df.drop_duplicates(subset=["year", "response_id"])
    _log(steps, "1. sem ResponseId duplicado", df, years)

    df = filter_professionals(df)
    _log(steps, "2. empregados (Employed)", df, years)

    df = add_experience(df)
    df = df[df["years_pro"].notna() & (df["years_pro"] <= MAX_YEARS_PRO)].copy()
    _log(steps, "3. valid experience (WorkExp)", df, years)

    df = df[df["country"].notna()].copy()
    _log(steps, "4. known country", df, years)

    df = clean_compensation(df)
    _log(steps, "5. valid compensation, no outliers", df, years)

    df = add_ai_features(df)
    df = df.reset_index(drop=True)

    if save:
        PROCESSED.mkdir(parents=True, exist_ok=True)
        df.to_parquet(OUTPUT, index=False)
    return df, pd.DataFrame(steps)
