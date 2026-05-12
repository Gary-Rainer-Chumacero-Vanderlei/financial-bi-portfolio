# =============================================================================
# src/analysis/outliers.py
# Detecção de outliers nos dados de centro de custos.
#
# POR QUE PYTHON E NÃO SQL?
# A query SQL do Bloco 2.4 calculava o desvio padrão manualmente com:
#   SQRT(AVG(x*x) - AVG(x)*AVG(x))
# Essa fórmula é matematicamente equivalente, mas numericamente instável
# para valores grandes (como os R$ milhares do projeto) — pode gerar
# resultados imprecisos por acumulação de erro de ponto flutuante.
#
# scipy.stats.zscore usa o algoritmo de Welford, que é numericamente
# estável e é a implementação de referência da indústria.
#
# USO:
#   from src.analysis.outliers import detectar_outliers_zscore
#   resultado = detectar_outliers_zscore(centro_custos)
# =============================================================================

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

# Limiar padrão de Z-score para classificação de outlier.
# |Z| > 2.0 → ~4.5% dos dados em distribuição normal
# |Z| > 1.5 → ~13.4% dos dados (limiar mais sensível, usado no SQL original)
_LIMIAR_OUTLIER: float = 2.0
_LIMIAR_ATENCAO: float = 1.5


def calcular_zscore_por_departamento(
    centro_custos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Calcula o Z-score de gasto mensal para cada departamento.

    Agrupa os lançamentos por (departamento, competência), soma o gasto
    mensal e calcula o Z-score de cada mês em relação à média histórica
    daquele departamento.

    Args:
        centro_custos: DataFrame do centro de custos com colunas
                       'departamento', 'competencia' e 'valor'.

    Returns:
        DataFrame com uma linha por (departamento, competencia) e colunas:
            - departamento, competencia
            - gasto_mes: soma dos lançamentos no mês
            - media_historica: média mensal do departamento
            - desvio_padrao: desvio padrão mensal do departamento
            - z_score: quantos desvios o mês está da média
            - status: 'Outlier', 'Atenção' ou 'Normal'

    Note:
        scipy.stats.zscore usa o algoritmo de Welford — numericamente
        estável, ao contrário da fórmula SQRT(AVG(x²) - AVG(x)²) usada
        no SQL original, que pode acumular erro de ponto flutuante.
    """
    # Agrupa por departamento e competência, somando os lançamentos
    mensais = (
        centro_custos
        .groupby(["departamento", "competencia"], sort=True)
        .agg(gasto_mes=("valor", "sum"))
        .reset_index()
    )

    # Calcula Z-score dentro de cada departamento separadamente
    # groupby + transform garante que o Z-score é calculado por grupo
    # e o resultado é alinhado de volta com o índice original
    def zscore_seguro(series: pd.Series) -> pd.Series:
        """
        Calcula Z-score tratando o caso de desvio padrão zero.

        Se todos os valores do grupo forem iguais, o desvio padrão é zero
        e o Z-score seria indefinido (divisão por zero). Nesse caso,
        retornamos 0.0 para todos os valores do grupo.
        """
        if series.std() == 0:
            return pd.Series(0.0, index=series.index)
        return pd.Series(
            stats.zscore(series, ddof=1),  # ddof=1: desvio padrão amostral
            index=series.index,
        )

    mensais["z_score"] = (
        mensais
        .groupby("departamento")["gasto_mes"]
        .transform(zscore_seguro)
        .round(2)
    )

    # Estatísticas históricas por departamento (para referência no relatório)
    stats_depto = (
        mensais
        .groupby("departamento")["gasto_mes"]
        .agg(media_historica="mean", desvio_padrao="std")
        .reset_index()
    )

    mensais = mensais.merge(stats_depto, on="departamento")
    mensais["media_historica"] = mensais["media_historica"].round(2)
    mensais["desvio_padrao"]   = mensais["desvio_padrao"].round(2)

    # Classificação por faixa de Z-score
    # np.select é mais legível que múltiplos np.where aninhados
    condicoes = [
        mensais["z_score"].abs() > _LIMIAR_OUTLIER,
        mensais["z_score"].abs() > _LIMIAR_ATENCAO,
    ]
    escolhas = ["⚠️ Outlier", "🔶 Atenção"]
    mensais["status"] = np.select(condicoes, escolhas, default="✅ Normal")

    return mensais.sort_values("z_score", ascending=False).reset_index(drop=True)


def detectar_outliers_zscore(
    centro_custos: pd.DataFrame,
    limiar: float = _LIMIAR_OUTLIER,
) -> pd.DataFrame:
    """
    Retorna apenas os registros classificados como outlier ou atenção.

    Filtra o resultado de calcular_zscore_por_departamento para mostrar
    apenas os meses que merecem investigação.

    Args:
        centro_custos: DataFrame do centro de custos.
        limiar: Z-score mínimo (em valor absoluto) para inclusão.
                Padrão: 2.0 (outlier). Use 1.5 para mais sensibilidade.

    Returns:
        DataFrame filtrado e ordenado por Z-score decrescente,
        contendo apenas registros com |Z| > limiar.

    Example:
        >>> outliers = detectar_outliers_zscore(centro_custos)
        >>> outliers[["departamento", "competencia", "z_score", "status"]].head()
    """
    todos = calcular_zscore_por_departamento(centro_custos)
    outliers = todos[todos["z_score"].abs() > limiar].copy()

    logger.info(
        "Outliers detectados: %d de %d registros mensais (limiar |Z| > %.1f)",
        len(outliers),
        len(todos),
        limiar,
    )
    return outliers


def resumo_outliers_por_departamento(
    centro_custos: pd.DataFrame,
) -> pd.DataFrame:
    """
    Gera um resumo consolidado de outliers agrupado por departamento.

    Útil para o painel executivo identificar quais departamentos
    têm maior frequência de gastos anômalos.

    Args:
        centro_custos: DataFrame do centro de custos.

    Returns:
        DataFrame com uma linha por departamento e colunas:
            - departamento
            - total_meses: quantidade de meses analisados
            - meses_outlier: meses com |Z| > 2.0
            - meses_atencao: meses com 1.5 < |Z| ≤ 2.0
            - pct_anomalias: percentual de meses com alguma anomalia
            - max_z_score: maior Z-score registrado
    """
    todos = calcular_zscore_por_departamento(centro_custos)

    resumo = (
        todos
        .groupby("departamento")
        .agg(
            total_meses=("competencia", "count"),
            meses_outlier=("z_score", lambda s: (s.abs() > _LIMIAR_OUTLIER).sum()),
            meses_atencao=("z_score", lambda s: (
                (s.abs() > _LIMIAR_ATENCAO) & (s.abs() <= _LIMIAR_OUTLIER)
            ).sum()),
            max_z_score=("z_score", lambda s: s.abs().max()),
        )
        .reset_index()
    )

    resumo["pct_anomalias"] = (
        (resumo["meses_outlier"] + resumo["meses_atencao"])
        / resumo["total_meses"] * 100
    ).round(1)

    resumo["max_z_score"] = resumo["max_z_score"].round(2)

    return resumo.sort_values("pct_anomalias", ascending=False).reset_index(drop=True)
