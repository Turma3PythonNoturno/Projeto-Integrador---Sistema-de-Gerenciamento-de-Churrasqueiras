# 📁 Scripts - Sistema de Reserva de Churrasqueiras

**Propósito:** Scripts auxiliares organizados por categoria para facilitar manutenção e desenvolvimento.

---

## 📂 Estrutura de Diretórios

```
scripts/
├── tests/           # Scripts de teste ad-hoc (antes da implementação de pytest)
├── maintenance/     # Scripts de manutenção e migração do banco de dados
├── utilities/       # Scripts utilitários para operações pontuais
├── deprecated/      # Scripts obsoletos mantidos para referência histórica
└── README.md        # Este arquivo
```

---

## 🧪 tests/

Scripts de teste manuais criados durante o desenvolvimento inicial.

| Script | Descrição | Status |
|--------|-----------|--------|
| `test_cpf.py` | Testa validação e limpeza de CPF | ⚠️ Substituir por pytest |
| `test_reservas.py` | Testa lógica de criação de reservas | ⚠️ Substituir por pytest |
| `test_taxa.py` | Testa cálculo e geração de taxas | ⚠️ Substituir por pytest |

**Uso:**
```bash
cd scripts/tests
python test_cpf.py
```

**Nota:** Estes scripts devem ser substituídos por testes unitários usando pytest (ver `/tests` na raiz).

---

## 🔧 maintenance/

Scripts de manutenção e migração do banco de dados.

| Script | Descrição | Quando Usar |
|--------|-----------|-------------|
| `atualizar_bd.py` | Atualiza schema do banco de dados | Após mudanças no modelo |
| `fix_cpf_taxas.py` | Corrige CPFs em registros de taxas | Limpeza de dados históricos |
| `migrate_db.py` | Migração manual de dados entre versões | Upgrade de versão |

**Uso:**
```bash
cd scripts/maintenance
python atualizar_bd.py
```

**⚠️ CUIDADO:** Sempre faça backup do banco de dados antes de executar scripts de manutenção:
```bash
cp churrasqueira.db churrasqueira.db.backup
```

---

## 🛠️ utilities/

Scripts utilitários para operações pontuais de administração.

| Script | Descrição | Quando Usar |
|--------|-----------|-------------|
| `add_associado.py` | Adiciona associado manualmente ao banco | Cadastro emergencial |
| `set_admin.py` | Define permissões de administrador | Criar/modificar admins |
| `check_cpf.py` | Valida CPF e consulta na API | Verificar dados de associado |
| `check_db.py` | Inspeciona estado atual do banco de dados | Debug e diagnóstico |
| `update_nome.py` | Atualiza nome de associado existente | Correção de dados |

**Uso típico:**
```bash
cd scripts/utilities
python set_admin.py --cpf 12345678901
```

**Nota:** Muitas dessas funcionalidades devem ser integradas à interface web no futuro.

---

## 🗑️ deprecated/

Scripts obsoletos mantidos apenas para referência histórica.

| Script | Descrição | Por que está obsoleto |
|--------|-----------|----------------------|
| `create_db.py` | Criação inicial do banco de dados | Substituído por `app.py` com migrations |
| `tabela-senhas.py` | Geração de senhas para logins | Integrado ao `app.py` |

**⚠️ NÃO USAR:** Estes scripts não devem ser executados. Mantidos apenas para referência.

---

## 🚀 Migração para Pytest

**Status atual:** Scripts de teste ad-hoc  
**Objetivo:** Implementar estrutura completa de testes com pytest

**Plano de migração:**
1. ✅ Organizar scripts existentes (COMPLETO)
2. ⏳ Criar estrutura `/tests` com pytest
3. ⏳ Migrar lógica de `scripts/tests/` para testes unitários
4. ⏳ Adicionar testes de integração
5. ⏳ Configurar CI/CD com GitHub Actions

**Ver:** `PLANO_ACOES.md` na raiz do projeto para timeline completo.

---

## 📝 Convenções

### Nomenclatura
- `test_*.py` - Scripts de teste (mover para pytest)
- `check_*.py` - Scripts de verificação/diagnóstico
- `fix_*.py` - Scripts de correção de dados
- `update_*.py` - Scripts de atualização pontual
- `migrate_*.py` - Scripts de migração de dados

### Estrutura de Script
Todos os scripts devem seguir este template:

```python
"""
Script: nome_do_script.py
Descrição: O que este script faz
Autor: [Nome]
Data: [Data]
Uso: python nome_do_script.py [args]
"""

import sys
import os

# Adicionar raiz do projeto ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app
from app.models import db

def main():
    """Função principal do script"""
    app = create_app()
    with app.app_context():
        # Sua lógica aqui
        pass

if __name__ == '__main__':
    main()
```

---

## 🔒 Segurança

**Importante:**
- ⚠️ Scripts com `--force` ou operações destrutivas requerem confirmação
- ⚠️ Nunca commitar senhas ou tokens em scripts
- ⚠️ Sempre fazer backup antes de scripts de manutenção
- ⚠️ Testar em ambiente de desenvolvimento primeiro

---

## 📚 Recursos

- **Documentação principal:** `/README_SINT.md`
- **Plano de ações:** `/PLANO_ACOES.md`
- **Revisão técnica:** `/REVISAO_PROJETO.md`
- **Documentação técnica:** `/DOCUMENTACAO_TECNICA.md`

---

## 🆘 Precisa de Ajuda?

**Perguntas frequentes:**

**P: Como executar um script?**
```bash
cd scripts/[categoria]
python nome_do_script.py
```

**P: O script não encontra os módulos**
Certifique-se de estar na raiz do projeto ou adicione ao path:
```python
sys.path.insert(0, '../../')
```

**P: Posso deletar scripts/deprecated?**
Sim, mas recomendamos manter por 6 meses após migração completa.

---

*Última atualização: 20/01/2026*  
*Organização: Fase 1 - Ação 2 (Consolidação Imediata)*
