"""Mapeamento de colunas equivalentes entre edições do survey.

Verificado contra docs/columns_diff.csv e a saída de `python -m src.check_mapping`
(2024: 65 437 respostas | 2025: 49 191 respostas).

Estrutura: nome_canónico -> {ano: nome_da_coluna_nesse_ano}
None = a coluna não existe nesse ano.
"""

MAPPING: dict[str, dict[int, str | None]] = {
    # --- Identificação / filtros -------------------------------------------
    "response_id":   {2024: "ResponseId", 2025: "ResponseId"},
    "employment":    {2024: "Employment", 2025: "Employment"},   # validar valores
    "country":       {2024: "Country", 2025: "Country"},
    "dev_type":      {2024: "DevType", 2025: "DevType"},
    "ed_level":      {2024: "EdLevel", 2025: "EdLevel"},
    "org_size":      {2024: "OrgSize", 2025: "OrgSize"},
    "remote_work":   {2024: "RemoteWork", 2025: "RemoteWork"},

    # --- Experiência e remuneração -----------------------------------------
    # YearsCodePro só existe em 2024 -> usar WorkExp (existe nos dois anos).
    "years_pro":     {2024: "WorkExp", 2025: "WorkExp"},
    "years_code":    {2024: "YearsCode", 2025: "YearsCode"},
    "comp_total":    {2024: "CompTotal", 2025: "CompTotal"},
    "comp_yearly":   {2024: "ConvertedCompYearly", 2025: "ConvertedCompYearly"},
    "job_sat":       {2024: "JobSat", 2025: "JobSat"},

    # --- Tecnologias (multi-valor, separadas por ';') ----------------------
    "languages":     {2024: "LanguageHaveWorkedWith", 2025: "LanguageHaveWorkedWith"},
    "databases":     {2024: "DatabaseHaveWorkedWith", 2025: "DatabaseHaveWorkedWith"},
    "platforms":     {2024: "PlatformHaveWorkedWith", 2025: "PlatformHaveWorkedWith"},
    "webframes":     {2024: "WebframeHaveWorkedWith", 2025: "WebframeHaveWorkedWith"},

    # --- IA: comparáveis nos dois anos (harmonizar valores, ver docs) ------
    "ai_use":        {2024: "AISelect", 2025: "AISelect"},
    "ai_sentiment":  {2024: "AISent", 2025: "AISent"},
    "ai_accuracy":   {2024: "AIAcc", 2025: "AIAcc"},
    "ai_complexity": {2024: "AIComplex", 2025: "AIComplex"},
    "ai_threat":     {2024: "AIThreat", 2025: "AIThreat"},

    # --- IA: só num dos anos (análises complementares, NÃO comparáveis) ----
    "ai_benefits":      {2024: "AIBen", 2025: None},
    "ai_ethics":        {2024: "AIEthics", 2025: None},
    "ai_challenges":    {2024: "AIChallenges", 2025: None},
    "ai_agents":        {2024: None, 2025: "AIAgents"},
    "ai_models_used":   {2024: None, 2025: "AIModelsHaveWorkedWith"},
    "ai_frustration":   {2024: None, 2025: "AIFrustration"},
    "ai_learn_how":     {2024: None, 2025: "AILearnHow"},
}