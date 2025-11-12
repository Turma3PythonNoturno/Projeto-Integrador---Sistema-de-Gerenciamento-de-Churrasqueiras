from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Optional


@dataclass
class Reserva:
    """Entidade de domínio para Reserva"""
    
    nome: str

    data_reserva: date
    horario_inicio: time
    horario_fim: time
    numero_convidados: int = 1
    email: Optional[str] = None
    telefone: Optional[str] = None
    observacoes: Optional[str] = None
    status: str = 'ativa'
    id: Optional[int] = None
    data_criacao: Optional[datetime] = None
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if self.data_criacao is None:
            self.data_criacao = datetime.utcnow()
    
    def calcular_duracao_horas(self) -> float:
        """Calcula a duração da reserva em horas"""
        inicio_total = self.horario_inicio.hour + self.horario_inicio.minute / 60
        fim_total = self.horario_fim.hour + self.horario_fim.minute / 60
        return fim_total - inicio_total
    
    def is_ativa(self) -> bool:
        """Verifica se a reserva está ativa"""
        return self.status == 'ativa'
    
    def pode_ser_cancelada(self) -> tuple[bool, str]:
        """Verifica se a reserva pode ser cancelada"""
        if not self.is_ativa():
            return False, "Reserva já foi cancelada"
        
        agora = datetime.now()
        data_hora_reserva = datetime.combine(self.data_reserva, self.horario_inicio)
        
        if data_hora_reserva <= agora:
            return False, "Não é possível cancelar reservas que já começaram"
        
        diferenca = data_hora_reserva - agora
        if diferenca.total_seconds() < 24 * 3600:  # 24 horas
            return False, "Cancelamento deve ser feito com pelo menos 24h de antecedência"
        
        return True, "Reserva pode ser cancelada"
    
    def cancelar(self, motivo: Optional[str] = None) -> None:
        """Cancela a reserva"""
        self.status = 'cancelada'
        if motivo:
            self.observacoes = (self.observacoes or '') + f"\nCancelada: {motivo}"
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
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
            'data_criacao': self.data_criacao.strftime('%d/%m/%Y %H:%M') if self.data_criacao else '',
            'observacoes': self.observacoes or '',
            'duracao_horas': self.calcular_duracao_horas()
        }