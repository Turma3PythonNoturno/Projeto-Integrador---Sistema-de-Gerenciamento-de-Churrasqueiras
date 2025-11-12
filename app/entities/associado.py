from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional
import re


@dataclass
class Associado:
    """Entidade de domínio para Associado do SINT-IFESGO"""
    
    cpf: str
    nome: str
    email: str
    telefone: str
    status_adimplencia: str = 'adimplente'  # adimplente, inadimplente
    data_ultimo_pagamento: Optional[date] = None
    data_cadastro: Optional[datetime] = None
    ativo: bool = True
    id: Optional[int] = None
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if self.data_cadastro is None:
            self.data_cadastro = datetime.utcnow()
        
        # Limpar e validar CPF
        self.cpf = self._limpar_cpf(self.cpf)
    
    def _limpar_cpf(self, cpf: str) -> str:
        """Remove formatação do CPF"""
        return re.sub(r'[^\d]', '', cpf)
    
    def cpf_formatado(self) -> str:
        """Retorna CPF formatado"""
        cpf = self.cpf
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    def is_adimplente(self) -> bool:
        """Verifica se o associado está adimplente"""
        return self.status_adimplencia == 'adimplente' and self.ativo
    
    def pode_fazer_reserva(self) -> tuple[bool, str]:
        """Verifica se o associado pode fazer reserva"""
        if not self.ativo:
            return False, "Associado inativo no sistema"
        
        if not self.is_adimplente():
            return False, "Associado inadimplente com taxa sindical. Regularize sua situação para fazer reservas."
        
        return True, "Associado pode fazer reserva"
    
    def marcar_inadimplente(self, motivo: Optional[str] = None) -> None:
        """Marca associado como inadimplente"""
        self.status_adimplencia = 'inadimplente'
    
    def marcar_adimplente(self, data_pagamento: Optional[date] = None) -> None:
        """Marca associado como adimplente"""
        self.status_adimplencia = 'adimplente'
        self.data_ultimo_pagamento = data_pagamento or date.today()
    
    @staticmethod
    def validar_cpf(cpf: str) -> tuple[bool, str]:
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
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'cpf': self.cpf,
            'cpf_formatado': self.cpf_formatado(),
            'nome': self.nome,
            'email': self.email,
            'telefone': self.telefone,
            'status_adimplencia': self.status_adimplencia,
            'status_display': 'Adimplente' if self.status_adimplencia == 'adimplente' else 'Inadimplente',
            'data_ultimo_pagamento': self.data_ultimo_pagamento.strftime('%d/%m/%Y') if self.data_ultimo_pagamento else 'Nunca',
            'data_cadastro': self.data_cadastro.strftime('%d/%m/%Y %H:%M') if self.data_cadastro else '',
            'ativo': self.ativo,
            'pode_reservar': self.is_adimplente() and self.ativo
        }