from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
from decimal import Decimal


@dataclass
class Taxa:
    """Entidade de domínio para Taxa de Reserva"""
    
    valor: Decimal
    tipo: str  # 'reserva', 'sindical', etc.
    status: str = 'pendente'  # pendente, pago, vencido, cancelado
    data_vencimento: Optional[date] = None
    data_pagamento: Optional[datetime] = None
    reserva_id: Optional[int] = None
    associado_cpf: Optional[str] = None
    codigo_pagamento: Optional[str] = None
    observacoes: Optional[str] = None
    id: Optional[int] = None
    data_criacao: Optional[datetime] = None
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if self.data_criacao is None:
            self.data_criacao = datetime.utcnow()
        
        # Se não definiu vencimento e é taxa de reserva, define 24h
        if self.data_vencimento is None and self.tipo == 'reserva':
            self.data_vencimento = date.today()
            # Para reserva, vencimento é em 24h para confirmar pagamento
    
    def is_pendente(self) -> bool:
        """Verifica se a taxa está pendente"""
        return self.status == 'pendente'
    
    def is_paga(self) -> bool:
        """Verifica se a taxa foi paga"""
        return self.status == 'pago'
    
    def is_vencida(self) -> bool:
        """Verifica se a taxa está vencida"""
        if self.status == 'vencido':
            return True
        
        if self.status == 'pendente' and self.data_vencimento:
            return date.today() > self.data_vencimento
        
        return False
    
    def pode_ser_paga(self) -> tuple[bool, str]:
        """Verifica se a taxa pode ser paga"""
        if self.is_paga():
            return False, "Taxa já foi paga"
        
        if self.status == 'cancelado':
            return False, "Taxa foi cancelada"
        
        if self.is_vencida():
            return False, "Taxa está vencida"
        
        return True, "Taxa pode ser paga"
    
    def marcar_como_paga(self, data_pagamento: Optional[datetime] = None, codigo_transacao: Optional[str] = None) -> None:
        """Marca a taxa como paga"""
        self.status = 'pago'
        self.data_pagamento = data_pagamento or datetime.utcnow()
        
        if codigo_transacao:
            self.codigo_pagamento = codigo_transacao
    
    def marcar_como_vencida(self) -> None:
        """Marca a taxa como vencida"""
        self.status = 'vencido'
    
    def cancelar(self, motivo: Optional[str] = None) -> None:
        """Cancela a taxa"""
        self.status = 'cancelado'
        if motivo:
            self.observacoes = (self.observacoes or '') + f"\\nCancelada: {motivo}"
    
    def gerar_codigo_pagamento(self) -> str:
        """Gera código único para pagamento"""
        import uuid
        codigo = str(uuid.uuid4())[:8].upper()
        self.codigo_pagamento = f"SINT{codigo}"
        return self.codigo_pagamento
    
    def valor_formatado(self) -> str:
        """Retorna valor formatado em Real"""
        return f"R$ {self.valor:.2f}".replace('.', ',')
    
    def dias_para_vencimento(self) -> int:
        """Retorna quantos dias faltam para vencimento"""
        if not self.data_vencimento:
            return 0
        
        delta = self.data_vencimento - date.today()
        return max(0, delta.days)
    
    def to_dict(self) -> dict:
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
            'dias_para_vencimento': self.dias_para_vencimento(),
            'pode_pagar': self.pode_ser_paga()[0],
            'is_vencida': self.is_vencida()
        }
    
    def _get_status_display(self) -> str:
        """Retorna status formatado para exibição"""
        status_map = {
            'pendente': 'Pendente',
            'pago': 'Pago',
            'vencido': 'Vencido',
            'cancelado': 'Cancelado'
        }
        return status_map.get(self.status, self.status.title())