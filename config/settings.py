# =============================================================================
# config/settings.py
# =============================================================================
from __future__ import annotations
from pathlib import Path
import os


def _find_root() -> Path:
    env = os.environ.get("PROJECT_ROOT")
    if env:
        return Path(env).resolve()
    candidate = Path(__file__).resolve().parent
    for _ in range(5):
        if any((candidate / m).exists() for m in ("src", "data", "requirements.txt")):
            return candidate
        candidate = candidate.parent
    return Path.cwd().resolve()


PROJECT_ROOT: Path = _find_root()


class Settings:
    SEED: int = 42
    START_DATE: str = "2023-01-01"
    N_MONTHS: int = 24

    RAW_DATA_DIR: Path = PROJECT_ROOT / "data" / "raw"
    EXPORTS_DIR: Path  = PROJECT_ROOT / "exports" / "prints"

    DRE_CSV:            Path = RAW_DATA_DIR / "dre.csv"
    FLUXO_CAIXA_CSV:    Path = RAW_DATA_DIR / "fluxo_caixa.csv"
    CONTAS_RECEBER_CSV: Path = RAW_DATA_DIR / "contas_receber.csv"
    CENTRO_CUSTOS_CSV:  Path = RAW_DATA_DIR / "centro_custos.csv"

    RECEITA_BASE:        float = 4_800_000.0
    SALDO_INICIAL_CAIXA: float = 1_200_000.0
    ALIQUOTA_IR_CSLL:    float = 0.34

    SCORE_PESO_MARGEM:        int   = 40
    SCORE_PESO_FCO:           int   = 30
    SCORE_PESO_INADIMPLENCIA: int   = 30
    SCORE_META_MARGEM:        float = 25.0
    SCORE_META_INADIMPLENCIA: float = 10.0
    SCORE_FAIXA_SAUDAVEL:     int   = 70
    SCORE_FAIXA_ATENCAO:      int   = 50

    DASHBOARD_TITLE:  str = "Financial BI · Energética Norte"
    DASHBOARD_ICON:   str = "⚡"
    DASHBOARD_LAYOUT: str = "wide"
