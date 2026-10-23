from pathlib import Path
import pandas as pd
import requests

BASE = "https://github.com/StackExchange/Survey/raw/refs/heads/main/packages/archive"
RAW = Path("data/raw")

YEARS = (2024, 2025)

def download_year(year: int) -> Path:
    RAW.mkdir(parents= True, exist_ok= True)
    dest = RAW / f"results_{year}.csv"
    if not dest.exists():
        r = requests.get(f"{BASE}/{year}/results.csv", timeout=120)
        r.raise_for_status()
        dest.write_bytes(r.content)
    return dest

def load_year(year: int) -> pd.DataFrame:
    df = pd.read_csv(download_year(year), low_memory=False)
    df["year"] = year
    return df

if __name__ == "__main__":
    for y in (2024, 2025):
        df = load_year(y)
        print(y, df.shape)