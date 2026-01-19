# PLANO DE AÇÕES - REVISÃO DO PROJETO

**Data:** 19/01/2026  
**Status:** Pronto para implementação

---

## 🎯 OBJETIVO

Consolidar, refatorar e organizar o Sistema de Reserva de Churrasqueira para melhorar manutenibilidade, performance e qualidade do código.

---

## 📋 AÇÕES PRIORITÁRIAS

### PHASE 1: CONSOLIDAÇÃO IMEDIATA (Sprint 1 - Esta semana)

#### ✅ Ação 1.1: Centralizar Utilitários de CPF
- **Status:** ✅ COMPLETO
- **Arquivo criado:** `app/utils/cpf_utils.py`
- **Próximo passo:** Refatorar referencias em 4 lugares

**Locais a refatorar:**
1. `app.py` linha 172 - Usar `CPFUtils.limpar()`
2. `app/services/webservice_sinsind.py` linha 87 - Usar `CPFUtils.limpar()`
3. `app/routes.py` (múltiplos lugares) - Usar `CPFUtils.limpar()`
4. `app/services/associado_service.py` - Já tem `_limpar_cpf()`, integrar com novo utils

**Estimativa:** 1-2 horas

---

#### ❌ Ação 1.2: Organizar Scripts Soltos

**Problema:** 12 scripts de teste/manutenção desorganizados na raiz

**Solução:**
```
Criar estrutura:
scripts/
├── tests/                    # Scripts de teste antigos (para revisar)
│   ├── test_cpf.py
│   ├── test_reservas.py
│   ├── test_taxa.py
│   └── README.md
├── maintenance/              # Scripts de manutenção
│   ├── add_associado.py
│   ├── check_cpf.py
│   ├── fix_cpf_taxas.py
│   ├── set_admin.py
│   └── README.md
└── deprecated/               # Antigos (para documentar)
    ├── migrate_db.py
    ├── create_db.py
    ├── tabela-senhas.py
    └── update_nome.py
```

**Ações:**
1. [ ] Revisar cada script e documentar seu propósito
2. [ ] Mover para `scripts/` com organização acima
3. [ ] Criar `scripts/README.md` explicando cada um
4. [ ] Atualizar `.gitignore` se necessário

**Estimativa:** 2-3 horas

---

#### ❌ Ação 1.3: Criar Estrutura de Testes Unitários

**Problema:** Testes desorganizados, sem pytest

**Solução:** Estrutura pytest profissional

```
tests/
├── conftest.py               # Fixtures compartilhadas
├── pytest.ini                # Configuração pytest
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_models.py        # Testes de modelos
│   ├── test_services.py      # Testes de services
│   ├── test_validators.py    # Testes de validadores
│   └── test_utils.py         # Testes de utilitários
├── integration/
│   ├── __init__.py
│   ├── test_routes.py        # Testes de rotas
│   └── test_api.py           # Testes de API
└── e2e/
    └── test_user_flows.py    # Testes end-to-end
```

**Arquivos a criar:**
1. `tests/conftest.py` - Fixtures pytest
2. `tests/pytest.ini` - Configuração
3. `tests/unit/test_utils.py` - Testes de CPFUtils
4. `tests/unit/test_models.py` - Testes de models

**Estimativa:** 4-6 horas

---

### PHASE 2: REFATORAÇÃO (Sprint 2 - Próxima semana)

#### ⚠️ Ação 2.1: Dividir routes.py

**Problema:** 1334 linhas, difícil manutenção

**Solução:**
```
app/routes/
├── __init__.py              # Blueprint agregado
├── auth.py                  # Login, logout, recuperação
├── reservas.py              # CRUD de reservas
├── associados.py            # Gestão de associados
├── taxas.py                 # Gestão de taxas
└── api.py                   # Endpoints de API
```

**Mapeamento:**
- **auth.py:** login, logout, esqueci_senha, resetar_senha, reset_senha_post
- **reservas.py:** listar_reservas, criar_reserva, editar_reserva, deletar_reserva, etc
- **associados.py:** listar_associados, criar_associado, editar_associado, etc
- **taxas.py:** listar_taxas, marcar_paga, etc
- **api.py:** api_listar_associados, api_criar_reserva, api_verificar_disponibilidade, etc

**Estimativa:** 3-4 horas

---

#### ⚠️ Ação 2.2: Refatorar to_dict() com Base Class

**Problema:** 4 modelos com `to_dict()` sem padronização

**Solução:** Implementar Serializable base class

```python
# app/models/base.py
from abc import ABC, abstractmethod
from typing import Dict

class Serializable(ABC):
    """Base class para modelos que podem ser serializados"""
    
    @abstractmethod
    def to_dict(self) -> Dict:
        """Converte modelo para dicionário"""
        pass
    
    def to_json(self) -> str:
        """Converte modelo para JSON"""
        import json
        return json.dumps(self.to_dict(), default=str)

# app/models.py
class Reserva(db.Model, Serializable):
    def to_dict(self) -> Dict:
        return { ... }

class Associado(db.Model, Serializable):
    def to_dict(self) -> Dict:
        return { ... }
```

**Estimativa:** 1-2 horas

---

#### 🟡 Ação 2.3: Melhorar Validação de Adimplência

**Problema:** Lógica duplicada em 3+ lugares

**Localidades:**
1. `Associado.is_adimplente()`
2. `Associado.pode_fazer_reserva()`
3. `AssociadoService.verificar_adimplencia()`
4. `webservice_sinsind.verificar_adimplencia()`

**Solução:** Centralizar em `AssociadoService`

```python
class AssociadoService:
    def verificar_adimplencia_completa(self, cpf: str) -> Tuple[bool, str]:
        """
        Verifica adimplência com fallback:
        1. Tenta web service
        2. Fallback para banco local
        """
        # Implementar lógica única aqui
        pass
```

**Estimativa:** 1-2 horas

---

### PHASE 3: TESTES E QUALIDADE (Sprint 3)

#### 📊 Ação 3.1: Escrever Testes Unitários Essenciais

**Cobertura Mínima:**
- [ ] `test_utils.py` - CPFUtils (limpar, formatar, validar)
- [ ] `test_models.py` - Reserva, Associado, Taxa
- [ ] `test_services.py` - AssociadoService, ReservaService
- [ ] `test_validators.py` - ValidadorReserva

**Comando para rodar:**
```bash
pytest tests/ -v --cov=app --cov-report=html
```

**Meta:** Mínimo 50% cobertura

**Estimativa:** 6-8 horas

---

#### 🔍 Ação 3.2: Adicionar Linting e Formatação

**Ferramentas:**
```bash
pip install flake8 black isort pytest-cov
```

**Arquivo: `.flake8`**
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,.venv
```

**Rodar:**
```bash
black app/                  # Formatar
isort app/                  # Organizar imports
flake8 app/                 # Verificar estilo
```

**Estimativa:** 2 horas

---

### PHASE 4: DOCUMENTAÇÃO (Sprint 4)

#### 📚 Ação 4.1: Documentar Banco de Dados

**Criar:** `docs/database_schema.md`

Incluir:
- [ ] ER Diagram (text-based ou image)
- [ ] Descrição de cada tabela
- [ ] Relacionamentos
- [ ] Índices
- [ ] Contraints

**Estimativa:** 2 horas

---

#### 📚 Ação 4.2: Documentar APIs

**Criar:** `docs/api_documentation.md`

Incluir:
- [ ] Endpoints
- [ ] Métodos HTTP
- [ ] Parâmetros
- [ ] Respostas (sucesso e erro)
- [ ] Autenticação

**Estimativa:** 3 horas

---

#### 📚 Ação 4.3: Documentar Arquitetura

**Criar:** `docs/architecture.md`

Incluir:
- [ ] Diagrama de camadas
- [ ] Design patterns utilizados
- [ ] Flow de dados
- [ ] Decisões arquiteturais

**Estimativa:** 2 horas

---

## 📊 TIMELINE ESTIMADA

| Phase | Ações | Duração | Semana |
|-------|-------|---------|--------|
| 1 | 1.1, 1.2, 1.3 | 7-11h | Semana 1 |
| 2 | 2.1, 2.2, 2.3 | 6-8h | Semana 2 |
| 3 | 3.1, 3.2 | 10-12h | Semana 3 |
| 4 | 4.1, 4.2, 4.3 | 7h | Semana 4 |
| **TOTAL** | | **30-38h** | **~1 mês** |

---

## ✅ CHECKLIST DE PRIORIDADES

### CRÍTICAS 🔴 (Fazer em 1-2 semanas)
- [ ] Centralizar CPFUtils (1.1)
- [ ] Organizar scripts (1.2)
- [ ] Estruturar testes (1.3)

### ALTAS 🟠 (Fazer em 2-3 semanas)
- [ ] Dividir routes.py (2.1)
- [ ] Refatorar to_dict() (2.2)
- [ ] Testes unitários (3.1)

### MÉDIAS 🟡 (Fazer em 1 mês)
- [ ] Validação adimplência (2.3)
- [ ] Linting (3.2)
- [ ] Documentação (4.x)

---

## 🎬 PRÓXIMOS PASSOS

**Hoje:**
1. ✅ Criar `app/utils/cpf_utils.py` - FEITO
2. ✅ Revisar arquitetura - FEITO

**Amanhã:**
1. Refatorar app.py para usar CPFUtils.limpar()
2. Refatorar webservice_sinsind.py
3. Começar refatoração de routes.py

**Semana que vem:**
1. Implementar estrutura de testes
2. Escrever testes unitários de CPFUtils
3. Organizar scripts

---

## 📝 NOTAS

- Manter backup do código antes de refatorações grandes
- Testar cada mudança no navegador antes de mergear
- Documentar decisões no commit message
- Revisar código em pares quando possível

---

**Revisão:** 19/01/2026  
**Próxima revisão:** 16/02/2026
