# Guia: dashboard em Power BI (Dia 5)

> **Aviso:** não consigo criar o ficheiro `.pbix` (é binário e precisa do Power BI Desktop, só para Windows).
> Este guia, as medidas DAX e o script de exportação foram preparados para o construíres tu.
> O script de exportação foi testado; as medidas DAX e os passos na interface **não** foram testados no Power BI Desktop
> (valida-os com a secção "Validação").

## 0. Pré-requisitos
- Power BI Desktop (gratuito, Windows).
- Dias 2 a 4 concluídos: existem `data/processed/survey_clean.parquet` e os CSV em `reports/`.

## 1. Gerar os dados
```
python -m src.export_powerbi
```
Cria `powerbi/data/` com:

| Ficheiro | Linhas (aprox.) | Conteúdo |
|---|---|---|
| `fato_respostas.csv` | 39 mil | uma linha por resposta |
| `ponte_funcoes.csv` | ~60 mil | `id_resposta` x função (multi-valor desdobrado) |
| `ponte_linguagens.csv` | ~230 mil | `id_resposta` x linguagem |
| `dim_pais.csv` | ~100 | país, nome curto, n por ano, `elegivel` (n ≥ 100 nos dois anos) |
| `dim_faixa.csv` | 5 | faixa de experiência + `ordem` |
| `modelo_*.csv` | pequenas | resultados do Dia 4 (OLS, SHAP, testes, clusters) |

**Porquê `id_resposta = ano-ResponseId`?** O `ResponseId` repete-se entre 2024 e 2025; sozinho não identifica uma resposta.
**Porquê tabelas-ponte?** Uma pessoa tem várias funções/linguagens numa só célula (`A;B;C`). Desdobrá-las (como o `unnest` do SQL) permite filtrar por elas.

## 2. Importar
1. *Obter dados > Texto/CSV* e carrega os ficheiros (podes selecionar a pasta inteira).
2. **Localização (importante em PT):** em cada ficheiro, *Transformar dados* e, se os números aparecerem mal (texto ou com vírgulas trocadas), usa *Alterar tipo > Usar localização... > Inglês (Estados Unidos)*. Alternativa global: *Ficheiro > Opções > Definições regionais > Inglês (EUA)*.
3. Tipos: `ano` = número inteiro; `usa_ia`, `*_score`, `salario_usd`, `anos_exp` = número inteiro (com vazios); o resto, texto. **Não substituas vazios por 0** em `usa_ia`: o vazio significa "não respondeu".
4. Fechar e aplicar.

## 3. Modelo (separador *Modelo*)
| De | Para | Cardinalidade | Direção do filtro |
|---|---|---|---|
| `dim_pais[pais]` | `fato_respostas[pais]` | 1 : muitos | única |
| `dim_faixa[faixa_exp]` | `fato_respostas[faixa_exp]` | 1 : muitos | única |
| `fato_respostas[id_resposta]` | `ponte_funcoes[id_resposta]` | 1 : muitos | **ambas** |
| `fato_respostas[id_resposta]` | `ponte_linguagens[id_resposta]` | 1 : muitos | **ambas** |

- **Ordenar as faixas:** na tabela `dim_faixa`, seleciona a coluna `faixa_exp` e usa *Ordenar por coluna > `ordem`*. Nos gráficos, usa `dim_faixa[faixa_exp]` (e não a da tabela de factos) para as faixas saírem na ordem certa.
- A direção **ambas** é necessária para que escolher uma linguagem/função filtre as respostas (e, por isso, o salário). Sem isso, o salário por linguagem não funciona. É o equivalente ao `JOIN` do SQL.
- Tabelas `modelo_*`: sem relações (são tabelas de resultados).

## 4. Medidas
1. Cria o parâmetro: *Modelação > Novo parâmetro > Intervalo numérico*, nome **`Amostra minima`**, mín. 30, máx. 300, incremento 10, valor 100. Mostra o segmentador.
2. Cria as medidas de `medidas.dax` (uma por uma, em *Nova medida*).
3. Formata: `% ...` como percentagem; `Mediana salario...` como moeda USD sem decimais; `Variacao adocao (pp)` com 1 decimal.

**Decisão tua:** o valor por defeito da amostra mínima (100, como no Dia 3). Mostra-o sempre no relatório.

## 5. Páginas (sugestão)
Usa o tema: *Vista > Temas > Procurar temas > `tema_projeto.json`*. Segmentadores sincronizados: `ano`, `faixa_exp`.

**Página 1: Visão geral**
- Cartões: `Respostas`, `% Usa IA 2024`, `% Usa IA 2025`, `Variacao adocao (pp)`, `Mediana salario 2024`, `Mediana salario 2025`.
- Colunas: `% Usa IA` por `ano` (com `Respostas com info IA` na dica de ferramenta).
- Texto: "Descritivo; amostra do Stack Overflow; ver Metodologia".

**Página 2: Quem usa IA? (Q1)**
- Barras: `% Usa IA (n minimo)` por `dim_pais[pais_curto]`, legenda `ano`. Filtro visual: `dim_pais[elegivel] = 1`. Título: `Titulo adocao`.
- Barras por `ponte_funcoes[funcao]` e por `dim_faixa[faixa_exp]` (ordenado).
- Dica de ferramenta: `Respostas com info IA`, `Margem de erro (pp)`.
- **O que aprender:** DAX não tem `HAVING`; o limiar faz-se numa medida que devolve vazio (`IF(n >= ...)`).

**Página 3: Salário (Q2)**
- Colunas agrupadas: eixo `dim_faixa[faixa_exp]`, valores `Mediana salario com IA` e `Mediana salario sem IA`; segmentador `ano`.
- Matriz da composição: `% da amostra do ano` por `faixa_exp` x `ano` (mostra que 2025 é mais sénior).
- Texto fixo: "Diferença estratificada, sem controlar país nem função; o modelo (Dia 4) mostra +3% ajustado."

**Página 4: Tecnologias (Q3)**
- Barras horizontais: `Mediana salario (n minimo)` por `ponte_linguagens[linguagem]`, filtro visual *N superior* (15) por `Respostas`.
- Matriz de ranking: linhas `dim_pais[pais_curto]` (filtro `elegivel = 1`, N superior 10), colunas `ponte_linguagens[linguagem]` (N superior 10), valores `Ranking salario da linguagem no pais`, filtro de página `ano = 2025`, formatação condicional (escala de cor).
- **Empates:** o ranking dá a mesma posição aos empatados (como no `RANK` do SQL); lê-o como patamares.

**Página 5: Confiança (Q4)**
- Cartões: `% Desconfia`, `% Confia`, `Confianca media (1-5)`, por `ano` (filtro de página `usa_ia = 1`).
- Barras 100% empilhadas: `confianca_cat` por `ano`, contagem de `id_resposta`, filtro `usa_ia = 1`. Ordena as categorias de "Highly distrust" a "Highly trust".

**Página 6: Resultados do modelo (Dia 4)**
- Tabelas/gráficos a partir de `modelo_q2_ols` (efeito de IA e de 2025 por modelo), `modelo_q2_faixa`, `modelo_q3_grupos` (barras), `modelo_q3_linguagens` (barras), `modelo_q4_testes`, `modelo_q5_clusters`.
- Para os intervalos de confiança do OLS, usa barras de erro se a tua versão as suportar; se não, uma tabela com formatação condicional.
- Mensagem central: "salário 2025: +0,6% ajustado (IC inclui 0) vs +22% bruto" (confirma com os teus valores).

**Página 7: Metodologia e limitações** (caixa de texto)
- Fonte, amostra, filtros (empregados com salário), regra "NULL não é No", amostra mínima, USD nominais, composição da amostra mudou, associação ≠ causalidade.

## 6. Validação (faz sempre)
Compara com o notebook (Dia 3). Se não baterem, há um erro de importação ou de medida.

| Verificação | Valor esperado |
|---|---|
| `Respostas` por ano | 20.669 (2024) e 18.513 (2025) |
| `% Usa IA` por ano | 62,6% e 80,8% |
| `Respostas com info IA` 2025 | 18.037 |
| `Mediana salario` por ano | 66.592 e 81.210 |
| `% Usa IA` 2025, faixa 0-1 anos | 84,7% |

## 7. Entrega e partilha
- **Guarda o `.pbix`** em `powerbi/` e faz commit (tem os dados embutidos; confirma o tamanho).
- **Exporta** *Ficheiro > Exportar > PDF* e tira **capturas de ecrã** de cada página para `figures/powerbi/` e para o README.
- **Link público:** o serviço Power BI exige conta de trabalho ou escola (não aceita Gmail/Outlook pessoais), e o "Publicar na web" é controlado por um administrador. Pode não estar disponível. Se não for possível, usa PDF + capturas (+ vídeo curto) no README e no LinkedIn.
- Nota de privacidade: "Publicar na web" torna o relatório **público**. Aqui os dados são abertos, mas nunca o uses com dados privados.

## 8. Checklist final
- [ ] Os 5 valores de validação batem com o notebook
- [ ] Amostra mínima visível e `n` nas dicas de ferramenta
- [ ] Página de metodologia e limitações
- [ ] Segmentadores `ano` e `faixa_exp` sincronizados
- [ ] `.pbix`, PDF e capturas no repositório
