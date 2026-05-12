# =============================================================================
# src/data/generator.py
# =============================================================================
from __future__ import annotations
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from config.settings import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger(__name__)

_MESES = np.arange(1, 13)
_SAZONALIDADE: np.ndarray = np.round(1.0 + 0.18 * np.sin(np.pi / 6 * _MESES - np.pi / 3), 4)

_DEPARTAMENTOS: dict[str, list[str]] = {
    "Comercial":      ["Comissões", "Marketing", "Eventos", "CRM"],
    "Operações":      ["Logística", "Manutenção", "EPI", "Combustível"],
    "Administrativo": ["Pessoal", "Aluguel", "TI", "Jurídico"],
    "Financeiro":     ["IOF/Taxas", "Seguros", "Auditoria", "Câmbio"],
}

_SETORES: list[str] = ["Indústria", "Comércio", "Serviços", "Agronegócio", "Construção"]
_PORTES: list[str] = ["Pequeno", "Médio", "Grande"]
_PROB_INADIMPLENCIA: dict[str, float] = {"Pequeno": 0.25, "Médio": 0.12, "Grande": 0.05}
_FAIXAS_AGING: list[str] = ["A vencer", "1-30 dias", "31-60 dias", "61-90 dias", "91-180 dias", ">180 dias"]
_PESOS_AGING: list[float] = [0.55, 0.20, 0.10, 0.07, 0.05, 0.03]


class FinancialDataGenerator:
    """
    Gerador de dados sintéticos financeiros.

    CORREÇÃO: output_dir não é mais avaliado como default argument —
    era avaliado em tempo de importação, antes do PROJECT_ROOT estar
    estável. Agora é resolvido dentro do __init__.
    """

    def __init__(self, seed: int = Settings.SEED, output_dir: Path | None = None) -> None:
        self.rng = np.random.default_rng(seed)
        # Resolução lazy: evita avaliação em tempo de importação
        self.output_dir: Path = output_dir if output_dir is not None else Settings.RAW_DATA_DIR
        self.datas: pd.DatetimeIndex = pd.date_range(
            start=Settings.START_DATE, periods=Settings.N_MONTHS, freq="MS"
        )
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _gerar_dre(self) -> pd.DataFrame:
        logger.info("Gerando DRE...")
        receitas: list[float] = []
        for data in self.datas:
            mes_idx = data.month - 1
            fator_ano = 1.08 if data.year == 2024 else 1.0
            ruido = self.rng.normal(loc=1.0, scale=0.05)
            receita_bruta = Settings.RECEITA_BASE * _SAZONALIDADE[mes_idx] * fator_ano * ruido
            receitas.append(receita_bruta)

        receitas_arr = np.array(receitas)
        aliq_deducoes = self.rng.uniform(0.17, 0.19, size=len(self.datas))
        deducoes = receitas_arr * aliq_deducoes
        receita_liquida = receitas_arr - deducoes
        aliq_cmv = self.rng.uniform(0.55, 0.62, size=len(self.datas))
        cmv = receita_liquida * aliq_cmv
        lucro_bruto = receita_liquida - cmv
        desp_vendas = receita_liquida * self.rng.uniform(0.04, 0.07, size=len(self.datas))
        desp_adm    = receita_liquida * self.rng.uniform(0.03, 0.05, size=len(self.datas))
        desp_outras = receita_liquida * self.rng.uniform(0.01, 0.02, size=len(self.datas))
        total_opex  = desp_vendas + desp_adm + desp_outras
        ebitda        = lucro_bruto - total_opex
        depreciacao   = receita_liquida * self.rng.uniform(0.008, 0.015, size=len(self.datas))
        ebit          = ebitda - depreciacao
        resultado_fin = receita_liquida * self.rng.uniform(-0.015, -0.005, size=len(self.datas))
        lair          = ebit + resultado_fin
        ir_csll       = np.where(lair > 0, lair * Settings.ALIQUOTA_IR_CSLL, 0.0)
        lucro_liquido = lair - ir_csll

        return pd.DataFrame({
            "competencia": self.datas.strftime("%Y-%m"),
            "ano": self.datas.year,
            "mes": self.datas.month,
            "receita_bruta":     np.round(receitas_arr, 2),
            "deducoes":          np.round(deducoes, 2),
            "receita_liquida":   np.round(receita_liquida, 2),
            "cmv":               np.round(cmv, 2),
            "lucro_bruto":       np.round(lucro_bruto, 2),
            "desp_vendas":       np.round(desp_vendas, 2),
            "desp_administrativas": np.round(desp_adm, 2),
            "desp_outras":       np.round(desp_outras, 2),
            "total_desp_opex":   np.round(total_opex, 2),
            "ebitda":            np.round(ebitda, 2),
            "depreciacao":       np.round(depreciacao, 2),
            "ebit":              np.round(ebit, 2),
            "resultado_financeiro": np.round(resultado_fin, 2),
            "lair":              np.round(lair, 2),
            "ir_csll":           np.round(ir_csll, 2),
            "lucro_liquido":     np.round(lucro_liquido, 2),
            "margem_bruta_pct":  np.round(lucro_bruto / receita_liquida * 100, 4),
            "margem_ebitda_pct": np.round(ebitda / receita_liquida * 100, 4),
            "margem_liquida_pct": np.round(lucro_liquido / receita_liquida * 100, 4),
        })

    def _gerar_fluxo_caixa(self, dre: pd.DataFrame) -> pd.DataFrame:
        logger.info("Gerando Fluxo de Caixa...")
        n = len(self.datas)
        pct_conversao = self.rng.uniform(0.88, 0.96, size=n)
        recebimentos  = dre["receita_liquida"].values * pct_conversao
        saidas_op     = (dre["cmv"].values + dre["total_desp_opex"].values) * self.rng.uniform(0.95, 1.05, size=n)
        fco           = recebimentos - saidas_op
        capex = np.where(
            self.datas.month.isin([1, 7]),
            self.rng.uniform(80_000, 200_000, size=n),
            self.rng.uniform(10_000, 60_000, size=n),
        )
        financiamento = self.rng.uniform(-120_000, 50_000, size=n)
        variacao_caixa = fco - capex + financiamento
        saldo_final = np.zeros(n)
        saldo_final[0] = Settings.SALDO_INICIAL_CAIXA + variacao_caixa[0]
        for i in range(1, n):
            saldo_final[i] = saldo_final[i - 1] + variacao_caixa[i]

        return pd.DataFrame({
            "competencia":    self.datas.strftime("%Y-%m"),
            "ano":            self.datas.year,
            "mes":            self.datas.month,
            "recebimentos":   np.round(recebimentos, 2),
            "total_saidas":   np.round(saidas_op, 2),
            "fco":            np.round(fco, 2),
            "capex":          np.round(capex, 2),
            "financiamento":  np.round(financiamento, 2),
            "variacao_caixa": np.round(variacao_caixa, 2),
            "saldo_final":    np.round(saldo_final, 2),
        })

    def _gerar_centro_custos(self) -> pd.DataFrame:
        logger.info("Gerando Centro de Custos...")
        registros: list[dict] = []
        for data in self.datas:
            mes_idx = data.month - 1
            fator_ano = 1.06 if data.year == 2024 else 1.0
            sazonalidade = float(_SAZONALIDADE[mes_idx])
            for depto, categorias in _DEPARTAMENTOS.items():
                for categoria in categorias:
                    valor_base = self.rng.uniform(15_000, 80_000)
                    fator_outlier = self.rng.uniform(2.0, 3.5) if self.rng.random() < 0.08 else 1.0
                    valor = valor_base * sazonalidade * fator_ano * fator_outlier
                    registros.append({
                        "competencia":  data.strftime("%Y-%m"),
                        "ano":          data.year,
                        "mes":          data.month,
                        "departamento": depto,
                        "categoria":    categoria,
                        "valor":        round(valor, 2),
                        "variacao_pct": round((fator_outlier - 1.0) * 100, 2),
                        "is_outlier":   fator_outlier > 1.0,
                    })
        return pd.DataFrame(registros)

    def _gerar_contas_receber(self) -> pd.DataFrame:
        logger.info("Gerando Contas a Receber...")
        n_clientes = 60
        clientes = [
            {
                "cod_cliente": f"CLI-{i+1:04d}",
                "cliente":     f"Cliente {i+1:04d}",
                "setor":       self.rng.choice(_SETORES),
                "porte":       self.rng.choice(_PORTES, p=[0.50, 0.35, 0.15]),
            }
            for i in range(n_clientes)
        ]
        registros: list[dict] = []
        for data in self.datas:
            n_ativos = int(self.rng.integers(8, 16))
            clientes_mes = self.rng.choice(clientes, size=n_ativos, replace=False)
            for cliente in clientes_mes:
                porte = cliente["porte"]
                faixa_aging = self.rng.choice(_FAIXAS_AGING, p=_PESOS_AGING)
                valor_ranges = {"Pequeno": (5_000, 80_000), "Médio": (80_000, 400_000), "Grande": (400_000, 1_200_000)}
                lo, hi = valor_ranges[porte]
                valor = round(float(self.rng.uniform(lo, hi)), 2)
                prob = _PROB_INADIMPLENCIA[porte]
                inadimplente = int(faixa_aging != "A vencer" and bool(self.rng.random() < prob))
                registros.append({
                    "competencia": data.strftime("%Y-%m"),
                    "ano": data.year, "mes": data.month,
                    **cliente,
                    "faixa_aging": faixa_aging,
                    "valor": valor,
                    "inadimplente": inadimplente,
                })
        return pd.DataFrame(registros)

    def gerar_todos(self, salvar: bool = True) -> dict[str, pd.DataFrame]:
        logger.info("Iniciando geração de dados — seed=%d", Settings.SEED)
        dre            = self._gerar_dre()
        fluxo_caixa    = self._gerar_fluxo_caixa(dre)
        centro_custos  = self._gerar_centro_custos()
        contas_receber = self._gerar_contas_receber()
        dataframes = {
            "dre": dre, "fluxo_caixa": fluxo_caixa,
            "centro_custos": centro_custos, "contas_receber": contas_receber,
        }
        if salvar:
            for nome, df in dataframes.items():
                destino = self.output_dir / f"{nome}.csv"
                df.to_csv(destino, index=False, encoding="utf-8")
                logger.info("  ✓ %s → %s (%d linhas)", nome, destino, len(df))
        logger.info("Geração concluída.")
        return dataframes


def main() -> None:
    FinancialDataGenerator().gerar_todos(salvar=True)


if __name__ == "__main__":
    main()
