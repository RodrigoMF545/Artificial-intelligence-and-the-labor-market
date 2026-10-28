"""Validates MAPPING against the actual data and displays the values in the AI columns.

Uso:
    python -m src.check_mapping
"""
from column_mapping import MAPPING
from data_loading import YEARS, load_year


def main() -> None:
    data = {y: load_year(y) for y in YEARS}
    print("=== Mapping validation ===")
    ok = True
    for canon, per_year in MAPPING.items():
        for y, col in per_year.items():
            if col is None:
                continue
            if col not in data[y].columns:
                ok = False
                print(f"[MISSING] {canon}: '{col}' does not exist in {y}")
    if ok:
        print("All mapped columns exist.")

    print("\n=== AI column values (for harmonization across years) ===")
    for canon in [k for k in MAPPING if k.startswith("ai_")]:
        for y in YEARS:
            col = MAPPING[canon].get(y)
            if col and col in data[y].columns:
                print(f"\n[{canon} | {y} | {col}]")
                print(data[y][col].value_counts(dropna=False).head(10).to_string())

    print("\n=== Columns with 'AI' in the name (candidates for the mapping) ===")
    for y in YEARS:
        ai_cols = [c for c in data[y].columns if "AI" in c]
        print(f"{y}: {ai_cols}")


if __name__ == "__main__":
    main()
