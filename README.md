# Artificial-intelligence-and-the-labor-market

This 5 questions will e responde over the follow projects

Perguntas de negócio
Quem usa IA? A adoção varia com país, experiência, função (DevType) e tecnologia?
IA e salário: devs que usam IA ganham mais? Ou é um efeito de confusão (seniores usam mais e ganham mais)?
Que skills pagam mais, controlando experiência e país?
Confiança e medo: o sentimento e a confiança na IA mudaram entre 2024 e 2025? Que perfis estão mais céticos?
Perfis de developers: que clusters existem (por stack, experiência, uso de IA)?

# Estrutura do repositório

ai-job-market-analysis/
├── README.md
├── requirements.txt
├── data/
│   ├── raw/            # CSV originais (não commitar se forem grandes; usar .gitignore)
│   └── processed/      # dados limpos (parquet)
├── notebooks/
│   ├── 01_cleaning.ipynb
│   ├── 02_eda_sql.ipynb
│   ├── 03_modeling.ipynb
├── src/
│   ├── data_loading.py
│   ├── cleaning.py
│   └── features.py
├── sql/
│   └── queries.sql
├── app/
│   └── streamlit_app.py
├── reports/
│   └── report.pdf
└── figures/