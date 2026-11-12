"""Exporta as tabelas para o Power BI (CSV, UTF-8 com BOM) em powerbi/data/.

Uso (a partir da raiz do projeto):
    python -m src.export_powerbi

Tabelas geradas
    fato_respostas     uma linha por resposta (dataset limpo)
    ponte_funcoes      id_resposta x função       (coluna multi-valor desdobrada)
    ponte_linguagens   id_resposta x linguagem    (coluna multi-valor desdobrada)
    dim_pais           país, nome curto, n por ano, elegível (n >= MIN_N nos dois anos)
    dim_faixa          faixas de experiência com ordem (para ordenar os gráficos)
    modelo_*           resultados do Dia 4 (copiados de reports/)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from eda_utils import short_country
from models_moduls.features import OTHER_ROLE, ORDEM_EXP, exp_band, load_clean

OUT = Path("powerbi/data")
REPORTS = Path("reports")
MIN_N = 100   # mesma decisão do Dia 3: n mínimo por país e ano

MODEL_TABLES = {
    "q1_adocao_ajustada.csv": "modelo_q1_adocao.csv",
    "q2_ols.csv": "modelo_q2_ols.csv",
    "q2_efeito_por_faixa.csv": "modelo_q2_faixa.csv",
    "q3_metricas.csv": "modelo_q3_metricas.csv",
    "q3_shap_grupos.csv": "modelo_q3_grupos.csv",
    "q3_shap_linguagens.csv": "modelo_q3_linguagens.csv",
    "q3_shap_funcoes.csv": "modelo_q3_funcoes.csv",
    "q4_testes.csv": "modelo_q4_testes.csv",
    "q5_clusters.csv": "modelo_q5_clusters.csv",
}


def _save(df: pd.DataFrame, name: str) -> None:
    df.to_csv(OUT / f"{name}.csv", index=False, encoding="utf-8-sig")
    print(f"  {name}.csv: {len(df):,} linhas x {df.shape[1]} colunas")


def _int(s: pd.Series) -> pd.Series:
    """Inteiro com vazios (em vez de decimais): evita problemas de vírgula/ponto no Power BI."""
    return pd.to_numeric(s, errors="coerce").round().astype("Int64")


def explode_multi(df: pd.DataFrame, col: str, name: str, exclude=()) -> pd.DataFrame:
    s = df[["id_resposta", "year", col]].dropna(subset=[col]).copy()
    s[col] = s[col].astype(str).str.split(";")
    s = s.explode(col)
    s[col] = s[col].str.strip()
    s = s[(s[col] != "") & (~s[col].isin(exclude))]
    return s.rename(columns={"year": "ano", col: name}).drop_duplicates().reset_index(drop=True)


def build_fact(df: pd.DataFrame) -> pd.DataFrame:
    faixa = exp_band(df["years_pro"])
    fact = pd.DataFrame({
        "id_resposta": df["id_resposta"],
        "ano": df["year"].astype(int),
        "pais": df["country"],
        "pais_curto": df["country"].map(short_country),
        "anos_exp": _int(df["years_pro"]),
        "faixa_exp": faixa.astype(str),
        "salario_usd": _int(df["comp_yearly"]),
        "usa_ia": _int(df["uses_ai"].astype("Int64")),            # 1 / 0 / vazio (nunca "0" para em falta)
        "grupo_uso_ia": df["ai_use_group"],
        "frequencia_ia": df["ai_use_frequency"],
        "sentimento_cat": df["ai_sentiment"],
        "confianca_cat": df["ai_accuracy"],
        "complexidade_cat": df["ai_complexity"],
        "ameaca_emprego": df["ai_threat_group"],
        "sentimento_score": _int(df["ai_sentiment_score"]),
        "confianca_score": _int(df["ai_accuracy_score"]),
        "complexidade_score": _int(df["ai_complexity_score"]),
    })
    for src, dst in (("remote_work", "trabalho_remoto"), ("org_size", "tamanho_empresa"),
                     ("ed_level", "educacao")):
        if src in df.columns:
            fact[dst] = df[src]
    return fact


def build_dim_pais(fact: pd.DataFrame) -> pd.DataFrame:
    base = (fact[fact["usa_ia"].notna()].groupby(["pais", "ano"]).size()
            .unstack(fill_value=0).reindex(columns=[2024, 2025], fill_value=0))
    dim = base.rename(columns={2024: "n_2024", 2025: "n_2025"}).reset_index()
    dim["pais_curto"] = dim["pais"].map(short_country)
    dim["elegivel"] = ((dim[["n_2024", "n_2025"]].min(axis=1)) >= MIN_N).astype(int)
    return dim[["pais", "pais_curto", "n_2024", "n_2025", "elegivel"]]


def copy_model_tables() -> None:
    for src, dst in MODEL_TABLES.items():
        path = REPORTS / src
        if not path.exists():
            print(f"  [aviso] {src} não encontrado (corre o notebook 03_modeling): ignorado")
            continue
        t = pd.read_csv(path)
        if str(t.columns[0]).startswith("Unnamed"):
            t = t.rename(columns={t.columns[0]: "item"})
        _save(t, dst.removesuffix(".csv"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    df = load_clean()
    df["id_resposta"] = df["year"].astype(str) + "-" + df["response_id"].astype(str)
    assert df["id_resposta"].is_unique, "id_resposta não é único"

    print("A exportar para", OUT)
    fact = build_fact(df)
    _save(fact, "fato_respostas")
    _save(explode_multi(df, "dev_type", "funcao", exclude=(OTHER_ROLE,)), "ponte_funcoes")
    _save(explode_multi(df, "languages", "linguagem"), "ponte_linguagens")
    _save(build_dim_pais(fact), "dim_pais")
    _save(pd.DataFrame({"faixa_exp": ORDEM_EXP, "ordem": range(1, len(ORDEM_EXP) + 1)}), "dim_faixa")
    copy_model_tables()
    print("Concluído.")


if __name__ == "__main__":
    main()
