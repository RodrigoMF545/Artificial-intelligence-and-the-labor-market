# Project Objectives

**Main question:** How is AI adoption related to developers’ skills, compensation, and professional profiles, and what changed between 2024 and 2025?

**Data source:** Stack Overflow Annual Developer Survey, 2024 and 2025 editions
(<https://survey.stackoverflow.co/>).

**Scope:** Full-time professionals who reported annual compensation.
Countries with small samples (n < 200 per year) are excluded from cross-country comparisons.

---

## Q1. Who uses AI?
- **Hypothesis:** Adoption is higher among younger profiles and in certain roles, and varies by country.
- **Variables:** To be defined.
- **Method:** Adoption rates by segment (SQL); logistic regression of `uses_ai`.
- **Success criteria:** A table and charts of adoption by segment with confidence intervals and interpretable coefficients.

## Q2. Do AI users earn more?
- **Hypothesis:** There is a raw difference, but it decreases (or disappears) after controlling for experience, country, and role.
- **Variables:** To be defined.
- **Method:** Raw difference (Mann–Whitney test + effect size) versus adjusted linear regression (OLS, robust standard errors).
- **Success criteria:** Side-by-side raw and adjusted effects, with a clear distinction between correlation and causation.

## Q3. Which skills are associated with higher salaries?
- **Hypothesis:** Some technologies carry a salary premium even after controlling for experience and country.
- **Variables:** Languages, databases, and platforms; log salary; controls.
- **Method:** Random forest/XGBoost + SHAP; comparison with linear regression.
- **Success criteria:** A ranking of technologies by estimated impact and validation metrics (R², MAE on the log scale and in USD).

## Q4. How did sentiment toward AI and trust in it change between 2024 and 2025?
- **Hypothesis:** Adoption increased, but trust in AI accuracy did not keep pace.
- **Variables:** Sentiment, trust in accuracy, perceived threat, year, experience, and role.
- **Method:** Compare distributions across years; chi-square tests/Cramér’s V; harmonize the scales.
- **Success criteria:** Comparable charts across years and a conclusion about which profiles are more skeptical.

## Q5. What developer profiles can be identified?
- **Hypothesis:** Distinct clusters emerge based on technology stack, experience, and AI use.
- **Variables:** Technologies (one-hot encoded), experience, AI use, and role.
- **Method:** K-means (choose k using silhouette score) and UMAP/PCA projection for visualization.
- **Success criteria:** 3–5 interpretable profiles, each with a name and description, plus median salary by profile.

## Assumed Limitations (to be expanded in the report)
- Self-selected sample (Stack Overflow community), not representative of all developers.
- Salaries converted to USD by the survey itself, with no cost-of-living adjustment.
- AI questions changed between editions; only harmonizable items are compared.
- Results are associations, not causal effects.
