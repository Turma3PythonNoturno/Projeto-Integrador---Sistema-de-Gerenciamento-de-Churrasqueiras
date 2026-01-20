"""
Unit Tests for CPFUtils
Tests for CPF cleaning, formatting, and validation functions
"""

import pytest
from app.utils import CPFUtils


class TestCPFUtilsLimpar:
    """Tests for CPFUtils.limpar()"""
    
    def test_limpar_cpf_formatado(self):
        """Should remove formatting from CPF"""
        cpf_formatado = '123.456.789-01'
        resultado = CPFUtils.limpar(cpf_formatado)
        assert resultado == '12345678901'
    
    def test_limpar_cpf_sem_formatacao(self):
        """Should keep unformatted CPF as is"""
        cpf = '12345678901'
        resultado = CPFUtils.limpar(cpf)
        assert resultado == '12345678901'
    
    def test_limpar_cpf_com_espacos(self):
        """Should remove spaces from CPF"""
        cpf_com_espacos = '123 456 789 01'
        resultado = CPFUtils.limpar(cpf_com_espacos)
        assert resultado == '12345678901'
    
    def test_limpar_cpf_vazio(self):
        """Should handle empty string"""
        resultado = CPFUtils.limpar('')
        assert resultado == ''
    
    def test_limpar_cpf_apenas_pontuacao(self):
        """Should return empty when only punctuation"""
        cpf_invalido = '...-'
        resultado = CPFUtils.limpar(cpf_invalido)
        assert resultado == ''


class TestCPFUtilsFormatar:
    """Tests for CPFUtils.formatar()"""
    
    def test_formatar_cpf_limpo(self):
        """Should format clean CPF"""
        cpf_limpo = '12345678901'
        resultado = CPFUtils.formatar(cpf_limpo)
        assert resultado == '123.456.789-01'
    
    def test_formatar_cpf_ja_formatado(self):
        """Should handle already formatted CPF"""
        cpf_formatado = '123.456.789-01'
        resultado = CPFUtils.formatar(cpf_formatado)
        assert resultado == '123.456.789-01'
    
    def test_formatar_cpf_incompleto(self):
        """Should return as-is if CPF is incomplete"""
        cpf_incompleto = '123456'
        resultado = CPFUtils.formatar(cpf_incompleto)
        assert resultado == '123456'
    
    def test_formatar_cpf_vazio(self):
        """Should handle empty string"""
        resultado = CPFUtils.formatar('')
        assert resultado == ''


class TestCPFUtilsValidar:
    """Tests for CPFUtils.validar()"""
    
    def test_validar_cpf_valido(self):
        """Should validate correct CPF"""
        # CPF válido real: 111.444.777-35
        cpf_valido = '11144477735'
        valido, mensagem = CPFUtils.validar(cpf_valido)
        assert valido is True
        assert 'válido' in mensagem.lower()
    
    def test_validar_cpf_invalido_digito(self):
        """Should reject CPF with invalid check digit"""
        cpf_invalido = '12345678901'
        valido, mensagem = CPFUtils.validar(cpf_invalido)
        assert valido is False
        assert 'inválido' in mensagem.lower()
    
    def test_validar_cpf_curto(self):
        """Should reject CPF with less than 11 digits"""
        cpf_curto = '123456789'
        valido, mensagem = CPFUtils.validar(cpf_curto)
        assert valido is False
        assert '11 dígitos' in mensagem.lower()
    
    def test_validar_cpf_longo(self):
        """Should reject CPF with more than 11 digits"""
        cpf_longo = '123456789012'
        valido, mensagem = CPFUtils.validar(cpf_longo)
        assert valido is False
        assert '11 dígitos' in mensagem.lower()
    
    def test_validar_cpf_todos_iguais(self):
        """Should reject CPF with all same digits"""
        cpf_todos_iguais = '11111111111'
        valido, mensagem = CPFUtils.validar(cpf_todos_iguais)
        assert valido is False
        assert 'inválido' in mensagem.lower()
    
    def test_validar_cpf_com_formatacao(self):
        """Should validate formatted CPF"""
        cpf_formatado = '111.444.777-35'
        valido, mensagem = CPFUtils.validar(cpf_formatado)
        assert valido is True


class TestCPFUtilsEhValido:
    """Tests for CPFUtils.eh_valido()"""
    
    def test_eh_valido_cpf_correto(self):
        """Should return True for valid CPF"""
        cpf_valido = '11144477735'
        assert CPFUtils.eh_valido(cpf_valido) is True
    
    def test_eh_valido_cpf_incorreto(self):
        """Should return False for invalid CPF"""
        cpf_invalido = '12345678901'
        assert CPFUtils.eh_valido(cpf_invalido) is False
    
    def test_eh_valido_cpf_vazio(self):
        """Should return False for empty CPF"""
        assert CPFUtils.eh_valido('') is False


class TestCPFUtilsSanitizar:
    """Tests for CPFUtils.sanitizar()"""
    
    def test_sanitizar_sem_formatacao(self):
        """Should clean CPF without formatting"""
        cpf = '123.456.789-01'
        resultado = CPFUtils.sanitizar(cpf, formatar=False)
        assert resultado == '12345678901'
    
    def test_sanitizar_com_formatacao(self):
        """Should clean and format CPF"""
        cpf = '12345678901'
        resultado = CPFUtils.sanitizar(cpf, formatar=True)
        assert resultado == '123.456.789-01'
    
    def test_sanitizar_cpf_ja_limpo(self):
        """Should handle already clean CPF"""
        cpf = '12345678901'
        resultado = CPFUtils.sanitizar(cpf, formatar=False)
        assert resultado == '12345678901'


@pytest.mark.parametrize("cpf_entrada,cpf_esperado", [
    ('123.456.789-01', '12345678901'),
    ('123 456 789 01', '12345678901'),
    ('123-456-789-01', '12345678901'),
    ('12345678901', '12345678901'),
    ('', ''),
])
def test_limpar_variacoes(cpf_entrada, cpf_esperado):
    """Test various CPF input formats"""
    resultado = CPFUtils.limpar(cpf_entrada)
    assert resultado == cpf_esperado


@pytest.mark.parametrize("cpf_valido", [
    '11144477735',  # CPF real válido
    '111.444.777-35',  # CPF formatado válido
])
def test_validacao_cpfs_validos(cpf_valido):
    """Test validation of known valid CPFs"""
    valido, _ = CPFUtils.validar(cpf_valido)
    assert valido is True


@pytest.mark.parametrize("cpf_invalido", [
    '12345678901',  # Dígito verificador incorreto
    '00000000000',  # Todos zeros
    '11111111111',  # Todos iguais
    '123',  # Muito curto
    '',  # Vazio
])
def test_validacao_cpfs_invalidos(cpf_invalido):
    """Test validation of known invalid CPFs"""
    valido, _ = CPFUtils.validar(cpf_invalido)
    assert valido is False
