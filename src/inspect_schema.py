
from pathlib import Path

import pandas as pd

from data_loading import YEARS, load_year

DOCS = Path("docs")


def overview(df: pd.DataFrame, year: int) -> pd.DataFrame:
    rows = []
    for col in df.columns:
        s = df[col]
        rows.append({
            "year": year,
            "column": col,
            "dtype": str(s.dtype),
            "pct_missing": round(100 * s.isna().mean(), 1),
            "n_unique": s.nunique(dropna=True),
            "examples": " | ".join(map(str, s.dropna().unique()[:3]))[:120],
        })
    return pd.DataFrame(rows)


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    frames, cols = [], {}
    for y in YEARS:
        df = load_year(y)
        cols[y] = set(df.columns)
        frames.append(overview(df, y))
        print(f"{y}: {df.shape[0]:,} rows x {df.shape[1]} columns")
    pd.concat(frames).to_csv(DOCS / "columns_overview.csv", index=False)

    a, b = YEARS
    diff = (
        [(c, "both") for c in sorted(cols[a] & cols[b])]
        + [(c, f"only {a}") for c in sorted(cols[a] - cols[b])]
        + [(c, f"only {b}") for c in sorted(cols[b] - cols[a])]
    )
    pd.DataFrame(diff, columns=["column", "present_in"]).to_csv(
        DOCS / "columns_diff.csv", index=False
    )
    print(f"In both: {len(cols[a] & cols[b])} | only {a}: {len(cols[a]-cols[b])} "
          f"| only {b}: {len(cols[b]-cols[a])}")


if __name__ == "__main__":
    main()
