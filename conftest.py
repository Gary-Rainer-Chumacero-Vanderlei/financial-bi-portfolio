# conftest.py — raiz do projeto
# Este arquivo é carregado automaticamente pelo pytest E pode ser importado
# por outros módulos para garantir que a raiz do projeto esteja no sys.path.
#
# PROPÓSITO:
# Quando o Streamlit executa dashboard/app.py, ele adiciona apenas a pasta
# 'dashboard/' ao sys.path — não a raiz do projeto. Isso faz com que
# 'from src.data.loader import ...' falhe com ModuleNotFoundError.
#
# A solução é garantir que a raiz do projeto esteja sempre no sys.path,
# independente de onde o script é chamado.

import sys
from pathlib import Path

# Raiz do projeto (onde este arquivo está)
ROOT = Path(__file__).parent.resolve()

# Adiciona a raiz ao início do sys.path se ainda não estiver lá
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
