# =============================================================================
# financial-bi/app.py
# =============================================================================

from __future__ import annotations
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent.resolve()
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd

from src.data.loader import DataLoader, DataNotFoundError, SchemaValidationError
from src.data.generator import FinancialDataGenerator
from config.settings import Settings

from dashboard import (
    p1_visao_executiva,
    p2_dre,
    p3_fluxo_caixa,
    p4_centro_custos,
)

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

st.set_page_config(
    page_title="Financial BI · Energética Norte",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# CSS GLOBAL — tema escuro fiel às imagens de referência
# =============================================================================

st.markdown("""
<style>
/* ── Fundo global ── */
.stApp { background-color: #0e1117; }
[data-testid="stSidebar"] { background-color: #13161f; border-right: 1px solid #1f2333; }

/* ── Cards KPI ── */
[data-testid="metric-container"] {
    background: #1a1d2e;
    border: 1px solid #1f2333;
    border-radius: 10px;
    padding: 16px 20px 14px;
    position: relative;
    overflow: hidden;
}
[data-testid="stMetricLabel"] p {
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
    color: #8b92a5 !important;
}
[data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #e8eaf0 !important;
    letter-spacing: -0.02em !important;
}
[data-testid="stMetricDelta"] {
    font-size: 12px !important;
    font-weight: 600 !important;
}

/* ── Texto global ── */
html, body, [class*="css"] { color: #c9cdd8; }
h1 { color: #e8eaf0 !important; font-size: 28px !important; font-weight: 700 !important; }
h2 { color: #c9cdd8 !important; font-size: 16px !important; font-weight: 600 !important;
     letter-spacing: 0.06em !important; text-transform: uppercase !important; }
h3 { color: #e8eaf0 !important; font-size: 15px !important; font-weight: 600 !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] label { color: #c9cdd8 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label { font-size: 12px !important; color: #8b92a5 !important; }

/* ── Selectbox e sliders ── */
[data-testid="stSelectbox"] > div > div {
    background: #1a1d2e !important;
    border-color: #1f2333 !important;
    color: #e8eaf0 !important;
}
.stSlider [data-testid="stSlider"] { color: #e8eaf0; }

/* ── Tabelas ── */
[data-testid="stDataFrame"] { background: #1a1d2e !important; }
.stDataFrame thead th { background: #13161f !important; color: #8b92a5 !important;
    font-size: 12px !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; }
.stDataFrame tbody td { color: #c9cdd8 !important; border-bottom: 1px solid #1f2333 !important; }
.stDataFrame tbody tr:hover td { background: #1f2333 !important; }

/* ── Divider ── */
hr { border-color: #1f2333 !important; margin: 8px 0 !important; }

/* ── Expander ── */
[data-testid="stExpander"] { background: #1a1d2e !important; border: 1px solid #1f2333 !important;
    border-radius: 8px !important; }

/* ── Botões genéricos ── */
.stButton > button { background: #1f2333 !important; color: #e8eaf0 !important;
    border: 1px solid #2d3148 !important; border-radius: 8px !important; font-weight: 500 !important; }
.stButton > button:hover { background: #2d3148 !important; }

/* ── Botões de download (Baixar PDF / Baixar Excel) ── */
[data-testid="stDownloadButton"] > button {
    background: #1f2333 !important;
    color: #e0f0ff !important;
    border: 1px solid #3a4a72 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #2d3d60 !important;
    color: #ffffff !important;
    border-color: #5a7abf !important;
}

/* ── Itens de navegação da sidebar (Visão Executiva, DRE, etc.) ── */
[data-testid="stSidebarNavLink"] {
    color: #c9d8f5 !important;
    font-weight: 500 !important;
}
[data-testid="stSidebarNavLink"]:hover {
    color: #ffffff !important;
    background: #1f2a45 !important;
}
[data-testid="stSidebarNavLink"][aria-selected="true"] {
    color: #ffffff !important;
    background: #2a3a5e !important;
    font-weight: 700 !important;
}
[data-testid="stSidebarNavLink"] span,
[data-testid="stSidebarNavLink"] p {
    color: inherit !important;
}

/* ── Botão de recolher a sidebar (chevron ‹/›) ── */
[data-testid="stSidebarCollapseButton"] {
    background: #1a1d2e !important;
    border: 1px solid #2d3148 !important;
    border-radius: 6px !important;
}
[data-testid="stSidebarCollapseButton"] svg {
    fill: #c9d8f5 !important;
    color: #c9d8f5 !important;
}
[data-testid="stSidebarCollapseButton"]:hover {
    background: #2d3148 !important;
}
[data-testid="stSidebarCollapseButton"]:hover svg {
    fill: #ffffff !important;
    color: #ffffff !important;
}

/* ── Caption sidebar ── */
.sidebar-caption { font-size: 11px; color: #4a5068; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CARREGAMENTO DE DADOS
# =============================================================================

@st.cache_data(ttl=3600, show_spinner="Carregando dados financeiros...")
def _carregar_dados(data_dir_str: str) -> dict[str, pd.DataFrame]:
    from pathlib import Path
    loader = DataLoader(data_dir=Path(data_dir_str))
    return loader.carregar_todos()


def _gerar_e_carregar() -> dict[str, pd.DataFrame]:
    with st.spinner("Gerando dados sintéticos pela primeira vez..."):
        gen = FinancialDataGenerator()
        gen.gerar_todos(salvar=True)
    st.success("Dados gerados com sucesso!")
    return _carregar_dados(str(Settings.RAW_DATA_DIR))


dados: dict[str, pd.DataFrame] | None = None

try:
    dados = _carregar_dados(str(Settings.RAW_DATA_DIR))
except DataNotFoundError:
    st.warning("⚠️ Dados não encontrados.")
    if st.button("⚡ Gerar dados agora", type="primary"):
        dados = _gerar_e_carregar()
        st.rerun()
except SchemaValidationError as e:
    st.error("❌ Erro de validação nos dados.")
    st.code(str(e))
    if st.button("🔄 Regenerar dados", type="primary"):
        dados = _gerar_e_carregar()
        st.rerun()


# =============================================================================
# SIDEBAR COM FILTROS GLOBAIS
# Filtros definidos aqui e passados para todas as páginas via session_state
# =============================================================================

def _construir_sidebar(dados: dict[str, pd.DataFrame]) -> dict:
    """
    Constrói a sidebar com identidade visual e filtros globais.
    Retorna dicionário com os filtros selecionados.
    """
    with st.sidebar:
        # ── Links sociais ──
        st.markdown("""
        <div style="display:flex; gap:12px; padding: 8px 0 12px;">
            <a href="https://www.linkedin.com/in/garyrainercv/" target="_blank"
               title="LinkedIn — Gary Rainer Chumacero Vanderlei"
               style="display:flex; align-items:center; justify-content:center;
                      width:34px; height:34px; border-radius:8px;
                      background:#0A66C2; text-decoration:none;">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white">
                    <path d="M20.447 20.452H17.21v-5.569c0-1.328-.027-3.037-1.852-3.037
                             -1.853 0-2.136 1.445-2.136 2.939v5.667H9.984V9h3.102v1.561h.046
                             c.432-.816 1.489-1.676 3.065-1.676 3.278 0 3.884 2.157 3.884 4.966v6.601zM5.337
                             7.433a1.8 1.8 0 1 1 0-3.601 1.8 1.8 0 0 1 0 3.601zM6.959
                             20.452H3.713V9h3.246v11.452zM22.225 0H1.771C.792 0 0 .774 0
                             1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227
                             24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                </svg>
            </a>
            <a href="https://github.com/gary-rainer-chumacero-vanderlei" target="_blank"
               title="GitHub — Gary Rainer Chumacero Vanderlei"
               style="display:flex; align-items:center; justify-content:center;
                      width:34px; height:34px; border-radius:8px;
                      background:#24292e; border:1px solid #444d56; text-decoration:none;">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="white">
                    <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205
                             11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04
                             -3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755
                             -1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838
                             1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776
                             .417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93
                             0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176
                             0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006
                             2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653
                             .24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805
                             5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896
                             -.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24
                             12.297c0-6.627-5.373-12-12-12"/>
                </svg>
            </a>
        </div>
        """, unsafe_allow_html=True)

        # ── Identidade ──
        st.markdown("""
        <div style="padding: 4px 0 16px;">
            <div style="font-size:11px; font-weight:700; letter-spacing:0.12em;
                        color:#4a5068; text-transform:uppercase; margin-bottom:6px;">
                Gary Rainer Chumacero Vanderlei<br>Portfolio BI
            </div>
            <div style="font-size:18px; font-weight:700; color:#e8eaf0;">
                ⚡ Energética Norte
            </div>
            <div style="font-size:12px; color:#8b92a5; margin-top:2px;">
                Distribuidora Ltda.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── Filtros ──
        st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;'
                    'color:#4a5068;text-transform:uppercase;margin-bottom:12px;">Filtros</p>',
                    unsafe_allow_html=True)

        dre = dados["dre"]
        anos = ["Todos"] + sorted(str(a) for a in dre["ano"].unique())
        ano = st.selectbox("Ano", anos, key="filtro_global_ano")

        todas_comp = sorted(dre["competencia"].unique().tolist())
        if ano != "Todos":
            comp_ano = sorted(dre[dre["ano"] == int(ano)]["competencia"].unique().tolist())
        else:
            comp_ano = todas_comp

        n = len(comp_ano)
        range_atual = st.session_state.get("filtro_global_range", (0, n - 1))
        idx_min = max(0, min(range_atual[0], n - 1))
        idx_max = max(idx_min, min(range_atual[1], n - 1))

        st.markdown('<p style="font-size:12px;color:#8b92a5;margin-bottom:4px;">Período (meses)</p>',
                    unsafe_allow_html=True)
        idx_i, idx_f = st.select_slider(
            "Período",
            options=list(range(n)),
            value=(idx_min, idx_max),
            format_func=lambda i: comp_ano[i][:7],
            key="filtro_global_range",
            label_visibility="collapsed",
        )

        comp_sel = comp_ano[idx_i: idx_f + 1]

        # Label do período selecionado
        st.markdown(
            f'<p style="font-size:11px;color:#4a5068;margin-top:2px;">'
            f'{comp_sel[0]} – {comp_sel[-1]}</p>',
            unsafe_allow_html=True,
        )

        st.divider()

        # ── Exportar Relatórios ──
        st.markdown('<p style="font-size:11px;font-weight:700;letter-spacing:0.1em;'
                    'color:#4a5068;text-transform:uppercase;margin-bottom:10px;">Exportar</p>',
                    unsafe_allow_html=True)

        # Geração do Excel em memória — funciona no Streamlit Cloud sem arquivos locais
        @st.cache_data(show_spinner=False)
        def _gerar_excel_bytes(_dados: dict) -> bytes:
            import io
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                for nome, df in _dados.items():
                    df.to_excel(writer, sheet_name=nome[:31], index=False)
            return output.getvalue()

        try:
            excel_bytes = _gerar_excel_bytes(dados)
            st.download_button(
                label="📊 Baixar Excel",
                data=excel_bytes,
                file_name="relatorio_financeiro.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        except Exception as e:
            st.caption(f"⚠️ Erro ao gerar Excel: {e}")

        # Geração do PDF em memória — funciona no Streamlit Cloud sem arquivos locais
        @st.cache_data(show_spinner=False)
        def _gerar_pdf_bytes(_dados: dict) -> bytes | None:
            """
            Gera o relatório PDF reutilizando as funções do eda_financeiro.
            Usa arquivo temporário internamente (contorna str(output_path) do ReportLab)
            e retorna os bytes prontos para download.
            """
            import tempfile
            from pathlib import Path as _Path

            try:
                from notebooks.eda_financeiro import (
                    fig_receita_ebitda,
                    fig_sazonalidade,
                    fig_margens,
                    fig_custos_heatmap,
                    fig_outliers,
                    fig_inadimplencia,
                    fig_fluxo_caixa,
                    fig_waterfall,
                    fig_score,
                    gerar_pdf,
                )
            except ImportError:
                return None

            dre    = _dados["dre"].sort_values("competencia").reset_index(drop=True)
            fluxo  = _dados["fluxo_caixa"].sort_values("competencia").reset_index(drop=True)
            contas = _dados["contas_receber"].sort_values("competencia").reset_index(drop=True)
            centro = _dados["centro_custos"].sort_values("competencia").reset_index(drop=True)

            with tempfile.TemporaryDirectory() as tmp_str:
                tmp      = _Path(tmp_str)
                pdf_path = tmp / "relatorio_financeiro.pdf"

                pngs = [
                    fig_receita_ebitda(dre, tmp),
                    fig_sazonalidade(dre, tmp),
                    fig_margens(dre, tmp),
                    fig_custos_heatmap(centro, tmp),
                    fig_outliers(centro, tmp),
                    fig_inadimplencia(contas, tmp),
                    fig_fluxo_caixa(fluxo, tmp),
                    fig_waterfall(dre, tmp),
                    fig_score(dre, fluxo, contas, tmp),
                ]
                gerar_pdf(pngs, _dados, pdf_path)
                return pdf_path.read_bytes()

        with st.spinner("Gerando PDF..."):
            pdf_bytes = _gerar_pdf_bytes(dados)

        if pdf_bytes:
            st.download_button(
                label="📄 Baixar PDF",
                data=pdf_bytes,
                file_name="relatorio_financeiro.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        else:
            st.caption("⚠️ PDF indisponível: verifique se notebooks/eda_financeiro.py está no projeto.")

        st.divider()

        # ── Rodapé ──
        st.markdown(
            '<div class="sidebar-caption">'
            f'Jan 2023 · Dez 2024<br><br>'
            'Stack: Python · Plotly · Streamlit<br>'
            'Portfólio · Data Analytics'
            '</div>',
            unsafe_allow_html=True,
        )

    return {"ano": ano, "competencias": comp_sel, "todas_comp": todas_comp}


# =============================================================================
# NAVEGAÇÃO
# =============================================================================

if dados is not None:
    filtros = _construir_sidebar(dados)

    def pagina_visao_executiva():
        p1_visao_executiva.render(dados, filtros)

    def pagina_dre():
        p2_dre.render(dados, filtros)

    def pagina_fluxo_caixa():
        p3_fluxo_caixa.render(dados, filtros)

    def pagina_custos():
        p4_centro_custos.render(dados, filtros)

    paginas = [
        st.Page(pagina_visao_executiva, title="Visão Executiva",   icon="🏠", default=True),
        st.Page(pagina_dre,             title="DRE Interativa",    icon="📊"),
        st.Page(pagina_fluxo_caixa,     title="Fluxo de Caixa",    icon="💵"),
        st.Page(pagina_custos,          title="Centro de Custos",  icon="📋"),
    ]

    pg = st.navigation(paginas, position="sidebar")
    pg.run()