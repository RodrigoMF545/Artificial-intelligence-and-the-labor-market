# Column Mapping 2024 ↔ 2025

Base: 2024 = 65,437 responses | 2025 = 49,191 responses.
Verified against `docs/columns_diff.csv` and `python -m src.check_mapping`.

## Columns Present in Both Years

| Canonical name | Column (2024 and 2025) | Notes |
|---|---|---|
| response_id | ResponseId | |
| employment | Employment | Validate values in both years (2025 also has `EmploymentAddl`) |
| country | Country | |
| dev_type | DevType | Multi-value (`;`) |
| ed_level | EdLevel | |
| org_size | OrgSize | |
| remote_work | RemoteWork | |
| years_pro | **WorkExp** | Replaces `YearsCodePro` (available only in 2024) |
| years_code | YearsCode | Special strings ("Less than 1 year") |
| comp_total / comp_yearly | CompTotal / ConvertedCompYearly | Use `ConvertedCompYearly` (USD) |
| job_sat | JobSat | |
| languages | LanguageHaveWorkedWith | Multi-value |
| databases | DatabaseHaveWorkedWith | Multi-value |
| platforms | PlatformHaveWorkedWith | Multi-value |
| webframes | WebframeHaveWorkedWith | Multi-value |
| ai_use | AISelect | **Scale changed** (see below) |
| ai_sentiment | AISent | Same (5 levels + Indifferent/Unsure) |
| ai_accuracy | AIAcc | Same (5-level trust scale) |
| ai_complexity | AIComplex | 2025 adds the option "I don't use AI tools for complex tasks / I don't know" |
| ai_threat | AIThreat | Same (Yes / No / I'm not sure) |

## Columns That Are Not Comparable (Present in Only One Year)

| Topic | 2024 | 2025 |
|---|---|---|
| AI tools | `AIToolCurrently Using`, `AIToolInterested in Using`, `AIToolNot interested in Using` | `AIToolCurrently mostly AI`, `AIToolCurrently partially AI`, `AIToolPlan to ...`, `AIToolDon't plan ...` (different structure) |
| Benefits/ethics/challenges | `AIBen`, `AIEthics`, `AIChallenges` | n/a |
| AI agents | n/a | `AIAgents`, `AIAgent*` (new section) |
| AI models | n/a | `AIModels*` |
| Frustration/learning | n/a | `AIFrustration`, `AILearnHow`, `LearnCodeAI` |

Use these for supplementary analyses within each year, never for direct 2024-versus-2025 comparisons.

## Harmonization Decisions

**1. Experience.** `YearsCodePro` is unavailable in 2025. Use `WorkExp` in both years.
On Day 2, validate that `WorkExp` is numeric and compare it with `YearsCodePro` in 2024 (correlation) before adopting it.

**2. AI use (`AISelect`).** Values differ:
- 2024: `Yes` | `No, but I plan to soon` | `No, and I don't plan to`
- 2025: `Yes, I use AI tools daily` | `... weekly` | `... monthly or infrequently` | `No, but I plan to soon` | `No, and I don't plan to`

Proposed rule:
- `uses_ai` (binary): `True` if the value starts with "Yes", `False` if it starts with "No", **NaN if missing**.
- `ai_use_group` (3 levels): `uses` / `plans` / `no`.
- `ai_use_frequency`: 2025 only (daily/weekly/monthly); supplementary analysis.

**3. Missing values in AI columns.** Do not treat NaN as "No".
- `AISelect` is missing for ~7% in 2024 versus ~31% in 2025—a large difference, probably due to questionnaire design. Report it and test the robustness of the conclusions to this difference.
- `AIAcc` and `AIComplex` have many NaNs because they were probably asked only of AI users. Analyze only respondents who answered, and state this in the report.

**4. `AIComplex` in 2025.** The option "I don't use AI tools for complex tasks / I don't know" is unavailable in 2024; treat it as NaN in comparisons across years.

**5. Ordinal scales.** Convert `AISent`, `AIAcc`, and `AIComplex` to ordinal values (1–5) for comparisons across years; keep "Indifferent/Unsure/Neither" as a separate category where appropriate.
