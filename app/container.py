"""Container de dependências para injeção de dependência"""

from app.interfaces.reserva_interfaces import IReservaRepository, IValidadorReserva
from app.repositories.reserva_repository import ReservaRepository  
from app.validators.reserva_validator import ValidadorReserva
from app.services.reserva_service import ReservaService
from app.services.associado_service import AssociadoService
from app.services.taxa_service import TaxaService
from app.services.boletim_service import BoletimService
from config import Config


class DependencyContainer:
    """Container para gerenciar todas as dependências da aplicação"""
    
    def __init__(self):
        self._config = Config()
        self._instances = {}
    
    def get_config(self) -> Config:
        """Retorna a configuração da aplicação"""
        return self._config
    
    def get_reserva_validator(self) -> IValidadorReserva:
        """Retorna o validador de reservas"""
        if 'reserva_validator' not in self._instances:
            self._instances['reserva_validator'] = ValidadorReserva(self._config)
        return self._instances['reserva_validator']
    
    def get_reserva_repository(self) -> IReservaRepository:
        """Retorna o repositório de reservas"""
        if 'reserva_repository' not in self._instances:
            self._instances['reserva_repository'] = ReservaRepository()
        return self._instances['reserva_repository']
    
    def get_reserva_service(self) -> ReservaService:
        """Retorna o serviço de reservas com todas as dependências injetadas"""
        if 'reserva_service' not in self._instances:
            repository = self.get_reserva_repository()
            validator = self.get_reserva_validator()
            self._instances['reserva_service'] = ReservaService(repository, validator)
        return self._instances['reserva_service']
    
    def get_associado_service(self) -> AssociadoService:
        """Retorna o serviço de associados"""
        if 'associado_service' not in self._instances:
            self._instances['associado_service'] = AssociadoService()
        return self._instances['associado_service']
    
    def get_taxa_service(self) -> TaxaService:
        """Retorna o serviço de taxas"""
        if 'taxa_service' not in self._instances:
            self._instances['taxa_service'] = TaxaService()
        return self._instances['taxa_service']
    
    def get_boletim_service(self) -> BoletimService:
        """Retorna o serviço de boletins"""
        if 'boletim_service' not in self._instances:
            self._instances['boletim_service'] = BoletimService()
        return self._instances['boletim_service']
    
    def clear_instances(self):
        """Limpa todas as instâncias (útil para testes)"""
        self._instances.clear()


# Instância global do container (singleton)
container = DependencyContainer()