# DUPLICIDADES E PROBLEMAS - MAPEAMENTO COMPLETO

**Gerado em:** 19/01/2026  
**Status:** Completo com soluções propostas

---

## 🔴 DUPLICIDADES CRÍTICAS

### D1: Limpeza de CPF em 4 Lugares

#### Localização 1: `app.py` - Linha 172
```python
cpf_limpo = ''.join(filter(str.isdigit, assoc.get('cpf', '')))
```
**Contexto:** Sincronização de associados da API

#### Localização 2: `app/services/webservice_sinsind.py` - Linha 87
```python
cpf_limpo = ''.join(filter(str.isdigit, cpf))
```
**Contexto:** Consulta ao web service

#### Localização 3: `app/routes.py` - Múltiplas linhas
```python
cpf_form.replace('.', '').replace('-', '')  # E variações
```
**Contexto:** Processamento de formulários

#### Localização 4: `app/services/associado_service.py` - Método `_limpar_cpf()`
```python
def _limpar_cpf(self, cpf: str) -> str:
    return ''.join(filter(str.isdigit, cpf))
```
**Contexto:** Serviço de associados

#### ✅ Solução Implementada
Criado `app/utils/cpf_utils.py` com:
- `CPFUtils.limpar()` - Limpeza centralizada
- `CPFUtils.formatar()` - Formatação centralizada
- `CPFUtils.validar()` - Validação algoritmo oficial
- `CPFUtils.eh_valido()` - Verificação simples
- `CPFUtils.sanitizar()` - Limpeza + formatação opcional

---

### D2: Scripts Soltos na Raiz (12 arquivos)

#### Testes Desorganizados
```
❌ test_cpf.py              - Testa CPF (44 linhas)
❌ test_reservas.py         - Testa reservas (? linhas)
❌ test_taxa.py             - Testa taxa (? linhas)
```
**Problema:** Sem estrutura de teste (pytest), sem cobertura

#### Scripts de Manutenção Duplicados
```
❌ add_associado.py         - Duplicado com API
❌ check_cpf.py             - Verificação simples
❌ check_db.py              - Verifica BD
❌ fix_cpf_taxas.py         - Script de manutenção
❌ set_admin.py             - Define admin (duplicado)
❌ update_nome.py           - Atualiza nome (duplicado)
❌ atualizar_bd.py          - Atualiza BD (duplicado)
```
**Problema:** Confusão sobre qual script usar

#### Scripts Obsoletos
```
❌ migrate_db.py            - Antigo/obsoleto
❌ create_db.py             - Duplicado com app.py
❌ tabela-senhas.py         - Obsoleto
```

#### 📋 Solução Proposta
Reorganizar em:
```
scripts/
├── tests/
│   ├── test_cpf.py
│   ├── test_reservas.py
│   ├── test_taxa.py
│   └── README.md
├── maintenance/
│   ├── add_associado.py
│   ├── check_cpf.py
│   ├── fix_cpf_taxas.py
│   ├── set_admin.py
│   └── README.md
└── deprecated/
    ├── migrate_db.py
    ├── create_db.py
    └── README.md
```

---

### D3: Testes Completamente Desorganizados

#### Problema
- ❌ Sem pytest configurado
- ❌ Sem cobertura de testes
- ❌ 0% de cobertura automatizada
- ❌ Scripts misturados entre raiz e `/tests`
- ❌ Sem fixtures compartilhadas
- ❌ Sem CI/CD

#### Testes Existentes
```
tests/
├── test_disponibilidade.py      (72 linhas)
└── run_disponibilidade_check.py (79 linhas)

Raiz/
├── test_cpf.py
├── test_reservas.py
└── test_taxa.py
```

#### 📋 Solução Proposta
```
tests/
├── conftest.py           # Fixtures pytest
├── pytest.ini            # Configuração
├── unit/
│   ├── test_models.py
│   ├── test_services.py
│   ├── test_validators.py
│   └── test_utils.py
├── integration/
│   ├── test_routes.py
│   └── test_api.py
└── e2e/
    └── test_user_flows.py
```

**Comando:**
```bash
pytest tests/ -v --cov=app --cov-report=html
```

---

### D4: Métodos `to_dict()` Duplicados (4 modelos)

#### Localização 1: `Reserva.to_dict()` - Linha 111
```python
def to_dict(self):
    try: 
        return {
            'id': self.id,
            'nome': self.nome or '',
            'email': self.email or '',
            # ... 14 campos
        }
    except Exception as e:
        return { ... }  # Fallback com erro
```

#### Localização 2: `Associado.to_dict()` - Linha 335
```python
def to_dict(self):
    try:
        # Formatação segura das datas
        data_ultimo_pagamento_str = 'Nunca'
        # ... similar structure
    except:
        # Fallback
```

#### Localização 3: `LoginSistema.to_dict()` - Linha 560
```python
def to_dict(self):
    return {
        'cpf': self.cpf,
        'is_admin': self.is_admin(),
        # ... campos
    }
```

#### Localização 4: `TokenRecuperacaoSenha.to_dict()` - (inferido)
Similar pattern

#### 📋 Solução Proposta
```python
# app/models/serializable.py
from abc import ABC, abstractmethod
from typing import Dict

class Serializable(ABC):
    """Base class para modelos serializáveis"""
    
    @abstractmethod
    def to_dict(self) -> Dict:
        """Converte modelo para dicionário"""
        pass
    
    def to_json(self) -> str:
        """Converte para JSON"""
        import json
        return json.dumps(self.to_dict(), default=str)

# Em cada model
class Reserva(db.Model, Serializable):
    def to_dict(self) -> Dict:
        return { ... }
```

---

## 🟠 DUPLICIDADES ALTAS

### D5: Routes.py Muito Grande (1334 linhas)

#### Problema
- ❌ 1334 linhas em um único arquivo
- ❌ Difícil navegação
- ❌ Difícil testes
- ❌ Responsabilidade única violada

#### Rotas por Categoria
```
Autenticação (5 rotas):
  - login (GET/POST)
  - logout
  - esqueci_senha (GET/POST)
  - resetar_senha (GET/POST)
  - reset_senha (método antigo?)

Reservas (15 rotas):
  - listar_reservas
  - criar_reserva
  - editar_reserva
  - deletar_reserva
  - api_* (múltiplos endpoints)

Associados (8 rotas):
  - listar_associados
  - criar_associado
  - editar_associado
  - api_listar_associados
  - api_estatisticas_associados

Taxas (5 rotas):
  - listar_taxas
  - marcar_como_paga
  - api_* (endpoints)

Dashboard (2 rotas):
  - inicio
  - webservice
```

#### 📋 Solução Proposta
```
app/routes/
├── __init__.py          # Blueprint agregado
├── auth.py              # 5 rotas de autenticação
├── reservas.py          # 15 rotas de reservas
├── associados.py        # 8 rotas de associados
├── taxas.py             # 5 rotas de taxas
├── dashboard.py         # 2 rotas de dashboard
└── api.py               # Endpoints de API
```

---

### D6: Validação de Adimplência em 3 Lugares

#### Localização 1: `Associado.is_adimplente()` - Model
```python
def is_adimplente(self):
    return self.inadimplencia != 'SIM' and self.ativo
```

#### Localização 2: `Associado.pode_fazer_reserva()` - Model
```python
def pode_fazer_reserva(self):
    if not self.ativo:
        return False, "..."
    if not self.is_adimplente():
        return False, "Associado inadimplente..."
    return True, "..."
```

#### Localização 3: `AssociadoService.verificar_adimplencia()` - Service
```python
def verificar_adimplencia(self, cpf: str) -> Tuple[bool, str]:
    # Tenta web service
    # Fallback para banco local
```

#### Localização 4: `webservice_sinsind.verificar_adimplencia()` - Web Service
```python
def verificar_adimplencia(self, cpf):
    # Consulta web service externo
```

#### 📋 Solução Proposta
Centralizar em `AssociadoService`:
```python
class AssociadoService:
    def verificar_adimplencia_completa(self, cpf: str) -> Tuple[bool, str]:
        """
        Verifica adimplência com fallback:
        1. Tenta web service (origem autoritativa)
        2. Fallback para banco local
        3. Fallback para modelo em memória
        """
        # Implementar lógica única aqui
        pass
```

---

## 🟡 PROBLEMAS ADICIONAIS

### P1: Routes.py com Lógica Misturada
```
❌ Templates renderizados diretamente em rotas
❌ Lógica de negócio em rotas (deveria estar em services)
❌ Queries SQL diretas em rotas (usar repositories)
```

### P2: Falta de Camada de Validação
```
❌ Validações espalhadas entre routes, models e services
✅ Existe `ValidadorReserva` mas não é usado consistentemente
```

### P3: Tratamento de Erros Inconsistente
```
❌ Alguns try/except muito genéricos
❌ Logging não padronizado
❌ Mensagens de erro para usuário inconsistentes
```

### P4: Banco de Dados
```
⚠️ Coluna `inadimplencia` (SIM/NÃO) é redundante?
⚠️ Campos `nome`, `email`, `telefone` duplicados em Reserva e Associado
⚠️ Falta índice em `Reserva.data_reserva` (query frequente)
```

---

## ✅ CONFIRMAÇÕES

- [x] Análise completa finalizada
- [x] 6 duplicidades identificadas (4 críticas, 2 altas)
- [x] 4 problemas adicionais encontrados
- [x] 12 scripts desorganizados mapeados
- [x] Soluções propostas para cada item
- [x] CPFUtils criado como prova de conceito
- [x] Roadmap com timeline definido
- [x] 5 documentos gerados

---

## 📊 SUMMARY

| Tipo | Qty | Severity |
|------|-----|----------|
| Duplicidades Críticas | 3 | 🔴 |
| Duplicidades Altas | 2 | 🟠 |
| Problemas Adicionais | 4 | 🟡 |
| **TOTAL** | **9** | |

**Todos os problemas têm solução proposta e estão documentados em PLANO_ACOES.md**

---

Fim do mapeamento de duplicidades.
