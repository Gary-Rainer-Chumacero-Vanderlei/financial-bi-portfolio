# =============================================================================
# dashboard/p2_dre.py
# =============================================================================

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.analysis import kpis
from src.analysis.kpis import formatar_brl

_BG    = "#1a1d2e"
_GRID  = "#1f2333"
_TEXT  = "#e8eaf0"
_MUTED = "#8b92a5"
_CORES = ["#3b82f6", "#10b981", "#f59e0b", "#f59e0b", "#a78bfa"]
_POS   = "#3b82f6"
_NEG   = "#ef4444"


def _layout(titulo="", cor="#3b82f6", h=380):
    return dict(
        height=h, title=dict(text=titulo, font=dict(size=13, color=cor), x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=_MUTED, size=11), margin=dict(l=8, r=8, t=44, b=8),
        legend=dict(orientation="h", y=-0.2, x=0, font=dict(size=11, color=_MUTED)),
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


def _waterfall(dre_f):
    rb  = dre_f["receita_bruta"].sum()
    ded = dre_f["deducoes"].sum()
    rl  = dre_f["receita_liquida"].sum()
    cmv = dre_f["cmv"].sum()
    lb  = dre_f["lucro_bruto"].sum()
    opx = dre_f["total_desp_opex"].sum()
    ebt = dre_f["ebitda"].sum()
    dep = dre_f["depreciacao"].sum()
    rf  = dre_f["resultado_financeiro"].sum()
    ll  = dre_f["lucro_liquido"].sum()

    labels  = ["Rec. Bruta","Deduções","Rec. Líquida","CMV","Lucro Bruto","OPEX","EBITDA","Deprec.","Res. Fin.","Lucro Líq."]
    valores = [rb, -ded, rl, -cmv, lb, -opx, ebt, -dep, rf, ll]
    medida  = ["absolute","relative","total","relative","total","relative","total","relative","relative","total"]

    fig = go.Figure(go.Waterfall(
        orientation="v", measure=medida, x=labels, y=valores,
        text=[formatar_brl(v) for v in valores], textposition="outside",
        textfont=dict(size=10, color=_MUTED),
        connector=dict(line=dict(color=_GRID, width=1, dash="dot")),
        decreasing=dict(marker=dict(color=_NEG)),
        increasing=dict(marker=dict(color=_POS)),
        totals=dict(marker=dict(color="#3b82f6")),
        opacity=0.88,
    ))
    lay = _layout("Demonstração de Resultado do Exercício", "#3b82f6", 420)
    lay["showlegend"] = False
    lay["yaxis"]["tickprefix"] = "R$"
    fig.update_layout(**lay)
    return fig


def _margens_yoy(dre):
    d23 = dre[dre["ano"]==2023].sort_values("mes")
    d24 = dre[dre["ano"]==2024].sort_values("mes")
    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    fig = go.Figure()
    for col, nome, cor in [("margem_bruta_pct","Mg. Bruta","#3b82f6"),
                            ("margem_ebitda_pct","Mg. EBITDA","#f59e0b"),
                            ("margem_liquida_pct","Mg. Líquida","#a78bfa")]:
        fig.add_trace(go.Scatter(x=meses[:len(d23)], y=d23[col], name=f"{nome} 2023",
                                 mode="lines", line=dict(color=cor, width=1.5, dash="dot"), opacity=0.55))
        fig.add_trace(go.Scatter(x=meses[:len(d24)], y=d24[col], name=f"{nome} 2024",
                                 mode="lines+markers", line=dict(color=cor, width=2), marker=dict(size=3)))
    lay = _layout("Margens % (YoY)", "#f59e0b", 320)
    lay["yaxis"]["ticksuffix"] = "%"
    lay["legend"]["y"] = -0.28
    fig.update_layout(**lay)
    return fig


def _ebitda_yoy(dre):
    d23 = dre[dre["ano"]==2023].sort_values("mes")
    d24 = dre[dre["ano"]==2024].sort_values("mes")
    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=meses[:len(d23)], y=d23["ebitda"]/1e6, name="2023", marker_color="#4a5068", opacity=0.8))
    fig.add_trace(go.Bar(x=meses[:len(d24)], y=d24["ebitda"]/1e6, name="2024", marker_color="#10b981", opacity=0.9))
    lay = _layout("EBITDA Mensal YoY (R$ MM)", "#10b981", 320)
    lay["barmode"] = "group"
    fig.update_layout(**lay)
    return fig


def render(dados: dict[str, pd.DataFrame], filtros: dict) -> None:
    comp_sel  = filtros["competencias"]
    ano_label = filtros["ano"]

    dre_all = kpis.enriquecer_dre(dados["dre"])
    dre_f   = dre_all[dre_all["competencia"].isin(comp_sel)].sort_values("competencia")

    rb = dre_f["receita_bruta"].sum()
    rl = dre_f["receita_liquida"].sum()
    mg_b = dre_f["margem_bruta_pct"].mean()
    mg_e = dre_f["margem_ebitda_pct"].mean()
    mg_l = dre_f["margem_liquida_pct"].mean()

    todas   = sorted(dre_all["competencia"].unique().tolist())
    idx_ini = todas.index(comp_sel[0]) if comp_sel[0] in todas else 0
    ant     = todas[max(0, idx_ini - len(comp_sel)): idx_ini]
    dre_ant = dre_all[dre_all["competencia"].isin(ant)] if ant else dre_f
    rb_ant  = dre_ant["receita_bruta"].sum()
    rl_ant  = dre_ant["receita_liquida"].sum()

    def _var(a, b): return f"{((a-b)/abs(b)*100):+.1f}%" if b else "—"

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;'
                'color:#4a5068;text-transform:uppercase;margin-bottom:4px;">Demonstração de Resultado</p>',
                unsafe_allow_html=True)
    st.markdown(f"## DRE Interativa — {ano_label}")

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin:16px 0 12px;">Resultado Consolidado</p>', unsafe_allow_html=True)

    cols = st.columns(5)
    kpi_data = [
        ("Receita Bruta",   formatar_brl(rb),  _var(rb, rb_ant),  True,  _CORES[0]),
        ("Receita Líquida", formatar_brl(rl),  _var(rl, rl_ant),  True,  _CORES[1]),
        ("Margem Bruta",    f"{mg_b:.1f}%",     f"{mg_b:.1f}%",    True,  _CORES[2]),
        ("Margem EBITDA",   f"{mg_e:.1f}%",     f"{mg_e:.1f}%",    True,  _CORES[3]),
        ("Margem Líquida",  f"{mg_l:.1f}%",     f"{mg_l:.1f}%",    True,  _CORES[4]),
    ]
    for col, (label, valor, delta, up, cor) in zip(cols, kpi_data):
        with col: st.markdown(_card(label, valor, delta, cor, up), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin-bottom:12px;">Estrutura da DRE (Waterfall)</p>',
                unsafe_allow_html=True)
    st.plotly_chart(_waterfall(dre_f), use_container_width=True)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin-bottom:12px;">Evolução das Margens — YoY</p>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: st.plotly_chart(_margens_yoy(dre_all), use_container_width=True)
    with c2: st.plotly_chart(_ebitda_yoy(dre_all), use_container_width=True)

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin:8px 0 12px;">Tabela DRE Detalhada</p>',
                unsafe_allow_html=True)

    meses_abrev = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    tab = dre_f.copy()
    tab["Competência"] = tab.apply(lambda r: f"{meses_abrev[int(r['mes'])-1]}/{int(r['ano'])}", axis=1)
    cols_map = {
        "Competência":"Competência","receita_bruta":"Rec. Bruta","deducoes":"Deduções",
        "receita_liquida":"Rec. Líquida","lucro_bruto":"Lucro Bruto","margem_bruta_pct":"Mg. Bruta %",
        "total_desp_opex":"OPEX","ebitda":"EBITDA","margem_ebitda_pct":"Mg. EBITDA %",
        "lucro_liquido":"Lucro Líq.","margem_liquida_pct":"Mg. Líq. %",
    }
    tab_show = tab[[c for c in cols_map if c in tab.columns or c == "Competência"]].rename(columns=cols_map)
    fmt = {c: ("{:.1f}%" if "%" in c else (lambda v: formatar_brl(v))) for c in tab_show.columns if c != "Competência"}
    st.dataframe(tab_show.style.format(fmt), use_container_width=True, hide_index=True, height=380)
