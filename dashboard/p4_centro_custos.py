# =============================================================================
# dashboard/p4_centro_custos.py
# =============================================================================

from __future__ import annotations

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.analysis.kpis import formatar_brl
from src.analysis.outliers import calcular_zscore_por_departamento

_BG    = "#1a1d2e"
_GRID  = "#1f2333"
_TEXT  = "#e8eaf0"
_MUTED = "#8b92a5"
_CORES = ["#3b82f6", "#6366f1", "#ef4444", "#f59e0b"]
_PAL   = ["#3b82f6","#10b981","#f59e0b","#a78bfa","#ef4444","#06b6d4","#ec4899","#84cc16"]


def _layout(titulo="", cor="#3b82f6", h=340):
    return dict(
        height=h, title=dict(text=titulo, font=dict(size=13, color=cor), x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=_MUTED, size=11), margin=dict(l=8, r=8, t=44, b=8),
        legend=dict(orientation="h", y=-0.22, x=0, font=dict(size=11, color=_MUTED)),
        xaxis=dict(showgrid=False, linecolor=_GRID, tickfont=dict(color=_MUTED, size=10)),
        yaxis=dict(showgrid=True, gridcolor=_GRID, zeroline=False, tickfont=dict(color=_MUTED, size=10)),
        hovermode="x unified",
    )


def _card(label, valor, delta, cor, up=True):
    cor_d = "#10b981" if up else "#ef4444"
    seta  = "▲" if up else "▼"
    return (
        f'<div style="background:{_BG};border:1px solid {_GRID};border-top:3px solid {cor};'
        f'border-radius:10px;padding:16px 18px 14px;">'
        f'<div style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;'
        f'color:{_MUTED};margin-bottom:8px;">{label}</div>'
        f'<div style="font-size:24px;font-weight:700;color:{_TEXT};margin-bottom:6px;">{valor}</div>'
        f'<div style="font-size:12px;font-weight:600;color:{cor_d};background:{cor_d}22;'
        f'border-radius:4px;padding:2px 8px;display:inline-block;">{seta} {delta}</div></div>'
    )


def _fig_barras(centro, deptos):
    tot = (centro[centro["departamento"].isin(deptos)]
           .groupby("departamento")["valor"].sum().reset_index().sort_values("valor", ascending=True))
    fig = go.Figure(go.Bar(
        x=tot["valor"]/1e6, y=tot["departamento"], orientation="h",
        marker_color=_PAL[:len(tot)],
        text=[formatar_brl(v) for v in tot["valor"]], textposition="outside",
        textfont=dict(size=10, color=_MUTED),
    ))
    lay = _layout("Custo por Departamento (R$ MM)", "#3b82f6", 320)
    lay["xaxis"]["showgrid"] = True
    lay["xaxis"]["gridcolor"] = _GRID
    lay["yaxis"]["showgrid"] = False
    lay["margin"]["l"] = 100
    lay["showlegend"] = False
    fig.update_layout(**lay)
    return fig


def _fig_evolucao(centro, deptos):
    mensal = (centro[centro["departamento"].isin(deptos)]
              .groupby(["competencia","departamento"])["valor"].sum().reset_index().sort_values("competencia"))
    fig = go.Figure()
    for i, depto in enumerate(sorted(deptos)):
        sub = mensal[mensal["departamento"] == depto]
        fig.add_trace(go.Scatter(x=sub["competencia"], y=sub["valor"]/1e6, name=depto,
                                 mode="lines+markers", line=dict(color=_PAL[i%len(_PAL)], width=2),
                                 marker=dict(size=3)))
    lay = _layout("Evolução Mensal por Departamento (R$ MM)", "#3b82f6", 320)
    lay["legend"]["y"] = -0.35
    fig.update_layout(**lay)
    return fig


def _fig_heatmap(centro, deptos):
    zscore_df = calcular_zscore_por_departamento(centro[centro["departamento"].isin(deptos)])
    pivot = zscore_df.pivot_table(index="departamento", columns="competencia",
                                  values="z_score", aggfunc="mean").fillna(0)
    meses_abrev = {"01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
                   "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"}
    cols_fmt = [meses_abrev.get(c.split("-")[1], c) for c in pivot.columns]
    textos   = [[f"{v:+.1f}" for v in row] for row in pivot.values]

    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=cols_fmt, y=pivot.index.tolist(),
        text=textos, texttemplate="%{text}", textfont=dict(size=10),
        colorscale=[[0.0,"#ef4444"],[0.35,"#1a1d2e"],[0.5,"#1a1d2e"],[0.65,"#1a1d2e"],[1.0,"#10b981"]],
        zmid=0,
        colorbar=dict(title=dict(text="Z", font=dict(color=_MUTED, size=11)),
                      tickfont=dict(color=_MUTED, size=10), len=0.8),
        hovertemplate="<b>%{y}</b> · %{x}<br>Z-score: %{z:.2f}<extra></extra>",
    ))
    fig.update_layout(
        height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=_MUTED, size=11), margin=dict(l=100, r=60, t=44, b=8),
        title=dict(text="Z-score por Departamento × Mês", font=dict(size=13, color="#3b82f6"), x=0),
        xaxis=dict(tickfont=dict(color=_MUTED, size=10)),
        yaxis=dict(tickfont=dict(color=_MUTED, size=10)),
    )
    return fig


def _fig_donut(centro, deptos):
    top5 = (centro[centro["departamento"].isin(deptos)]
            .groupby("categoria")["valor"].sum().nlargest(5).reset_index())
    fig = go.Figure(go.Pie(
        labels=top5["categoria"], values=top5["valor"], hole=0.55,
        marker=dict(colors=_PAL[:5], line=dict(color="#0e1117", width=2)),
        textinfo="label+percent", textfont=dict(size=11, color=_TEXT),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(height=300, paper_bgcolor="rgba(0,0,0,0)", font=dict(color=_MUTED, size=11),
                      margin=dict(l=8, r=8, t=44, b=8), showlegend=False,
                      title=dict(text="Top 5 Categorias de Custo", font=dict(size=13, color="#3b82f6"), x=0))
    return fig


def render(dados: dict[str, pd.DataFrame], filtros: dict) -> None:
    centro_full = dados["centro_custos"]
    comp_sel    = filtros["competencias"]
    ano_label   = filtros["ano"]

    todos_deptos = sorted(centro_full["departamento"].unique().tolist())

    with st.sidebar:
        st.markdown('<p style="font-size:12px;color:#8b92a5;margin:8px 0 4px;">Departamento</p>',
                    unsafe_allow_html=True)
        deptos_sel = st.multiselect("Departamento", options=todos_deptos, default=todos_deptos,
                                    key="filtro_depto_cc", label_visibility="collapsed")
        if not deptos_sel:
            deptos_sel = todos_deptos

    centro = centro_full[
        centro_full["competencia"].isin(comp_sel) &
        centro_full["departamento"].isin(deptos_sel)
    ].copy()

    total_real = centro["valor"].sum()
    orcamento  = (centro_full[centro_full["departamento"].isin(deptos_sel)]["valor"].mean()
                  * len(deptos_sel) * len(comp_sel))
    desvio_pct = (total_real - orcamento) / orcamento * 100 if orcamento else 0
    n_outliers = int(centro["is_outlier"].sum())

    todas_comp = sorted(centro_full["competencia"].unique().tolist())
    idx    = todas_comp.index(comp_sel[0]) if comp_sel[0] in todas_comp else 0
    ant    = todas_comp[max(0, idx - len(comp_sel)): idx]
    centro_ant  = centro_full[centro_full["competencia"].isin(ant) & centro_full["departamento"].isin(deptos_sel)] \
                  if ant else centro
    total_ant   = centro_ant["valor"].sum()

    def _var(a, b): return f"{((a-b)/abs(b)*100):+.1f}%" if b else "—"

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;'
                'color:#4a5068;text-transform:uppercase;margin-bottom:4px;">Gestão de Custos</p>',
                unsafe_allow_html=True)
    st.markdown(f"## Centro de Custos — {ano_label}")

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin:16px 0 12px;">Visão Geral</p>', unsafe_allow_html=True)

    cols = st.columns(4)
    kpi_data = [
        ("Custo Total Real",    formatar_brl(total_real),  _var(total_real, total_ant), total_real<=total_ant, _CORES[0]),
        ("Orçamento Total",     formatar_brl(orcamento),   "—",                          True,                  _CORES[1]),
        ("Desvio vs Orçamento", f"{desvio_pct:+.1f}%",    f"{abs(desvio_pct):.1f}%",    desvio_pct<=0,         _CORES[2]),
        ("Desvios > 20%",       str(n_outliers),           f"{n_outliers} outliers",      n_outliers==0,         _CORES[3]),
    ]
    for col, (label, valor, delta, up, cor) in zip(cols, kpi_data):
        with col: st.markdown(_card(label, valor, delta, cor, up), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin-bottom:12px;">Análise por Departamento</p>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: st.plotly_chart(_fig_barras(centro, deptos_sel), use_container_width=True)
    with c2: st.plotly_chart(_fig_evolucao(centro, deptos_sel), use_container_width=True)

    if len(comp_sel) > 1:
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        st.plotly_chart(_fig_heatmap(centro, deptos_sel), use_container_width=True)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin-bottom:12px;">Top 5 Categorias</p>', unsafe_allow_html=True)

    c_donut, c_tab = st.columns(2)
    with c_donut:
        st.plotly_chart(_fig_donut(centro, deptos_sel), use_container_width=True)

    with c_tab:
        st.markdown('<p style="font-size:11px;font-weight:700;color:#4a5068;'
                    'text-transform:uppercase;margin-bottom:8px;">Desvio por Departamento</p>',
                    unsafe_allow_html=True)
        tab_depto = (centro.groupby("departamento")["valor"].sum().reset_index().rename(columns={"valor":"Real"}))
        orc_depto = (centro_full[centro_full["departamento"].isin(deptos_sel)]
                     .groupby("departamento")["valor"].mean().reset_index().rename(columns={"valor":"Orcamento_medio"}))
        tab_depto = tab_depto.merge(orc_depto, on="departamento")
        tab_depto["Orçamento"] = tab_depto["Orcamento_medio"] * len(comp_sel)
        tab_depto["Desvio R$"] = tab_depto["Real"] - tab_depto["Orçamento"]
        tab_depto["Desvio %"]  = tab_depto["Desvio R$"] / tab_depto["Orçamento"] * 100
        tab_show = tab_depto[["departamento","Real","Orçamento","Desvio R$","Desvio %"]].rename(
            columns={"departamento":"Departamento"})
        st.dataframe(
            tab_show.style.format({"Real":formatar_brl,"Orçamento":formatar_brl,
                                   "Desvio R$":formatar_brl,"Desvio %":"{:+.1f}%"}),
            use_container_width=True, hide_index=True, height=300,
        )
