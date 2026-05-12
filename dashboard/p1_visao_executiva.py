# =============================================================================
# dashboard/p1_visao_executiva.py
# =============================================================================

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.analysis import kpis
from src.analysis.kpis import calcular_score_saude, classificar_score, formatar_brl

_BG    = "#1a1d2e"
_GRID  = "#1f2333"
_TEXT  = "#e8eaf0"
_MUTED = "#8b92a5"
_CORES = ["#3b82f6", "#10b981", "#f59e0b", "#06b6d4", "#ef4444"]
_ANOS  = {"2023": "#4a5068", "2024": "#3b82f6"}


def _layout(h: int = 340) -> dict:
    return dict(
        height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=_MUTED, size=11, family="sans-serif"),
        margin=dict(l=8, r=8, t=36, b=8),
        legend=dict(orientation="h", y=-0.18, x=0, font=dict(size=11, color=_MUTED)),
        xaxis=dict(showgrid=False, linecolor=_GRID, tickfont=dict(color=_MUTED, size=10)),
        yaxis=dict(showgrid=True, gridcolor=_GRID, zeroline=False, tickfont=dict(color=_MUTED, size=10)),
        hovermode="x unified",
    )


def _card(label, valor, delta, cor, up=True, neutro=False):
    cor_d = "#10b981" if up else "#ef4444"
    if neutro: cor_d = _MUTED
    seta = "▲" if up else "▼"
    return (
        f'<div style="background:{_BG};border:1px solid {_GRID};border-top:3px solid {cor};'
        f'border-radius:10px;padding:16px 20px 14px;height:100%;">'
        f'<div style="font-size:11px;font-weight:600;letter-spacing:0.08em;text-transform:uppercase;'
        f'color:{_MUTED};margin-bottom:8px;">{label}</div>'
        f'<div style="font-size:26px;font-weight:700;color:{_TEXT};letter-spacing:-0.02em;margin-bottom:6px;">{valor}</div>'
        f'<div style="font-size:12px;font-weight:600;color:{cor_d};background:{cor_d}22;'
        f'border-radius:4px;padding:2px 8px;display:inline-block;">{seta} {delta}</div>'
        f'</div>'
    )


def _gauge(score, classif):
    cor = {"Saudável": "#10b981", "Atenção": "#f59e0b", "Crítico": "#ef4444"}.get(classif, _MUTED)
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=score,
        number=dict(font=dict(size=48, color=_TEXT)),
        gauge=dict(
            axis=dict(range=[0, 100], tickfont=dict(size=10, color=_MUTED)),
            bar=dict(color=cor, thickness=0.25),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            steps=[
                dict(range=[0, 50],   color="rgba(239,68,68,0.13)"),
                dict(range=[50, 70],  color="rgba(245,158,11,0.13)"),
                dict(range=[70, 100], color="rgba(16,185,129,0.13)"),
            ],
            threshold=dict(line=dict(color=cor, width=3), thickness=0.75, value=score),
        ),
    ))
    fig.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", font=dict(color=_MUTED),
                      margin=dict(l=20, r=20, t=20, b=10),
                      title=dict(text="Score de Saúde Financeira", font=dict(size=13, color=_MUTED), x=0.5))
    return fig


def _fig_receita_yoy(dre):
    d23 = dre[dre["ano"] == 2023].sort_values("mes")
    d24 = dre[dre["ano"] == 2024].sort_values("mes")
    meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=meses[:len(d23)], y=d23["receita_liquida"]/1e6, name="Receita 2023",
                         marker_color=_ANOS["2023"], opacity=0.8))
    fig.add_trace(go.Bar(x=meses[:len(d24)], y=d24["receita_liquida"]/1e6, name="Receita 2024",
                         marker_color=_ANOS["2024"], opacity=0.9))
    fig.add_trace(go.Scatter(x=meses[:len(d23)], y=d23["ebitda"]/1e6, name="EBITDA 2023",
                             mode="lines+markers", line=dict(color="#94a3b8", width=2, dash="dot"), marker=dict(size=4)))
    fig.add_trace(go.Scatter(x=meses[:len(d24)], y=d24["ebitda"]/1e6, name="EBITDA 2024",
                             mode="lines+markers", line=dict(color="#34d399", width=2.5), marker=dict(size=4)))
    lay = _layout(320)
    lay["title"] = dict(text="Receita Líquida & EBITDA (R$ MM)", font=dict(size=13, color="#3b82f6"), x=0)
    lay["barmode"] = "group"
    fig.update_layout(**lay)
    return fig


def _fig_margem(dre):
    d = dre.sort_values("competencia")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=d["competencia"], y=d["margem_ebitda_pct"], name="Mg. EBITDA",
                             mode="lines+markers", line=dict(color="#f59e0b", width=2),
                             fill="tozeroy", fillcolor="rgba(245,158,11,0.08)", marker=dict(size=4)))
    fig.add_hline(y=20, line_dash="dash", line_color="#10b981", line_width=1.5,
                  annotation_text="Meta 20%", annotation_font=dict(color="#10b981", size=11))
    lay = _layout(320)
    lay["title"] = dict(text="Margem EBITDA % (mensal)", font=dict(size=13, color="#f59e0b"), x=0)
    lay["yaxis"]["ticksuffix"] = "%"
    lay["legend"] = dict(visible=False)
    fig.update_layout(**lay)
    return fig


def render(dados: dict[str, pd.DataFrame], filtros: dict) -> None:
    dre_full = dados["dre"]
    comp_sel  = filtros["competencias"]
    ano_label = filtros["ano"]

    dre   = kpis.enriquecer_dre(dre_full)
    dre_f = dre[dre["competencia"].isin(comp_sel)].sort_values("competencia")

    todas = sorted(dre["competencia"].unique().tolist())
    idx_ini = todas.index(comp_sel[0]) if comp_sel[0] in todas else 0
    periodo_ant = todas[max(0, idx_ini - len(comp_sel)): idx_ini]
    dre_ant = dre[dre["competencia"].isin(periodo_ant)] if periodo_ant else dre_f

    rec  = dre_f["receita_liquida"].sum()
    ebit = dre_f["ebitda"].sum()
    mg   = dre_f["margem_ebitda_pct"].mean()
    ll   = dre_f["lucro_liquido"].sum()

    fl_f = dados["fluxo_caixa"][dados["fluxo_caixa"]["competencia"].isin(comp_sel)]
    fco  = fl_f["fco"].sum()

    cn_f     = dados["contas_receber"][dados["contas_receber"]["competencia"].isin(comp_sel)]
    carteira = cn_f["valor"].sum()
    inad     = (cn_f[cn_f["inadimplente"] == 1]["valor"].sum() / carteira * 100) if carteira > 0 else 0.0

    rec_ant  = dre_ant["receita_liquida"].sum()
    ebit_ant = dre_ant["ebitda"].sum()
    fco_ant  = dados["fluxo_caixa"][dados["fluxo_caixa"]["competencia"].isin(periodo_ant)]["fco"].sum() \
               if periodo_ant else fco

    def _var(a, b): return f"{((a-b)/abs(b)*100):+.1f}%" if b else "—"

    score   = calcular_score_saude(mg, fco, inad)
    classif = classificar_score(score)

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;'
                'color:#4a5068;text-transform:uppercase;margin-bottom:4px;">Dashboard Executivo</p>',
                unsafe_allow_html=True)
    st.markdown(f"## Visão Executiva — {ano_label}")

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin:16px 0 12px;">Indicadores Chave de Performance</p>',
                unsafe_allow_html=True)

    cols = st.columns(5)
    kpi_data = [
        ("Receita Líquida", formatar_brl(rec),  _var(rec, rec_ant),   True,  _CORES[0]),
        ("EBITDA",          formatar_brl(ebit), _var(ebit, ebit_ant), True,  _CORES[1]),
        ("Margem EBITDA",   f"{mg:.1f}%",        f"{mg:.1f}%",         True,  _CORES[2]),
        ("FCO",             formatar_brl(fco),  _var(fco, fco_ant),   fco>0, _CORES[3]),
        ("Inadimplência",   f"{inad:.1f}%",      f"{inad:.1f}%",       False, _CORES[4]),
    ]
    for col, (label, valor, delta, up, cor) in zip(cols, kpi_data):
        with col:
            st.markdown(_card(label, valor, delta, cor, up), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px;'></div>", unsafe_allow_html=True)

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin-bottom:12px;">Evolução Mensal</p>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1: st.plotly_chart(_fig_receita_yoy(dre_f), use_container_width=True)
    with c2: st.plotly_chart(_fig_margem(dre_f), use_container_width=True)

    st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;color:#4a5068;'
                'text-transform:uppercase;margin:8px 0 12px;">Score de Saúde Financeira</p>',
                unsafe_allow_html=True)

    cor_classif = {"Saudável": "#10b981", "Atenção": "#f59e0b", "Crítico": "#ef4444"}
    score_comp  = [
        ("Score Global",        f"{score:.0f}",                  classif, _CORES[1]),
        ("Margem (40 pts)",     f"{min(mg/25*40,40):.0f} / 40", "",      _CORES[0]),
        ("FCO Positivo (30 pts)", f"{'30' if fco>0 else '0'} / 30", "",  _CORES[3]),
        ("Inadimpl. (30 pts)",  f"{max(0,(1-inad/10)*30):.0f} / 30", "", _CORES[4]),
    ]

    c_gauge, c1, c2, c3, c4 = st.columns([2, 1, 1, 1, 1])
    with c_gauge:
        st.plotly_chart(_gauge(score, classif), use_container_width=True)

    for col, (label, val, badge, cor) in zip([c1, c2, c3, c4], score_comp):
        badge_html = (
            f'<div style="background:{cor_classif.get(badge,"transparent")}22;'
            f'color:{cor_classif.get(badge,_MUTED)};font-size:12px;font-weight:700;'
            f'border-radius:4px;padding:2px 8px;display:inline-block;margin-top:4px;">{badge}</div>'
        ) if badge else ""
        with col:
            st.markdown(
                f'<div style="background:{_BG};border:1px solid {_GRID};border-top:3px solid {cor};'
                f'border-radius:10px;padding:16px 18px;min-height:100px;">'
                f'<div style="font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;'
                f'color:{_MUTED};margin-bottom:8px;">{label}</div>'
                f'<div style="font-size:28px;font-weight:700;color:{_TEXT};">{val}</div>'
                f'{badge_html}</div>',
                unsafe_allow_html=True,
            )
