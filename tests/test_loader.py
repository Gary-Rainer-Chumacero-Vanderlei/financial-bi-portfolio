# =============================================================================
# tests/test_loader.py
# Testes para src/data/loader.py
#
# ESTRATÉGIA:
# Testamos três cenários distintos:
#   1. Caminho feliz — dados válidos carregam corretamente
#   2. Arquivo ausente — DataNotFoundError é levantado
#   3. Schema inválido — SchemaValidationError é levantado
#
# Usamos tmp_path (fixture nativa do pytest) para criar arquivos
# temporários sem poluir o sistema de arquivos real.
# =============================================================================

import pytest
import pandas as pd
from pathlib import Path

from src.data.loader import DataLoader, DataNotFoundError, SchemaValidationError
from src.data.generator import FinancialDataGenerator
from config.settings import Settings


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="module")
def dados_reais():
    """
    Gera os dados reais e retorna o diretório onde foram salvos.

    scope="module" garante que os dados são gerados uma única vez
    para todos os testes deste módulo.
    """
    gen = FinancialDataGenerator(seed=42)
    gen.gerar_todos(salvar=True)
    return Settings.RAW_DATA_DIR


@pytest.fixture(scope="module")
def loader_real(dados_reais):
    """DataLoader apontando para os dados reais gerados."""
    return DataLoader(data_dir=dados_reais)


@pytest.fixture
def diretorio_vazio(tmp_path):
    """
    Diretório temporário vazio para simular ausência de arquivos.

    tmp_path é uma fixture nativa do pytest — cria um diretório
    temporário único para cada teste e o remove após a execução.
    """
    return tmp_path


@pytest.fixture
def diretorio_schema_invalido(tmp_path):
    """
    Diretório com CSVs que têm colunas incorretas.

    Simula o cenário de arquivos corrompidos ou gerados por versão
    incompatível do projeto.
    """
    # Cria um CSV com apenas duas colunas — schema inválido para todos os datasets
    df_invalido = pd.DataFrame({
        "competencia": ["2023-01"],
        "coluna_errada": [999],
    })
    for nome in ["dre", "fluxo_caixa", "centro_custos", "contas_receber"]:
        df_invalido.to_csv(tmp_path / f"{nome}.csv", index=False)
    return tmp_path


# =============================================================================
# TESTES — Caminho feliz (dados válidos)
# =============================================================================

def test_loader_carrega_dre(loader_real):
    """DataLoader deve carregar a DRE sem erros."""
    dre = loader_real.carregar_dre()
    assert isinstance(dre, pd.DataFrame)
    assert len(dre) == 24


def test_loader_carrega_fluxo_caixa(loader_real):
    """DataLoader deve carregar o fluxo de caixa sem erros."""
    fluxo = loader_real.carregar_fluxo_caixa()
    assert isinstance(fluxo, pd.DataFrame)
    assert len(fluxo) == 24


def test_loader_carrega_centro_custos(loader_real):
    """DataLoader deve carregar o centro de custos sem erros."""
    centro = loader_real.carregar_centro_custos()
    assert isinstance(centro, pd.DataFrame)
    assert len(centro) > 0


def test_loader_carrega_contas_receber(loader_real):
    """DataLoader deve carregar as contas a receber sem erros."""
    contas = loader_real.carregar_contas_receber()
    assert isinstance(contas, pd.DataFrame)
    assert len(contas) > 0


def test_loader_carregar_todos_retorna_quatro_datasets(loader_real):
    """carregar_todos() deve retornar exatamente 4 datasets."""
    dados = loader_real.carregar_todos()
    assert set(dados.keys()) == {
        "dre", "fluxo_caixa", "centro_custos", "contas_receber"
    }


def test_loader_carregar_todos_retorna_dataframes(loader_real):
    """Todos os datasets retornados devem ser DataFrames."""
    dados = loader_real.carregar_todos()
    for nome, df in dados.items():
        assert isinstance(df, pd.DataFrame), (
            f"'{nome}' não é um DataFrame: {type(df)}"
        )


def test_loader_verificar_disponibilidade_retorna_todos_true(loader_real):
    """
    Com dados válidos, verificar_disponibilidade() deve retornar True para todos.
    """
    status = loader_real.verificar_disponibilidade()
    assert set(status.keys()) == {
        "dre", "fluxo_caixa", "centro_custos", "contas_receber"
    }
    for nome, ok in status.items():
        assert ok is True, f"Dataset '{nome}' reportado como indisponível"


# =============================================================================
# TESTES — Arquivo ausente (DataNotFoundError)
# =============================================================================

def test_loader_levanta_data_not_found_dre(diretorio_vazio):
    """
    Deve levantar DataNotFoundError quando dre.csv não existe.

    pytest.raises() é o equivalente do try/except nos testes —
    verifica que a exceção esperada é levantada.
    """
    loader = DataLoader(data_dir=diretorio_vazio)
    with pytest.raises(DataNotFoundError):
        loader.carregar_dre()


def test_loader_levanta_data_not_found_fluxo(diretorio_vazio):
    """Deve levantar DataNotFoundError quando fluxo_caixa.csv não existe."""
    loader = DataLoader(data_dir=diretorio_vazio)
    with pytest.raises(DataNotFoundError):
        loader.carregar_fluxo_caixa()


def test_loader_mensagem_erro_contem_instrucao(diretorio_vazio):
    """
    A mensagem de erro deve conter instrução para o usuário.

    Um bom erro não apenas descreve o problema — indica como resolver.
    Verificamos que a mensagem contém a instrução de como gerar os dados.
    """
    loader = DataLoader(data_dir=diretorio_vazio)
    with pytest.raises(DataNotFoundError, match="generator"):
        loader.carregar_dre()


def test_loader_verificar_disponibilidade_retorna_false(diretorio_vazio):
    """
    Com diretório vazio, verificar_disponibilidade() deve retornar False para todos
    sem levantar exceção.
    """
    loader  = DataLoader(data_dir=diretorio_vazio)
    status  = loader.verificar_disponibilidade()
    for nome, ok in status.items():
        assert ok is False, f"Dataset '{nome}' reportado como disponível (não deveria)"


# =============================================================================
# TESTES — Schema inválido (SchemaValidationError)
# =============================================================================

def test_loader_levanta_schema_error_dre(diretorio_schema_invalido):
    """
    Deve levantar SchemaValidationError quando o CSV tem colunas incorretas.
    """
    loader = DataLoader(data_dir=diretorio_schema_invalido)
    with pytest.raises(SchemaValidationError):
        loader.carregar_dre()


def test_loader_mensagem_schema_error_lista_colunas(diretorio_schema_invalido):
    """
    A mensagem de SchemaValidationError deve listar as colunas ausentes.

    O usuário precisa saber exatamente o que está faltando para agir.
    """
    loader = DataLoader(data_dir=diretorio_schema_invalido)
    with pytest.raises(SchemaValidationError, match="ausentes"):
        loader.carregar_dre()


def test_loader_schema_error_nao_afeta_outros_datasets(diretorio_schema_invalido):
    """
    Um erro de schema em um dataset não deve impedir a verificação dos outros.

    verificar_disponibilidade() deve retornar False para o dataset com
    schema inválido sem levantar exceção.
    """
    loader = DataLoader(data_dir=diretorio_schema_invalido)
    status = loader.verificar_disponibilidade()
    # Todos devem ser False (schema inválido) — mas sem exceção
    for nome, ok in status.items():
        assert ok is False


# =============================================================================
# TESTES — Integridade dos dados carregados
# =============================================================================

def test_loader_dre_sem_nulos(loader_real):
    """DRE carregada não deve ter valores nulos."""
    dre = loader_real.carregar_dre()
    assert dre.isnull().sum().sum() == 0


def test_loader_colunas_numericas_sao_numericas(loader_real):
    """Colunas financeiras da DRE devem ser numéricas após carregamento."""
    dre = loader_real.carregar_dre()
    for col in ["receita_bruta", "receita_liquida", "ebitda", "lucro_liquido"]:
        assert pd.api.types.is_numeric_dtype(dre[col]), (
            f"Coluna '{col}' não é numérica: dtype={dre[col].dtype}"
        )


def test_loader_competencia_e_string(loader_real):
    """
    Coluna competencia deve ser do tipo string após carregamento.

    Pandas 2.x pode usar StringDtype em vez de object para colunas de texto.
    Verificamos com pd.api.types.is_string_dtype() que cobre ambos os casos.
    """
    dre = loader_real.carregar_dre()
    assert pd.api.types.is_string_dtype(dre["competencia"]), (
        f"competencia não é string: dtype={dre['competencia'].dtype}"
    )
