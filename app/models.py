"""
Modelos de Dados do Sistema de Reserva - SINT-IFESGO

Este módulo contém todas as definições de modelos SQLAlchemy para o banco de dados
do sistema de reserva de churrasqueira do SINT-IFESGO. 

Modelos implementados:
1. Associado - Dados dos membros do sindicato
2. Reserva - Reservas de churrasqueira
3. Taxa - Sistema de cobrança de taxas
4. LoginSistema - Sistema de autenticação

Relacionamentos:
- Associado -> Reservas (1:N)
- Associado -> Taxas (1:N) 
- Reserva -> Taxas (1:N)
- LoginSistema -> Associado (1:1)

Regras de negócio implementadas:
- Validação de CPF brasileiro
- Controle de adimplência sindical
- Gestão de status de reservas
- Sistema de cobrança de taxas
- Autenticação de usuários

Autor: Sistema SINT-IFESGO
Versão: 1.0
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time, timezone
from decimal import Decimal
import re
from werkzeug.security import generate_password_hash, check_password_hash

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
    
    churrasqueira_id = db.Column(
        db.Integer,
        db.ForeignKey("churrasqueiras.id"),
        nullable=False,
        comment="Churrasqueira reservada"
    )
    
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
    taxas = db.relationship('Taxa', backref='reserva_obj', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Reserva {self.nome} em {self.data_reserva} das {self.horario_inicio} às {self.horario_fim} da churrasqueira: {self.churrasqueira_id}>'
    
    
    def to_dict(self):
        try: 
            taxa_info = None
            if getattr(self, 'taxas', None):
                taxa_ord = sorted(self.taxas, key=lambda t: t.id or 0, reverse=True)
                if taxa_ord:
                    t = taxa_ord[0]
                    taxa_info = {
                        'id': t.id,
                        'valor': float(t.valor or 0),
                        'status': t.status or '',
                        'vencimento': t.vencimento.strftime('%Y-%m-%d') if getattr(t, 'vencimento', None) else None
                    }

            return {
                'id': self.id,
                'nome': self.nome or '',
                'email': self.email or '',
                'telefone': self.telefone or '',
                'cpf_associado': self.cpf_associado or '',
                'churrasqueira_id': self.churrasqueira_id or '',
                'churrasqueira_nome': getattr(self.churrasqueira, 'nome', '') if hasattr(self, 'churrasqueira') else '',
                'data_reserva': self.data_reserva.strftime('%d/%m/%Y') if self.data_reserva else '',
                'data_reserva_iso': self.data_reserva.strftime('%Y-%m-%d') if self.data_reserva else '',
                'horario_inicio': self.horario_inicio.strftime('%H:%M') if self.horario_inicio else '',
                'horario_fim': self.horario_fim.strftime('%H:%M') if self.horario_fim else '',
                'numero_convidados': self.numero_convidados,
                'status': self.status,
                'status_display': self._get_status_display() if hasattr(self, '_get_status_display') else self.status,
                'data_criacao': self.data_criacao.strftime('%d/%m/%Y %H:%M') if self.data_criacao else '',
                'observacoes': self.observacoes or '',
                'taxa': taxa_info
            }
        except Exception as e:
            return {
                'id': self.id,
                'nome': str(self.nome) if self.nome else 'Erro',
                'email': '',
                'telefone': '',
                'cpf_associado': '',
                'churrasqueira_id': None,
                'churrasqueira_nome': '',
                'data_reserva': '',
                'data_reserva_iso': '',
                'horario_inicio': '',
                'horario_fim': '',
                'numero_convidados': 0,
                'status': 'erro',
                'status_display': f'Erro: {str(e)}',
                'data_criacao': '',
                'observacoes': ''
            }

    def _get_status_display(self):
        """Retorna descrição amigável do status"""
        status_map = {
            'pendente': 'Pendente',
            'paga': 'Paga',
            'ativa': 'Ativa',
            'cancelada': 'Cancelada',
            'realizada': 'Realizada',
            'vencida': 'Vencida'
        }
        return status_map.get(self.status, 'Desconhecido')
    
   
    @classmethod
    def verificar_disponibilidade(cls, churrasqueira_id, data_reserva, horario_inicio, horario_fim, excluir_id=None):
        """Verifica disponibilidade para a churrasqueira específica.

        Assinatura ajustada para corresponder aos testes: (churrasqueira_id, data, inicio, fim).
        """
        query = cls.query.filter(
            cls.data_reserva == data_reserva,
            cls.churrasqueira_id == churrasqueira_id,
            cls.status.in_(('ativa', 'paga', 'pendente', 'confirmada'))
        )

        if excluir_id:
            query = query.filter(cls.id != excluir_id)

        reservas_existentes = query.all()

        for reserva in reservas_existentes:
            if (horario_inicio < reserva.horario_fim and horario_fim > reserva.horario_inicio):
                return False, (
                    f"Conflito com reserva existente "
                    f"{reserva.horario_inicio.strftime('%H:%M')} - {reserva.horario_fim.strftime('%H:%M')} "
                    f"({reserva.nome})"
                )

        return True, "Horário disponível"


    @classmethod
    def obter_horarios_ocupados(cls, data_reserva, churrasqueira_id):
        reservas = cls.query.filter(
            cls.data_reserva == data_reserva,
            cls.churrasqueira_id == churrasqueira_id,
            cls.status.in_(('ativa', 'paga', 'pendente', 'confirmada'))
        ).all()

        return [
            {
                'inicio': r.horario_inicio.strftime('%H:%M'),
                'fim': r.horario_fim.strftime('%H:%M'),
                'nome': r.nome
            }
            for r in reservas
        ]

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
    

class Churrasqueira(db.Model):
    __tablename__ = "churrasqueiras"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.String(255), nullable=True)
    capacidade = db.Column(db.Integer, nullable=True)
    foto_url = db.Column(db.String(255), nullable=True)
    preco = db.Column(db.Numeric(10, 2), default=30.00, comment="Preço de reserva da churrasqueira")

    reservas = db.relationship("Reserva", backref="churrasqueira", lazy=True)

    def __repr__(self):
        return f"<Churrasqueira {self.nome}>"






class Associado(db.Model):
    """Modelo para Associados do SINT-IFESGO"""
    __tablename__ = 'associados'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), nullable=True, index=True)  # Código do associado na API
    cpf = db.Column(db.String(11), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(200), nullable=False)
    lotacao = db.Column(db.String(200), nullable=True)  # Lotação do servidor
    categoria = db.Column(db.String(50), nullable=True)  # PENSIONISTA, SERVIDOR, etc
    situacao = db.Column(db.String(50), nullable=True)  # FILIADO, NÃO FILIADO
    inadimplencia = db.Column(db.String(10), nullable=True, default=None)  # SIM, NÃO
    
    # Campos locais opcionais
    email = db.Column(db.String(100), nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    data_ultimo_pagamento = db.Column(db.Date, nullable=True)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    data_ultima_sincronizacao = db.Column(db.DateTime, nullable=True)  # Última sincronização com API
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    reservas = db.relationship('Reserva', backref='associado_obj', lazy=True, foreign_keys='Reserva.cpf_associado')
    taxas = db.relationship('Taxa', backref='associado_obj', lazy=True, foreign_keys='Taxa.associado_cpf')
    credencial = db.relationship('LoginSistema', backref='associado_obj', uselist=False, lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Associado {self.nome} - CPF: {self.cpf_formatado}>'
    
    @property
    def cpf_formatado(self):
        """Retorna CPF formatado"""
        cpf = self.cpf
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    @property
    def status_adimplencia(self):
        """Retorna status de adimplência baseado no campo inadimplencia.

        Considera adimplente somente quando `inadimplencia` é explicitamente 'NÃO'.
        """
        valor = str(self.inadimplencia or '').upper()
        nao_vals = {'NÃO', 'NAO', 'NO', 'N'}
        return 'adimplente' if valor in nao_vals else 'inadimplente'
    
    def is_adimplente(self):
        """Verifica se o associado está adimplente.

        Apenas considera adimplente quando `inadimplencia` == 'NÃO'.
        Valores ausentes ou diferentes de 'NÃO' são tratados como inadimplente.
        """
        valor = str(self.inadimplencia or '').upper()
        nao_vals = {'NÃO', 'NAO', 'NO', 'N'}
        return (valor in nao_vals) and self.ativo
    
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
        try:
            # Formatação segura das datas
            data_ultimo_pagamento_str = 'Nunca'
            if self.data_ultimo_pagamento:
                try:
                    data_ultimo_pagamento_str = self.data_ultimo_pagamento.strftime('%d/%m/%Y')
                except:
                    data_ultimo_pagamento_str = str(self.data_ultimo_pagamento)
            
            data_cadastro_str = ''
            if self.data_cadastro:
                try:
                    data_cadastro_str = self.data_cadastro.strftime('%d/%m/%Y %H:%M')
                except:
                    data_cadastro_str = str(self.data_cadastro)
            
            data_sincronizacao_str = 'Nunca'
            if self.data_ultima_sincronizacao:
                try:
                    data_sincronizacao_str = self.data_ultima_sincronizacao.strftime('%d/%m/%Y %H:%M')
                except:
                    data_sincronizacao_str = str(self.data_ultima_sincronizacao)
            
            # CPF formatado seguro
            cpf_formatado_str = self.cpf
            try:
                cpf_formatado_str = self.cpf_formatado
            except:
                cpf_formatado_str = self.cpf
            
            return {
                'id': self.id,
                'codigo': self.codigo or '',
                'cpf': self.cpf or '',
                'cpf_formatado': cpf_formatado_str,
                'nome': self.nome or '',
                'lotacao': self.lotacao or '',
                'categoria': self.categoria or '',
                'situacao': self.situacao or '',
                'inadimplencia': self.inadimplencia or 'NÃO',
                'email': self.email or '',
                'telefone': self.telefone or '',
                'status_adimplencia': self.status_adimplencia,
                'status_display': 'Adimplente' if self.inadimplencia != 'SIM' else 'Inadimplente',
                'data_ultimo_pagamento': data_ultimo_pagamento_str,
                'data_cadastro': data_cadastro_str,
                'data_ultima_sincronizacao': data_sincronizacao_str,
                'ativo': self.ativo if self.ativo is not None else True,
                'pode_reservar': self.is_adimplente()
            }
        except Exception as e:
            # Fallback em caso de erro
            return {
                'id': getattr(self, 'id', 0),
                'cpf': getattr(self, 'cpf', ''),
                'cpf_formatado': getattr(self, 'cpf', ''),
                'nome': getattr(self, 'nome', ''),
                'email': getattr(self, 'email', ''),
                'telefone': getattr(self, 'telefone', ''),
                'status_adimplencia': getattr(self, 'status_adimplencia', 'adimplente'),
                'status_display': 'Adimplente',
                'data_ultimo_pagamento': 'Nunca',
                'data_cadastro': '',
                'ativo': True,
                'pode_reservar': True,
                'erro_conversao': str(e)
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
        # Buscar nome do associado (primeiro na API, depois no banco local)
        associado_nome = None
        if self.associado_cpf:
            # Limpar CPF para busca (remover formatação)
            cpf_limpo = self.associado_cpf.replace('.', '').replace('-', '') if '.' in self.associado_cpf or '-' in self.associado_cpf else self.associado_cpf
            
            # Tentar buscar na API primeiro
            try:
                from app.services.webservice_sinsind import web_service_sinsind
                sucesso, dados_ws, _ = web_service_sinsind.consultar_associado(cpf_limpo)
                if sucesso and dados_ws:
                    associado_nome = dados_ws.get('nome')
            except Exception:
                pass
            
            # Se não encontrou na API, buscar no banco local
            if not associado_nome:
                associado = Associado.query.filter_by(cpf=cpf_limpo).first()
                if associado:
                    associado_nome = associado.nome
        
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
            'associado_nome': associado_nome,
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

        
class LoginSistema(db.Model):
    """
    Modelo de Credenciais de Acesso.
    
    Gerencia o login e nível de permissão dos associados.
    Relacionamento 1:1 com a tabela Associado através do CPF.
    
    Attributes:
        id (int): Identificador interno
        cpf (str): Chave estrangeira para Associado (Unique)
        senha_hash (str): Hash seguro da senha
        adm (int): Nível de permissão (0=Comum, 1=Admin)
    """
    __tablename__ = 'login_sistema'

    id = db.Column(db.Integer, primary_key=True)
    
    # Chave estrangeira ligando ao CPF da tabela associados
    cpf = db.Column(db.String(11), db.ForeignKey('associados.cpf'), unique=True, nullable=False, comment='CPF do associado (Login)')
    
    senha_hash = db.Column(db.String(128), nullable=False, comment='Hash da senha')
    adm = db.Column(db.Integer, default=0, comment='Nível de acesso: 0=Usuário, 1=Admin')
    
    data_criacao = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    ultimo_login = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        tipo = "Admin" if self.adm == 1 else "Usuário"
        return f'<Login {self.cpf} - {tipo}>'

    def definir_senha(self, senha):
        """Gera o hash da senha antes de salvar"""
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        """Verifica se a senha em texto bate com o hash salvo"""
        return check_password_hash(self.senha_hash, senha)
    
    def is_admin(self):
        """Retorna True se for administrador"""
        return self.adm == 1

    def to_dict(self):
        """Converte para dicionário (seguro, sem a senha)"""
        return {
            'cpf': self.cpf,
            'is_admin': self.is_admin(),
            'tipo_usuario': 'Administrador' if self.adm == 1 else 'Associado',
            'data_criacao': self.data_criacao.strftime('%d/%m/%Y %H:%M') if self.data_criacao else '',
            'ultimo_login': self.ultimo_login.strftime('%d/%m/%Y %H:%M') if self.ultimo_login else 'Nunca'
        }


class TokenRecuperacaoSenha(db.Model):
    """
    Modelo para tokens de recuperação de senha.
    
    Gera tokens únicos e temporários para recuperação de senha.
    Tokens expiram em 1 hora por segurança.
    
    Attributes:
        id (int): Identificador único
        cpf (str): CPF do associado
        token (str): Token único de 32 caracteres
        data_criacao (datetime): Quando o token foi gerado
        data_expiracao (datetime): Quando o token expira
        usado (bool): Se o token já foi utilizado
    """
    __tablename__ = 'token_recuperacao_senha'
    
    id = db.Column(db.Integer, primary_key=True)
    cpf = db.Column(db.String(11), db.ForeignKey('associados.cpf'), nullable=False, comment='CPF do associado')
    token = db.Column(db.String(64), unique=True, nullable=False, comment='Token único de recuperação')
    data_criacao = db.Column(db.DateTime, default=datetime.now(timezone.utc), comment='Data de criação')
    data_expiracao = db.Column(db.DateTime, nullable=False, comment='Data de expiração (1 hora)')
    usado = db.Column(db.Boolean, default=False, comment='Se o token já foi usado')
    
    def __repr__(self):
        return f'<TokenRecuperacaoSenha {self.cpf} - {self.token[:8]}...>'
    
    @staticmethod
    def gerar_token():
        """Gera um token aleatório de 32 caracteres"""
        import secrets
        return secrets.token_urlsafe(32)
    
    @classmethod
    def criar_token(cls, cpf: str):
        """Cria um novo token de recuperação para o CPF"""
        # Invalidar tokens anteriores não usados
        tokens_antigos = cls.query.filter_by(cpf=cpf, usado=False).all()
        for token_antigo in tokens_antigos:
            token_antigo.usado = True
        
        # Criar novo token válido por 1 hora
        from datetime import timedelta
        novo_token = cls(
            cpf=cpf,
            token=cls.gerar_token(),
            data_expiracao=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        db.session.add(novo_token)
        db.session.commit()
        
        return novo_token
    
    def is_valido(self) -> bool:
        """Verifica se o token ainda é válido"""
        if self.usado:
            return False
        if datetime.now(timezone.utc) > self.data_expiracao:
            return False
        return True
    
    def marcar_como_usado(self):
        """Marca o token como usado"""
        self.usado = True
        db.session.commit()
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'cpf': self.cpf,
            'token': self.token,
            'valido': self.is_valido(),
            'data_criacao': self.data_criacao.strftime('%d/%m/%Y %H:%M') if self.data_criacao else '',
            'data_expiracao': self.data_expiracao.strftime('%d/%m/%Y %H:%M') if self.data_expiracao else ''
        }