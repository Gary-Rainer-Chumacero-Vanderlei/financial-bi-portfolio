# =============================================================================
# dashboard/p3_fluxo_caixa.py
# =============================================================================

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.analysis.kpis import formatar_brl

_BG    = "#1a1d2e"
_GRID  = "#1f2333"
_TEXT  = "#e8eaf0"
_MUTED = "#8b92a5"
_CORES = ["#10b981", "#ef4444", "#10b981", "#3b82f6", "#f59e0b"]
_POS   = "#10b981"
_NEG   = "#ef4444"


def _layout(titulo="", cor="#10b981", h=340):
    return dict(
        height=h, title=dict(text=titulo, font=dict(size=13, color=cor), x=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=_MUTED, size=11), margin=dict(l=8, r=8, t=44, b=8),
        legend=dict(orientation="h", y=-0.22, x=0, font=dict(size=11, color=_MUTED)),
        xaxis=dict(showgrid=False, linecolor=_GRID, tickfont=dict(color=_MUTED, size=10)),
        yaxis=dict(showgrid=True, gridcolor=_GRID, zeroline=True,
                   zerolinecolor=_GRID, tickfont=dict(color=_MUTED, size=10)),
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


def _fig_fco_saldo(fl):
    fl = fl.sort_values("competencia")
    cores_fco = [_POS if v >= 0 else _NEG for v in fl["fco"]]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=fl["competencia"], y=fl["fco"]/1e6, name="FCO Mensal",
                         marker_color=cores_fco, opacity=0.9, yaxis="y",
                         hovertemplate="<b>%{x}</b><br>FCO: R$ %{y:.2f}MM<extra></extra>"))
    fig.add_trace(go.Scatter(x=fl["competencia"], y=fl["saldo_final"]/1e6, name="Saldo Final",
                             mode="lines+markers", line=dict(color="#3b82f6", width=2),
                             marker=dict(size=4), yaxis="y2",
                             hovertemplate="<b>%{x}</b><br>Saldo: R$ %{y:.2f}MM<extra></extra>"))
    lay = _layout("FCO & Saldo Acumulado (R$ MM)", _POS, 360)
    lay["yaxis2"] = dict(overlaying="y", side="right", showgrid=False, zeroline=False,
                         tickfont=dict(color=_MUTED, size=10),
                         title=dict(text="Saldo (R$ MM)", font=dict(color=_MUTED, size=11)))
    fig.update_layout(**lay)
    return fig


def _fig_saidas(fl):
    fl = fl.sort_values("competencia")
    fig = go.Figure()
    for nome, pct, cor in [("Fornecedores",0.45,"#ef4444"),("Pessoal",0.22,"#f59e0b"),
                            ("OPEX",0.20,"#a78bfa"),("Impostos",0.13,"#ec4899")]:
        fig.add_trace(go.Bar(x=fl["competencia"], y=fl["total_saidas"]*pct/1e6,
                             name=nome, marker_color=cor, opacity=0.88))
    lay = _layout("Saídas por Categoria (R$ MM)", _NEG, 320)
    lay["barmode"] = "stack"
    lay["legend"]["y"] = -0.28
    fig.update_layout(**lay)
    return fig


def _fig_rec_saidas(fl, dr):
    fl = fl.sort_values("competencia")
    dr = dr.sort_values("competencia")
    merged = fl.merge(dr[["competencia","receita_liquida"]], on="competencia", how="left")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=merged["competencia"], y=merged["recebimentos"]/1e6, name="Recebimentos",
                             mode="lines+markers", line=dict(color=_POS, width=2), marker=dict(size=4),
                             fill="tozeroy", fillcolor="rgba(16,185,129,0.06)"))
    fig.add_trace(go.Scatter(x=merged["competencia"], y=merged["total_saidas"]/1e6, name="Total Saídas",
                             mode="lines+markers", line=dict(color=_NEG, width=2), marker=dict(size=4)))
    fig.update_layout(**_layout("Recebimentos vs Saídas (R$ MM)", _POS, 320))
    return fig


def render(dados: dict[str, pd.DataFrame], filtros: dict) -> None:
    comp_sel  = filtros["competencias"]
    ano_label = filtros["ano"]

    fl_full = dados["fluxo_caixa"].sort_values("competencia")
    dr_full = dados["dre"].sort_values("competencia")
    fl_f = fl_full[fl_full["competencia"].isin(comp_sel)].copy()
    dr_f = dr_full[dr_full["competencia"].isin(comp_sel)].copy()

    fco_total   = fl_f["fco"].sum()
    capex_total = fl_f["capex"].sum()
    var_caixa   = fl_f["variacao_caixa"].sum()
    saldo_final = fl_f["saldo_final"].iloc[-1] if len(fl_f) else 0
    rec_total   = fl_f["recebimentos"].sum()
    conv_pct    = rec_total / dr_f["receita_liquida"].sum() * 100 if dr_f["receita_liquida"].sum() else 0

    todas   = sorted(fl_full["competencia"].unique().tolist())
    idx     = todas.index(comp_sel[0]) if comp_sel[0] in todas else 0
    ant     = todas[max(0, idx - len(comp_sel)): idx]
    fl_ant  = fl_full[fl_full["competencia"].isin(ant)] if ant else fl_f
    fco_ant = fl_ant["fco"].sum()

    def _var(a, b): return f"{((a-b)/abs(b)*100):+.1f}%" if b else "—"

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;'
                'color:#4a5068;text-transform:uppercase;margin-bottom:4px;">Tesouraria & Liquidez</p>',
                unsafe_allow_html=True)
    st.markdown(f"## Fluxo de Caixa — {ano_label}")

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin:16px 0 12px;">Posição de Caixa</p>', unsafe_allow_html=True)

    cols = st.columns(5)
    kpi_data = [
        ("FCO Total",      formatar_brl(fco_total),   _var(fco_total, fco_ant), fco_total>=0, _CORES[0]),
        ("CAPEX",          formatar_brl(capex_total),  f"{abs(capex_total/1e3):.0f}K",         False,     _CORES[1]),
        ("Variação Caixa", formatar_brl(var_caixa),   f"{abs(var_caixa/1e3):.0f}K",            var_caixa>=0, _CORES[2]),
        ("Saldo Final",    formatar_brl(saldo_final),  f"{saldo_final/1e6:.1f}MM",              True,      _CORES[3]),
        ("Conv. Caixa %",  f"{conv_pct:.1f}%",         f"{conv_pct:.1f}%",                      True,      _CORES[4]),
    ]
    for col, (label, valor, delta, up, cor) in zip(cols, kpi_data):
        with col: st.markdown(_card(label, valor, delta, cor, up), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin-bottom:12px;">FCO Mensal & Saldo Acumulado</p>',
                unsafe_allow_html=True)
    st.plotly_chart(_fig_fco_saldo(fl_f), use_container_width=True)

    st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin-bottom:12px;">Decomposição do Fluxo</p>',
                unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: st.plotly_chart(_fig_saidas(fl_f), use_container_width=True)
    with c2: st.plotly_chart(_fig_rec_saidas(fl_f, dr_f), use_container_width=True)

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin:8px 0 12px;">Demonstrativo Detalhado</p>',
                unsafe_allow_html=True)

    meses_abrev = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    tab = fl_f.copy()
    tab["Competência"] = tab.apply(lambda r: f"{meses_abrev[int(r['mes'])-1]}/{int(r['ano'])}", axis=1)
    cols_rename = {"recebimentos":"Recebimentos","total_saidas":"Total Saídas","fco":"FCO",
                   "capex":"CAPEX","financiamento":"Financiamento","variacao_caixa":"Variação Caixa","saldo_final":"Saldo Final"}
    cols_sel = ["Competência","recebimentos","total_saidas","fco","capex","financiamento","variacao_caixa","saldo_final"]
    tab_show = tab[[c for c in cols_sel if c in tab.columns]].rename(columns=cols_rename)
    fmt = {c: (lambda v: formatar_brl(v)) for c in tab_show.columns if c != "Competência"}
    st.dataframe(tab_show.style.format(fmt), use_container_width=True, hide_index=True, height=360)
