# =============================================================================
# tests/test_generator.py
# Testes para src/data/generator.py
#
# ESTRATÉGIA:
# Testamos sem salvar arquivos (salvar=False) — os testes não devem
# depender do sistema de arquivos. Cada teste verifica uma propriedade
# específica dos dados gerados, seguindo o padrão AAA.
# =============================================================================

import pytest
import numpy as np
import pandas as pd

from src.data.generator import FinancialDataGenerator


# =============================================================================
# FIXTURES
# Criadas uma vez e reutilizadas por múltiplos testes.
# =============================================================================

@pytest.fixture(scope="module")
def generator():
    """
    Instância do gerador com seed fixo.

    scope="module" significa que a fixture é criada uma vez por arquivo
    de teste — não a cada função. Economiza tempo pois a instância é
    reutilizada por todos os testes deste módulo.
    """
    return FinancialDataGenerator(seed=42)


@pytest.fixture(scope="module")
def todos_datasets(generator):
    """
    Todos os DataFrames gerados sem salvar em disco.

    Depende da fixture 'generator' — pytest resolve a dependência
    automaticamente pela assinatura da função.
    """
    return generator.gerar_todos(salvar=False)


@pytest.fixture(scope="module")
def dre(todos_datasets):
    return todos_datasets["dre"]


@pytest.fixture(scope="module")
def fluxo(todos_datasets):
    return todos_datasets["fluxo_caixa"]


@pytest.fixture(scope="module")
def centro(todos_datasets):
    return todos_datasets["centro_custos"]


@pytest.fixture(scope="module")
def contas(todos_datasets):
    return todos_datasets["contas_receber"]


# =============================================================================
# TESTES — FinancialDataGenerator (instância e configuração)
# =============================================================================

def test_generator_cria_instancia():
    """Verifica que o gerador é instanciado sem erros."""
    gen = FinancialDataGenerator(seed=42)
    assert gen is not None


def test_generator_seed_diferente_gera_dados_diferentes():
    """
    Dois geradores com seeds diferentes devem produzir dados distintos.

    Garante que o seed realmente controla a aleatoriedade — um gerador
    com seed diferente não pode produzir os mesmos valores.
    """
    gen_a = FinancialDataGenerator(seed=42)
    gen_b = FinancialDataGenerator(seed=99)

    dre_a = gen_a.gerar_todos(salvar=False)["dre"]
    dre_b = gen_b.gerar_todos(salvar=False)["dre"]

    assert not dre_a["receita_bruta"].equals(dre_b["receita_bruta"])


def test_generator_seed_igual_reproduz_dados():
    """
    Dois geradores com o mesmo seed devem produzir dados idênticos.

    Esta é a propriedade de reprodutibilidade — essencial para que
    qualquer pessoa que clone o repositório obtenha os mesmos CSVs.
    """
    gen_a = FinancialDataGenerator(seed=42)
    gen_b = FinancialDataGenerator(seed=42)

    dre_a = gen_a.gerar_todos(salvar=False)["dre"]
    dre_b = gen_b.gerar_todos(salvar=False)["dre"]

    pd.testing.assert_frame_equal(dre_a, dre_b)


def test_gerar_todos_retorna_quatro_datasets(todos_datasets):
    """Verifica que gerar_todos() retorna exatamente 4 datasets."""
    assert set(todos_datasets.keys()) == {
        "dre", "fluxo_caixa", "centro_custos", "contas_receber"
    }


# =============================================================================
# TESTES — DRE
# =============================================================================

def test_dre_shape(dre):
    """DRE deve ter 24 linhas (Jan/2023–Dez/2024) e pelo menos 20 colunas."""
    assert dre.shape[0] == 24
    assert dre.shape[1] >= 20


def test_dre_colunas_obrigatorias(dre):
    """Verifica presença das colunas críticas da DRE."""
    colunas_esperadas = {
        "competencia", "ano", "mes",
        "receita_bruta", "receita_liquida",
        "ebitda", "lucro_liquido",
        "margem_ebitda_pct", "margem_liquida_pct",
    }
    assert colunas_esperadas.issubset(set(dre.columns))


def test_dre_anos_corretos(dre):
    """A DRE deve cobrir exatamente os anos 2023 e 2024."""
    assert set(dre["ano"].unique()) == {2023, 2024}


def test_dre_meses_completos(dre):
    """Cada ano deve ter exatamente 12 meses."""
    for ano in [2023, 2024]:
        meses = dre[dre["ano"] == ano]["mes"].tolist()
        assert sorted(meses) == list(range(1, 13)), (
            f"Ano {ano} não tem os 12 meses completos: {meses}"
        )


def test_dre_receita_bruta_positiva(dre):
    """Receita bruta deve ser sempre positiva."""
    assert (dre["receita_bruta"] > 0).all(), (
        "Encontrado mês com receita bruta <= 0"
    )


def test_dre_receita_liquida_menor_que_bruta(dre):
    """Receita líquida deve ser sempre menor que receita bruta (há deduções)."""
    assert (dre["receita_liquida"] < dre["receita_bruta"]).all()


def test_dre_margens_em_intervalo_razoavel(dre):
    """
    Margens devem estar em intervalos economicamente plausíveis.

    Uma distribuidora de energia com margens fora desses intervalos
    indicaria bug no gerador, não comportamento esperado.
    """
    assert dre["margem_bruta_pct"].between(20, 60).all(), (
        "Margem bruta fora do intervalo esperado (20%–60%)"
    )
    assert dre["margem_ebitda_pct"].between(-5, 40).all(), (
        "Margem EBITDA fora do intervalo esperado (-5%–40%)"
    )


def test_dre_sem_valores_nulos(dre):
    """Nenhuma coluna da DRE deve ter valores nulos."""
    nulos = dre.isnull().sum()
    colunas_com_nulo = nulos[nulos > 0].index.tolist()
    assert len(colunas_com_nulo) == 0, (
        f"Colunas com valores nulos: {colunas_com_nulo}"
    )


def test_dre_competencia_formato_correto(dre):
    """Coluna competencia deve seguir o formato AAAA-MM."""
    import re
    padrao = re.compile(r"^\d{4}-\d{2}$")
    invalidas = dre[~dre["competencia"].str.match(padrao)]["competencia"].tolist()
    assert len(invalidas) == 0, f"Competências com formato inválido: {invalidas}"


# =============================================================================
# TESTES — Fluxo de Caixa
# =============================================================================

def test_fluxo_shape(fluxo):
    """Fluxo de caixa deve ter 24 linhas."""
    assert fluxo.shape[0] == 24


def test_fluxo_colunas_obrigatorias(fluxo):
    """Verifica presença das colunas críticas do fluxo de caixa."""
    colunas_esperadas = {
        "competencia", "fco", "saldo_final",
        "recebimentos", "total_saidas", "variacao_caixa",
    }
    assert colunas_esperadas.issubset(set(fluxo.columns))


def test_fluxo_saldo_acumulado_coerente(fluxo):
    """
    O saldo_final de cada mês deve ser igual ao saldo anterior mais a variação.

    Testa a lógica de acumulação — o principal invariante do fluxo de caixa.
    Usamos tolerância de R$ 1,00 para erros de arredondamento.
    """
    fluxo_ord = fluxo.sort_values("competencia").reset_index(drop=True)
    for i in range(1, len(fluxo_ord)):
        saldo_esperado = fluxo_ord.loc[i - 1, "saldo_final"] + fluxo_ord.loc[i, "variacao_caixa"]
        saldo_real     = fluxo_ord.loc[i, "saldo_final"]
        assert abs(saldo_esperado - saldo_real) < 1.0, (
            f"Saldo incoerente no mês {fluxo_ord.loc[i, 'competencia']}: "
            f"esperado {saldo_esperado:.2f}, obtido {saldo_real:.2f}"
        )


def test_fluxo_sem_valores_nulos(fluxo):
    """Nenhuma coluna do fluxo deve ter valores nulos."""
    nulos = fluxo.isnull().sum()
    assert nulos.sum() == 0, f"Colunas com nulos: {nulos[nulos > 0].to_dict()}"


# =============================================================================
# TESTES — Centro de Custos
# =============================================================================

def test_centro_shape_minimo(centro):
    """Centro de custos deve ter pelo menos 100 registros."""
    assert len(centro) >= 100


def test_centro_colunas_obrigatorias(centro):
    """Verifica presença das colunas críticas do centro de custos."""
    colunas_esperadas = {
        "competencia", "departamento", "categoria",
        "valor", "variacao_pct", "is_outlier",
    }
    assert colunas_esperadas.issubset(set(centro.columns))


def test_centro_valores_positivos(centro):
    """Todos os valores de gasto devem ser positivos."""
    assert (centro["valor"] > 0).all()


def test_centro_outliers_sao_minoria(centro):
    """
    Outliers intencionais devem representar menos de 15% dos registros.

    O gerador cria outliers com probabilidade de 8%. Em 384 registros,
    esperamos entre 15 e 60 outliers. Mais que 15% indica bug no gerador.
    """
    pct_outliers = centro["is_outlier"].mean() * 100
    assert pct_outliers < 15, (
        f"Outliers representam {pct_outliers:.1f}% — acima do esperado (< 15%)"
    )


def test_centro_departamentos_esperados(centro):
    """Os quatro departamentos devem estar presentes."""
    esperados = {"Comercial", "Operações", "Administrativo", "Financeiro"}
    presentes = set(centro["departamento"].unique())
    assert esperados == presentes


# =============================================================================
# TESTES — Contas a Receber
# =============================================================================

def test_contas_shape_minimo(contas):
    """Contas a receber deve ter pelo menos 100 registros."""
    assert len(contas) >= 100


def test_contas_colunas_obrigatorias(contas):
    """Verifica presença das colunas críticas de contas a receber."""
    colunas_esperadas = {
        "competencia", "cod_cliente", "cliente",
        "setor", "porte", "faixa_aging",
        "valor", "inadimplente",
    }
    assert colunas_esperadas.issubset(set(contas.columns))


def test_contas_inadimplente_binario(contas):
    """A coluna inadimplente deve conter apenas 0 ou 1."""
    valores_unicos = set(contas["inadimplente"].unique())
    assert valores_unicos.issubset({0, 1}), (
        f"Valores inesperados em 'inadimplente': {valores_unicos}"
    )


def test_contas_faixas_aging_validas(contas):
    """Apenas faixas de aging válidas devem estar presentes."""
    faixas_validas = {
        "A vencer", "1-30 dias", "31-60 dias",
        "61-90 dias", "91-180 dias", ">180 dias",
    }
    faixas_presentes = set(contas["faixa_aging"].unique())
    invalidas = faixas_presentes - faixas_validas
    assert len(invalidas) == 0, f"Faixas de aging inválidas: {invalidas}"


def test_contas_valores_positivos(contas):
    """Todos os valores das contas a receber devem ser positivos."""
    assert (contas["valor"] > 0).all()


def test_contas_inadimplencia_so_em_vencidas(contas):
    """
    Títulos 'A vencer' não devem ser marcados como inadimplentes.

    Um título que ainda não venceu não pode estar inadimplente —
    é uma regra de negócio fundamental da gestão de recebíveis.
    """
    a_vencer_inadimplentes = contas[
        (contas["faixa_aging"] == "A vencer") &
        (contas["inadimplente"] == 1)
    ]
    assert len(a_vencer_inadimplentes) == 0, (
        f"Encontrados {len(a_vencer_inadimplentes)} títulos 'A vencer' marcados como inadimplentes"
    )
