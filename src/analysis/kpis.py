# =============================================================================
# src/analysis/kpis.py
# Cálculo de KPIs e métricas financeiras.
#
# PRINCÍPIO CENTRAL: Funções Puras
# Todas as funções aqui recebem dados como argumento e retornam resultados.
# Nenhuma função acessa variáveis globais, modifica estado externo ou
# depende do dashboard. Isso as torna previsíveis, reutilizáveis e testáveis.
#
# ORGANIZAÇÃO:
#   1. Funções escalares  — recebem números, retornam números
#   2. Funções de série   — recebem pd.Series, retornam pd.Series
#   3. Funções de DataFrame — recebem df, retornam df enriquecido ou dict
#
# USO:
#   from src.analysis.kpis import calcular_margem, calcular_kpis_executivos
# =============================================================================

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from config.settings import Settings

logger = logging.getLogger(__name__)


# =============================================================================
# SEÇÃO 1 — FUNÇÕES ESCALARES
# Recebem valores numéricos simples, retornam um único valor.
# São a base para as funções de DataFrame e as mais fáceis de testar.
# =============================================================================

def calcular_margem(lucro: float, receita: float) -> float:
    """
    Calcula a margem percentual de lucro sobre a receita.

    Args:
        lucro: Valor do lucro no período (R$). Pode ser negativo.
        receita: Valor da receita líquida no período (R$).

    Returns:
        Margem percentual arredondada em 2 casas decimais.
        Retorna 0.0 se receita for zero (evita ZeroDivisionError).

    Example:
        >>> calcular_margem(480_000, 4_800_000)
        10.0
        >>> calcular_margem(-100_000, 4_800_000)
        -2.08
        >>> calcular_margem(100, 0)
        0.0
    """
    if receita == 0:
        return 0.0
    return round(lucro / receita * 100, 2)


def calcular_variacao_yoy(valor_atual: float, valor_anterior: float) -> float:
    """
    Calcula a variação percentual Year-over-Year (ano atual vs ano anterior).

    Args:
        valor_atual: Valor do período atual (ex: 2024).
        valor_anterior: Valor do período anterior (ex: 2023).

    Returns:
        Variação percentual arredondada em 2 casas decimais.
        Retorna 0.0 se valor_anterior for zero.

    Example:
        >>> calcular_variacao_yoy(110, 100)
        10.0
        >>> calcular_variacao_yoy(90, 100)
        -10.0
    """
    if valor_anterior == 0:
        return 0.0
    return round((valor_atual - valor_anterior) / abs(valor_anterior) * 100, 2)


def calcular_score_saude(
    margem_ebitda: float,
    fco: float,
    taxa_inadimplencia: float,
) -> float:
    """
    Calcula o Score de Saúde Financeira composto (0–100).

    Combina três componentes ponderados, cada um com peso definido
    em Settings para facilitar ajuste sem alterar o código:

        Componente 1 — Margem EBITDA  (peso: Settings.SCORE_PESO_MARGEM)
            Score proporcional à margem, capped no máximo quando
            margem ≥ Settings.SCORE_META_MARGEM (25%).

        Componente 2 — FCO positivo   (peso: Settings.SCORE_PESO_FCO)
            Score binário: FCO > 0 recebe pontuação máxima.

        Componente 3 — Inadimplência  (peso: Settings.SCORE_PESO_INADIMPLENCIA)
            Score inversamente proporcional à taxa, zerando quando
            taxa ≥ Settings.SCORE_META_INADIMPLENCIA (10%).

    Args:
        margem_ebitda: Margem EBITDA percentual do período (ex: 18.5).
        fco: Fluxo de Caixa Operacional do período (R$).
        taxa_inadimplencia: Taxa de inadimplência percentual (ex: 4.2).

    Returns:
        Score entre 0.0 e 100.0 arredondado em 1 casa decimal.

    Example:
        >>> calcular_score_saude(margem_ebitda=20.0, fco=300_000, taxa_inadimplencia=5.0)
        87.0
        >>> calcular_score_saude(margem_ebitda=-5.0, fco=-50_000, taxa_inadimplencia=15.0)
        0.0
    """
    # Componente 1: Margem EBITDA
    # min() garante que nunca ultrapasse o peso máximo
    if margem_ebitda > 0:
        score_margem = min(
            margem_ebitda / Settings.SCORE_META_MARGEM * Settings.SCORE_PESO_MARGEM,
            float(Settings.SCORE_PESO_MARGEM),
        )
    else:
        score_margem = 0.0

    # Componente 2: FCO — binário (positivo ou não)
    score_fco = float(Settings.SCORE_PESO_FCO) if fco > 0 else 0.0

    # Componente 3: Inadimplência — inversamente proporcional
    if taxa_inadimplencia < Settings.SCORE_META_INADIMPLENCIA:
        score_inadimplencia = (
            1 - taxa_inadimplencia / Settings.SCORE_META_INADIMPLENCIA
        ) * Settings.SCORE_PESO_INADIMPLENCIA
    else:
        score_inadimplencia = 0.0

    total = score_margem + score_fco + score_inadimplencia
    return round(total, 1)


def classificar_score(score: float) -> str:
    """
    Classifica o Score de Saúde Financeira em faixas qualitativas.

    Faixas definidas em Settings para facilitar ajuste:
        ≥ SCORE_FAIXA_SAUDAVEL (70) → 'Saudável'
        ≥ SCORE_FAIXA_ATENCAO  (50) → 'Atenção'
        < SCORE_FAIXA_ATENCAO  (50) → 'Crítico'

    Args:
        score: Score entre 0.0 e 100.0.

    Returns:
        String com a classificação qualitativa.

    Example:
        >>> classificar_score(82.0)
        'Saudável'
        >>> classificar_score(55.0)
        'Atenção'
        >>> classificar_score(30.0)
        'Crítico'
    """
    if score >= Settings.SCORE_FAIXA_SAUDAVEL:
        return "Saudável"
    if score >= Settings.SCORE_FAIXA_ATENCAO:
        return "Atenção"
    return "Crítico"


def formatar_brl(valor: float) -> str:
    """
    Formata um valor numérico no padrão monetário brasileiro abreviado.

    Usa sufixos M (milhões) e K (milhares) para leitura rápida em KPIs
    de dashboard, onde espaço é limitado.

    Args:
        valor: Valor numérico a formatar (pode ser negativo).

    Returns:
        String formatada com prefixo R$ e sufixo M ou K.

    Example:
        >>> formatar_brl(4_800_000)
        'R$ 4,80M'
        >>> formatar_brl(320_000)
        'R$ 320,0K'
        >>> formatar_brl(-150_000)
        'R$ -150,0K'
    """
    sinal = "-" if valor < 0 else ""
    abs_valor = abs(valor)

    if abs_valor >= 1_000_000:
        valor_fmt = f"{abs_valor / 1_000_000:.2f}".replace(".", ",")
        return f"R$ {sinal}{valor_fmt}M"
    if abs_valor >= 1_000:
        valor_fmt = f"{abs_valor / 1_000:.1f}".replace(".", ",")
        return f"R$ {sinal}{valor_fmt}K"
    return f"R$ {sinal}{abs_valor:.0f}"


# =============================================================================
# SEÇÃO 2 — FUNÇÕES DE DATAFRAME
# Recebem um ou mais DataFrames, retornam DataFrames enriquecidos ou dicts.
# Aplicam as funções escalares da Seção 1 em escala.
# =============================================================================

def enriquecer_dre(dre: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona colunas calculadas ao DataFrame da DRE.

    Adiciona margens recalculadas a partir dos valores brutos e
    classificação do período (crescimento / queda) para uso nos gráficos.
    Trabalha em uma cópia do DataFrame original — não modifica o input.

    Args:
        dre: DataFrame da DRE carregado pelo DataLoader.

    Returns:
        Novo DataFrame com colunas adicionais:
            - margem_bruta_pct, margem_ebitda_pct, margem_liquida_pct
              (recalculadas para garantir consistência)
            - crescimento_receita: variação percentual mês a mês
            - periodo_label: string legível ex. 'Jan/2023'

    Note:
        Usa .copy() para não modificar o DataFrame original.
        Esta é uma boa prática: funções não devem alterar seus inputs.
    """
    # .copy() garante que não modificamos o DataFrame recebido
    df = dre.copy()

    # Recalcula margens a partir dos valores brutos
    # (garante consistência mesmo que os valores do CSV tenham arredondamentos)
    df["margem_bruta_pct"]   = (df["lucro_bruto"]   / df["receita_liquida"] * 100).round(2)
    df["margem_ebitda_pct"]  = (df["ebitda"]         / df["receita_liquida"] * 100).round(2)
    df["margem_liquida_pct"] = (df["lucro_liquido"]  / df["receita_liquida"] * 100).round(2)

    # Variação percentual mês a mês da receita líquida
    # pct_change() calcula (valor_atual - valor_anterior) / valor_anterior
    # * 100 converte para percentual; round(2) para 2 casas decimais
    df["crescimento_receita"] = (df["receita_liquida"].pct_change() * 100).round(2)

    # Label legível para eixo X dos gráficos
    meses_abrev = ["Jan","Fev","Mar","Abr","Mai","Jun",
                   "Jul","Ago","Set","Out","Nov","Dez"]
    df["periodo_label"] = df.apply(
        lambda row: f"{meses_abrev[int(row['mes']) - 1]}/{int(row['ano'])}",
        axis=1,
    )

    return df


def calcular_kpis_executivos(
    dre: pd.DataFrame,
    fluxo: pd.DataFrame,
    contas: pd.DataFrame,
) -> dict[str, float | str]:
    """
    Calcula os KPIs executivos do período mais recente disponível.

    Esses são os valores exibidos nos cards do topo do dashboard:
    receita, EBITDA, margem, FCO, saldo e score de saúde financeira.

    Args:
        dre: DataFrame da DRE completo.
        fluxo: DataFrame do Fluxo de Caixa completo.
        contas: DataFrame das Contas a Receber completo.

    Returns:
        Dicionário com os KPIs do último período disponível:
            - receita_liquida: float
            - ebitda: float
            - margem_ebitda_pct: float
            - lucro_liquido: float
            - fco: float
            - saldo_caixa: float
            - taxa_inadimplencia: float
            - score_saude: float
            - classificacao_saude: str
            - periodo: str (ex: '2024-12')

    Note:
        Usa .iloc[-1] para acessar a última linha do DataFrame,
        que representa o período mais recente após ordenação.
    """
    # Ordena por competência para garantir que .iloc[-1] seja o mais recente
    dre_ord   = dre.sort_values("competencia")
    fluxo_ord = fluxo.sort_values("competencia")

    # Período mais recente
    ultima_competencia: str = dre_ord["competencia"].iloc[-1]

    # Valores do último mês da DRE
    ultimo_dre   = dre_ord.iloc[-1]
    ultimo_fluxo = fluxo_ord.iloc[-1]

    # Taxa de inadimplência do último mês
    contas_mes = contas[contas["competencia"] == ultima_competencia]
    if len(contas_mes) > 0 and contas_mes["valor"].sum() > 0:
        taxa_inadimplencia = float(
            contas_mes[contas_mes["inadimplente"] == 1]["valor"].sum()
            / contas_mes["valor"].sum() * 100
        )
    else:
        taxa_inadimplencia = 0.0

    # Score e classificação
    score = calcular_score_saude(
        margem_ebitda=float(ultimo_dre["margem_ebitda_pct"]),
        fco=float(ultimo_fluxo["fco"]),
        taxa_inadimplencia=taxa_inadimplencia,
    )

    return {
        "periodo":              ultima_competencia,
        "receita_liquida":      round(float(ultimo_dre["receita_liquida"]), 2),
        "ebitda":               round(float(ultimo_dre["ebitda"]), 2),
        "margem_ebitda_pct":    round(float(ultimo_dre["margem_ebitda_pct"]), 2),
        "lucro_liquido":        round(float(ultimo_dre["lucro_liquido"]), 2),
        "fco":                  round(float(ultimo_fluxo["fco"]), 2),
        "saldo_caixa":          round(float(ultimo_fluxo["saldo_final"]), 2),
        "taxa_inadimplencia":   round(taxa_inadimplencia, 2),
        "score_saude":          score,
        "classificacao_saude":  classificar_score(score),
    }


def calcular_comparativo_yoy(dre: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o comparativo Year-over-Year entre 2024 e 2023.

    Faz o join da DRE consigo mesma por mês, alinhando 2024 com 2023
    para calcular as variações absolutas e percentuais.

    Args:
        dre: DataFrame da DRE com dados dos dois anos.

    Returns:
        DataFrame com 12 linhas (um por mês) e colunas:
            - mes, periodo_2024, periodo_2023
            - receita_2024, receita_2023, var_receita_pct
            - ebitda_2024, ebitda_2023, var_ebitda_pct
            - margem_ebitda_2024, margem_ebitda_2023, delta_margem_pp

    Note:
        'pp' = pontos percentuais — diferença entre duas porcentagens.
        Ex: margem foi de 18% para 22% → variação de +4 pp (não +22%).
    """
    dre_2024 = dre[dre["ano"] == 2024].copy()
    dre_2023 = dre[dre["ano"] == 2023].copy()

    # Merge por mês — join que alinha Jan/2024 com Jan/2023, etc.
    comparativo = dre_2024.merge(
        dre_2023,
        on="mes",
        suffixes=("_2024", "_2023"),
    )

    meses_abrev = ["Jan","Fev","Mar","Abr","Mai","Jun",
                   "Jul","Ago","Set","Out","Nov","Dez"]

    comparativo["periodo_2024"] = comparativo["mes"].apply(
        lambda m: f"{meses_abrev[m - 1]}/2024"
    )
    comparativo["periodo_2023"] = comparativo["mes"].apply(
        lambda m: f"{meses_abrev[m - 1]}/2023"
    )

    # Variações usando a função escalar — reutilização
    comparativo["var_receita_pct"] = comparativo.apply(
        lambda r: calcular_variacao_yoy(r["receita_liquida_2024"], r["receita_liquida_2023"]),
        axis=1,
    )
    comparativo["var_ebitda_pct"] = comparativo.apply(
        lambda r: calcular_variacao_yoy(r["ebitda_2024"], r["ebitda_2023"]),
        axis=1,
    )

    # Delta em pontos percentuais (pp) — diferença simples entre margens
    comparativo["delta_margem_pp"] = (
        comparativo["margem_ebitda_pct_2024"] - comparativo["margem_ebitda_pct_2023"]
    ).round(2)

    colunas_finais = [
        "mes", "periodo_2024", "periodo_2023",
        "receita_liquida_2024", "receita_liquida_2023", "var_receita_pct",
        "ebitda_2024", "ebitda_2023", "var_ebitda_pct",
        "margem_ebitda_pct_2024", "margem_ebitda_pct_2023", "delta_margem_pp",
    ]

    return comparativo[colunas_finais].sort_values("mes").reset_index(drop=True)


def calcular_inadimplencia_mensal(contas: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega a inadimplência por mês com valor total, carteira e taxa.

    Args:
        contas: DataFrame das Contas a Receber.

    Returns:
        DataFrame com uma linha por competência e colunas:
            - competencia, valor_inadimplente, carteira_total,
              taxa_inadimplencia_pct

    Note:
        groupby + agg é mais explícito e legível que múltiplos apply().
        Cada chave do dicionário passado ao agg() vira uma coluna no
        DataFrame resultante.
    """
    inadimplente = contas[contas["inadimplente"] == 1]["valor"].sum
    total        = contas["valor"].sum

    resultado = (
        contas
        .groupby("competencia", sort=True)
        .agg(
            valor_inadimplente=("valor", lambda s: s[contas.loc[s.index, "inadimplente"] == 1].sum()),
            carteira_total=("valor", "sum"),
        )
        .reset_index()
    )

    resultado["taxa_inadimplencia_pct"] = (
        resultado["valor_inadimplente"] / resultado["carteira_total"] * 100
    ).round(2)

    return resultado


def calcular_aging_consolidado(contas: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega a carteira de contas a receber por faixa de aging.

    Args:
        contas: DataFrame das Contas a Receber.

    Returns:
        DataFrame com uma linha por (competencia, faixa_aging) e colunas:
            - competencia, faixa_aging, valor_total,
              qtd_clientes, pct_carteira

    Note:
        A ordem das faixas de aging é definida por um Categorical do pandas,
        que garante ordenação correta mesmo que o groupby não preserve a
        ordem original das strings.
    """
    # Define a ordem correta das faixas — aging vai do mais recente ao mais antigo
    ordem_faixas = ["A vencer", "1-30 dias", "31-60 dias",
                    "61-90 dias", "91-180 dias", ">180 dias"]

    contas_ord = contas.copy()
    contas_ord["faixa_aging"] = pd.Categorical(
        contas_ord["faixa_aging"],
        categories=ordem_faixas,
        ordered=True,        # permite ordenação e comparação entre faixas
    )

    aging = (
        contas_ord
        .groupby(["competencia", "faixa_aging"], sort=True, observed=True)
        .agg(
            valor_total=("valor", "sum"),
            qtd_clientes=("cod_cliente", "nunique"),
        )
        .reset_index()
    )

    # pct_carteira: participação de cada faixa na carteira total do mês
    total_por_mes = aging.groupby("competencia")["valor_total"].transform("sum")
    aging["pct_carteira"] = (aging["valor_total"] / total_por_mes * 100).round(2)

    return aging
