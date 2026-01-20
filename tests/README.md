# 🧪 Tests - Sistema de Reserva de Churrasqueiras

**Propósito:** Estrutura completa de testes usando pytest com cobertura de código.

---

## 📂 Estrutura

```
tests/
├── __init__.py
├── conftest.py           # Fixtures compartilhadas e configuração pytest
├── pytest.ini            # (na raiz) Configuração pytest
├── unit/                 # Testes unitários (funções/métodos isolados)
│   ├── __init__.py
│   ├── test_cpf_utils.py
│   └── test_associado_model.py
├── integration/          # Testes de integração (componentes interagindo)
│   ├── __init__.py
│   └── test_reserva_flow.py
├── e2e/                  # Testes end-to-end (fluxos completos do usuário)
│   └── __init__.py
└── fixtures/             # Dados de teste e mocks
```

---

## 🚀 Executando os Testes

### Todos os testes
```bash
pytest
```

### Por categoria
```bash
# Apenas testes unitários
pytest tests/unit

# Apenas testes de integração
pytest tests/integration

# Apenas testes E2E
pytest tests/e2e
```

### Por marcador
```bash
# Apenas testes rápidos (não marcados como slow)
pytest -m "not slow"

# Apenas testes de database
pytest -m database

# Apenas testes de API
pytest -m api
```

### Com cobertura
```bash
# Ver cobertura no terminal
pytest --cov=app --cov-report=term-missing

# Gerar relatório HTML
pytest --cov=app --cov-report=html
# Abrir: htmlcov/index.html
```

### Testes específicos
```bash
# Um arquivo específico
pytest tests/unit/test_cpf_utils.py

# Uma classe específica
pytest tests/unit/test_cpf_utils.py::TestCPFUtilsLimpar

# Um teste específico
pytest tests/unit/test_cpf_utils.py::TestCPFUtilsLimpar::test_limpar_cpf_formatado

# Por padrão no nome
pytest -k "cpf"
```

### Modo verboso
```bash
# Ver detalhes de cada teste
pytest -v

# Ver prints e logs
pytest -s

# Ver motivo de skips/xfails
pytest -ra
```

---

## 📋 Fixtures Disponíveis (conftest.py)

### Aplicação e Cliente
- `app` - Aplicação Flask configurada para testes
- `client` - Cliente de teste HTTP
- `runner` - CLI runner para comandos
- `db_session` - Sessão de banco de dados (limpa a cada teste)

### Autenticação
- `login_admin` - Login de administrador
- `login_usuario` - Login de usuário regular
- `authenticated_client` - Cliente autenticado
- `admin_client` - Cliente autenticado como admin

### Modelos
- `associado_adimplente` - Associado em dia com pagamentos
- `associado_inadimplente` - Associado com pendências
- `churrasqueira` - Churrasqueira cadastrada
- `reserva_futura` - Reserva para data futura
- `taxa_pendente` - Taxa não paga

### Dados de Teste
- `sample_cpf` - CPF válido (12345678901)
- `sample_cpf_formatado` - CPF formatado (123.456.789-01)
- `data_hoje` - Data atual
- `data_futura` - Data 7 dias à frente
- `horario_manha` - 08:00
- `horario_tarde` - 14:00

**Uso de fixtures:**
```python
def test_exemplo(associado_adimplente, churrasqueira):
    # Fixtures são injetadas automaticamente
    assert associado_adimplente.is_adimplente() is True
```

---

## 🏷️ Marcadores (Markers)

Organizamos testes com marcadores pytest:

```python
@pytest.mark.unit          # Teste unitário
@pytest.mark.integration   # Teste de integração
@pytest.mark.e2e           # Teste end-to-end
@pytest.mark.slow          # Teste demorado (>1s)
@pytest.mark.database      # Requer banco de dados
@pytest.mark.api           # Chama API externa
@pytest.mark.smoke         # Teste crítico para CI/CD
```

**Executar apenas smoke tests:**
```bash
pytest -m smoke
```

---

## 📊 Cobertura de Código

**Meta:** 80%+ de cobertura

**Status atual:**
```bash
pytest --cov=app --cov-report=term-missing
```

**Arquivos omitidos da cobertura:**
- `*/tests/*` - Próprios testes
- `*/migrations/*` - Migrações de banco
- `*/__pycache__/*` - Cache Python
- `*/venv/*` - Ambiente virtual

---

## ✅ Checklist de Testes

### Unit Tests (Testados)
- ✅ CPFUtils (limpar, formatar, validar)
- ✅ Associado Model (criação, validação, adimplência)
- ⏳ Reserva Model
- ⏳ Taxa Model
- ⏳ LoginSistema Model
- ⏳ Services (AssociadoService, ReservaService, TaxaService)

### Integration Tests (Testados)
- ✅ Fluxo de criação de reserva
- ⏳ Fluxo de pagamento de taxa
- ⏳ Sincronização com API externa
- ⏳ Autenticação e autorização

### E2E Tests (A fazer)
- ⏳ Login → Criar reserva → Pagar taxa
- ⏳ Admin: Gerenciar associados
- ⏳ Admin: Visualizar relatórios

---

## 🔧 Configuração (pytest.ini)

Configurações importantes:

```ini
[pytest]
testpaths = tests              # Buscar testes em tests/
python_files = test_*.py       # Padrão de arquivos
python_classes = Test*         # Padrão de classes
python_functions = test_*      # Padrão de funções

addopts =
    -v                         # Modo verboso
    --cov=app                  # Cobertura do app/
    --cov-report=html          # Relatório HTML
    --cov-report=term-missing  # Mostrar linhas não cobertas
    --maxfail=1                # Parar no primeiro erro
```

---

## 📝 Convenções

### Nomenclatura
- Arquivos: `test_*.py` ou `*_test.py`
- Classes: `Test*` (sem __init__)
- Funções: `test_*`
- Fixtures: nomes descritivos sem prefixo

### Estrutura de Teste
```python
"""
Module docstring explaining what is tested
"""

import pytest
from app.models import Model


class TestModelFeature:
    """Test suite for specific feature"""
    
    def test_should_do_something(self, fixture):
        """Test description in English"""
        # Arrange
        dado = "valor"
        
        # Act
        resultado = funcao(dado)
        
        # Assert
        assert resultado == "esperado"
```

### Assertions
- Use `assert` simples sempre que possível
- Mensagens descritivas quando necessário:
  ```python
  assert resultado == esperado, f"Esperava {esperado}, obteve {resultado}"
  ```

### Parametrização
Use `@pytest.mark.parametrize` para múltiplos casos:
```python
@pytest.mark.parametrize("entrada,esperado", [
    ("123.456.789-01", "12345678901"),
    ("123 456 789 01", "12345678901"),
])
def test_limpar(entrada, esperado):
    assert CPFUtils.limpar(entrada) == esperado
```

---

## 🐛 Debug

### Entrar no debugger
```bash
pytest --pdb  # Parar no erro
pytest --trace  # Parar no início do teste
```

### Ver prints
```bash
pytest -s  # Não capturar stdout/stderr
```

### Último teste que falhou
```bash
pytest --lf  # (last-failed)
```

### Testes mais lentos
```bash
pytest --durations=10  # Mostrar 10 testes mais lentos
```

---

## 📚 Recursos

- **Pytest docs:** https://docs.pytest.org
- **Coverage.py:** https://coverage.readthedocs.io
- **Flask Testing:** https://flask.palletsprojects.com/en/latest/testing/

---

## 🆘 Problemas Comuns

**ImportError: No module named 'app'**
```bash
# Rodar pytest da raiz do projeto
cd /caminho/para/Sistema\ de\ reserva
pytest
```

**Database locked**
```python
# Usar transações em fixtures:
@pytest.fixture
def db_session(app):
    with app.app_context():
        db.session.begin_nested()
        yield db.session
        db.session.rollback()
```

**Fixtures não encontradas**
```bash
# Verificar conftest.py está no lugar certo
# Verificar __init__.py em todas as pastas
```

---

## 🎯 Próximos Passos

1. ✅ Estrutura básica criada
2. ✅ Testes de CPFUtils (100%)
3. ✅ Testes de Associado Model (80%)
4. ⏳ Completar testes de models
5. ⏳ Adicionar testes de services
6. ⏳ Adicionar testes E2E
7. ⏳ Integrar com CI/CD

---

*Última atualização: 20/01/2026*  
*Estruturação: Fase 1 - Ação 3 (Estruturar Testes)*
