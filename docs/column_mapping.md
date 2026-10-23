# Mapeamento de colunas 2024 ↔ 2025

Base: 2024 = 65 437 respostas | 2025 = 49 191 respostas.
Verificado com `docs/columns_diff.csv` e `python -m src.check_mapping`.

## Colunas presentes nos dois anos

| Nome canónico | Coluna (2024 e 2025) | Notas |
|---|---|---|
| response_id | ResponseId | |
| employment | Employment | Validar valores nos dois anos (2025 tem também `EmploymentAddl`) |
| country | Country | |
| dev_type | DevType | multi-valor (`;`) |
| ed_level | EdLevel | |
| org_size | OrgSize | |
| remote_work | RemoteWork | |
| years_pro | **WorkExp** | substitui `YearsCodePro` (só existe em 2024) |
| years_code | YearsCode | strings especiais ("Less than 1 year") |
| comp_total / comp_yearly | CompTotal / ConvertedCompYearly | usar `ConvertedCompYearly` (USD) |
| job_sat | JobSat | |
| languages | LanguageHaveWorkedWith | multi-valor |
| databases | DatabaseHaveWorkedWith | multi-valor |
| platforms | PlatformHaveWorkedWith | multi-valor |
| webframes | WebframeHaveWorkedWith | multi-valor |
| ai_use | AISelect | **escala mudou** (ver abaixo) |
| ai_sentiment | AISent | igual (5 níveis + Indifferent/Unsure) |
| ai_accuracy | AIAcc | igual (escala de confiança 5 níveis) |
| ai_complexity | AIComplex | 2025 acrescenta opção "I don't use AI tools for complex tasks / I don't know" |
| ai_threat | AIThreat | igual (Yes / No / I'm not sure) |

## Colunas que NÃO são comparáveis (só num dos anos)

| Tema | 2024 | 2025 |
|---|---|---|
| Ferramentas de IA | `AIToolCurrently Using`, `AIToolInterested in Using`, `AIToolNot interested in Using` | `AIToolCurrently mostly AI`, `AIToolCurrently partially AI`, `AIToolPlan to ...`, `AIToolDon't plan ...` (estrutura diferente) |
| Benefícios/ética/desafios | `AIBen`, `AIEthics`, `AIChallenges` | n/a |
| Agentes de IA | n/a | `AIAgents`, `AIAgent*` (secção nova) |
| Modelos de IA | n/a | `AIModels*` |
| Frustração/aprendizagem | n/a | `AIFrustration`, `AILearnHow`, `LearnCodeAI` |

Uso: análises complementares dentro de cada ano, nunca comparações diretas 2024 vs 2025.

## Decisões de harmonização

**1. Experiência.** `YearsCodePro` não existe em 2025. Usar `WorkExp` nos dois anos.
Validar no Dia 2 que `WorkExp` é numérica e comparar com `YearsCodePro` em 2024 (correlação) antes de a adotar.

**2. Uso de IA (`AISelect`).** Valores diferentes:
- 2024: `Yes` | `No, but I plan to soon` | `No, and I don't plan to`
- 2025: `Yes, I use AI tools daily` | `... weekly` | `... monthly or infrequently` | `No, but I plan to soon` | `No, and I don't plan to`

Regra proposta:
- `uses_ai` (binária): `True` se começa por "Yes", `False` se começa por "No", **NaN se em falta**.
- `ai_use_group` (3 níveis): `uses` / `plans` / `no`.
- `ai_use_frequency`: só 2025 (diária/semanal/mensal); análise complementar.

**3. Valores em falta nas colunas de IA.** Não tratar NaN como "No".
- `AISelect` em falta: ~7% em 2024 vs ~31% em 2025 → diferença grande, provavelmente do desenho do questionário. Reportar e testar a robustez das conclusões a isto.
- `AIAcc`, `AIComplex` têm muitos NaN porque (provavelmente) só foram perguntadas a quem usa IA. Analisar apenas sobre quem respondeu e dizê-lo no relatório.

**4. `AIComplex` 2025.** A opção "I don't use AI tools for complex tasks / I don't know" não existe em 2024: tratá-la como NaN nas comparações entre anos.

**5. Escalas ordinais.** Converter `AISent`, `AIAcc`, `AIComplex` em ordinais (1-5) para comparar entre anos; manter "Indifferent/Unsure/Neither" como categoria à parte quando fizer sentido.

