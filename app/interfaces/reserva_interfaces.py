from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple
from datetime import date, time


class IReservaRepository(ABC):
    """Interface para repositório de reservas"""
    
    @abstractmethod
    def criar_reserva(self, reserva_data: Dict) -> Dict:
        """Cria uma nova reserva"""
        pass
    
    @abstractmethod
    def buscar_por_id(self, reserva_id: int) -> Optional[Dict]:
        """Busca reserva por ID"""
        pass
    
    @abstractmethod
    def listar_reservas_ativas(self, data_inicio: date, data_fim: date) -> List[Dict]:
        """Lista reservas ativas em um período"""
        pass
    
    @abstractmethod
    def verificar_disponibilidade(self, data: date, inicio: time, fim: time) -> Tuple[bool, str]:
        """Verifica disponibilidade de horário"""
        pass
    
    @abstractmethod
    def cancelar_reserva(self, reserva_id: int) -> bool:
        """Cancela uma reserva"""
        pass
    
    @abstractmethod
    def obter_horarios_ocupados(self, data_reserva: date) -> List[Dict]:
        """Retorna horários ocupados para uma data"""
        pass
    
    @abstractmethod
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas das reservas"""
        pass


class IValidadorReserva(ABC):
    """Interface para validação de reservas"""
    
    @abstractmethod
    def validar_dados_reserva(self, dados: Dict) -> Tuple[bool, str]:
        """Valida os dados de uma reserva"""
        pass
    
    @abstractmethod
    def validar_horario_funcionamento(self, inicio: time, fim: time) -> Tuple[bool, str]:
        """Valida se o horário está dentro do funcionamento"""
        pass
    
    @abstractmethod
    def validar_antecedencia(self, data_reserva: date) -> Tuple[bool, str]:
        """Valida a antecedência da reserva"""
        pass


class INotificadorReserva(ABC):
    """Interface para notificações de reserva"""
    
    @abstractmethod
    def notificar_reserva_criada(self, reserva_data: Dict) -> bool:
        """Notifica sobre reserva criada"""
        pass
    
    @abstractmethod
    def notificar_reserva_cancelada(self, reserva_data: Dict) -> bool:
        """Notifica sobre reserva cancelada"""
        pass