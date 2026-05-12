# =============================================================================
# tests/test_kpis.py
# Testes para src/analysis/kpis.py
#
# ESTRATÉGIA:
# Funções puras são as mais fáceis de testar — passamos valores conhecidos
# e verificamos resultados exatos. Não precisamos de arquivos nem de estado.
#
# Para funções que operam sobre DataFrames, construímos fixtures mínimas
# com apenas as colunas necessárias para cada teste.
# =============================================================================

import pytest
import pandas as pd
import numpy as np

from src.analysis.kpis import (
    calcular_margem,
    calcular_variacao_yoy,
    calcular_score_saude,
    classificar_score,
    formatar_brl,
    enriquecer_dre,
    calcular_kpis_executivos,
    calcular_comparativo_yoy,
    calcular_inadimplencia_mensal,
    calcular_aging_consolidado,
)
from config.settings import Settings


# =============================================================================
# FIXTURES — DataFrames mínimos para testes
# =============================================================================

@pytest.fixture
def dre_minima():
    """
    DRE mínima com 4 meses (2 por ano) para testes de cálculo.

    Usamos valores redondos para que os resultados esperados sejam
    exatos — sem erros de ponto flutuante.
    """
    return pd.DataFrame({
        "competencia":       ["2023-01", "2023-02", "2024-01", "2024-02"],
        "ano":               [2023, 2023, 2024, 2024],
        "mes":               [1, 2, 1, 2],
        "receita_bruta":     [5_000_000.0, 5_200_000.0, 5_400_000.0, 5_600_000.0],
        "deducoes":          [  900_000.0,   936_000.0,   972_000.0, 1_008_000.0],
        "receita_liquida":   [4_100_000.0, 4_264_000.0, 4_428_000.0, 4_592_000.0],
        "cmv":               [2_460_000.0, 2_558_400.0, 2_656_800.0, 2_755_200.0],
        "lucro_bruto":       [1_640_000.0, 1_705_600.0, 1_771_200.0, 1_836_800.0],
        "desp_vendas":       [  164_000.0,   170_560.0,   177_120.0,   183_680.0],
        "desp_administrativas": [123_000.0, 127_920.0,  132_840.0,   137_760.0],
        "desp_outras":       [   41_000.0,    42_640.0,    44_280.0,    45_920.0],
        "total_desp_opex":   [  328_000.0,   341_120.0,   354_240.0,   367_360.0],
        "ebitda":            [1_312_000.0, 1_364_480.0, 1_416_960.0, 1_469_440.0],
        "depreciacao":       [   41_000.0,    42_640.0,    44_280.0,    45_920.0],
        "ebit":              [1_271_000.0, 1_321_840.0, 1_372_680.0, 1_423_520.0],
        "resultado_financeiro": [-61_500.0,  -63_960.0,  -66_420.0,   -68_880.0],
        "lair":              [1_209_500.0, 1_257_880.0, 1_306_260.0, 1_354_640.0],
        "ir_csll":           [  411_230.0,   427_679.2,  444_128.4,   460_577.6],
        "lucro_liquido":     [  798_270.0,   830_200.8,  862_131.6,   894_062.4],
        "margem_bruta_pct":  [        40.0,        40.0,       40.0,        40.0],
        "margem_ebitda_pct": [        32.0,        32.0,       32.0,        32.0],
        "margem_liquida_pct":[        19.47,       19.47,      19.47,       19.47],
    })


@pytest.fixture
def fluxo_minimo():
    """Fluxo de caixa mínimo para testes de KPIs executivos."""
    return pd.DataFrame({
        "competencia":    ["2023-01", "2023-02", "2024-01", "2024-02"],
        "ano":            [2023, 2023, 2024, 2024],
        "mes":            [1, 2, 1, 2],
        "recebimentos":   [3_900_000.0, 4_050_000.0, 4_200_000.0, 4_350_000.0],
        "total_saidas":   [3_500_000.0, 3_640_000.0, 3_780_000.0, 3_920_000.0],
        "fco":            [  400_000.0,   410_000.0,   420_000.0,   430_000.0],
        "capex":          [   50_000.0,    30_000.0,    60_000.0,    40_000.0],
        "financiamento":  [  -20_000.0,   -20_000.0,   -20_000.0,   -20_000.0],
        "variacao_caixa": [  330_000.0,   360_000.0,   340_000.0,   370_000.0],
        "saldo_final":    [1_530_000.0, 1_890_000.0, 2_230_000.0, 2_600_000.0],
    })


@pytest.fixture
def contas_minimas():
    """Contas a receber mínimas com casos de inadimplência."""
    return pd.DataFrame({
        "competencia":  ["2024-02", "2024-02", "2024-02", "2024-02"],
        "ano":          [2024, 2024, 2024, 2024],
        "mes":          [2, 2, 2, 2],
        "cod_cliente":  ["CLI-001", "CLI-002", "CLI-003", "CLI-004"],
        "cliente":      ["Cliente A", "Cliente B", "Cliente C", "Cliente D"],
        "setor":        ["Indústria"] * 4,
        "porte":        ["Médio"] * 4,
        "faixa_aging":  ["A vencer", "1-30 dias", "31-60 dias", "1-30 dias"],
        "valor":        [100_000.0, 200_000.0, 150_000.0, 50_000.0],
        "inadimplente": [0, 0, 1, 1],
    })


# =============================================================================
# TESTES — calcular_margem
# =============================================================================

def test_calcular_margem_caso_normal():
    """Margem deve ser lucro/receita * 100."""
    assert calcular_margem(480_000, 4_800_000) == 10.0


def test_calcular_margem_negativa():
    """Margem negativa deve ser calculada corretamente."""
    assert calcular_margem(-100_000, 4_800_000) == round(-100_000 / 4_800_000 * 100, 2)


def test_calcular_margem_receita_zero():
    """Divisão por zero deve retornar 0.0, não levantar exceção."""
    assert calcular_margem(100_000, 0) == 0.0


def test_calcular_margem_arredondamento():
    """Resultado deve ter no máximo 2 casas decimais."""
    resultado = calcular_margem(1, 3)
    assert resultado == round(1 / 3 * 100, 2)


def test_calcular_margem_cem_por_cento():
    """Margem de 100% quando lucro == receita."""
    assert calcular_margem(1_000, 1_000) == 100.0


# =============================================================================
# TESTES — calcular_variacao_yoy
# =============================================================================

def test_variacao_yoy_crescimento():
    """Crescimento de 10% deve retornar 10.0."""
    assert calcular_variacao_yoy(110, 100) == 10.0


def test_variacao_yoy_queda():
    """Queda de 10% deve retornar -10.0."""
    assert calcular_variacao_yoy(90, 100) == -10.0


def test_variacao_yoy_sem_mudanca():
    """Sem variação deve retornar 0.0."""
    assert calcular_variacao_yoy(100, 100) == 0.0


def test_variacao_yoy_base_zero():
    """Com base zero deve retornar 0.0 sem exceção."""
    assert calcular_variacao_yoy(100, 0) == 0.0


def test_variacao_yoy_base_negativa():
    """Variação com base negativa deve usar valor absoluto."""
    resultado = calcular_variacao_yoy(-80, -100)
    assert resultado == round((-80 - (-100)) / 100 * 100, 2)


# =============================================================================
# TESTES — calcular_score_saude
# =============================================================================

def test_score_maximo():
    """Score máximo quando margem alta, FCO positivo, inadimplência zero."""
    score = calcular_score_saude(
        margem_ebitda=Settings.SCORE_META_MARGEM,
        fco=500_000,
        taxa_inadimplencia=0.0,
    )
    assert score == 100.0


def test_score_minimo():
    """Score zero quando margem negativa, FCO negativo, inadimplência alta."""
    score = calcular_score_saude(
        margem_ebitda=-5.0,
        fco=-100_000,
        taxa_inadimplencia=15.0,
    )
    assert score == 0.0


def test_score_nao_ultrapassa_cem():
    """Score não deve ultrapassar 100 mesmo com margem muito alta."""
    score = calcular_score_saude(
        margem_ebitda=100.0,
        fco=999_999,
        taxa_inadimplencia=0.0,
    )
    assert score <= 100.0


def test_score_componente_fco_binario():
    """FCO positivo deve contribuir com SCORE_PESO_FCO; negativo com zero."""
    score_positivo = calcular_score_saude(0.0, fco=1.0, taxa_inadimplencia=10.0)
    score_negativo = calcular_score_saude(0.0, fco=-1.0, taxa_inadimplencia=10.0)
    diferenca = score_positivo - score_negativo
    assert diferenca == Settings.SCORE_PESO_FCO


# =============================================================================
# TESTES — classificar_score
# =============================================================================

@pytest.mark.parametrize("score,esperado", [
    (100.0, "Saudável"),
    (70.0,  "Saudável"),   # exatamente no limiar
    (69.9,  "Atenção"),
    (50.0,  "Atenção"),    # exatamente no limiar
    (49.9,  "Crítico"),
    (0.0,   "Crítico"),
])
def test_classificar_score_faixas(score, esperado):
    """
    Verifica todas as faixas de classificação incluindo os limiares.

    @pytest.mark.parametrize executa o mesmo teste com múltiplos
    conjuntos de valores — evita repetição e documenta os casos de borda.
    """
    assert classificar_score(score) == esperado


# =============================================================================
# TESTES — formatar_brl
# =============================================================================

@pytest.mark.parametrize("valor,esperado", [
    (4_800_000, "R$ 4,80M"),
    (1_000_000, "R$ 1,00M"),
    (320_000,   "R$ 320,0K"),
    (1_000,     "R$ 1,0K"),
    (-150_000,  "R$ -150,0K"),
    (-4_800_000,"R$ -4,80M"),
])
def test_formatar_brl(valor, esperado):
    """Verifica formatação monetária abreviada para múltiplos casos."""
    assert formatar_brl(valor) == esperado


# =============================================================================
# TESTES — enriquecer_dre
# =============================================================================

def test_enriquecer_dre_adiciona_colunas(dre_minima):
    """enriquecer_dre() deve adicionar as colunas esperadas."""
    resultado = enriquecer_dre(dre_minima)
    assert "periodo_label" in resultado.columns
    assert "crescimento_receita" in resultado.columns


def test_enriquecer_dre_nao_modifica_original(dre_minima):
    """enriquecer_dre() não deve modificar o DataFrame original."""
    colunas_antes = set(dre_minima.columns)
    enriquecer_dre(dre_minima)
    assert set(dre_minima.columns) == colunas_antes


def test_enriquecer_dre_periodo_label_formato(dre_minima):
    """periodo_label deve seguir o formato 'Mês/AAAA'."""
    resultado = enriquecer_dre(dre_minima)
    labels = resultado["periodo_label"].tolist()
    assert labels[0] == "Jan/2023"
    assert labels[2] == "Jan/2024"


def test_enriquecer_dre_margens_recalculadas(dre_minima):
    """Margens recalculadas devem ser coerentes com os valores base."""
    resultado = enriquecer_dre(dre_minima)
    margem_esperada = round(
        dre_minima["ebitda"].iloc[0] / dre_minima["receita_liquida"].iloc[0] * 100, 2
    )
    assert abs(resultado["margem_ebitda_pct"].iloc[0] - margem_esperada) < 0.01


# =============================================================================
# TESTES — calcular_kpis_executivos
# =============================================================================

def test_kpis_executivos_retorna_chaves_esperadas(dre_minima, fluxo_minimo, contas_minimas):
    """calcular_kpis_executivos() deve retornar todas as chaves esperadas."""
    resultado = calcular_kpis_executivos(dre_minima, fluxo_minimo, contas_minimas)
    chaves_esperadas = {
        "periodo", "receita_liquida", "ebitda", "margem_ebitda_pct",
        "lucro_liquido", "fco", "saldo_caixa",
        "taxa_inadimplencia", "score_saude", "classificacao_saude",
    }
    assert chaves_esperadas.issubset(set(resultado.keys()))


def test_kpis_executivos_periodo_e_ultimo_mes(dre_minima, fluxo_minimo, contas_minimas):
    """O período retornado deve ser o mais recente do dataset."""
    resultado = calcular_kpis_executivos(dre_minima, fluxo_minimo, contas_minimas)
    assert resultado["periodo"] == "2024-02"


def test_kpis_executivos_score_entre_zero_e_cem(dre_minima, fluxo_minimo, contas_minimas):
    """Score de saúde deve estar entre 0 e 100."""
    resultado = calcular_kpis_executivos(dre_minima, fluxo_minimo, contas_minimas)
    assert 0 <= resultado["score_saude"] <= 100


# =============================================================================
# TESTES — calcular_inadimplencia_mensal
# =============================================================================

def test_inadimplencia_taxa_calculada(contas_minimas):
    """
    Taxa de inadimplência deve ser calculada corretamente.

    No fixture: valor inadimplente = 150k + 50k = 200k
                carteira total    = 100k + 200k + 150k + 50k = 500k
                taxa esperada     = 200k / 500k * 100 = 40%
    """
    resultado = calcular_inadimplencia_mensal(contas_minimas)
    assert len(resultado) == 1  # apenas um mês no fixture
    assert resultado["taxa_inadimplencia_pct"].iloc[0] == pytest.approx(40.0, abs=0.01)


def test_inadimplencia_sem_inadimplentes():
    """Taxa deve ser 0.0 quando não há inadimplentes."""
    contas_ok = pd.DataFrame({
        "competencia":  ["2023-01", "2023-01"],
        "valor":        [100_000.0, 200_000.0],
        "inadimplente": [0, 0],
    })
    resultado = calcular_inadimplencia_mensal(contas_ok)
    assert resultado["taxa_inadimplencia_pct"].iloc[0] == 0.0


# =============================================================================
# TESTES — calcular_comparativo_yoy
# =============================================================================

def test_comparativo_yoy_shape(dre_minima):
    """Comparativo YoY deve ter 2 linhas (um por mês presente nos dois anos)."""
    resultado = calcular_comparativo_yoy(dre_minima)
    # Fixture tem meses 1 e 2 em ambos os anos
    assert len(resultado) == 2


def test_comparativo_yoy_colunas(dre_minima):
    """Comparativo deve conter colunas de variação e delta de margem."""
    resultado = calcular_comparativo_yoy(dre_minima)
    assert "var_receita_pct" in resultado.columns
    assert "delta_margem_pp" in resultado.columns


def test_comparativo_yoy_crescimento_correto(dre_minima):
    """
    Variação de receita deve refletir o crescimento real dos dados.

    Receita Jan/2023: 4_100_000 | Jan/2024: 4_428_000
    Variação esperada: (4_428_000 - 4_100_000) / 4_100_000 * 100 ≈ +8.0%
    """
    resultado = calcular_comparativo_yoy(dre_minima)
    var_jan = resultado[resultado["mes"] == 1]["var_receita_pct"].iloc[0]
    esperado = round((4_428_000 - 4_100_000) / 4_100_000 * 100, 2)
    assert abs(var_jan - esperado) < 0.1
