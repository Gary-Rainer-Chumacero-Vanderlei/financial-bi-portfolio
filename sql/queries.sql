-- =============================================================================
-- queries.sql
-- Financial Performance Dashboard — Energética Norte Distribuidora Ltda.
-- Período: Jan/2023 – Dez/2024
-- Banco:   SQLite (compatível com DuckDB e PostgreSQL com ajustes mínimos)
--
-- CORREÇÕES APLICADAS:
--   Bug 1 (query 2.2): ORDER BY usava alias 'total_gasto' que não existe
--                       no escopo do GROUP BY em SQLite. Corrigido para
--                       usar a expressão original SUM(valor).
--   Bug 2 (queries 1.1, 1.3, 3.3, 4.2): divisões sem proteção contra
--                       zero. Corrigido com NULLIF() em todas as divisões.
--   Bug 3 (query 2.4): desvio padrão manual SQRT(AVG(x²) - AVG(x)²) é
--                       numericamente instável para valores grandes.
--                       Adicionado comentário técnico explicativo e proteção
--                       contra desvio zero com NULLIF().
-- =============================================================================


-- =============================================================================
-- BLOCO 1 — VISÃO EXECUTIVA: KPIs MENSAIS DA DRE
-- =============================================================================

-- 1.1 DRE Resumida com KPIs mensais
-- CORREÇÃO Bug 2: NULLIF() adicionado em todas as divisões para evitar
-- divisão por zero quando receita_bruta ou receita_liquida forem zero.
SELECT
    competencia,
    ano,
    mes,
    ROUND(receita_bruta, 2)                                             AS receita_bruta,
    ROUND(receita_liquida, 2)                                           AS receita_liquida,
    ROUND(lucro_bruto, 2)                                               AS lucro_bruto,
    ROUND(ebitda, 2)                                                    AS ebitda,
    ROUND(lucro_liquido, 2)                                             AS lucro_liquido,
    ROUND(margem_bruta_pct, 2)                                          AS margem_bruta_pct,
    ROUND(margem_ebitda_pct, 2)                                         AS margem_ebitda_pct,
    ROUND(margem_liquida_pct, 2)                                        AS margem_liquida_pct,
    -- Participação das deduções sobre receita bruta
    ROUND(deducoes / NULLIF(receita_bruta, 0) * 100, 2)                AS pct_deducoes,
    -- Participação do CMV sobre receita líquida
    ROUND(cmv / NULLIF(receita_liquida, 0) * 100, 2)                   AS pct_cmv,
    -- Peso das despesas operacionais
    ROUND(total_desp_opex / NULLIF(receita_liquida, 0) * 100, 2)       AS pct_opex
FROM dre
ORDER BY competencia;


-- 1.2 Receita acumulada no ano (YTD)
SELECT
    ano,
    competencia,
    mes,
    ROUND(receita_liquida, 2)                                           AS receita_liquida_mes,
    ROUND(SUM(receita_liquida) OVER (
        PARTITION BY ano ORDER BY mes
    ), 2)                                                               AS receita_liquida_ytd,
    ROUND(SUM(ebitda) OVER (
        PARTITION BY ano ORDER BY mes
    ), 2)                                                               AS ebitda_ytd,
    ROUND(SUM(lucro_liquido) OVER (
        PARTITION BY ano ORDER BY mes
    ), 2)                                                               AS lucro_liquido_ytd
FROM dre
ORDER BY competencia;


-- 1.3 Comparativo Year-over-Year (YoY) — 2024 vs 2023
-- CORREÇÃO Bug 2: NULLIF() nas divisões de variação percentual para evitar
-- divisão por zero se o valor de 2023 for zero.
SELECT
    a.mes,
    ROUND(a.receita_liquida, 2)                                         AS receita_2024,
    ROUND(b.receita_liquida, 2)                                         AS receita_2023,
    ROUND((a.receita_liquida - b.receita_liquida)
          / NULLIF(b.receita_liquida, 0) * 100, 2)                      AS var_receita_pct,
    ROUND(a.ebitda, 2)                                                  AS ebitda_2024,
    ROUND(b.ebitda, 2)                                                  AS ebitda_2023,
    ROUND((a.ebitda - b.ebitda)
          / NULLIF(b.ebitda, 0) * 100, 2)                               AS var_ebitda_pct,
    ROUND(a.margem_ebitda_pct, 2)                                       AS margem_ebitda_2024,
    ROUND(b.margem_ebitda_pct, 2)                                       AS margem_ebitda_2023,
    ROUND(a.margem_ebitda_pct - b.margem_ebitda_pct, 2)                AS delta_margem_pp
FROM       dre a
INNER JOIN dre b ON a.mes = b.mes AND a.ano = 2024 AND b.ano = 2023
ORDER BY a.mes;


-- 1.4 Totais anuais consolidados
-- CORREÇÃO Bug 2: NULLIF() na margem EBITDA consolidada para evitar
-- divisão por zero se SUM(receita_liquida) for zero.
SELECT
    ano,
    ROUND(SUM(receita_bruta), 2)                                        AS receita_bruta_total,
    ROUND(SUM(receita_liquida), 2)                                      AS receita_liquida_total,
    ROUND(SUM(lucro_bruto), 2)                                          AS lucro_bruto_total,
    ROUND(SUM(ebitda), 2)                                               AS ebitda_total,
    ROUND(SUM(lucro_liquido), 2)                                        AS lucro_liquido_total,
    ROUND(AVG(margem_bruta_pct), 2)                                     AS margem_bruta_media,
    ROUND(AVG(margem_ebitda_pct), 2)                                    AS margem_ebitda_media,
    ROUND(AVG(margem_liquida_pct), 2)                                   AS margem_liquida_media,
    ROUND(SUM(ebitda) / NULLIF(SUM(receita_liquida), 0) * 100, 2)      AS margem_ebitda_consolidada
FROM dre
GROUP BY ano
ORDER BY ano;


-- =============================================================================
-- BLOCO 2 — ANÁLISE DE CUSTOS E DESPESAS
-- =============================================================================

-- 2.1 Ranking de departamentos por total de gastos (período completo)
SELECT
    departamento,
    ROUND(SUM(valor), 2)                                                AS total_gasto,
    ROUND(AVG(valor), 2)                                                AS media_mensal,
    ROUND(SUM(valor) / (SELECT SUM(valor) FROM centro_custos) * 100, 2) AS pct_total,
    COUNT(DISTINCT competencia)                                         AS meses_ativos
FROM centro_custos
GROUP BY departamento
ORDER BY total_gasto DESC;


-- 2.2 Evolução mensal de gastos por departamento
-- CORREÇÃO Bug 1: ORDER BY usava o alias 'total_gasto' que não existe no
-- escopo do SELECT externo em SQLite. Corrigido para ORDER BY competencia,
-- SUM(valor) DESC — que é a expressão real e funciona em todos os bancos.
-- CORREÇÃO Bug 2: NULLIF() na divisão da variação percentual.
SELECT
    competencia,
    ano,
    mes,
    departamento,
    ROUND(SUM(valor), 2)                                                AS gasto_mes,
    ROUND(SUM(valor) - LAG(SUM(valor)) OVER (
        PARTITION BY departamento ORDER BY competencia
    ), 2)                                                               AS variacao_abs,
    ROUND((SUM(valor) - LAG(SUM(valor)) OVER (
        PARTITION BY departamento ORDER BY competencia)
    ) / NULLIF(LAG(SUM(valor)) OVER (
        PARTITION BY departamento ORDER BY competencia
    ), 0) * 100, 2)                                                     AS variacao_pct
FROM centro_custos
GROUP BY competencia, ano, mes, departamento
ORDER BY competencia, SUM(valor) DESC;
--                    ^^^^^^^^^^
-- CORREÇÃO Bug 1: expressão SUM(valor) em vez do alias 'total_gasto'


-- 2.3 Top 10 categorias de custo com maior impacto total
SELECT
    departamento,
    categoria,
    ROUND(SUM(valor), 2)                                                AS total_gasto,
    ROUND(AVG(valor), 2)                                                AS media_mensal,
    ROUND(MAX(valor), 2)                                                AS pico_maximo,
    ROUND(SUM(valor) / (SELECT SUM(valor) FROM centro_custos) * 100, 2) AS pct_total
FROM centro_custos
GROUP BY departamento, categoria
ORDER BY total_gasto DESC
LIMIT 10;


-- 2.4 Detecção de outliers — meses com gasto > 2 desvios padrão da média
-- NOTA TÉCNICA: SQLite não possui STDDEV nativo. O desvio padrão é calculado
-- manualmente com a identidade:  σ = √(E[X²] - E[X]²)
-- Esta fórmula é matematicamente correta, mas pode acumular erro de ponto
-- flutuante para valores muito grandes (como valores financeiros em R$ milhares).
-- Para análises de produção, prefira DuckDB (tem STDDEV_SAMP nativo) ou exporte
-- para Python onde scipy.stats.zscore(ddof=1) usa o algoritmo de Welford,
-- que é numericamente estável.
-- CORREÇÃO Bug 2: NULLIF() no denominador do z_score para evitar divisão por
-- zero quando todos os meses de um departamento têm o mesmo gasto (desvio = 0).
WITH stats AS (
    SELECT
        departamento,
        AVG(gasto_mes)                                                  AS media,
        SQRT(
            AVG(gasto_mes * gasto_mes) - AVG(gasto_mes) * AVG(gasto_mes)
        )                                                               AS desvio
    FROM (
        SELECT
            departamento,
            competencia,
            SUM(valor)                                                  AS gasto_mes
        FROM centro_custos
        GROUP BY departamento, competencia
    )
    GROUP BY departamento
),
mensais AS (
    SELECT
        departamento,
        competencia,
        SUM(valor)                                                      AS gasto_mes
    FROM centro_custos
    GROUP BY departamento, competencia
)
SELECT
    m.competencia,
    m.departamento,
    ROUND(m.gasto_mes, 2)                                               AS gasto_mes,
    ROUND(s.media, 2)                                                   AS media_historica,
    ROUND(s.desvio, 2)                                                  AS desvio_padrao,
    -- NULLIF(s.desvio, 0): retorna NULL se desvio = 0, evitando divisão por zero
    ROUND((m.gasto_mes - s.media) / NULLIF(s.desvio, 0), 2)            AS z_score,
    CASE
        WHEN s.desvio = 0                                        THEN 'Sem variação'
        WHEN ABS((m.gasto_mes - s.media) / s.desvio) > 2        THEN '⚠️ Outlier'
        WHEN ABS((m.gasto_mes - s.media) / s.desvio) > 1.5      THEN '🔶 Atenção'
        ELSE 'Normal'
    END                                                                 AS status
FROM mensais m
JOIN stats s ON m.departamento = s.departamento
WHERE s.desvio = 0
   OR ABS((m.gasto_mes - s.media) / NULLIF(s.desvio, 0)) > 1.5
ORDER BY ABS((m.gasto_mes - s.media) / NULLIF(s.desvio, 0)) DESC;


-- =============================================================================
-- BLOCO 3 — FLUXO DE CAIXA
-- =============================================================================

-- 3.1 Evolução do fluxo de caixa com saldo e variação
SELECT
    competencia,
    ano,
    mes,
    ROUND(recebimentos, 2)                                              AS recebimentos,
    ROUND(total_saidas, 2)                                              AS total_saidas,
    ROUND(fco, 2)                                                       AS fco,
    ROUND(capex, 2)                                                     AS capex,
    ROUND(financiamento, 2)                                             AS financiamento,
    ROUND(variacao_caixa, 2)                                            AS variacao_caixa,
    ROUND(saldo_final, 2)                                               AS saldo_final,
    CASE WHEN fco > 0 THEN 'Positivo' ELSE 'Negativo' END              AS status_fco,
    -- Cobertura: quantos meses o saldo atual cobre as saídas médias
    ROUND(saldo_final / NULLIF(total_saidas, 0), 1)                     AS meses_cobertura
FROM fluxo_caixa
ORDER BY competencia;


-- 3.2 FCO acumulado e média móvel 3 meses
SELECT
    competencia,
    ROUND(fco, 2)                                                       AS fco_mes,
    ROUND(SUM(fco) OVER (ORDER BY competencia), 2)                      AS fco_acumulado,
    ROUND(AVG(fco) OVER (
        ORDER BY competencia
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2)                                                               AS fco_mm3,
    ROUND(saldo_final, 2)                                               AS saldo_final
FROM fluxo_caixa
ORDER BY competencia;


-- 3.3 Análise de conversão: receita líquida vs recebimentos efetivos
-- CORREÇÃO Bug 2: NULLIF() na divisão do pct_conversao.
SELECT
    f.competencia,
    ROUND(d.receita_liquida, 2)                                         AS receita_liquida,
    ROUND(f.recebimentos, 2)                                            AS recebimentos,
    ROUND(f.recebimentos - d.receita_liquida, 2)                        AS gap_conversao,
    ROUND(f.recebimentos / NULLIF(d.receita_liquida, 0) * 100, 2)       AS pct_conversao
FROM fluxo_caixa f
JOIN dre d ON f.competencia = d.competencia
ORDER BY f.competencia;


-- =============================================================================
-- BLOCO 4 — INADIMPLÊNCIA E CONTAS A RECEBER
-- =============================================================================

-- 4.1 Aging consolidado por mês
SELECT
    competencia,
    ano,
    mes,
    faixa_aging,
    ROUND(SUM(valor), 2)                                                AS valor_total,
    COUNT(DISTINCT cod_cliente)                                         AS qtd_clientes,
    ROUND(SUM(valor) / NULLIF(SUM(SUM(valor)) OVER (
        PARTITION BY competencia
    ), 0) * 100, 2)                                                     AS pct_carteira
FROM contas_receber
GROUP BY competencia, ano, mes, faixa_aging
ORDER BY competencia,
    CASE faixa_aging
        WHEN 'A vencer'    THEN 1
        WHEN '1-30 dias'   THEN 2
        WHEN '31-60 dias'  THEN 3
        WHEN '61-90 dias'  THEN 4
        WHEN '91-180 dias' THEN 5
        WHEN '>180 dias'   THEN 6
    END;


-- 4.2 Taxa de inadimplência mensal
-- CORREÇÃO Bug 2: NULLIF() na divisão da taxa para evitar divisão por zero
-- em meses sem movimentação de contas a receber.
SELECT
    competencia,
    ROUND(SUM(CASE WHEN inadimplente = 1 THEN valor ELSE 0 END), 2)    AS valor_inadimplente,
    ROUND(SUM(valor), 2)                                                AS carteira_total,
    ROUND(SUM(CASE WHEN inadimplente = 1 THEN valor ELSE 0 END)
          / NULLIF(SUM(valor), 0) * 100, 2)                             AS taxa_inadimplencia_pct
FROM contas_receber
GROUP BY competencia
ORDER BY competencia;


-- 4.3 Ranking de clientes por inadimplência acumulada
-- CORREÇÃO Bug 2: NULLIF() na taxa de inadimplência por cliente.
SELECT
    cod_cliente,
    cliente,
    setor,
    porte,
    ROUND(SUM(CASE WHEN inadimplente = 1 THEN valor ELSE 0 END), 2)    AS total_inadimplente,
    ROUND(SUM(valor), 2)                                                AS carteira_total,
    ROUND(SUM(CASE WHEN inadimplente = 1 THEN valor ELSE 0 END)
          / NULLIF(SUM(valor), 0) * 100, 2)                             AS taxa_inadimplencia_pct,
    COUNT(DISTINCT competencia)                                         AS meses_com_atraso
FROM contas_receber
WHERE inadimplente = 1
GROUP BY cod_cliente, cliente, setor, porte
ORDER BY total_inadimplente DESC;


-- 4.4 Inadimplência por setor
-- CORREÇÃO Bug 2: NULLIF() na taxa de inadimplência por setor.
SELECT
    setor,
    ROUND(SUM(CASE WHEN inadimplente = 1 THEN valor ELSE 0 END), 2)    AS total_inadimplente,
    ROUND(SUM(valor), 2)                                                AS carteira_total,
    ROUND(SUM(CASE WHEN inadimplente = 1 THEN valor ELSE 0 END)
          / NULLIF(SUM(valor), 0) * 100, 2)                             AS taxa_inadimplencia_pct
FROM contas_receber
GROUP BY setor
ORDER BY total_inadimplente DESC;


-- =============================================================================
-- BLOCO 5 — VISÃO INTEGRADA (JOIN entre datasets)
-- =============================================================================

-- 5.1 Painel executivo consolidado: DRE + Caixa + Inadimplência + Score
-- CORREÇÃO Bug 2: NULLIF() na divisão do score de margem e na taxa de
-- inadimplência do subquery.
SELECT
    d.competencia,
    d.ano,
    d.mes,
    -- DRE
    ROUND(d.receita_liquida, 2)                                         AS receita_liquida,
    ROUND(d.ebitda, 2)                                                  AS ebitda,
    ROUND(d.margem_ebitda_pct, 2)                                       AS margem_ebitda_pct,
    ROUND(d.lucro_liquido, 2)                                           AS lucro_liquido,
    -- Caixa
    ROUND(f.fco, 2)                                                     AS fco,
    ROUND(f.saldo_final, 2)                                             AS saldo_caixa,
    -- Inadimplência
    ROUND(i.taxa_inadimplencia_pct, 2)                                  AS taxa_inadimplencia_pct,
    -- Score de saúde financeira (0–100): quanto maior, melhor
    -- Componente 1: Margem EBITDA  → máx 40 pts (meta: 25%)
    -- Componente 2: FCO positivo   → máx 30 pts (binário)
    -- Componente 3: Inadimplência  → máx 30 pts (meta: < 10%)
    ROUND(
        (CASE
            WHEN d.margem_ebitda_pct > 0
            THEN MIN(d.margem_ebitda_pct / 25.0 * 40, 40)
            ELSE 0
         END)
      + (CASE WHEN f.fco > 0 THEN 30 ELSE 0 END)
      + (CASE
            WHEN i.taxa_inadimplencia_pct < 10
            THEN (1.0 - i.taxa_inadimplencia_pct / 10.0) * 30
            ELSE 0
         END)
    , 1)                                                                AS score_saude_financeira
FROM dre d
JOIN fluxo_caixa f ON d.competencia = f.competencia
JOIN (
    SELECT
        competencia,
        ROUND(
            SUM(CASE WHEN inadimplente = 1 THEN valor ELSE 0 END)
            / NULLIF(SUM(valor), 0) * 100
        , 2)                                                            AS taxa_inadimplencia_pct
    FROM contas_receber
    GROUP BY competencia
) i ON d.competencia = i.competencia
ORDER BY d.competencia;
