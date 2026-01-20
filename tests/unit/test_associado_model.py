"""
Unit Tests for Associado Model
Tests for Associado business logic and validation
"""

import pytest
from datetime import date, timedelta
from app.models import Associado


class TestAssociadoCreation:
    """Tests for Associado creation"""
    
    def test_criar_associado_completo(self, db_session):
        """Should create associado with all fields"""
        associado = Associado(
            cpf='12345678901',
            codigo='001',
            nome='João Silva',
            lotacao='TI',
            categoria='EFETIVO',
            situacao='FILIADO',
            inadimplencia='NÃO',
            email='joao@example.com',
            telefone='62987654321',
            ativo=True
        )
        db_session.add(associado)
        db_session.commit()
        
        assert associado.cpf == '12345678901'
        assert associado.nome == 'João Silva'
        assert associado.ativo is True
    
    def test_criar_associado_campos_minimos(self, db_session):
        """Should create associado with minimum required fields"""
        associado = Associado(
            cpf='98765432100',
            nome='Maria Santos'
        )
        db_session.add(associado)
        db_session.commit()
        
        assert associado.cpf == '98765432100'
        assert associado.nome == 'Maria Santos'


class TestAssociadoValidarCPF:
    """Tests for CPF validation"""
    
    def test_validar_cpf_valido(self):
        """Should accept valid CPF"""
        valido, mensagem = Associado.validar_cpf('11144477735')
        assert valido is True
    
    def test_validar_cpf_invalido(self):
        """Should reject invalid CPF"""
        valido, mensagem = Associado.validar_cpf('12345678901')
        assert valido is False
        assert 'inválido' in mensagem.lower()
    
    def test_validar_cpf_vazio(self):
        """Should reject empty CPF"""
        valido, mensagem = Associado.validar_cpf('')
        assert valido is False


class TestAssociadoIsAdimplente:
    """Tests for adimplência check"""
    
    def test_associado_adimplente(self, associado_adimplente):
        """Should return True for adimplente associado"""
        assert associado_adimplente.is_adimplente() is True
    
    def test_associado_inadimplente(self, associado_inadimplente):
        """Should return False for inadimplente associado"""
        assert associado_inadimplente.is_adimplente() is False
    
    def test_associado_sem_inadimplencia_definida(self, db_session):
        """Should handle associado without inadimplencia field"""
        associado = Associado(
            cpf='11111111111',
            nome='Teste',
            inadimplencia=None
        )
        db_session.add(associado)
        db_session.commit()
        
        # None ou vazio deve ser tratado como inadimplente por segurança
        assert associado.is_adimplente() is False


class TestAssociadoPodeFazerReserva:
    """Tests for reservation permission"""
    
    def test_adimplente_pode_reservar(self, associado_adimplente):
        """Adimplente should be able to make reservation"""
        pode, mensagem = associado_adimplente.pode_fazer_reserva()
        assert pode is True
    
    def test_inadimplente_nao_pode_reservar(self, associado_inadimplente):
        """Inadimplente should not be able to make reservation"""
        pode, mensagem = associado_inadimplente.pode_fazer_reserva()
        assert pode is False
        assert 'inadimplente' in mensagem.lower()
    
    def test_associado_inativo_nao_pode_reservar(self, db_session):
        """Inactive associado should not be able to make reservation"""
        associado = Associado(
            cpf='22222222222',
            nome='Inativo',
            inadimplencia='NÃO',
            ativo=False
        )
        db_session.add(associado)
        db_session.commit()
        
        pode, mensagem = associado.pode_fazer_reserva()
        assert pode is False
        assert 'inativo' in mensagem.lower()


class TestAssociadoToDict:
    """Tests for to_dict() method"""
    
    def test_to_dict_campos_basicos(self, associado_adimplente):
        """Should convert associado to dict with basic fields"""
        dados = associado_adimplente.to_dict()
        
        assert dados['cpf'] == associado_adimplente.cpf
        assert dados['nome'] == associado_adimplente.nome
        assert dados['email'] == associado_adimplente.email
        assert 'inadimplencia' in dados
    
    def test_to_dict_inclui_todas_propriedades(self, associado_adimplente):
        """Should include all properties in dict"""
        dados = associado_adimplente.to_dict()
        
        campos_esperados = [
            'cpf', 'codigo', 'nome', 'lotacao', 'categoria',
            'situacao', 'inadimplencia', 'email', 'telefone', 'ativo'
        ]
        
        for campo in campos_esperados:
            assert campo in dados


class TestAssociadoDataUltimoPagamento:
    """Tests for last payment date"""
    
    def test_associado_com_pagamento_recente(self, db_session):
        """Associado with recent payment"""
        associado = Associado(
            cpf='33333333333',
            nome='Pagamento Recente',
            data_ultimo_pagamento=date.today(),
            inadimplencia='NÃO'
        )
        db_session.add(associado)
        db_session.commit()
        
        assert associado.data_ultimo_pagamento == date.today()
        assert associado.is_adimplente() is True
    
    def test_associado_com_pagamento_antigo(self, db_session):
        """Associado with old payment"""
        data_antiga = date.today() - timedelta(days=365)
        associado = Associado(
            cpf='44444444444',
            nome='Pagamento Antigo',
            data_ultimo_pagamento=data_antiga,
            inadimplencia='SIM'
        )
        db_session.add(associado)
        db_session.commit()
        
        assert associado.data_ultimo_pagamento == data_antiga
        assert associado.is_adimplente() is False


@pytest.mark.parametrize("inadimplencia,esperado", [
    ('NÃO', True),
    ('NAO', True),
    ('nao', True),
    ('SIM', False),
    ('sim', False),
    (None, False),
    ('', False),
])
def test_is_adimplente_variacoes(db_session, inadimplencia, esperado):
    """Test is_adimplente with various inadimplencia values"""
    associado = Associado(
        cpf='55555555555',
        nome='Teste Variações',
        inadimplencia=inadimplencia
    )
    db_session.add(associado)
    db_session.commit()
    
    assert associado.is_adimplente() is esperado
