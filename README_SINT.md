# Sistema de Reserva de Churrasqueira - SINT-IFESGO

Sistema web desenvolvido em Flask para gerenciar reservas de churrasqueira exclusivo para associados do **Sindicato dos Trabalhadores Técnico-Administrativos em Educação das Instituições Federais de Ensino Superior do Estado de Goiás (SINT-IFESGO)**.

## FUNCIONALIDADES PRINCIPAIS

### GESTÃO DE ASSOCIADOS
- Cadastro e validação de CPF
- Verificação de adimplência com taxa sindical
- Controle de acesso baseado em situação sindical

### SISTEMA DE RESERVAS
- Reserva de churrasqueira para associados adimplentes
- Validação de disponibilidade de horários
- Horário de funcionamento: **08:00 às 18:00h**
- Reservas apenas para o dia (não pernoite)

### SISTEMA DE PAGAMENTO
- Taxa de reserva: **R$ 25,00**
- Prazo de 24h para confirmação do pagamento
- Reserva fica pendente até confirmação do pagamento
- Geração automática de código de pagamento

### BOLETIM INFORMATIVO
- Comunicados para associados
- Filtragem por status de adimplência
- Boletins urgentes e normais
- Sistema de prioridades

### VALIDAÇÕES E CONTROLES
- Verificação de adimplência antes da reserva
- Validação de CPF brasileiro
- Controle de conflitos de horários
- Interface responsiva e intuitiva

## COMO USAR

### 1. Instalar dependências:
```bash
pip install -r requirements.txt
```

### 2. Executar o sistema:
```bash
python app.py
```

### 3. Acessar no navegador:
```
http://localhost:5000
```

## ESTRUTURA DO PROJETO

```
├── app.py                  # Aplicação principal
├── config.py              # Configurações específicas do SINT-IFESGO
├── requirements.txt       # Dependências Python
├── README_SINT.md         # Esta documentação
├── app/
│   ├── __init__.py
│   ├── container.py      # Container de dependências
│   ├── models.py         # Modelos: Reserva, Associado, Taxa, Boletim
│   ├── routes.py         # Rotas e endpoints da API
│   ├── entities/         # Entidades de domínio
│   │   ├── associado.py  # Entidade Associado
│   │   ├── reserva.py    # Entidade Reserva
│   │   ├── taxa.py       # Entidade Taxa
│   │   └── boletim.py    # Entidade Boletim
│   ├── services/         # Lógica de negócios
│   │   ├── associado_service.py
│   │   ├── reserva_service.py
│   │   ├── taxa_service.py
│   │   └── boletim_service.py
│   ├── repositories/     # Acesso a dados
│   ├── validators/       # Validações
│   ├── interfaces/       # Interfaces e contratos
│   └── templates/        # Templates HTML atualizados
└── static/              # Arquivos estáticos (CSS, JS)
```

## REGRAS DE NEGÓCIO - SINT-IFESGO

### Horários e Funcionamento
- **Horário:** 08:00 às 18:00h (segunda a domingo)
- **Duração:** 2 a 6 horas por reserva
- **Antecedência:** 1 a 30 dias
- **Capacidade:** até 20 pessoas por evento

### Requisitos para Reserva
- Ser associado do SINT-IFESGO
- Estar **adimplente** com taxa sindical
- Pagar taxa de reserva (R$ 25,00)
- Confirmar pagamento em até 24h

### Processo de Reserva
1. **Validação do CPF** - Sistema verifica se é associado
2. **Verificação de Adimplência** - Confirma situação sindical
3. **Seleção de Data/Horário** - Conforme disponibilidade
4. **Geração da Taxa** - R$ 25,00 com código de pagamento
5. **Confirmação** - Pagamento deve ser confirmado em 24h
6. **Ativação** - Reserva fica ativa após confirmação

### Cancelamentos
- Permitido até **24h** antes do evento
- Taxa não é reembolsada após confirmação
- Reservas não pagas são canceladas automaticamente

## 🔧 Configurações Técnicas

### Banco de Dados
- **SQLite** para desenvolvimento
- **PostgreSQL/MySQL** recomendado para produção
- Migrations automáticas com Flask-SQLAlchemy

### Tecnologias Utilizadas
- **Flask** - Framework web Python
- **SQLAlchemy** - ORM para banco de dados
- **HTML5/CSS3/JavaScript** - Interface do usuário
- **Clean Architecture** - Separação de responsabilidades

### Variáveis de Ambiente
```bash
SECRET_KEY=sua-chave-secreta-aqui
DATABASE_URL=sqlite:///churrasqueira.db  # ou PostgreSQL/MySQL
```

## TIPOS DE USUÁRIO

### Associado
- Fazer reservas (se adimplente)
- Ver suas taxas e pagamentos
- Consultar boletins informativos
- Acompanhar status de reservas

### Administrador
- Gerenciar associados
- Confirmar pagamentos
- Criar boletins informativos
- Relatórios financeiros
- Controle geral do sistema

## FUNCIONALIDADES ADMINISTRATIVAS

### Relatórios
- Relatório financeiro de taxas
- Lista de associados inadimplentes
- Estatísticas de uso da churrasqueira
- Histórico de reservas

### Gestão de Boletins
- Criar comunicados gerais
- Boletins urgentes com prioridade
- Segmentação por status de adimplência
- Controle de validade dos boletins

## SEGURANÇA

- Validação de CPF com algoritmo oficial
- Verificação de adimplência em tempo real
- Controle de acesso por status sindical
- Sanitização de dados de entrada
- Proteção contra conflitos de reserva

## EXEMPLO DE USO

### Para Associado:
1. Acesse o sistema com seu CPF
2. Sistema verifica automaticamente sua adimplência
3. Se adimplente, pode fazer reserva
4. Escolhe data/horário disponível
5. Confirma reserva e recebe código de pagamento
6. Efetua pagamento da taxa (R$ 25,00) em até 24h
7. Sistema confirma pagamento e ativa a reserva

### Para Administrador:
1. Cadastra novos associados
2. Atualiza status de adimplência
3. Confirma pagamentos de taxas
4. Cria boletins informativos
5. Gera relatórios financeiros

## FLUXO DE ESTADOS DA RESERVA

```
[Criada] -> [Pendente Pagamento] -> [Paga/Ativa] -> [Realizada]
    |              |                      |
    v              v                      v
[Cancelada]   [Vencida]              [Cancelada]
```

## SUPORTE

Para dúvidas sobre o sistema, entre em contato com:
- **SINT-IFESGO**: contato@sintifesgo.org.br
- **Telefone**: (62) 3555-0000

---

**SINT-IFESGO** - Sistema desenvolvido especificamente para atender as necessidades dos trabalhadores técnico-administrativos das instituições federais de ensino superior do Estado de Goiás.