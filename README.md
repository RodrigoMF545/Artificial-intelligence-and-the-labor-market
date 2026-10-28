# AI and the Tech Labor Market: Stack Overflow Developer Survey Analysis (2024–2025)

This data analysis project explores how AI adoption relates to developers’ skills,
salaries, and professional profiles by comparing the 2024 and 2025 survey editions.

## Research Questions
1. Who uses AI?
2. Do AI users earn more (before and after adjustment)?
3. Which skills are associated with higher salaries?
4. How did sentiment toward AI and trust in it change between 2024 and 2025?
5. What developer profiles can be identified?

Details, hypotheses, and methods are documented in [`docs/objectives.md`](docs/objectives.md).

## Technology Stack
Python (pandas, NumPy), DuckDB (SQL), scikit-learn, XGBoost, SHAP, Plotly, and Streamlit.

## Reproducing the Analysis
```bash
git clone <repository-URL>
cd ai-job-market-analysis
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.data_loading       # downloads the 2024 and 2025 data to data/raw/
python -m src.inspect_schema     # creates a column inventory in docs/
python -m src.check_mapping      # validates the mapping between years
```

## Project Structure
```
data/raw, data/processed   data files (not versioned)
docs/                      objectives, column inventory, and mapping
notebooks/                 cleaning, EDA/SQL, and modeling
src/                       reusable code
sql/                       queries
app/                       Streamlit dashboard
reports/                   final report
```

## Data and License
Data: Stack Overflow Annual Developer Survey, subject to the license specified by Stack Overflow (see <https://survey.stackoverflow.co/>).
This repository does not redistribute the original data.
