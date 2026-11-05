"""Helper functions for the 02_eda_sql.ipynb notebook."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

FIGURES = Path("figures")

_NAMES = {
    "United States of America": "United States",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
}


def short_country(name: str) -> str:
    return _NAMES.get(name, name)


# --- SQL ---------------------------------------------------------------------
def load_queries(path: str = "sql/queries.sql") -> dict[str, str]:
    """Reads the .sql file and returns {name: text}. Each query starts with '-- name: <name>'."""
    text = Path(path).read_text(encoding="utf-8")
    parts = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.MULTILINE)
    queries = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        # remove the separator line (=====) that may appear at the end of a block
        lines = [ln for ln in body.strip().splitlines() if not ln.startswith("-- ====")]
        queries[name] = "\n".join(lines).strip().rstrip(";")
    return queries


def setup_views(con, queries: dict[str, str]) -> None:
    con.sql(queries["view_survey"])
    con.sql(queries["view_survey_exp"])


def run(con, queries: dict[str, str], name: str, **params) -> pd.DataFrame:
    """Executes a named query, filling in {parameters}."""
    return con.sql(queries[name].format(**params)).df()


# --- Statistics ------------------------------------------------------------------
def delta_ci(d: pd.DataFrame, label: str, z: float = 1.96) -> pd.DataFrame:
    """Change 2024->2025 in percentage points, with margin of error (95%).

    `d` must have columns: year, n, n_usa and the `label` column.
    If the interval includes 0, the change is indistinguishable from "nothing changed".
    """
    a = d[d["year"] == 2024].set_index(label)
    b = d[d["year"] == 2025].set_index(label)
    out = pd.DataFrame({
        "n_2024": a["n"], "n_2025": b["n"],
        "p24": a["n_usa"] / a["n"], "p25": b["n_usa"] / b["n"],
    }).dropna()
    out["delta_pp"] = 100 * (out["p25"] - out["p24"])
    se = ((out["p24"] * (1 - out["p24"]) / out["n_2024"])
          + (out["p25"] * (1 - out["p25"]) / out["n_2025"])) ** 0.5
    out["margin_pp"] = 100 * z * se
    out["ci_lo"] = out["delta_pp"] - out["margin_pp"]
    out["ci_hi"] = out["delta_pp"] + out["margin_pp"]
    out["distinct_from_zero"] = (out["ci_lo"] > 0) | (out["ci_hi"] < 0)
    cols = ["n_2024", "n_2025", "delta_pp", "margin_pp", "ci_lo", "ci_hi", "distinct_from_zero"]
    return out[cols].round(1).sort_values("delta_pp", ascending=False)


# --- Charts ----------------------------------------------------------------------
def dumbbell(d: pd.DataFrame, label: str, title: str, height_per_row: int = 22):
    """Two dots per category (2024 and 2025) connected by a line. Returns (fig, wide table)."""
    w = (d.pivot(index=label, columns="year", values="pct_usa_ia")
          .reset_index().sort_values(2025))
    fig = go.Figure()
    for _, r in w.iterrows():
        fig.add_trace(go.Scatter(x=[r[2024], r[2025]], y=[r[label]] * 2, mode="lines",
                                 line=dict(color="lightgray", width=3),
                                 showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=w[2024], y=w[label], mode="markers", name="2024", marker=dict(size=10)))
    fig.add_trace(go.Scatter(x=w[2025], y=w[label], mode="markers", name="2025", marker=dict(size=10)))
    fig.update_layout(title=title, xaxis_title="% using AI",
                      height=max(350, height_per_row * len(w)))
    return fig, w


def save_fig(fig, name: str) -> Path:
    """Saves to figures/: PNG if kaleido is available, otherwise interactive HTML."""
    FIGURES.mkdir(exist_ok=True)
    try:
        path = FIGURES / f"{name}.png"
        fig.write_image(str(path), scale=2)
    except Exception:  # noqa: BLE001
        path = FIGURES / f"{name}.html"
        fig.write_html(str(path))
    return path
