"""
Modelos de Dados do Sistema de Reserva - SINT-IFESGO

Este módulo contém todas as definições de modelos SQLAlchemy para o banco de dados
do sistema de reserva de churrasqueira do SINT-IFESGO. 

Modelos implementados:
1. Associado - Dados dos membros do sindicato
2. Reserva - Reservas de churrasqueira
3. Taxa - Sistema de cobrança de taxas
4. Boletim - Sistema de comunicados

Relacionamentos:
- Associado -> Reservas (1:N)
- Associado -> Taxas (1:N) 
- Reserva -> Taxas (1:N)
- Boletim (independente)

Regras de negócio implementadas:
- Validação de CPF brasileiro
- Controle de adimplência sindical
- Gestão de status de reservas
- Sistema de cobrança de taxas

Autor: Sistema SINT-IFESGO
Versão: 1.0
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time
from decimal import Decimal
import re

# Instância global do SQLAlchemy para uso em toda a aplicação
db = SQLAlchemy()

class Reserva(db.Model):
    """
    Modelo de dados para reservas de churrasqueira.
    
    Representa uma reserva feita por um associado do SINT-IFESGO,
    incluindo todas as informações necessárias para controle
    de horários, pagamentos e status da reserva.
    
    Attributes:
        id (int): Identificador único da reserva
        nome (str): Nome do responsável pela reserva
        email (str): Email para contato (opcional)
        telefone (str): Telefone para contato (opcional)
        cpf_associado (str): CPF do associado (chave estrangeira)
        data_reserva (date): Data da reserva
        horario_inicio (time): Horário de início da reserva
        horario_fim (time): Horário de término da reserva
        numero_convidados (int): Número de pessoas no evento
        status (str): Status atual da reserva (pendente, ativa, cancelada, paga)
        data_criacao (datetime): Timestamp de criação da reserva
        observacoes (str): Observações adicionais (opcional)
    
    Status possíveis:
        - 'pendente': Reserva criada, aguardando pagamento
        - 'paga': Pagamento confirmado, reserva ativa
        - 'ativa': Reserva confirmada e ativa
        - 'cancelada': Reserva cancelada pelo usuário ou sistema
        - 'realizada': Evento já ocorreu
        - 'vencida': Prazo de pagamento expirado
    """
    
    __tablename__ = 'reservas'
    
    # Campos principais da reserva
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, comment='Nome do responsável pela reserva')
    email = db.Column(db.String(100), nullable=True, comment='Email para contato')
    telefone = db.Column(db.String(20), nullable=True, comment='Telefone para contato')
    
    # Relacionamento com associado (obrigatório para SINT-IFESGO)
    cpf_associado = db.Column(db.String(11), db.ForeignKey('associados.cpf'), nullable=True, 
                             comment='CPF do associado responsável')
    
    # Dados temporais da reserva
    data_reserva = db.Column(db.Date, nullable=False, comment='Data da reserva')
    horario_inicio = db.Column(db.Time, nullable=False, comment='Horário de início')
    horario_fim = db.Column(db.Time, nullable=False, comment='Horário de término')
    
    # Informações do evento
    numero_convidados = db.Column(db.Integer, default=1, comment='Número de convidados')
    
    # Controle de status e auditoria
    status = db.Column(db.String(20), default='pendente', 
                      comment='Status: pendente, ativa, cancelada, paga, realizada, vencida')
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, 
                            comment='Timestamp de criação')
    observacoes = db.Column(db.Text, nullable=True, comment='Observações adicionais')
    
    # Relacionamentos
    taxas = db.relationship('Taxa', backref='reserva_obj', lazy=True)
    
    def __repr__(self):
        return f'<Reserva {self.nome} em {self.data_reserva} das {self.horario_inicio} às {self.horario_fim}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'data_reserva': self.data_reserva.strftime('%d/%m/%Y'),
            'data_reserva_iso': self.data_reserva.strftime('%Y-%m-%d'),
            'horario_inicio': self.horario_inicio.strftime('%H:%M'),
            'horario_fim': self.horario_fim.strftime('%H:%M'),
            'numero_convidados': self.numero_convidados,
            'status': self.status,
            'status_display': 'Ativa' if self.status == 'ativa' else 'Cancelada',
            'data_criacao': self.data_criacao.strftime('%d/%m/%Y %H:%M'),
            'observacoes': self.observacoes or ''
        }
    
    @classmethod
    def verificar_disponibilidade(cls, data_reserva, horario_inicio, horario_fim, excluir_id=None):
        """
        Verifica se há conflito de horários para uma data específica
        """
        query = cls.query.filter(
            cls.data_reserva == data_reserva,
            cls.status == 'ativa'
        )
        
        if excluir_id:
            query = query.filter(cls.id != excluir_id)
        
        reservas_existentes = query.all()
        
        for reserva in reservas_existentes:
            # Verifica sobreposição de horários
            if (horario_inicio < reserva.horario_fim and horario_fim > reserva.horario_inicio):
                return False, f"Conflito com reserva existente: {reserva.horario_inicio.strftime('%H:%M')} - {reserva.horario_fim.strftime('%H:%M')} ({reserva.nome})"
        
        return True, "Horário disponível"
    
    @classmethod
    def obter_horarios_ocupados(cls, data_reserva):
        """
        Retorna lista de horários ocupados para uma data
        """
        reservas = cls.query.filter(
            cls.data_reserva == data_reserva,
            cls.status == 'ativa'
        ).all()
        
        horarios_ocupados = []
        for reserva in reservas:
            horarios_ocupados.append({
                'inicio': reserva.horario_inicio.strftime('%H:%M'),
                'fim': reserva.horario_fim.strftime('%H:%M'),
                'nome': reserva.nome
            })
        
        return horarios_ocupados
    
    def cancelar_reserva(self, motivo=None):
        """
        Cancela a reserva
        """
        self.status = 'cancelada'
        if motivo:
            self.observacoes = (self.observacoes or '') + f"\nCancelada: {motivo}"
        return True
    
    def pode_ser_cancelada(self):
        """
        Verifica se a reserva pode ser cancelada (pelo menos 24h de antecedência)
        """
        if self.status != 'ativa':
            return False, "Reserva já foi cancelada"
        
        agora = datetime.now()
        data_hora_reserva = datetime.combine(self.data_reserva, self.horario_inicio)
        
        if data_hora_reserva <= agora:
            return False, "Não é possível cancelar reservas que já começaram"
        
        diferenca = data_hora_reserva - agora
        if diferenca.total_seconds() < 24 * 3600:  # 24 horas
            return False, "Cancelamento deve ser feito com pelo menos 24h de antecedência"
        
        return True, "Reserva pode ser cancelada"


class Associado(db.Model):
    """Modelo para Associados do SINT-IFESGO"""
    __tablename__ = 'associados'
    
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(11), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    telefone = db.Column(db.String(20), nullable=True)
    status_adimplencia = db.Column(db.String(20), default='adimplente')  # adimplente, inadimplente
    data_ultimo_pagamento = db.Column(db.Date, nullable=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    reservas = db.relationship('Reserva', backref='associado_obj', lazy=True, foreign_keys='Reserva.cpf_associado')
    taxas = db.relationship('Taxa', backref='associado_obj', lazy=True, foreign_keys='Taxa.associado_cpf')
    
    def __repr__(self):
        return f'<Associado {self.nome} - CPF: {self.cpf_formatado}>'
    
    @property
    def cpf_formatado(self):
        """Retorna CPF formatado"""
        cpf = self.cpf
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    def is_adimplente(self):
        """Verifica se o associado está adimplente"""
        return self.status_adimplencia == 'adimplente' and self.ativo
    
    def pode_fazer_reserva(self):
        """Verifica se o associado pode fazer reserva"""
        if not self.ativo:
            return False, "Associado inativo no sistema"
        
        if not self.is_adimplente():
            return False, "Associado inadimplente com taxa sindical. Regularize sua situação para fazer reservas."
        
        return True, "Associado pode fazer reserva"
    
    @staticmethod
    def validar_cpf(cpf: str):
        """Valida CPF usando algoritmo oficial"""
        cpf = re.sub(r'[^\d]', '', cpf)
        
        if len(cpf) != 11:
            return False, "CPF deve ter 11 dígitos"
        
        # CPFs inválidos conhecidos
        if cpf in ['00000000000', '11111111111', '22222222222', 
                   '33333333333', '44444444444', '55555555555',
                   '66666666666', '77777777777', '88888888888',
                   '99999999999']:
            return False, "CPF inválido"
        
        # Validação do primeiro dígito
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf[9]) != digito1:
            return False, "CPF inválido"
        
        # Validação do segundo dígito
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        if int(cpf[10]) != digito2:
            return False, "CPF inválido"
        
        return True, "CPF válido"
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'cpf': self.cpf,
            'cpf_formatado': self.cpf_formatado,
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'status_adimplencia': self.status_adimplencia,
            'status_display': 'Adimplente' if self.status_adimplencia == 'adimplente' else 'Inadimplente',
            'data_ultimo_pagamento': self.data_ultimo_pagamento.strftime('%d/%m/%Y') if self.data_ultimo_pagamento else 'Nunca',
            'data_cadastro': self.data_cadastro.strftime('%d/%m/%Y %H:%M') if self.data_cadastro else '',
            'ativo': self.ativo,
            'pode_reservar': self.is_adimplente()
        }


class Taxa(db.Model):
    """Modelo para Taxas de Reserva e outras taxas"""
    __tablename__ = 'taxas'
    
    id = db.Column(db.Integer, primary_key=True)
    valor = db.Column(db.Numeric(10, 2), nullable=False)  # Usando Numeric para decimal
    tipo = db.Column(db.String(20), nullable=False)  # 'reserva', 'sindical', etc.
    status = db.Column(db.String(20), default='pendente')  # pendente, pago, vencido, cancelado
    data_vencimento = db.Column(db.Date, nullable=True)
    data_pagamento = db.Column(db.DateTime, nullable=True)
    reserva_id = db.Column(db.Integer, db.ForeignKey('reservas.id'), nullable=True)
    associado_cpf = db.Column(db.String(11), db.ForeignKey('associados.cpf'), nullable=True)
    codigo_pagamento = db.Column(db.String(50), unique=True, nullable=True)
    observacoes = db.Column(db.Text, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Taxa {self.tipo} - R$ {self.valor} - Status: {self.status}>'
    
    def is_pendente(self):
        """Verifica se a taxa está pendente"""
        return self.status == 'pendente'
    
    def is_paga(self):
        """Verifica se a taxa foi paga"""
        return self.status == 'pago'
    
    def is_vencida(self):
        """Verifica se a taxa está vencida"""
        if self.status == 'vencido':
            return True
        
        if self.status == 'pendente' and self.data_vencimento:
            return date.today() > self.data_vencimento
        
        return False
    
    def valor_formatado(self):
        """Retorna valor formatado em Real"""
        return f"R$ {float(self.valor):.2f}".replace('.', ',')
    
    def gerar_codigo_pagamento(self):
        """Gera código único para pagamento"""
        import uuid
        codigo = str(uuid.uuid4())[:8].upper()
        self.codigo_pagamento = f"SINT{codigo}"
        return self.codigo_pagamento
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'valor': float(self.valor),
            'valor_formatado': self.valor_formatado(),
            'tipo': self.tipo,
            'status': self.status,
            'status_display': self._get_status_display(),
            'data_vencimento': self.data_vencimento.strftime('%d/%m/%Y') if self.data_vencimento else None,
            'data_pagamento': self.data_pagamento.strftime('%d/%m/%Y %H:%M') if self.data_pagamento else None,
            'reserva_id': self.reserva_id,
            'associado_cpf': self.associado_cpf,
            'codigo_pagamento': self.codigo_pagamento,
            'observacoes': self.observacoes or '',
            'data_criacao': self.data_criacao.strftime('%d/%m/%Y %H:%M') if self.data_criacao else '',
            'is_vencida': self.is_vencida()
        }
    
    def _get_status_display(self):
        """Retorna status formatado para exibição"""
        status_map = {
            'pendente': 'Pendente',
            'pago': 'Pago',
            'vencido': 'Vencido',
            'cancelado': 'Cancelado'
        }
        return status_map.get(self.status, self.status.title())


class Boletim(db.Model):
    """Modelo para Boletins Informativos do SINT-IFESGO"""
    __tablename__ = 'boletins'
    
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    tipo = db.Column(db.String(20), default='geral')  # geral, urgente, comunicado, evento
    prioridade = db.Column(db.String(20), default='normal')  # baixa, normal, alta, critica
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_expiracao = db.Column(db.DateTime, nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    autor = db.Column(db.String(100), nullable=True)
    destinatarios = db.Column(db.String(20), default='todos')  # todos, adimplentes, inadimplentes
    
    def __repr__(self):
        return f'<Boletim {self.titulo} - {self.tipo}>'
    
    def is_ativo(self):
        """Verifica se o boletim está ativo"""
        if not self.ativo:
            return False
        
        # Verifica se não expirou
        if self.data_expiracao and datetime.utcnow() > self.data_expiracao:
            return False
        
        return True
    
    def is_urgente(self):
        """Verifica se é boletim urgente"""
        return self.prioridade in ['alta', 'critica'] or self.tipo == 'urgente'
    
    def deve_notificar_associado(self, status_adimplencia: str):
        """Verifica se deve notificar associado baseado no status"""
        if self.destinatarios == 'todos':
            return True
        
        if self.destinatarios == 'adimplentes' and status_adimplencia == 'adimplente':
            return True
        
        if self.destinatarios == 'inadimplentes' and status_adimplencia == 'inadimplente':
            return True
        
        return False
    
    def resumo(self, max_chars: int = 100):
        """Retorna resumo do conteúdo"""
        if len(self.conteudo) <= max_chars:
            return self.conteudo
        
        return self.conteudo[:max_chars] + "..."
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'conteudo': self.conteudo,
            'resumo': self.resumo(),
            'tipo': self.tipo,
            'prioridade': self.prioridade,
            'data_publicacao': self.data_publicacao.strftime('%d/%m/%Y %H:%M') if self.data_publicacao else '',
            'data_expiracao': self.data_expiracao.strftime('%d/%m/%Y %H:%M') if self.data_expiracao else None,
            'ativo': self.ativo,
            'is_ativo': self.is_ativo(),
            'is_urgente': self.is_urgente(),
            'autor': self.autor or 'SINT-IFESGO',
            'destinatarios': self.destinatarios,
            'classe_css': self._get_classe_css()
        }
    
    def _get_classe_css(self):
        """Retorna classe CSS baseada no tipo e prioridade"""
        if self.prioridade == 'critica':
            return 'alert-danger'
        elif self.prioridade == 'alta' or self.tipo == 'urgente':
            return 'alert-warning'
        elif self.tipo == 'evento':
            return 'alert-info'
        else:
            return 'alert-primary'