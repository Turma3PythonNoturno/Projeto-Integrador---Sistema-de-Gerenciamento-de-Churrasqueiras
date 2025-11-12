import re
from datetime import date, time, timedelta
from typing import Dict, Tuple, Optional
from app.interfaces.reserva_interfaces import IValidadorReserva
from config import Config


class ValidadorReserva(IValidadorReserva):
    """Validador concreto para reservas"""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
    
    def validar_dados_reserva(self, dados: Dict) -> Tuple[bool, str]:
        """Valida todos os dados de uma reserva"""
        
        # Validar campos obrigatórios - incluindo CPF para SINT-IFESGO
        campos_obrigatorios = ['nome', 'cpf_associado', 'data_reserva', 'horario_inicio', 'horario_fim']
        for campo in campos_obrigatorios:
            if not dados.get(campo):
                return False, f"Campo obrigatório não preenchido: {campo}"
        
        # Validar CPF do associado
        cpf_valido, cpf_msg = self._validar_cpf(dados['cpf_associado'])
        if not cpf_valido:
            return False, cpf_msg
        
        # Validar nome
        nome_valido, nome_msg = self._validar_nome(dados['nome'])
        if not nome_valido:
            return False, nome_msg
        
        # Validar email se fornecido
        if dados.get('email'):
            email_valido, email_msg = self._validar_email(dados['email'])
            if not email_valido:
                return False, email_msg
        

        
        # Validar número de convidados
        convidados_valido, convidados_msg = self._validar_numero_convidados(
            dados.get('numero_convidados', 1)
        )
        if not convidados_valido:
            return False, convidados_msg
        
        return True, "Dados válidos"
    
    def validar_horario_funcionamento(self, inicio: time, fim: time) -> Tuple[bool, str]:
        """Valida se o horário está dentro do funcionamento"""
        horario_inicio_func = time(8, 0)  # 08:00
        horario_fim_func = time(18, 0)    # 18:00 - Atualizado para SINT-IFESGO
        
        if inicio < horario_inicio_func or fim > horario_fim_func:
            return False, "Horário de funcionamento: 08:00 às 18:00"
        
        if inicio >= fim:
            return False, "Horário de início deve ser anterior ao horário de fim"
        
        # Validar duração mínima e máxima
        duracao_horas = (fim.hour + fim.minute/60) - (inicio.hour + inicio.minute/60)
        
        if duracao_horas < self.config.MIN_DURATION_HOURS:
            return False, f"Duração mínima: {self.config.MIN_DURATION_HOURS} horas"
        
        if duracao_horas > self.config.MAX_DURATION_HOURS:
            return False, f"Duração máxima: {self.config.MAX_DURATION_HOURS} horas"
        
        return True, "Horário válido"
    
    def validar_antecedencia(self, data_reserva: date) -> Tuple[bool, str]:
        """Valida a antecedência da reserva"""
        hoje = date.today()
        
        # Não pode ser data passada
        if data_reserva < hoje:
            return False, "Não é possível reservar datas passadas"
        
        # Não pode ser hoje (mínimo 1 dia de antecedência)
        if data_reserva == hoje:
            return False, "Reserva deve ser feita com pelo menos 1 dia de antecedência"
        
        # Máximo de antecedência
        data_limite = hoje + timedelta(days=self.config.MAX_DIAS_ANTECEDENCIA)
        if data_reserva > data_limite:
            return False, f"Não é possível reservar com mais de {self.config.MAX_DIAS_ANTECEDENCIA} dias de antecedência"
        
        return True, "Data válida"
    
    def _validar_nome(self, nome: str) -> Tuple[bool, str]:
        """Valida o nome do responsável"""
        if not nome or len(nome.strip()) < 2:
            return False, "Nome deve ter pelo menos 2 caracteres"
        
        if len(nome.strip()) > 100:
            return False, "Nome deve ter no máximo 100 caracteres"
        
        # Verificar se contém apenas letras, espaços e acentos
        if not re.match(r'^[a-zA-ZÀ-ÿ\s]+$', nome.strip()):
            return False, "Nome deve conter apenas letras e espaços"
        
        return True, "Nome válido"
    
    def _validar_email(self, email: str) -> Tuple[bool, str]:
        """Valida formato de email"""
        padrao = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(padrao, email):
            return False, "Formato de email inválido"
        
        return True, "Email válido"
    

    
    def _validar_numero_convidados(self, numero: int) -> Tuple[bool, str]:
        """Valida o número de convidados"""
        try:
            num = int(numero)
            if num < 1:
                return False, "Deve haver pelo menos 1 pessoa"
            if num > 20:
                return False, "Máximo de 20 pessoas permitidas"
            return True, "Número de convidados válido"
        except (ValueError, TypeError):
            return False, "Número de convidados deve ser um número válido"
    
    def _validar_cpf(self, cpf: str) -> Tuple[bool, str]:
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