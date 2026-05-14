# Financial Performance Dashboard
### Energética Miramar Distribuidora Ltda. · Jan/2023 – Dez/2024

> Projeto de portfólio de Business Intelligence financeiro com dados sintéticos,
> pipeline end-to-end e dashboard interativo em Streamlit.

---

## O Problema

Toda virada de mês, o time financeiro de uma distribuidora de energia repete o mesmo ritual: exporta dados de sistemas diferentes, consolida planilhas separadas de DRE, fluxo de caixa e inadimplência, formata o relatório — e quando entrega para a diretoria, as informações já estão desatualizadas. Quando um custo fora do padrão aparece no departamento de Operações, a equipe só descobre no fechamento seguinte. Decisões estratégicas são tomadas no achismo, sem visibilidade integrada do que está acontecendo agora.

**Este projeto resolve esse problema:** um pipeline end-to-end que vai da geração dos dados até um dashboard executivo interativo, com exportação de relatório em PDF e Excel — tudo em um único lugar, sem consolidação manual.

---

## Visão Geral

Este projeto simula o ambiente analítico de uma distribuidora de energia elétrica,
cobrindo desde a geração de dados até a entrega de um dashboard executivo e um
relatório executivo exportável em PDF e Excel.
O objetivo é demonstrar boas práticas de engenharia de dados e análise financeira
em um contexto de negócio realista.

**Stack principal:** Python 3.10+ · Pandas · NumPy · Plotly · Streamlit · Matplotlib · Seaborn · ReportLab · OpenPyXL · pytest

---

## Demonstração

O dashboard é dividido em quatro visões analíticas:

| Página | Conteúdo |
|---|---|
| ⚡ Visão Executiva | KPIs do período, Score de Saúde Financeira, Receita vs EBITDA, YoY |
| 📊 DRE | Margens, composição de despesas OPEX, tabela mensal completa |
| 💰 Fluxo de Caixa | FCO, saldo acumulado, média móvel 3M, conversão de receita |
| 🔍 Custos & Inadimplência | Z-score por departamento, outliers, aging da carteira |

Todos os filtros de período operam sobre competências únicas (`AAAA-MM`),
eliminando ambiguidade entre meses de anos diferentes.

---

## Arquitetura do Projeto

```
financial-bi-portfolio/
│
├── .streamlit/                 ← Configuração de tema e servidor do Streamlit
│   └── config.toml             ← Tema, headless e telemetria
│
├── config/                     ← Configurações centralizadas
│   ├── settings.py             ← Caminhos, constantes de negócio e parâmetros
│   └── theme.py                ← Design system: cores e tipografia (dataclass)
│
├── src/                        ← Código-fonte principal (sem dependência do Streamlit)
│   ├── data/
│   │   ├── generator.py        ← Geração de dados sintéticos (FinancialDataGenerator)
│   │   └── loader.py           ← Carregamento e validação de schema (DataLoader)
│   ├── analysis/
│   │   ├── kpis.py             ← Funções puras de cálculo de KPIs e métricas
│   │   └── outliers.py         ← Detecção de outliers via Z-score (scipy)
│   └── visualization/
│       └── charts.py           ← Funções de gráfico Plotly reutilizáveis
│
├── dashboard/                  ← Interface Streamlit (usa src/, não recalcula)
│   ├── app.py                  ← Ponto de entrada: config, cache, navegação
│   └── pages/
│       ├── p1_visao_executiva.py
│       ├── p2_dre.py
│       ├── p3_fluxo_caixa.py
│       └── p4_centro_custos.py
│
├── sql/
│   └── queries.sql             ← 14 queries em 5 blocos analíticos (SQLite/DuckDB)
│
├── notebooks/
│   └── eda_financeiro.py       ← EDA com storytelling em 3 atos — gera PDF + Excel
│
├── tests/                      ← 83 testes automatizados com pytest
│   ├── test_generator.py       ← Shape, reprodutibilidade, regras de negócio
│   ├── test_loader.py          ← Carregamento, schema, exceções customizadas
│   └── test_kpis.py            ← Funções puras, fixtures, parametrize
│
├── data/raw/                   ← CSVs gerados (ignorados pelo Git)
├── exports/prints/             ← Saídas da EDA: PDF e Excel (ignorados pelo Git)
├── requirements.txt            ← Dependências de produção (versões fixadas)
├── requirements-dev.txt        ← Dependências de desenvolvimento (pytest, mypy)
├── pyproject.toml              ← Configuração do pytest e mypy
├── README.md                   ← Documentação do projeto
├── conftest.py                 ← Garante a raiz no sys.path para pytest e Streamlit
└── CONTRIBUTING.md             ← Padrões de código do projeto
```

---

## Instalação e Execução

### 1. Clone o repositório

```bash
git clone https://github.com/Gary-Rainer-Chumacero-Vanderlei/financial-bi-portfolio.git
cd financial-bi-portfolio
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Gere os dados sintéticos

```bash
python -m src.data.generator
```

Isso cria os quatro CSVs em `data/raw/`:
- `dre.csv` — 24 linhas (Jan/2023–Dez/2024)
- `fluxo_caixa.csv` — 24 linhas
- `centro_custos.csv` — ~384 linhas
- `contas_receber.csv` — ~260 linhas

> Os CSVs são ignorados pelo Git (`.gitignore`). Qualquer pessoa que clone
> o repositório recria os mesmos dados executando este comando — seed fixo
> garante reprodutibilidade.

### 5. Execute o dashboard

```bash
streamlit run app.py
```

O dashboard detecta automaticamente se os dados existem. Caso não existam,
exibe um botão para gerá-los sem precisar usar a linha de comando.

### 6. Execute a Análise Exploratória (EDA)

```bash
python -m notebooks.eda_financeiro
```

Gera dois arquivos em `exports/prints/`:
- `relatorio_financeiro.pdf` — Relatório executivo completo (ABNT NBR 14724:2011)
- `relatorio_financeiro.xlsx` — Workbook com 5 abas analíticas

---

## Análise Exploratória — `eda_financeiro.py`

A EDA segue uma **estrutura narrativa em 3 atos** para guiar a leitura dos dados:

**Ato 1 — Panorama**
- **G1** Receita Líquida mensal com média móvel de 3 meses e EBITDA com margem (%)
- **G2** Sazonalidade: índice mensal médio (base 100) e comparativo YoY (2023 vs 2024)
- **G3** Evolução das três margens operacionais — Bruta, EBITDA e Líquida — com meta de 20%

**Ato 2 — Diagnóstico**
- **G4** Heatmap de custos mensais por departamento (R$ Mil, anotado)
- **G5** Detecção de outliers via Z-score por departamento (|Z| > 2)
- **G6** Taxa de inadimplência mensal (área + linha) e donut de aging da última competência
- **G7** FCO mensal (barras coloridas positivo/negativo) + saldo final acumulado (eixo duplo)

**Ato 3 — Síntese**
- **G8** Waterfall DRE (Receita Bruta → Lucro Líquido)
- **G9** Score de Saúde Financeira mensal com faixas Saudável (≥ 70) e Atenção (≥ 50)

### Relatório PDF

Gerado com **ReportLab**, seguindo as margens da ABNT NBR 14724:2011 (Superior 3 cm, Inferior 2 cm, Esquerda 3 cm, Direita 2 cm). Corpo em Helvetica 12 pt com entrelinha 1,5; captions em 10 pt. A capa tem fundo escuro com links clicáveis para LinkedIn e GitHub; o corpo do relatório é em fundo branco para máxima legibilidade e impressão.

### Workbook Excel

Gerado com **OpenPyXL** e organizado em 5 abas com formatação condicional e totalizadores:

| Aba | Conteúdo |
|---|---|
| 📋 Resumo | KPIs consolidados do período |
| 📊 DRE | DRE mensal completa com formatação condicional na Margem EBITDA % |
| 💰 Fluxo de Caixa | FCO com coloração verde/vermelho por sinal |
| 🏢 Centro de Custos | Lançamentos com flag de outlier destacada |
| 📥 Contas a Receber | Aging e inadimplência com flag visual |

---

## Testes

```bash
# Instala dependências de desenvolvimento
pip install -r requirements-dev.txt

# Executa todos os 83 testes
pytest

# Com relatório de cobertura de linhas
pytest --cov=src --cov-report=term-missing

# Apenas um módulo
pytest tests/test_kpis.py -v
```

**Resultado esperado:** `83 passed in < 2s`

---

## Datasets Sintéticos

Os dados são gerados por `FinancialDataGenerator` com as seguintes características:

### DRE — Demonstração de Resultado

| Parâmetro | Valor |
|---|---|
| Receita base mensal | R$ 4.800.000 |
| Crescimento anual (2024) | +8% sobre 2023 |
| Sazonalidade | Função trigonométrica `sin()` — pico em meses de alta demanda |
| Ruído estocástico | Normal(μ=1,0, σ=0,05) por mês |
| CMV / Receita Líquida | 55% – 62% |
| Margem EBITDA típica | 27% – 35% |
| Alíquota IR/CSLL | 34% sobre LAIR positivo |

### Fluxo de Caixa

| Parâmetro | Valor |
|---|---|
| Saldo inicial (Jan/2023) | R$ 1.200.000 |
| Conversão receita → recebimentos | 88% – 96% por mês |
| CAPEX elevado | Janeiro e Julho (picos de investimento) |

### Centro de Custos

| Parâmetro | Valor |
|---|---|
| Departamentos | Comercial, Operações, Administrativo, Financeiro |
| Outliers intencionais | ~8% de probabilidade por lançamento (2× a 3,5× o valor base) |
| Detecção | Z-score com `scipy.stats.zscore(ddof=1)` — algoritmo de Welford |

### Contas a Receber

| Parâmetro | Valor |
|---|---|
| Pool de clientes | 60 empresas fictícias |
| Ativos por mês | 8 a 15 clientes |
| Probabilidade de inadimplência | Pequeno: 25% · Médio: 12% · Grande: 5% |
| Regra de negócio | Títulos "A vencer" nunca são marcados como inadimplentes |

---

## Queries SQL

O arquivo `sql/queries.sql` contém 14 queries organizadas em 5 blocos,
compatíveis com SQLite, DuckDB e PostgreSQL (com ajustes mínimos):

| Bloco | Conteúdo |
|---|---|
| 1 — Visão Executiva | DRE resumida, YTD acumulado, comparativo YoY, totais anuais |
| 2 — Custos e Despesas | Ranking por departamento, evolução mensal, top 10 categorias, outliers |
| 3 — Fluxo de Caixa | Evolução com saldo, FCO acumulado, média móvel, conversão |
| 4 — Inadimplência | Aging consolidado, taxa mensal, ranking de clientes, por setor |
| 5 — Visão Integrada | Painel executivo com JOIN entre DRE, Caixa e Inadimplência + Score |

> **Nota técnica:** a detecção de outliers (Bloco 2) usa `SQRT(AVG(x²) - AVG(x)²)`
> no SQL por compatibilidade com SQLite. Em Python, usamos `scipy.stats.zscore`
> com o algoritmo de Welford, que é numericamente mais estável para valores
> financeiros de grande magnitude.

---

## Boas Práticas Aplicadas

### Separação de responsabilidades
`src/` não importa Streamlit — pode ser usado em qualquer contexto
(EDA, API, scripts, notebooks). O dashboard em `dashboard/` consome
`src/` sem recalcular nada.

### Funções puras e testáveis
Todas as funções de `kpis.py` recebem dados como argumento e retornam
resultados — sem estado global, sem efeitos colaterais. Isso as torna
testáveis com valores simples e reutilizáveis em qualquer contexto.

### Validação de schema
`DataLoader` valida as colunas de cada CSV antes de usá-los. Erros
aparecem no momento do carregamento com mensagem clara — não no meio
de um cálculo de KPI.

### Exceções customizadas
`DataNotFoundError` e `SchemaValidationError` permitem que o dashboard
capture erros específicos e exiba mensagens acionáveis ao usuário.

### Cache com TTL
`@st.cache_data(ttl=3600)` evita recarregar os CSVs a cada interação.
O TTL de 1 hora garante que o cache expira — sem necessidade de reiniciar
o servidor para atualizar os dados.

### Reprodutibilidade
`np.random.default_rng(seed=42)` em vez de `np.random.seed()` global.
O gerador é isolado dentro da classe — não afeta nem é afetado por
outros módulos que usem numpy.random.

### Resolução de sys.path
`conftest.py` na raiz do projeto garante que a raiz esteja sempre no `sys.path`,
independente de onde o processo é iniciado. Quando o Streamlit executa
`dashboard/app.py`, ele adiciona apenas a pasta `dashboard/` ao path — sem
este arquivo, `from src.data.loader import ...` falharia com `ModuleNotFoundError`.
O arquivo é carregado automaticamente pelo pytest e pode ser importado por outros
módulos para obter o mesmo efeito.

---

## Tecnologias e Versões

| Biblioteca | Versão | Uso |
|---|---|---|
| Python | 3.10+ | Linguagem principal |
| Streamlit | 1.32.0 | Dashboard interativo |
| Plotly | 5.20.0 | Gráficos interativos |
| Pandas | 2.1.4 | Manipulação de dados |
| NumPy | 1.26.4 | Geração de dados e vetorização |
| SciPy | latest | Z-score (algoritmo de Welford) |
| Matplotlib | 3.8.3 | Gráficos estáticos na EDA |
| Seaborn | 0.13.2 | Estilo e heatmaps na EDA |
| ReportLab | latest | Geração do relatório em PDF (ABNT) |
| OpenPyXL | latest | Geração do workbook Excel |
| pytest | 8.1.1 | Testes automatizados |
| mypy | 1.9.0 | Verificação de tipos |

---

## Estrutura de Testes

```
83 testes · 3 arquivos · < 2 segundos

test_generator.py  (28 testes)
  ├── Reprodutibilidade e seed
  ├── Shape e colunas dos 4 datasets
  ├── Regras de negócio (inadimplência só em vencidos, etc.)
  └── Valores dentro de intervalos plausíveis

test_loader.py  (17 testes)
  ├── Carregamento correto dos 4 datasets
  ├── DataNotFoundError com mensagem acionável
  ├── SchemaValidationError com colunas listadas
  └── verificar_disponibilidade() sem exceções

test_kpis.py  (38 testes)
  ├── Funções escalares: margem, YoY, score, formatar_brl
  ├── Casos de borda: divisão por zero, score máximo/mínimo
  ├── @pytest.mark.parametrize nos limiares de classificação
  └── DataFrames: enriquecer_dre, kpis_executivos, comparativo YoY
```

---

## Autor

Desenvolvido como projeto de portfólio em Análise de Dados / Business Intelligence.

Contato: [LinkedIn](https://www.linkedin.com/in/garyrainercv/) · [GitHub](https://github.com/gary-rainer-chumacero-vanderlei)