# Objetivo do Projeto

**Main Question:** como  a adoção de IA se relaciona com competências, renumeração e perfil dos developers, e o que mudou entre 2024 e 2025?

**Fonte de dados:** Stack Overflow Annual Developer Survey, edições 2024 e 2025
(<https://survey.stackoverflow.co/>).

**Âmbito:** profissionais a tempo inteiro com remuneração anual reportada.
Países com amostra reduzida (n < 200 por ano) ficam fora das comparações entre países.

---

## Q1. Quem utiliza IA?
- **Hipótese:** a adoção é maior em perfis mais jovens e em certas funções e varia por país.
- **Variavéis:** A definir
- **Método:** Taxas de adoção por segmento (SQL), regressão logistica de `usa_ia`.
- **Critério de sucesso:** tabela e gráficos de adoção por segmento com intervalos de confiança, e coeficientes interpretáveis.

## Q2. Quem utiliza IA ganha mais?
- **Hipótese:** existe diferença bruta, mas diminui (ou desaparece) depois de controlar experiência, país e função.
- **Variavéis:** A definir
- **Método:** diferença bruta (MAnn-Whitney + tamanho de efeito) vs regrassão linear ajustada (OLS, erros robustos).
- **Critério de sucesso:** efeito bruto lado a lado, com leitura clara de correlação vs causalidade.

## Q3. Que competências estão assciadas a salário mais alto? 
- **Hipótese:** algumas tecnologias têm prémio salarial mesmo depois de controlar experiência e país.
- **Variavéis:** linguagens/bases de dados/plataformas, log(salário), controlos.
- **Método:** Modelo random forest/XGBoost + SHAP; comparação com regressão linear.
- **Critério de sucesso:** ranking de tecnologias com impacto estimado, métricas de validação (R², MAE em escala log e em USD).

## Q4. Como mudaram o sentimento e a confiança na IA entre 2024 e 2025?
- **Hipótese:** a adoção sobre, mas a confiança na precisão não acompanha.
- **Variavéis:** sentimento, confinaça na precisão, perceçao de ameaça, ano, experiência, função.
- **Método:** comparação de distribuições entre anos, testes qui-quadrado/Cramér's V; harmonização das escalas.
- **Critério de sucesso:** gráficos comparáveis entre anos e conclusão sobre que perfis são mais céticos.

## Q5. Que perfis de developers existem?
- **Hipótese:** emergem clusters distintos por stack, experiência e uso de IA.
- **Variavéis:** tecnologias (one-hot), experiência, uso de IA, função.
- **Método:** K-Means (escolha de k por silhouette) e projeção UMAP/PCA para visualização.
- **Critério de sucesso:** 3-5 perfis interpretáveis, com nome e descrição, e salário mediano por perfil.

## Limitações assumidas (a desenvolver no relatório)
-Amostra autosselecionada (comunidade Stack Overflow), não representativa de todos os developers.
-Salários convertidos para USD pelo próprio survey; sem ajuste por custo de vida.
-Questões de IA mudaram entre edições; só se comparam itens harmonizáveis.
-Resultados são associações, não efeitos causais.