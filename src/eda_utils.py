"""Funções de apoio ao notebook 02_eda_sql.ipynb."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

FIGURES = Path("figures")

_NOMES = {
    "United States of America": "United States",
    "United Kingdom of Great Britain and Northern Ireland": "United Kingdom",
}


def short_country(name: str) -> str:
    return _NOMES.get(name, name)


# --- SQL ---------------------------------------------------------------------
def load_queries(path: str = "sql/queries.sql") -> dict[str, str]:
    """Lê o .sql e devolve {nome: texto}. Cada consulta começa com '-- name: <nome>'."""
    text = Path(path).read_text(encoding="utf-8")
    parts = re.split(r"^-- name:\s*(\w+)\s*$", text, flags=re.MULTILINE)
    queries = {}
    for name, body in zip(parts[1::2], parts[2::2]):
        # remove a linha de separadores (=====) que pode vir no fim do bloco
        lines = [ln for ln in body.strip().splitlines() if not ln.startswith("-- ====")]
        queries[name] = "\n".join(lines).strip().rstrip(";")
    return queries


def setup_views(con, queries: dict[str, str]) -> None:
    con.sql(queries["view_survey"])
    con.sql(queries["view_survey_exp"])


def run(con, queries: dict[str, str], name: str, **params) -> pd.DataFrame:
    """Executa uma consulta nomeada, preenchendo {parâmetros}."""
    return con.sql(queries[name].format(**params)).df()


# --- Estatística -----------------------------------------------------------------
def delta_ci(d: pd.DataFrame, label: str, z: float = 1.96) -> pd.DataFrame:
    """Variação 2024->2025 em pontos percentuais, com margem de erro (95%).

    `d` precisa das colunas: year, n, n_usa e a coluna `label`.
    Se o intervalo incluir 0, a variação não é distinguível de "nada mudou".
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
    out["margem_pp"] = 100 * z * se
    out["ic_inf"] = out["delta_pp"] - out["margem_pp"]
    out["ic_sup"] = out["delta_pp"] + out["margem_pp"]
    out["distinto_de_zero"] = (out["ic_inf"] > 0) | (out["ic_sup"] < 0)
    cols = ["n_2024", "n_2025", "delta_pp", "margem_pp", "ic_inf", "ic_sup", "distinto_de_zero"]
    return out[cols].round(1).sort_values("delta_pp", ascending=False)


# --- Gráficos --------------------------------------------------------------------
def dumbbell(d: pd.DataFrame, label: str, title: str, height_per_row: int = 22):
    """Dois pontos por categoria (2024 e 2025) ligados por uma linha. Devolve (fig, tabela larga)."""
    w = (d.pivot(index=label, columns="year", values="pct_usa_ia")
          .reset_index().sort_values(2025))
    fig = go.Figure()
    for _, r in w.iterrows():
        fig.add_trace(go.Scatter(x=[r[2024], r[2025]], y=[r[label]] * 2, mode="lines",
                                 line=dict(color="lightgray", width=3),
                                 showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=w[2024], y=w[label], mode="markers", name="2024", marker=dict(size=10)))
    fig.add_trace(go.Scatter(x=w[2025], y=w[label], mode="markers", name="2025", marker=dict(size=10)))
    fig.update_layout(title=title, xaxis_title="% que usa IA",
                      height=max(350, height_per_row * len(w)))
    return fig, w


def save_fig(fig, name: str) -> Path:
    """Guarda em figures/: PNG se o kaleido estiver disponível, senão HTML interativo."""
    FIGURES.mkdir(exist_ok=True)
    try:
        path = FIGURES / f"{name}.png"
        fig.write_image(str(path), scale=2)
    except Exception:  # noqa: BLE001
        path = FIGURES / f"{name}.html"
        fig.write_html(str(path))
    return path
