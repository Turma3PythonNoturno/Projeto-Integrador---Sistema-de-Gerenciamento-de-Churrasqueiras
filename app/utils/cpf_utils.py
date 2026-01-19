"""
Utilitários para manipulação de CPF

Centraliza todas as operações de CPF (limpeza, formatação, validação)
para evitar duplicação de código em todo o projeto.

Autor: Sistema SINT-IFESGO
Versão: 1.0
"""

from typing import Tuple
import re


class CPFUtils:
    """Utilitários para operações com CPF"""
    
    @staticmethod
    def limpar(cpf: str) -> str:
        """
        Remove toda formatação do CPF
        
        Exemplos:
            "123.456.789-01" -> "12345678901"
            "12345678901" -> "12345678901"
            "123-456-789.01" -> "12345678901"
        
        Args:
            cpf: CPF em qualquer formato
            
        Returns:
            CPF apenas com dígitos
        """
        if not cpf:
            return ""
        return ''.join(filter(str.isdigit, cpf))
    
    @staticmethod
    def formatar(cpf: str) -> str:
        """
        Formata CPF para XXX.XXX.XXX-XX
        
        Exemplos:
            "12345678901" -> "123.456.789-01"
            "123.456.789-01" -> "123.456.789-01"
        
        Args:
            cpf: CPF em qualquer formato
            
        Returns:
            CPF formatado ou vazio se inválido
        """
        cpf_limpo = CPFUtils.limpar(cpf)
        
        if len(cpf_limpo) != 11:
            return cpf_limpo
        
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    
    @staticmethod
    def validar(cpf: str) -> Tuple[bool, str]:
        """
        Valida CPF usando algoritmo oficial brasileiro
        
        Verifica:
        - Comprimento (11 dígitos)
        - CPFs inválidos conhecidos (000...000, 111...111, etc)
        - Dígito verificador 1
        - Dígito verificador 2
        
        Args:
            cpf: CPF em qualquer formato
            
        Returns:
            Tuple (válido: bool, mensagem: str)
        """
        cpf_limpo = CPFUtils.limpar(cpf)
        
        # Validação de comprimento
        if len(cpf_limpo) != 11:
            return False, "CPF deve ter 11 dígitos"
        
        # CPFs inválidos conhecidos
        cpfs_invalidos = [
            '00000000000', '11111111111', '22222222222',
            '33333333333', '44444444444', '55555555555',
            '66666666666', '77777777777', '88888888888',
            '99999999999'
        ]
        
        if cpf_limpo in cpfs_invalidos:
            return False, "CPF inválido"
        
        # Validação do primeiro dígito verificador
        soma = sum(int(cpf_limpo[i]) * (10 - i) for i in range(9))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        
        if int(cpf_limpo[9]) != digito1:
            return False, "CPF inválido"
        
        # Validação do segundo dígito verificador
        soma = sum(int(cpf_limpo[i]) * (11 - i) for i in range(10))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        
        if int(cpf_limpo[10]) != digito2:
            return False, "CPF inválido"
        
        return True, "CPF válido"
    
    @staticmethod
    def eh_valido(cpf: str) -> bool:
        """
        Verifica se CPF é válido (retorna apenas bool)
        
        Args:
            cpf: CPF em qualquer formato
            
        Returns:
            True se válido, False caso contrário
        """
        valido, _ = CPFUtils.validar(cpf)
        return valido
    
    @staticmethod
    def sanitizar(cpf: str, formatar: bool = False) -> str:
        """
        Sanitiza CPF - limpa e opcionalmente formata
        
        Args:
            cpf: CPF em qualquer formato
            formatar: Se True, retorna formatado (XXX.XXX.XXX-XX)
            
        Returns:
            CPF limpo ou formatado
        """
        cpf_limpo = CPFUtils.limpar(cpf)
        
        if formatar:
            return CPFUtils.formatar(cpf_limpo)
        
        return cpf_limpo
