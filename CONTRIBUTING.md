# Guia de Contribuição e Padrões de Código
**Projeto:** Financial Performance Dashboard — Energética Miramar Distribuidora Ltda.

Este documento descreve os padrões de código adotados no projeto.
Qualquer contribuição deve seguir estas convenções.

---

## 1. Type Hints

Todo parâmetro de função e todo retorno deve ser anotado com type hints.

```python
# ✅ Correto
def calcular_margem(lucro: float, receita: float) -> float:
    return round(lucro / receita * 100, 2)

# ❌ Evitar
def calcular_margem(lucro, receita):
    return lucro / receita * 100
```

Use `Optional[T]` (ou `T | None` no Python 3.10+) quando o valor pode ser `None`.

```python
from typing import Optional

def buscar_cliente(cod: str) -> Optional[str]:
    ...
```

---

## 2. Docstrings — Padrão Google Style

Toda função pública deve ter docstring. Use o padrão Google Style.

```python
def calcular_score(margem: float, fco: float, inadimplencia: float) -> float:
    """
    Calcula o Score de Saúde Financeira composto (0–100).

    Combina três componentes ponderados: margem EBITDA, FCO positivo
    e taxa de inadimplência. Quanto maior o score, melhor a saúde.

    Args:
        margem: Margem EBITDA percentual do período.
        fco: Fluxo de Caixa Operacional do período (R$).
        inadimplencia: Taxa de inadimplência percentual do período.

    Returns:
        Score entre 0.0 e 100.0 arredondado em uma casa decimal.

    Example:
        >>> calcular_score(margem=18.5, fco=320_000, inadimplencia=4.2)
        82.4
    """
```

---

## 3. Nomenclatura

| Elemento | Convenção | Exemplo |
|---|---|---|
| Variável | `snake_case` | `receita_liquida` |
| Função | `snake_case` com verbo | `calcular_margem()` |
| Constante de módulo | `UPPER_SNAKE_CASE` | `SEED = 42` |
| Classe | `PascalCase` | `DataLoader` |
| Arquivo | `snake_case` | `data_loader.py` |

**Prefixos recomendados para funções:**

| Prefixo | Uso |
|---|---|
| `calcular_` | Cômputo de métricas e KPIs |
| `carregar_` | Leitura de arquivos |
| `gerar_` | Criação de dados ou artefatos |
| `filtrar_` | Seleção de subconjunto de dados |
| `validar_` | Verificação de integridade |
| `formatar_` | Transformação de apresentação |

---

## 4. Responsabilidade Única

Cada função deve fazer **uma coisa só**.
Se a descrição usa "e", considere dividir em duas funções.

```python
# ❌ Evitar — faz três coisas
def processar_dre(caminho):
    df = pd.read_csv(caminho)
    df = df[df["ano"] == 2024]
    df["margem"] = df["lucro"] / df["receita"] * 100
    return df

# ✅ Correto — responsabilidades separadas
def carregar_dre(caminho: Path) -> pd.DataFrame: ...
def filtrar_ano(df: pd.DataFrame, ano: int) -> pd.DataFrame: ...
def adicionar_margem(df: pd.DataFrame) -> pd.DataFrame: ...
```

---

## 5. Tratamento de Erros

Capture erros **específicos** e forneça mensagens úteis.

```python
# ❌ Evitar
try:
    df = pd.read_csv(caminho)
except:
    pass

# ✅ Correto
try:
    df = pd.read_csv(caminho)
except FileNotFoundError:
    raise FileNotFoundError(
        f"Arquivo não encontrado: {caminho}\n"
        "Execute 'python -m src.data.generator' para gerar os dados."
    )
```

---

## 6. Ponto de Entrada com `__main__`

Scripts executáveis devem encapsular a execução em `main()`.

```python
def main() -> None:
    """Ponto de entrada do script."""
    ...

if __name__ == "__main__":
    main()
```

Isso garante que importar o módulo não cause efeitos colaterais.

---

## 7. Constantes vs. Valores Hardcoded

Nunca use valores literais espalhados pelo código.
Defina constantes em `config/settings.py`.

```python
# ❌ Evitar
if score >= 70:
    cor = "#2DD4A0"

# ✅ Correto
from config.settings import Settings
from config.theme import THEME

if score >= Settings.SCORE_FAIXA_SAUDAVEL:
    cor = THEME.green
```

---

## 8. Como Executar os Testes

```bash
# Todos os testes
pytest

# Com relatório de cobertura
pytest --cov=src --cov-report=term-missing

# Um arquivo específico
pytest tests/test_kpis.py -v
```

---

## 9. Verificação de Tipos

```bash
# Verifica type hints em todo o src/
mypy src/

# Verifica um arquivo específico
mypy src/analysis/kpis.py
```
