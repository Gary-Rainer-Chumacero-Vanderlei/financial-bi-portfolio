# =============================================================================
# src/data/loader.py
# Carregamento, validação e entrega dos datasets financeiros.
#
# CORREÇÃO PARA STREAMLIT CLOUD:
# O argumento padrão `data_dir` não é mais avaliado em tempo de importação.
# Antes: `def __init__(self, data_dir: Path = Settings.RAW_DATA_DIR)`
# Depois: `def __init__(self, data_dir: Path | None = None)` com resolução
# lazy dentro do método. Isso evita que um path inválido no momento da
# importação quebre o módulo inteiro antes do app iniciar.
# =============================================================================

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from config.settings import Settings

logger = logging.getLogger(__name__)


# =============================================================================
# SCHEMAS DE VALIDAÇÃO
# =============================================================================

_SCHEMAS: dict[str, list[str]] = {
    "dre": [
        "competencia", "ano", "mes",
        "receita_bruta", "deducoes", "receita_liquida",
        "cmv", "lucro_bruto",
        "desp_vendas", "desp_administrativas", "desp_outras", "total_desp_opex",
        "ebitda", "depreciacao", "ebit",
        "resultado_financeiro", "lair", "ir_csll", "lucro_liquido",
        "margem_bruta_pct", "margem_ebitda_pct", "margem_liquida_pct",
    ],
    "fluxo_caixa": [
        "competencia", "ano", "mes",
        "recebimentos", "total_saidas", "fco",
        "capex", "financiamento", "variacao_caixa", "saldo_final",
    ],
    "centro_custos": [
        "competencia", "ano", "mes",
        "departamento", "categoria", "valor",
        "variacao_pct", "is_outlier",
    ],
    "contas_receber": [
        "competencia", "ano", "mes",
        "cod_cliente", "cliente", "setor", "porte",
        "faixa_aging", "valor", "inadimplente",
    ],
}

_TIPOS_NUMERICOS: dict[str, list[str]] = {
    "dre":            ["receita_bruta", "receita_liquida", "ebitda", "lucro_liquido"],
    "fluxo_caixa":   ["recebimentos", "fco", "saldo_final"],
    "centro_custos":  ["valor"],
    "contas_receber": ["valor"],
}


# =============================================================================
# EXCEÇÕES CUSTOMIZADAS
# =============================================================================

class DataNotFoundError(FileNotFoundError):
    """Levantado quando um arquivo CSV não é encontrado."""


class SchemaValidationError(ValueError):
    """Levantado quando um CSV carregado não contém as colunas esperadas."""


# =============================================================================
# CLASSE PRINCIPAL
# =============================================================================

class DataLoader:
    """
    Carrega e valida os datasets financeiros do projeto.

    Args:
        data_dir: Diretório onde os CSVs estão armazenados.
                  Se None, usa Settings.RAW_DATA_DIR (resolvido lazily).

    Raises:
        DataNotFoundError: Se o CSV não existir no diretório.
        SchemaValidationError: Se o CSV não contiver as colunas esperadas.
    """

    def __init__(self, data_dir: Path | None = None) -> None:
        # CORREÇÃO: resolução lazy — Settings.RAW_DATA_DIR é acessado aqui,
        # dentro do __init__, não como default argument no def. Isso garante
        # que o módulo pode ser importado mesmo antes do PROJECT_ROOT estar
        # totalmente estável, e que qualquer mudança no env é refletida.
        self.data_dir: Path = data_dir if data_dir is not None else Settings.RAW_DATA_DIR

    # =========================================================================
    # MÉTODOS PRIVADOS
    # =========================================================================

    def _carregar_csv(self, nome: str) -> pd.DataFrame:
        """
        Lê um CSV pelo nome do dataset e retorna o DataFrame bruto.

        Raises:
            DataNotFoundError: Se o arquivo não existir ou estiver vazio.
            SchemaValidationError: Se o CSV não puder ser interpretado.
        """
        caminho: Path = self.data_dir / f"{nome}.csv"

        if not caminho.exists():
            raise DataNotFoundError(
                f"\nArquivo não encontrado: {caminho}\n"
                f"Execute o gerador para criar os dados:\n"
                f"  python -m src.data.generator\n"
            )

        try:
            df = pd.read_csv(caminho, encoding="utf-8")
            logger.debug("Carregado: %s (%d linhas)", caminho.name, len(df))
            return df

        except pd.errors.EmptyDataError:
            raise DataNotFoundError(
                f"O arquivo existe mas está vazio: {caminho}\n"
                f"Delete o arquivo e execute o gerador novamente."
            )

        except pd.errors.ParserError as e:
            raise SchemaValidationError(
                f"Erro ao interpretar o CSV '{nome}': {e}\n"
                f"O arquivo pode estar corrompido."
            )

    def _validar_schema(self, df: pd.DataFrame, nome: str) -> None:
        """
        Verifica se o DataFrame contém todas as colunas obrigatórias
        e se as colunas numéricas críticas têm o tipo correto.

        Raises:
            SchemaValidationError: Se colunas estiverem ausentes ou com
                                   tipo incorreto.
        """
        colunas_esperadas = set(_SCHEMAS[nome])
        colunas_presentes = set(df.columns)

        ausentes = colunas_esperadas - colunas_presentes
        if ausentes:
            raise SchemaValidationError(
                f"Dataset '{nome}' está com colunas ausentes:\n"
                f"  Faltando: {sorted(ausentes)}\n"
                f"  Presentes: {sorted(colunas_presentes)}\n"
                f"Regenere os dados com: python -m src.data.generator"
            )

        for coluna in _TIPOS_NUMERICOS.get(nome, []):
            if not pd.api.types.is_numeric_dtype(df[coluna]):
                raise SchemaValidationError(
                    f"Dataset '{nome}': coluna '{coluna}' deveria ser numérica "
                    f"mas foi lida como '{df[coluna].dtype}'.\n"
                    f"Verifique se o CSV contém valores não numéricos nesta coluna."
                )

        logger.debug("Schema válido: %s", nome)

    def _carregar_e_validar(self, nome: str) -> pd.DataFrame:
        """Combina carregamento e validação em uma única operação."""
        df = self._carregar_csv(nome)
        self._validar_schema(df, nome)
        return df

    # =========================================================================
    # MÉTODOS PÚBLICOS
    # =========================================================================

    def carregar_dre(self) -> pd.DataFrame:
        """Carrega e valida a Demonstração de Resultado do Exercício."""
        logger.info("Carregando DRE...")
        return self._carregar_e_validar("dre")

    def carregar_fluxo_caixa(self) -> pd.DataFrame:
        """Carrega e valida o Fluxo de Caixa."""
        logger.info("Carregando Fluxo de Caixa...")
        return self._carregar_e_validar("fluxo_caixa")

    def carregar_centro_custos(self) -> pd.DataFrame:
        """Carrega e valida o Centro de Custos."""
        logger.info("Carregando Centro de Custos...")
        return self._carregar_e_validar("centro_custos")

    def carregar_contas_receber(self) -> pd.DataFrame:
        """Carrega e valida as Contas a Receber."""
        logger.info("Carregando Contas a Receber...")
        return self._carregar_e_validar("contas_receber")

    def carregar_todos(self) -> dict[str, pd.DataFrame]:
        """
        Carrega e valida todos os datasets de uma vez.

        Returns:
            Dicionário com chaves 'dre', 'fluxo_caixa',
            'centro_custos', 'contas_receber'.
        """
        logger.info("Carregando todos os datasets...")

        dados: dict[str, pd.DataFrame] = {
            "dre":            self.carregar_dre(),
            "fluxo_caixa":    self.carregar_fluxo_caixa(),
            "centro_custos":  self.carregar_centro_custos(),
            "contas_receber": self.carregar_contas_receber(),
        }

        logger.info(
            "Todos os datasets carregados. Linhas: %s",
            {k: len(v) for k, v in dados.items()},
        )
        return dados

    def verificar_disponibilidade(self) -> dict[str, bool]:
        """
        Verifica quais datasets estão disponíveis sem lançar exceções.

        Returns:
            Dicionário nome → True se o CSV existe e é válido.
        """
        status: dict[str, bool] = {}

        for nome in _SCHEMAS:
            try:
                df = self._carregar_csv(nome)
                self._validar_schema(df, nome)
                status[nome] = True
            except (DataNotFoundError, SchemaValidationError) as e:
                logger.warning("Dataset indisponível '%s': %s", nome, e)
                status[nome] = False

        return status
