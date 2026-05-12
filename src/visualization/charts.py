# =============================================================================
# src/visualization/charts.py
# Funções de geração de gráficos Plotly reutilizáveis.
#
# PRINCÍPIO: Cada função recebe dados e retorna go.Figure.
# Quem chama não precisa conhecer Plotly — só passa os dados e exibe a figura.
#
# POR QUE SEPARAR OS GRÁFICOS DO DASHBOARD?
# No app.py original, os gráficos estavam construídos inline, misturados
# com a renderização do Streamlit. Isso tornava impossível:
#   1. Testar se o gráfico estava correto sem rodar o dashboard
#   2. Reutilizar o mesmo gráfico na EDA
#   3. Alterar o visual de um gráfico sem procurar no meio do app.py
#
# LAYOUT PADRÃO:
# Todos os gráficos compartilham _layout_base() para consistência visual.
# Alterar o tema exige mudar apenas essa função.
#
# USO:
#   from src.visualization.charts import grafico_receita_mensal
#   fig = grafico_receita_mensal(dre_enriquecida)
#   st.plotly_chart(fig, use_container_width=True)  # no dashboard
#   fig.write_image("exports/prints/receita.png")   # na EDA
# =============================================================================

from __future__ import annotations

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from config.theme import THEME
from config.settings import Settings


# =============================================================================
# LAYOUT BASE — compartilhado por todos os gráficos
# =============================================================================

def _layout_base(titulo: str = "", altura: int = 380) -> dict:
    """
    Retorna o dicionário de layout padrão para todos os gráficos.

    Centraliza configurações visuais: fundo transparente, grade sutil,
    tipografia e cores da paleta do projeto.

    Args:
        titulo: Título do gráfico. String vazia omite o título.
        altura: Altura em pixels. Padrão: 380.

    Returns:
        Dicionário compatível com go.Figure.update_layout(**layout).
    """
    return dict(
        title=dict(
            text=titulo,
            font=dict(size=14, color=THEME.text, family=THEME.to_rgba("text")),
            x=0.01,
        ),
        height=altura,
        paper_bgcolor="rgba(0,0,0,0)",  # fundo do papel transparente
        plot_bgcolor="rgba(0,0,0,0)",   # fundo do gráfico transparente
        font=dict(color=THEME.muted, size=11),
        margin=dict(l=10, r=10, t=40 if titulo else 10, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            font=dict(size=11, color=THEME.muted),
        ),
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(color=THEME.muted, size=10),
            linecolor=THEME.border,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=THEME.border,
            zeroline=False,
            tickfont=dict(color=THEME.muted, size=10),
        ),
        hovermode="x unified",   # mostra todos os valores do mesmo ponto X
    )


# =============================================================================
# GRÁFICOS DA DRE
# =============================================================================

def grafico_receita_mensal(dre: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras da receita líquida mensal com linha de EBITDA.

    Combina barras (receita) e linha (EBITDA) em um único gráfico
    de eixo duplo para mostrar volume e resultado simultaneamente.

    Args:
        dre: DataFrame da DRE — preferencialmente enriquecido com
             enriquecer_dre() para ter a coluna 'periodo_label'.

    Returns:
        Figura Plotly com barras de receita e linha de EBITDA.
    """
    label_col = "periodo_label" if "periodo_label" in dre.columns else "competencia"

    fig = go.Figure()

    # Barras de receita líquida
    fig.add_trace(go.Bar(
        x=dre[label_col],
        y=dre["receita_liquida"],
        name="Receita Líquida",
        marker_color=THEME.blue,
        marker_opacity=0.85,
        hovertemplate="<b>%{x}</b><br>Receita: R$ %{y:,.0f}<extra></extra>",
    ))

    # Linha de EBITDA sobreposta
    fig.add_trace(go.Scatter(
        x=dre[label_col],
        y=dre["ebitda"],
        name="EBITDA",
        mode="lines+markers",
        line=dict(color=THEME.teal, width=2.5),
        marker=dict(size=5, color=THEME.teal),
        hovertemplate="<b>%{x}</b><br>EBITDA: R$ %{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(**_layout_base("Receita Líquida vs EBITDA"))
    return fig


def grafico_margens(dre: pd.DataFrame) -> go.Figure:
    """
    Gráfico de linhas com as três margens ao longo do tempo.

    Exibe margem bruta, EBITDA e líquida como linhas para
    visualizar a evolução e compressão das margens.

    Args:
        dre: DataFrame da DRE com colunas de margem percentual.

    Returns:
        Figura Plotly com três linhas de margem.
    """
    label_col = "periodo_label" if "periodo_label" in dre.columns else "competencia"

    fig = go.Figure()

    margens = [
        ("margem_bruta_pct",   "Margem Bruta",   THEME.green),
        ("margem_ebitda_pct",  "Margem EBITDA",  THEME.blue),
        ("margem_liquida_pct", "Margem Líquida", THEME.purple),
    ]

    for coluna, nome, cor in margens:
        fig.add_trace(go.Scatter(
            x=dre[label_col],
            y=dre[coluna],
            name=nome,
            mode="lines+markers",
            line=dict(color=cor, width=2),
            marker=dict(size=4, color=cor),
            hovertemplate=f"<b>%{{x}}</b><br>{nome}: %{{y:.1f}}%<extra></extra>",
        ))

    fig.update_layout(**_layout_base("Evolução das Margens (%)"))
    fig.update_yaxes(ticksuffix="%")
    return fig


def grafico_comparativo_yoy(comparativo: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras agrupadas comparando receita 2024 vs 2023.

    Args:
        comparativo: DataFrame gerado por calcular_comparativo_yoy().

    Returns:
        Figura Plotly com barras agrupadas por mês.
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=comparativo["periodo_2023"],
        y=comparativo["receita_liquida_2023"],
        name="2023",
        marker_color=THEME.muted,
        marker_opacity=0.7,
        hovertemplate="<b>%{x}</b><br>2023: R$ %{y:,.0f}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=comparativo["periodo_2024"],
        y=comparativo["receita_liquida_2024"],
        name="2024",
        marker_color=THEME.blue,
        hovertemplate="<b>%{x}</b><br>2024: R$ %{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        **_layout_base("Receita Líquida — 2024 vs 2023"),
        barmode="group",   # barras lado a lado, não empilhadas
    )
    return fig


# =============================================================================
# GRÁFICOS DO FLUXO DE CAIXA
# =============================================================================

def grafico_fluxo_caixa(fluxo: pd.DataFrame) -> go.Figure:
    """
    Gráfico de área do saldo de caixa com barras de FCO.

    Combina área (saldo acumulado) e barras coloridas (FCO positivo/negativo)
    para mostrar a evolução patrimonial e a geração operacional de caixa.

    Args:
        fluxo: DataFrame do fluxo de caixa.

    Returns:
        Figura Plotly com área de saldo e barras de FCO.
    """
    fig = go.Figure()

    # Área do saldo final
    fig.add_trace(go.Scatter(
        x=fluxo["competencia"],
        y=fluxo["saldo_final"],
        name="Saldo Final",
        mode="lines",
        fill="tozeroy",
        line=dict(color=THEME.teal, width=2),
        fillcolor=THEME.to_rgba("teal", 0.15),
        hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:,.0f}<extra></extra>",
    ))

    # Barras de FCO coloridas por positivo/negativo
    cores_fco = [THEME.green if v > 0 else THEME.coral for v in fluxo["fco"]]

    fig.add_trace(go.Bar(
        x=fluxo["competencia"],
        y=fluxo["fco"],
        name="FCO",
        marker_color=cores_fco,
        marker_opacity=0.8,
        yaxis="y2",   # eixo secundário para FCO
        hovertemplate="<b>%{x}</b><br>FCO: R$ %{y:,.0f}<extra></extra>",
    ))

    layout = _layout_base("Saldo de Caixa e FCO Mensal")
    layout["yaxis2"] = dict(
        overlaying="y",
        side="right",
        showgrid=False,
        tickfont=dict(color=THEME.muted, size=10),
        title=dict(text="FCO (R$)", font=dict(color=THEME.muted, size=11)),
    )

    fig.update_layout(**layout)
    return fig


# =============================================================================
# GRÁFICOS DE CENTRO DE CUSTOS
# =============================================================================

def grafico_custos_por_departamento(centro_custos: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras horizontais com total de gastos por departamento.

    Barras horizontais são mais legíveis quando os rótulos do eixo Y
    são textos longos (nomes de departamentos e categorias).

    Args:
        centro_custos: DataFrame do centro de custos.

    Returns:
        Figura Plotly com barras horizontais ordenadas por valor total.
    """
    total_depto = (
        centro_custos
        .groupby("departamento")["valor"]
        .sum()
        .reset_index()
        .sort_values("valor", ascending=True)  # ascending=True para barras horizontais
    )

    fig = go.Figure(go.Bar(
        x=total_depto["valor"],
        y=total_depto["departamento"],
        orientation="h",    # barras horizontais
        marker_color=[THEME.blue, THEME.teal, THEME.purple, THEME.amber],
        hovertemplate="<b>%{y}</b><br>Total: R$ %{x:,.0f}<extra></extra>",
    ))

    fig.update_layout(**_layout_base("Total de Gastos por Departamento"))
    fig.update_xaxes(tickprefix="R$ ", showgrid=True, gridcolor=THEME.border)
    fig.update_yaxes(showgrid=False)
    return fig


def grafico_outliers_zscore(zscore_df: pd.DataFrame) -> go.Figure:
    """
    Gráfico de dispersão (scatter) dos Z-scores por departamento e mês.

    Cada ponto é um mês de um departamento. A posição vertical é o Z-score.
    Linhas de referência marcam os limiares de atenção e outlier.

    Args:
        zscore_df: DataFrame de calcular_zscore_por_departamento().

    Returns:
        Figura Plotly com scatter plot de Z-scores e linhas de referência.
    """
    # Mapa de cores por status
    cor_status = {
        "⚠️ Outlier": THEME.coral,
        "🔶 Atenção":  THEME.amber,
        "✅ Normal":   THEME.muted,
    }

    fig = go.Figure()

    for status, cor in cor_status.items():
        subset = zscore_df[zscore_df["status"] == status]
        if subset.empty:
            continue

        fig.add_trace(go.Scatter(
            x=subset["competencia"],
            y=subset["z_score"],
            mode="markers",
            name=status,
            marker=dict(color=cor, size=9, opacity=0.85),
            customdata=subset[["departamento", "gasto_mes"]],
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Departamento: %{customdata[0]}<br>"
                "Gasto: R$ %{customdata[1]:,.0f}<br>"
                "Z-score: %{y:.2f}<extra></extra>"
            ),
        ))

    # Linhas de referência para os limiares
    for y_val, cor, nome in [
        (2.0,  THEME.coral, "Outlier (|Z|=2)"),
        (-2.0, THEME.coral, ""),
        (1.5,  THEME.amber, "Atenção (|Z|=1.5)"),
        (-1.5, THEME.amber, ""),
    ]:
        fig.add_hline(
            y=y_val,
            line_dash="dot",
            line_color=cor,
            line_width=1,
            opacity=0.6,
            annotation_text=nome if nome else None,
            annotation_position="right",
        )

    fig.update_layout(**_layout_base("Z-score de Gastos por Departamento"))
    return fig


# =============================================================================
# GRÁFICOS DE INADIMPLÊNCIA
# =============================================================================

def grafico_inadimplencia_mensal(inadimplencia: pd.DataFrame) -> go.Figure:
    """
    Gráfico de linha com a taxa de inadimplência mensal.

    Adiciona uma área preenchida para facilitar a leitura da tendência
    e uma linha de referência em 5% (meta típica do setor).

    Args:
        inadimplencia: DataFrame de calcular_inadimplencia_mensal().

    Returns:
        Figura Plotly com linha de taxa e área preenchida.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=inadimplencia["competencia"],
        y=inadimplencia["taxa_inadimplencia_pct"],
        name="Taxa de Inadimplência",
        mode="lines+markers",
        fill="tozeroy",
        line=dict(color=THEME.coral, width=2.5),
        fillcolor=THEME.to_rgba("coral", 0.12),
        marker=dict(size=5, color=THEME.coral),
        hovertemplate="<b>%{x}</b><br>Inadimplência: %{y:.1f}%<extra></extra>",
    ))

    # Linha de referência — meta de inadimplência ≤ 5%
    fig.add_hline(
        y=5.0,
        line_dash="dash",
        line_color=THEME.amber,
        line_width=1.5,
        annotation_text="Meta: 5%",
        annotation_position="right",
    )

    fig.update_layout(**_layout_base("Taxa de Inadimplência Mensal (%)"))
    fig.update_yaxes(ticksuffix="%")
    return fig


def grafico_aging_stacked(aging: pd.DataFrame) -> go.Figure:
    """
    Gráfico de barras empilhadas com distribuição do aging por mês.

    Cada barra representa 100% da carteira do mês, dividida por faixa
    de aging. Permite visualizar a evolução da qualidade da carteira.

    Args:
        aging: DataFrame de calcular_aging_consolidado().

    Returns:
        Figura Plotly com barras 100% empilhadas.
    """
    faixas = ["A vencer", "1-30 dias", "31-60 dias",
              "61-90 dias", "91-180 dias", ">180 dias"]
    cores  = [THEME.green, THEME.teal, THEME.amber,
              THEME.coral, THEME.purple, THEME.pink]

    fig = go.Figure()

    for faixa, cor in zip(faixas, cores):
        subset = aging[aging["faixa_aging"] == faixa]

        fig.add_trace(go.Bar(
            x=subset["competencia"],
            y=subset["pct_carteira"],
            name=faixa,
            marker_color=cor,
            hovertemplate=(
                f"<b>%{{x}}</b><br>{faixa}: %{{y:.1f}}%<extra></extra>"
            ),
        ))

    fig.update_layout(
        **_layout_base("Distribuição do Aging da Carteira (%)"),
        barmode="stack",      # barras empilhadas
    )
    fig.update_yaxes(ticksuffix="%", range=[0, 100])
    return fig
