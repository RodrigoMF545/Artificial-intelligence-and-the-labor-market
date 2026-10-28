"""Validations to run BEFORE finalizing the cleaning rules (Day 2).

Each function takes `frames` = {year: raw DataFrame} and returns DataFrames
ready to display in the notebook.
"""
from __future__ import annotations

import pandas as pd

from src.cleaning import EMPLOYMENT_PATTERN, _norm, ai_use_group, parse_years


def check_duplicates(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rows = {
        y: {"rows": len(df), "duplicate_ResponseId": int(df["ResponseId"].duplicated().sum())}
        for y, df in frames.items()
    }
    return pd.DataFrame(rows).T


def check_experience(frames: dict[int, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """WorkExp: type, missing values, and range; plus consistency with YearsCodePro where available."""
    summary, coherence = {}, {}
    for y, df in frames.items():
        s = pd.to_numeric(df["WorkExp"], errors="coerce")
        summary[y] = {
            "dtype_original": str(df["WorkExp"].dtype),
            "pct_missing": round(100 * s.isna().mean(), 1),
            "min": s.min(), "median": s.median(), "max": s.max(),
        }
        if "YearsCodePro" in df.columns:
            pair = pd.concat(
                [s, df["YearsCodePro"].map(parse_years)], axis=1, keys=["WorkExp", "YearsCodePro"]
            ).dropna()
            coherence[y] = {
                "valid_pairs": len(pair),
                "correlation": round(float(pair.corr().iloc[0, 1]), 3),
                "median_absolute_difference": float((pair["WorkExp"] - pair["YearsCodePro"]).abs().median()),
                "WorkExp_missing_but_YearsCodePro_present": int(
                    (s.isna() & df["YearsCodePro"].notna()).sum()
                ),
            }
    return pd.DataFrame(summary).T, pd.DataFrame(coherence).T


def check_employment(
    frames: dict[int, pd.DataFrame], pattern: str = EMPLOYMENT_PATTERN, top: int = 12
) -> tuple[dict[int, pd.DataFrame], pd.DataFrame]:
    """Most common Employment values by year and how many rows the filter retains."""
    counts, kept = {}, {}
    for y, df in frames.items():
        counts[y] = df["Employment"].value_counts(dropna=False).head(top).to_frame("n")
        m = df["Employment"].astype("string").str.contains(pattern, case=False, na=False, regex=True)
        kept[y] = {"rows": len(df), "retained_by_filter": int(m.sum()),
                   "pct_retained": round(100 * m.mean(), 1)}
    return counts, pd.DataFrame(kept).T


def check_ai_base(frames: dict[int, pd.DataFrame]) -> dict[tuple[int, str], pd.DataFrame]:
    """For AIAcc, AISent, and AIComplex: who responded, by AI-use group.

    If many 2025 responses are in the 'no' group, the question was also asked
    of people who do not use AI (a different respondent base from 2024).
    """
    out = {}
    for y, df in frames.items():
        group = ai_use_group(df["AISelect"]).fillna("(missing)")
        for col in ("AIAcc", "AISent", "AIComplex"):
            ct = pd.crosstab(group, df[col].notna().rename("responded"))
            ct = ct.reindex(columns=[False, True], fill_value=0)
            ct.columns = ["no_response", "responded"]
            ct.index.name = "ai_use_group"
            ct["pct_responded"] = (100 * ct["responded"] / ct.sum(axis=1)).round(1)
            out[(y, col)] = ct
    return out


def check_missing_ai(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    cols = ["AISelect", "AISent", "AIAcc", "AIComplex", "AIThreat"]
    return pd.DataFrame(
        {y: {c: round(100 * df[c].isna().mean(), 1) for c in cols if c in df.columns}
         for y, df in frames.items()}
    )


def check_countries(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Countries that appear in only one year (possible naming differences)."""
    years = sorted(frames)
    counts = pd.DataFrame({y: frames[y]["Country"].value_counts() for y in years}).fillna(0).astype(int)
    one_year = counts[(counts > 0).sum(axis=1) < len(years)]
    return one_year.sort_values(years[-1], ascending=False)


def check_compensation(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rows = {}
    for y, df in frames.items():
        s = pd.to_numeric(df["ConvertedCompYearly"], errors="coerce")
        q = s.quantile([0, 0.01, 0.25, 0.5, 0.75, 0.99, 1]).round(0)
        rows[y] = {"pct_missing": round(100 * s.isna().mean(), 1),
                   **{f"q{int(k * 100)}": v for k, v in q.items()}}
    return pd.DataFrame(rows).T
