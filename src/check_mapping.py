"""Valida o MAPPING contra os dados reais e mostra os valores das colunas de IA.

Uso:
    python -m src.check_mapping
"""
from column_mapping import MAPPING
from data_loading import YEARS, load_year


def main() -> None:
    data = {y: load_year(y) for y in YEARS}
    print("=== Validação do mapeamento ===")
    ok = True
    for canon, per_year in MAPPING.items():
        for y, col in per_year.items():
            if col is None:
                continue
            if col not in data[y].columns:
                ok = False
                print(f"[FALTA] {canon}: '{col}' não existe em {y}")
    if ok:
        print("Todas as colunas mapeadas existem.")

    print("\n=== Valores das colunas de IA (para harmonizar entre anos) ===")
    for canon in [k for k in MAPPING if k.startswith("ai_")]:
        for y in YEARS:
            col = MAPPING[canon].get(y)
            if col and col in data[y].columns:
                print(f"\n[{canon} | {y} | {col}]")
                print(data[y][col].value_counts(dropna=False).head(10).to_string())

    print("\n=== Colunas com 'AI' no nome (candidatas a incluir no mapeamento) ===")
    for y in YEARS:
        ai_cols = [c for c in data[y].columns if "AI" in c]
        print(f"{y}: {ai_cols}")


if __name__ == "__main__":
    main()
