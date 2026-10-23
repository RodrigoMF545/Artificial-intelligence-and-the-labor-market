from __future__ import annotations

import pandas as pd

from src.cleaning import EMPLOYMENT_PATTERN, _norm, ai_use_group, parse_years


def check_duplicates(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rows = {
        y: {"linhas": len(df), "ResponseId_duplicados": int(df["ResponseId"].duplicated().sum())}
        for y, df in frames.items()
    }
    return pd.DataFrame(rows).T


def check_experience(frames: dict[int, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """WorkExp: tipo, faltas e intervalo; e coerência com YearsCodePro onde existir."""
    summary, coherence = {}, {}
    for y, df in frames.items():
        s = pd.to_numeric(df["WorkExp"], errors="coerce")
        summary[y] = {
            "dtype_original": str(df["WorkExp"].dtype),
            "pct_em_falta": round(100 * s.isna().mean(), 1),
            "min": s.min(), "mediana": s.median(), "max": s.max(),
        }
        if "YearsCodePro" in df.columns:
            pair = pd.concat(
                [s, df["YearsCodePro"].map(parse_years)], axis=1, keys=["WorkExp", "YearsCodePro"]
            ).dropna()
            coherence[y] = {
                "pares_validos": len(pair),
                "correlacao": round(float(pair.corr().iloc[0, 1]), 3),
                "diferenca_absoluta_mediana": float((pair["WorkExp"] - pair["YearsCodePro"]).abs().median()),
            }
    return pd.DataFrame(summary).T, pd.DataFrame(coherence).T


def check_employment(
    frames: dict[int, pd.DataFrame], pattern: str = EMPLOYMENT_PATTERN, top: int = 12
) -> tuple[dict[int, pd.DataFrame], pd.DataFrame]:
    """Valores mais comuns de Employment por ano e quantas linhas o filtro mantém."""
    counts, kept = {}, {}
    for y, df in frames.items():
        counts[y] = df["Employment"].value_counts(dropna=False).head(top).to_frame("n")
        m = df["Employment"].astype("string").str.contains(pattern, case=False, na=False, regex=True)
        kept[y] = {"linhas": len(df), "mantidas_pelo_filtro": int(m.sum()),
                   "pct_mantidas": round(100 * m.mean(), 1)}
    return counts, pd.DataFrame(kept).T


def check_ai_base(frames: dict[int, pd.DataFrame]) -> dict[tuple[int, str], pd.DataFrame]:
    """Para AIAcc, AISent e AIComplex: quem respondeu, por grupo de uso de IA.

    Se em 2025 houver muitas respostas no grupo 'no', a pergunta foi feita
    também a quem não usa IA (base diferente de 2024).
    """
    out = {}
    for y, df in frames.items():
        group = ai_use_group(df["AISelect"]).fillna("(em falta)")
        for col in ("AIAcc", "AISent", "AIComplex"):
            ct = pd.crosstab(group, df[col].notna().rename("respondeu"))
            ct = ct.reindex(columns=[False, True], fill_value=0)
            ct.columns = ["sem_resposta", "respondeu"]
            ct.index.name = "grupo_uso_ia"
            ct["pct_respondeu"] = (100 * ct["respondeu"] / ct.sum(axis=1)).round(1)
            out[(y, col)] = ct
    return out


def check_missing_ai(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    cols = ["AISelect", "AISent", "AIAcc", "AIComplex", "AIThreat"]
    return pd.DataFrame(
        {y: {c: round(100 * df[c].isna().mean(), 1) for c in cols if c in df.columns}
         for y, df in frames.items()}
    )


def check_countries(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Países que só aparecem num dos anos (possíveis diferenças de nomenclatura)."""
    years = sorted(frames)
    counts = pd.DataFrame({y: frames[y]["Country"].value_counts() for y in years}).fillna(0).astype(int)
    one_year = counts[(counts > 0).sum(axis=1) < len(years)]
    return one_year.sort_values(years[-1], ascending=False)


def check_compensation(frames: dict[int, pd.DataFrame]) -> pd.DataFrame:
    rows = {}
    for y, df in frames.items():
        s = pd.to_numeric(df["ConvertedCompYearly"], errors="coerce")
        q = s.quantile([0, 0.01, 0.25, 0.5, 0.75, 0.99, 1]).round(0)
        rows[y] = {"pct_em_falta": round(100 * s.isna().mean(), 1),
                   **{f"q{int(k * 100)}": v for k, v in q.items()}}
    return pd.DataFrame(rows).T
