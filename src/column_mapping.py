"""Mapping of equivalent columns across survey editions.

Verified against docs/columns_diff.csv and the output of `python -m src.check_mapping`
(2024: 65,437 responses | 2025: 49,191 responses).

Structure: canonical_name -> {year: column_name_for_that_year}
None = the column is not available in that year.
"""

MAPPING: dict[str, dict[int, str | None]] = {
    # --- Identification / filters -------------------------------------------
    "response_id":   {2024: "ResponseId", 2025: "ResponseId"},
    "employment":    {2024: "Employment", 2025: "Employment"},   # validate values
    "country":       {2024: "Country", 2025: "Country"},
    "dev_type":      {2024: "DevType", 2025: "DevType"},
    "ed_level":      {2024: "EdLevel", 2025: "EdLevel"},
    "org_size":      {2024: "OrgSize", 2025: "OrgSize"},
    "remote_work":   {2024: "RemoteWork", 2025: "RemoteWork"},

    # --- Experience and compensation -----------------------------------------
    # YearsCodePro is available only in 2024 -> use WorkExp (available in both years).
    "years_pro":     {2024: "WorkExp", 2025: "WorkExp"},
    # WorkExp is missing in ~55% of 2024 responses; YearsCodePro (2024 only)
    # has a 0.93 correlation and median difference of 0 with WorkExp -> used to fill missing values.
    "years_pro_alt": {2024: "YearsCodePro", 2025: None},
    "years_code":    {2024: "YearsCode", 2025: "YearsCode"},
    "comp_total":    {2024: "CompTotal", 2025: "CompTotal"},
    "comp_yearly":   {2024: "ConvertedCompYearly", 2025: "ConvertedCompYearly"},
    "job_sat":       {2024: "JobSat", 2025: "JobSat"},

    # --- Tecnologias (multi-valor, separadas por ';') ----------------------
    "languages":     {2024: "LanguageHaveWorkedWith", 2025: "LanguageHaveWorkedWith"},
    "databases":     {2024: "DatabaseHaveWorkedWith", 2025: "DatabaseHaveWorkedWith"},
    "platforms":     {2024: "PlatformHaveWorkedWith", 2025: "PlatformHaveWorkedWith"},
    "webframes":     {2024: "WebframeHaveWorkedWith", 2025: "WebframeHaveWorkedWith"},

    # --- AI: comparable across both years (harmonize values; see docs) ------
    "ai_use":        {2024: "AISelect", 2025: "AISelect"},
    "ai_sentiment":  {2024: "AISent", 2025: "AISent"},
    "ai_accuracy":   {2024: "AIAcc", 2025: "AIAcc"},
    "ai_complexity": {2024: "AIComplex", 2025: "AIComplex"},
    "ai_threat":     {2024: "AIThreat", 2025: "AIThreat"},

    # --- AI: available in only one year (supplementary analyses; NOT comparable) ----
    "ai_benefits":      {2024: "AIBen", 2025: None},
    "ai_ethics":        {2024: "AIEthics", 2025: None},
    "ai_challenges":    {2024: "AIChallenges", 2025: None},
    "ai_agents":        {2024: None, 2025: "AIAgents"},
    "ai_models_used":   {2024: None, 2025: "AIModelsHaveWorkedWith"},
    "ai_frustration":   {2024: None, 2025: "AIFrustration"},
    "ai_learn_how":     {2024: None, 2025: "AILearnHow"},
}
