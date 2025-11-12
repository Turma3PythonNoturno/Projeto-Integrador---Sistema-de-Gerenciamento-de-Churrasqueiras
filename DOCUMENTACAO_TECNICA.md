# DOCUMENTAÇÃO TÉCNICA - Sistema SINT-IFESGO

## ARQUITETURA DO SISTEMA

### VISÃO GERAL
O Sistema de Reserva de Churrasqueira do SINT-IFESGO (Sindicato dos Trabalhadores Técnico-Administrativos em Educação das Instituições Federais de Ensino Superior do Estado de Goiás) é uma aplicação web desenvolvida em Flask que implementa Clean Architecture para separação clara de responsabilidades.

### TECNOLOGIAS UTILIZADAS

#### Backend
- **Python 3.8+**: Linguagem de programação principal
- **Flask 2.3.3**: Framework web para APIs REST e templates
- **SQLAlchemy 3.1.1**: ORM para mapeamento objeto-relacional
- **SQLite**: Banco de dados para desenvolvimento (PostgreSQL/MySQL para produção)

#### Frontend
- **HTML5**: Estrutura das páginas web
- **CSS3**: Estilização responsiva
- **JavaScript**: Interatividade e validações client-side
- **Bootstrap**: Framework CSS para design responsivo

#### Arquitetura
- **Clean Architecture**: Separação de camadas (Entities, Services, Repositories)
- **Dependency Injection**: Container de dependências para desacoplamento
- **Repository Pattern**: Abstração de acesso a dados
- **Service Layer**: Lógica de negócio centralizada

## ESTRUTURA DE DIRETÓRIOS

```
Sistema de reserva/
├── app.py                      # Ponto de entrada da aplicação
├── config.py                   # Configurações do sistema
├── requirements.txt            # Dependências Python
├── README_SINT.md             # Documentação do usuário
├── DOCUMENTACAO_TECNICA.md    # Esta documentação
├── churrasqueira.db          # Banco SQLite (gerado automaticamente)
├── app/
│   ├── __init__.py           # Inicialização do módulo
│   ├── container.py          # Container de dependências
│   ├── models.py            # Modelos SQLAlchemy
│   ├── routes.py            # Rotas Flask e controllers
│   ├── entities/            # Entidades de domínio (Clean Architecture)
│   │   ├── __init__.py
│   │   ├── associado.py     # Entidade Associado
│   │   ├── reserva.py       # Entidade Reserva
│   │   ├── taxa.py          # Entidade Taxa
│   │   └── boletim.py       # Entidade Boletim
│   ├── services/            # Lógica de negócio (Application Layer)
│   │   ├── __init__.py
│   │   ├── associado_service.py  # Gestão de associados
│   │   ├── reserva_service.py    # Gestão de reservas
│   │   ├── taxa_service.py       # Sistema de cobrança
│   │   └── boletim_service.py    # Sistema de comunicados
│   ├── repositories/        # Acesso a dados (Infrastructure Layer)
│   │   ├── __init__.py
│   │   └── reserva_repository.py # Persistência de reservas
│   ├── validators/          # Validações de negócio
│   │   ├── __init__.py
│   │   └── reserva_validator.py  # Validações de reservas
│   ├── interfaces/          # Contratos e interfaces
│   │   ├── __init__.py
│   │   └── reserva_interfaces.py # Interfaces de reservas
│   └── templates/          # Templates HTML
│       ├── base.html       # Layout base
│       ├── inicio.html     # Página inicial
│       ├── nova_reserva.html    # Formulário de reserva
│       ├── lista_reservas.html  # Lista de reservas
│       └── reservas.html   # Visualização de reservas
└── static/                 # Arquivos estáticos
    ├── css/
    │   └── style.css      # Estilos customizados
    └── js/
        └── main.js        # Scripts JavaScript
```

## MODELOS DE DADOS

### Associado
```python
class Associado:
    cpf: str (PK)           # CPF único do associado
    nome: str               # Nome completo
    email: str              # Email para contato
    telefone: str           # Telefone para contato
    data_filiacao: date     # Data de entrada no sindicato
    situacao_sindical: str  # 'adimplente', 'inadimplente'
    data_criacao: datetime  # Timestamp de criação
```

### Reserva
```python
class Reserva:
    id: int (PK)                    # Identificador único
    nome: str                       # Nome do responsável
    email: str                      # Email para contato
    telefone: str                   # Telefone para contato

    cpf_associado: str (FK)         # Referência para Associado
    data_reserva: date              # Data da reserva
    horario_inicio: time            # Horário de início (08:00-18:00)
    horario_fim: time               # Horário de término
    numero_convidados: int          # Número de pessoas
    status: str                     # Status da reserva
    data_criacao: datetime          # Timestamp de criação
    observacoes: text               # Observações adicionais
```

### Taxa
```python
class Taxa:
    id: int (PK)                # Identificador único
    reserva_id: int (FK)        # Referência para Reserva
    cpf_associado: str (FK)     # Referência para Associado
    valor: decimal              # Valor da taxa (R$ 25,00)
    codigo_pagamento: str       # Código único para pagamento
    status: str                 # 'pendente', 'paga', 'vencida'
    data_geracao: datetime      # Timestamp de geração
    data_vencimento: datetime   # Prazo de 24h para pagamento
    data_pagamento: datetime    # Timestamp de confirmação
    forma_pagamento: str        # PIX, Transferência, Dinheiro
```

### Boletim
```python
class Boletim:
    id: int (PK)                # Identificador único
    titulo: str                 # Título do comunicado
    conteudo: text              # Conteúdo do boletim
    tipo: str                   # 'comunicado', 'urgente', 'informativo'
    prioridade: str             # 'baixa', 'normal', 'alta', 'urgente'
    destinatarios: str          # 'todos', 'adimplentes', 'inadimplentes'
    data_publicacao: datetime   # Timestamp de publicação
    data_expiracao: datetime    # Data de expiração (opcional)
    ativo: bool                 # Se o boletim está ativo
```

## STATUS E FLUXOS DE ESTADOS

### Status de Reservas
```
CRIADA → PENDENTE_PAGAMENTO → PAGA → ATIVA → REALIZADA
   ↓           ↓                ↓      ↓
CANCELADA   VENCIDA         CANCELADA  CANCELADA
```

### Status de Taxas
```
PENDENTE → PAGA
    ↓
  VENCIDA
```

### Status de Associados
```
ADIMPLENTE ⟷ INADIMPLENTE
```

## REGRAS DE NEGÓCIO IMPLEMENTADAS

### 1. HORÁRIO DE FUNCIONAMENTO
- **Período**: 08:00 às 18:00h (todos os dias)
- **Validação**: Sistema bloqueia reservas fora deste horário
- **Implementação**: `config.py` → `HORARIOS_FUNCIONAMENTO`

### 2. SISTEMA DE ADIMPLÊNCIA
- **Verificação obrigatória** antes de cada reserva
- **Bloqueio automático** para inadimplentes
- **Implementação**: `AssociadoService.verificar_adimplencia()`

### 3. TAXA DE RESERVA
- **Valor fixo**: R$ 25,00 por reserva
- **Prazo**: 24 horas para confirmação
- **Geração automática** do código de pagamento
- **Implementação**: `TaxaService.gerar_taxa_reserva()`

### 4. VALIDAÇÃO DE CPF
- **Algoritmo oficial** brasileiro de validação
- **Formato**: Apenas números (11 dígitos)
- **Implementação**: `validar_cpf()` em `models.py`

### 5. CONTROLE DE CONFLITOS
- **Verificação automática** de sobreposição de horários
- **Bloqueio** para reservas conflitantes
- **Implementação**: `ReservaService.verificar_conflito_horario()`

### 6. LIMITES TEMPORAIS
- **Antecedência mínima**: 1 dia
- **Antecedência máxima**: 30 dias
- **Duração mínima**: 2 horas
- **Duração máxima**: 6 horas

## SERVIÇOS PRINCIPAIS

### AssociadoService
**Responsabilidades:**
- Cadastro e atualização de associados
- Validação de CPF
- Controle de adimplência sindical
- Gestão de situação sindical

**Métodos principais:**
```python
def cadastrar_associado(dados) -> Dict
def verificar_adimplencia(cpf) -> Tuple[bool, str]
def atualizar_situacao_sindical(cpf, situacao) -> bool
def buscar_por_cpf(cpf) -> Optional[Associado]
```

### ReservaService
**Responsabilidades:**
- Orquestração completa do processo de reserva
- Aplicação de todas as regras de negócio
- Integração com outros serviços
- Controle de status e lifecycle

**Métodos principais:**
```python
def criar_reserva(dados) -> Dict
def listar_reservas() -> List[Dict]
def cancelar_reserva(reserva_id) -> Dict
def verificar_disponibilidade(data, horarios) -> bool
```

### TaxaService
**Responsabilidades:**
- Geração automática de taxas
- Controle de pagamentos
- Gestão de vencimentos
- Relatórios financeiros

**Métodos principais:**
```python
def gerar_taxa_reserva(reserva_id, cpf_associado) -> Dict
def confirmar_pagamento(codigo_pagamento) -> Dict
def verificar_vencimentos() -> List[Taxa]
def relatorio_financeiro() -> Dict
```

### BoletimService
**Responsabilidades:**
- Criação de comunicados
- Segmentação por status de adimplência
- Controle de prioridades e expiração
- Templates automáticos

**Métodos principais:**
```python
def criar_boletim(dados) -> Dict
def listar_boletins_ativos() -> List[Dict]
def gerar_boletim_automatico(tipo, detalhes) -> Dict
```

## INTERFACES E CONTRATOS

### IReservaRepository
```python
class IReservaRepository:
    def criar(self, reserva: ReservaEntity) -> int
    def buscar_por_id(self, id: int) -> Optional[ReservaEntity]
    def listar_todas(self) -> List[ReservaEntity]
    def atualizar(self, reserva: ReservaEntity) -> bool
    def excluir(self, id: int) -> bool
```

### IValidadorReserva
```python
class IValidadorReserva:
    def validar_dados_reserva(self, dados: Dict) -> Tuple[bool, str]
    def validar_horario_funcionamento(self, horarios: Dict) -> Tuple[bool, str]
    def validar_conflito_horario(self, data: date, horarios: Dict) -> Tuple[bool, str]
```

## CONFIGURAÇÕES DO SISTEMA

### Arquivo config.py
```python
# Horários de funcionamento
HORARIOS_FUNCIONAMENTO = {
    'inicio': '08:00',
    'fim': '18:00',
    'intervalo_minimo': 2
}

# Informações do SINT-IFESGO
ORGANIZACAO = {
    'nome': 'SINT-IFESGO',
    'nome_completo': 'Sindicato dos Trabalhadores...',
    'email_contato': 'contato@sintifesgo.org.br',
    'telefone': '(62) 3555-0000'
}

# Taxa de reserva
TAXA_RESERVA = {
    'valor': 25.00,
    'prazo_pagamento_horas': 24,
    'forma_pagamento': ['PIX', 'Transferência', 'Dinheiro']
}
```

## SEGURANÇA IMPLEMENTADA

### 1. Validação de Entrada
- Sanitização de todos os dados recebidos
- Validação de tipos e formatos
- Proteção contra SQL Injection (SQLAlchemy ORM)

### 2. Controle de Acesso
- Verificação de adimplência em tempo real
- Bloqueio automático para inadimplentes
- Validação de CPF com algoritmo oficial

### 3. Integridade de Dados
- Constraints no banco de dados
- Validações em múltiplas camadas
- Transações atômicas para operações críticas

## TESTES E QUALIDADE

### Tipos de Teste Implementados
- **Testes unitários**: Para validadores e entidades
- **Testes de integração**: Para services e repositories
- **Testes de sistema**: Para fluxos completos

### Métricas de Qualidade
- Cobertura de código: Meta 80%+
- Documentação: 100% dos métodos públicos
- Padrões de código: PEP 8 (Python)

## DEPLOY E PRODUÇÃO

### Ambiente de Desenvolvimento
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python app.py

# Acessar sistema
http://localhost:5000
```

### Ambiente de Produção
**Recomendações:**
- **Servidor web**: Gunicorn + Nginx
- **Banco de dados**: PostgreSQL ou MySQL
- **Variáveis de ambiente**: Para configurações sensíveis
- **HTTPS**: Certificado SSL obrigatório
- **Backup**: Rotina automatizada do banco

### Variáveis de Ambiente
```bash
SECRET_KEY=sua-chave-secreta-super-segura
DATABASE_URL=postgresql://usuario:senha@host:porta/banco
FLASK_ENV=production
```

## MONITORAMENTO E LOGS

### Logs Implementados
- **Criação de reservas**: Log completo com CPF e timestamps
- **Confirmação de pagamentos**: Rastreabilidade financeira
- **Falhas de validação**: Para debugging e auditoria
- **Acesso de inadimplentes**: Para controle sindical

### Métricas Importantes
- Taxa de reservas por mês
- Inadimplência vs. uso do sistema
- Tempo médio de confirmação de pagamento
- Horários de maior demanda

## MANUTENÇÃO E EVOLUÇÃO

### Backlog Técnico
1. **Cache**: Implementar Redis para performance
2. **API REST**: Expor APIs para integração
3. **Mobile**: Desenvolver app mobile nativo
4. **Relatórios**: Dashboard administrativo
5. **Integração**: API bancária para pagamentos

### Melhorias Futuras
1. **Notificações**: SMS/WhatsApp para lembretes
2. **Calendar**: Integração com Google Calendar
3. **QR Code**: Check-in automático na churrasqueira
4. **Analytics**: Dashboard de uso e estatísticas

---

**Sistema SINT-IFESGO v1.0**  
Desenvolvido especificamente para atender as necessidades dos trabalhadores técnico-administrativos das instituições federais de ensino superior do Estado de Goiás.

**Contato Técnico**: Sistema desenvolvido seguindo melhores práticas de Clean Architecture e princípios SOLID.