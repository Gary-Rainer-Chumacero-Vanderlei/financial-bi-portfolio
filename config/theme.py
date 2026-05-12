# =============================================================================
# config/theme.py
# Design system centralizado do projeto.
#
# POR QUE ESTE ARQUIVO EXISTE?
# No código original, as cores estavam duplicadas em app.py (dicionário "C")
# e em eda_financeiro.py (dicionário "P"). Qualquer mudança precisava ser
# feita em dois lugares — o que é uma fonte garantida de inconsistência.
#
# Aqui centralizamos tudo: qualquer arquivo do projeto que precisar de uma
# cor ou fonte importa deste módulo.
#
# USO:
#   from config.theme import THEME
#   cor = THEME.blue          # '#4F8EF7'
#   rgba = THEME.to_rgba('blue', 0.5)
# =============================================================================

from dataclasses import dataclass


# -----------------------------------------------------------------------------
# O QUE É UMA DATACLASS?
#
# É uma forma de criar um objeto com campos nomeados e tipados.
# Vantagem sobre dicionário: se você errar o nome do campo (ex: THEME.azul
# em vez de THEME.blue), o Python avisa imediatamente com AttributeError.
# Com dicionário (C["azul"]), o erro só aparece em tempo de execução.
#
# @dataclass é um "decorador" — uma instrução que transforma a classe
# automaticamente, gerando métodos como __init__ e __repr__.
# frozen=True torna o objeto imutável: ninguém pode alterar THEME.blue
# acidentalmente após a criação.
# -----------------------------------------------------------------------------

@dataclass(frozen=True)
class ColorPalette:
    """Paleta de cores do design system do projeto."""

    # Fundos
    bg:      str = "#0F1117"
    surface: str = "#1A1D27"
    border:  str = "#2A2D3E"

    # Texto
    text:  str = "#E8EAF0"
    muted: str = "#6B7490"

    # Cores de destaque
    blue:   str = "#4F8EF7"
    teal:   str = "#34D1BF"
    green:  str = "#2DD4A0"
    amber:  str = "#F5A623"
    coral:  str = "#F26B6B"
    purple: str = "#A78BFA"
    pink:   str = "#F472B6"

    # Cores para escalas sequenciais (heatmaps, gradientes)
    seq_lo: str = "#1E3A5F"
    seq_hi: str = "#4F8EF7"

    def to_rgba(self, color_name: str, alpha: float = 1.0) -> str:
        """
        Converte uma cor da paleta para o formato rgba().

        Args:
            color_name: Nome do atributo de cor (ex: 'blue', 'coral').
            alpha: Transparência entre 0.0 (invisível) e 1.0 (opaco).

        Returns:
            String no formato 'rgba(r, g, b, alpha)'.

        Raises:
            AttributeError: Se color_name não existir na paleta.

        Exemplo:
            THEME.to_rgba('blue', 0.15)  →  'rgba(79, 142, 247, 0.15)'
        """
        hex_color: str = getattr(self, color_name)
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    def as_list(self, *color_names: str) -> list[str]:
        """
        Retorna uma lista de cores da paleta pelo nome.

        Útil para passar sequências de cores para gráficos Plotly.

        Exemplo:
            THEME.as_list('blue', 'teal', 'green')
            → ['#4F8EF7', '#34D1BF', '#2DD4A0']
        """
        return [getattr(self, name) for name in color_names]


@dataclass(frozen=True)
class Typography:
    """Configurações de tipografia do design system."""

    font_mono: str = "'IBM Plex Mono', monospace"
    font_sans: str = "'Space Grotesk', sans-serif"
    font_url:  str = (
        "https://fonts.googleapis.com/css2?"
        "family=IBM+Plex+Mono:wght@300;400;500;600"
        "&family=Space+Grotesk:wght@300;400;500;600;700"
        "&display=swap"
    )


# -----------------------------------------------------------------------------
# INSTÂNCIAS GLOBAIS
#
# Criamos as instâncias aqui para que qualquer arquivo importe diretamente:
#   from config.theme import THEME, TYPOGRAPHY
#
# Não é necessário instanciar em cada arquivo que usar.
# -----------------------------------------------------------------------------

THEME      = ColorPalette()
TYPOGRAPHY = Typography()