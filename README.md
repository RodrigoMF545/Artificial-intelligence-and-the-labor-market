# IA e mercado de trabalho tech: análise do Stack Overflow Developer Survey (2024-2025)

Projeto de análise de dados que explora como a adoção de IA se relaciona com competências,
salários e perfis profissionais de developers, comparando as edições 2024 e 2025.


## Perguntas
1. Quem usa IA?
2. Quem usa IA ganha mais (efeito bruto vs. ajustado)?
3. Que competências estão associadas a salários mais altos?
4. Como mudaram o sentimento e a confiança na IA entre 2024 e 2025?
5. Que perfis de developers existem?

Detalhes, hipóteses e métodos em [`docs/objectives.md`](docs/objectives.md).

## Stack
Python (pandas, NumPy), DuckDB (SQL), scikit-learn, XGBoost, SHAP, Plotly, Streamlit.

## Como reproduzir
```bash
git clone <URL-do-repositório>
cd ai-job-market-analysis
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.data_loading       # descarrega 2024 e 2025 para data/raw/
python -m src.inspect_schema     # inventário de colunas -> docs/
python -m src.check_mapping      # valida o mapeamento entre anos
```

## Estrutura
```
data/raw, data/processed   dados (não versionados)
docs/                      objetivos, inventário de colunas, mapeamento
notebooks/                 limpeza, EDA/SQL, modelação
src/                       código reutilizável
sql/                       consultas
app/                       dashboard Streamlit
reports/                   relatório final
```

## Dados e licença
Dados: Stack Overflow Annual Developer Survey, sujeitos à licença indicada pelo Stack Overflow (ver <https://survey.stackoverflow.co/>).
Este repositório não redistribui os dados originais.

