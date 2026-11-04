-- ============================================================================
-- queries.sql: DuckDB queries for Day 3 (EDA)
-- Single source of truth: notebook 02_eda_sql.ipynb reads this file.
-- Parameters in braces, e.g. {MIN_N}, are filled in by the notebook.
--   MIN_N        minimum sample per country/role/technology and year (decision: 100)
--   MIN_CELL     minimum sample per cell in a median                (decision: 50)
--   MIN_CELL_TEC minimum sample per country x technology cell       (decision: 30)
--   TOP_PAISES, TOP_TEC   ranking map dimensions
-- Rule: percentages only over respondents (COUNT(col) ignores NULL;
--       AVG ignores NULL; NEVER treat NULL as "No").
-- ============================================================================


-- name: view_survey
-- Shortcut to the clean parquet (does not copy data).
CREATE OR REPLACE VIEW survey AS
SELECT * FROM 'data/processed/survey_clean.parquet'


-- name: view_survey_exp
-- Adds experience bands (numeric order for correct sorting).
-- The CASE evaluates in order: the upper bound of each band is sufficient.
CREATE OR REPLACE VIEW survey_exp AS
SELECT *,
       CASE WHEN years_pro < 2  THEN 1
            WHEN years_pro < 5  THEN 2
            WHEN years_pro < 10 THEN 3
            WHEN years_pro < 20 THEN 4
            ELSE 5 END AS ordem,
       CASE WHEN years_pro < 2  THEN '0-1 anos'
            WHEN years_pro < 5  THEN '2-4 anos'
            WHEN years_pro < 10 THEN '5-9 anos'
            WHEN years_pro < 20 THEN '10-19 anos'
            ELSE '20+ anos' END AS faixa
FROM survey
WHERE years_pro IS NOT NULL


-- ============================ Q1: who uses AI? ==============================

-- name: adocao_ano
-- G1. COUNT(*) counts all; COUNT(uses_ai) only respondents; AVG ignores NULL.
SELECT year,
       COUNT(*)                          AS n_total,
       COUNT(uses_ai)                    AS n_responderam,
       ROUND(100 * AVG(uses_ai::INT), 1) AS pct_usa_ia
FROM survey
GROUP BY year
ORDER BY year


-- name: frequencia_2025
-- G2. SUM(COUNT(*)) OVER () = window function over all rows.
SELECT ai_use_frequency,
       COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM survey
WHERE year = 2025 AND uses_ai
GROUP BY ai_use_frequency
ORDER BY n DESC


-- name: paises_n
-- Before setting the threshold: how many responses does each country have?
-- FILTER counts only the rows that meet the condition; LEAST = smaller of the two years.
SELECT country,
       COUNT(*) FILTER (WHERE year = 2024) AS n_2024,
       COUNT(*) FILTER (WHERE year = 2025) AS n_2025
FROM survey
WHERE uses_ai IS NOT NULL
GROUP BY country
ORDER BY LEAST(n_2024, n_2025) DESC
LIMIT 25


-- name: limiares
-- How many countries and what % of responses survive each threshold (CTE + VALUES).
WITH por_pais AS (
  SELECT country,
         COUNT(*) FILTER (WHERE year = 2024) AS n_2024,
         COUNT(*) FILTER (WHERE year = 2025) AS n_2025
  FROM survey
  WHERE uses_ai IS NOT NULL
  GROUP BY country
)
SELECT t.limiar,
       COUNT(*) FILTER (WHERE LEAST(n_2024, n_2025) >= t.limiar) AS paises,
       ROUND(100.0 * SUM(n_2024 + n_2025) FILTER (WHERE LEAST(n_2024, n_2025) >= t.limiar)
             / SUM(n_2024 + n_2025), 1) AS pct_respostas_cobertas
FROM por_pais
CROSS JOIN (VALUES (30), (50), (100), (200)) AS t(limiar)
GROUP BY t.limiar
ORDER BY t.limiar


-- name: adocao_pais
-- G3. WHERE filters rows before grouping; HAVING filters groups after.
WITH base AS (
  SELECT country, year,
         COUNT(uses_ai)         AS n,
         SUM(uses_ai::INT)::INT AS n_usa
  FROM survey
  GROUP BY country, year
),
validos AS (
  SELECT country
  FROM base
  GROUP BY country
  HAVING COUNT(*) = 2 AND MIN(n) >= {MIN_N}
)
SELECT b.country, b.year, b.n, b.n_usa,
       ROUND(100.0 * b.n_usa / b.n, 1) AS pct_usa_ia
FROM base b
JOIN validos v USING (country)
ORDER BY b.country, b.year


-- name: adocao_funcao
-- G4. Multi-value column: unnest(string_split(...)) creates one row per role.
-- The categories are NOT exclusive (one person can appear in multiple roles).
WITH longo AS (
  SELECT year, uses_ai,
         TRIM(unnest(string_split(dev_type, ';'))) AS funcao
  FROM survey
  WHERE dev_type IS NOT NULL
),
base AS (
  SELECT funcao, year,
         COUNT(uses_ai)         AS n,
         SUM(uses_ai::INT)::INT AS n_usa
  FROM longo
  GROUP BY funcao, year
)
SELECT funcao, year, n, n_usa,
       ROUND(100.0 * n_usa / n, 1) AS pct_usa_ia
FROM base
WHERE funcao IN (SELECT funcao FROM base GROUP BY funcao HAVING COUNT(*) = 2 AND MIN(n) >= {MIN_N})
ORDER BY funcao, year


-- name: adocao_experiencia
-- G5. Uses the survey_exp view (bands already created).
SELECT faixa, year,
       COUNT(uses_ai)         AS n,
       SUM(uses_ai::INT)::INT AS n_usa,
       ROUND(100.0 * SUM(uses_ai::INT) / COUNT(uses_ai), 1) AS pct_usa_ia
FROM survey_exp
GROUP BY ordem, faixa, year
ORDER BY ordem, year


-- ============================ Q2/Q3: salary =================================

-- name: salario_resumo
-- G6 (table). Median instead of mean: the distribution has a long tail.
SELECT year,
       COUNT(*)                                AS n,
       ROUND(AVG(comp_yearly))                 AS media,
       ROUND(MEDIAN(comp_yearly))              AS mediana,
       ROUND(QUANTILE_CONT(comp_yearly, 0.25)) AS q1,
       ROUND(QUANTILE_CONT(comp_yearly, 0.75)) AS q3
FROM survey
GROUP BY year
ORDER BY year


-- name: salario_experiencia
-- Stratify: compare 2024 vs 2025 WITHIN each band (tests the composition effect).
SELECT faixa, year, COUNT(*) AS n, ROUND(MEDIAN(comp_yearly)) AS mediana
FROM survey_exp
GROUP BY ordem, faixa, year
ORDER BY ordem, year


-- name: salario_ia_bruto
-- RAW difference (no controls): AI users vs non-users. Compare with salario_ia_experiencia.
SELECT year, uses_ai, COUNT(*) AS n, ROUND(MEDIAN(comp_yearly)) AS mediana
FROM survey
WHERE uses_ai IS NOT NULL
GROUP BY year, uses_ai
ORDER BY year, uses_ai


-- name: salario_ia_experiencia
-- G8. Stratified by experience. Descriptive only: country and role remain uncontrolled.
SELECT faixa, year, uses_ai, COUNT(*) AS n, ROUND(MEDIAN(comp_yearly)) AS mediana
FROM survey_exp
WHERE uses_ai IS NOT NULL
GROUP BY ordem, faixa, year, uses_ai
HAVING COUNT(*) >= {MIN_CELL}
ORDER BY ordem, year, uses_ai


-- name: salario_tecnologia
-- G7. Median by language. Descriptive, not causal (country and experience confound).
WITH longo AS (
  SELECT year, comp_yearly,
         TRIM(unnest(string_split(languages, ';'))) AS tecnologia
  FROM survey
  WHERE languages IS NOT NULL
)
SELECT tecnologia, year, COUNT(*) AS n, ROUND(MEDIAN(comp_yearly)) AS mediana
FROM longo
GROUP BY tecnologia, year
HAVING COUNT(*) >= {MIN_N}
ORDER BY tecnologia, year


-- name: ranking_tecnologia_pais
-- G9. Window function: RANK() OVER (PARTITION BY country ...) restarts for each country.
-- RANK gives the same position to ties and skips the next (1, 1, 1, 4).
WITH longo AS (
  SELECT country, comp_yearly,
         TRIM(unnest(string_split(languages, ';'))) AS tecnologia
  FROM survey
  WHERE year = 2025 AND languages IS NOT NULL
),
top_paises AS (SELECT country    FROM longo GROUP BY country    ORDER BY COUNT(*) DESC LIMIT {TOP_PAISES}),
top_tec    AS (SELECT tecnologia FROM longo GROUP BY tecnologia ORDER BY COUNT(*) DESC LIMIT {TOP_TEC}),
celulas AS (
  SELECT country, tecnologia, COUNT(*) AS n, MEDIAN(comp_yearly) AS mediana
  FROM longo
  WHERE country IN (SELECT country FROM top_paises)
    AND tecnologia IN (SELECT tecnologia FROM top_tec)
  GROUP BY country, tecnologia
  HAVING COUNT(*) >= {MIN_CELL_TEC}
)
SELECT country, tecnologia, n, ROUND(mediana) AS mediana,
       RANK() OVER (PARTITION BY country ORDER BY mediana DESC) AS ranking
FROM celulas
ORDER BY country, ranking


-- ============================ Q4: trust =====================================

-- name: confianca_ia
-- G10. Only users in both years (comparable base). PARTITION BY year = total per year.
SELECT year, ai_accuracy, COUNT(*) AS n,
       ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY year), 1) AS pct
FROM survey
WHERE uses_ai AND ai_accuracy IS NOT NULL
GROUP BY year, ai_accuracy
ORDER BY year, n DESC