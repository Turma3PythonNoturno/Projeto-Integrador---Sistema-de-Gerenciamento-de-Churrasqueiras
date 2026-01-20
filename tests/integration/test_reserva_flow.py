"""
Integration Tests for Reservation Flow
Tests complete reservation creation workflow
"""

import pytest
from datetime import date, time, timedelta
from app.models import Reserva, Taxa


class TestReservaCreationFlow:
    """Tests for complete reservation creation flow"""
    
    def test_criar_reserva_com_associado_adimplente(
        self, db_session, associado_adimplente, churrasqueira
    ):
        """Should create reservation for adimplente associado"""
        data_futura = date.today() + timedelta(days=7)
        
        reserva = Reserva(
            nome=associado_adimplente.nome,
            email=associado_adimplente.email,
            telefone=associado_adimplente.telefone,
            cpf_associado=associado_adimplente.cpf,
            churrasqueira_id=churrasqueira.id,
            data_reserva=data_futura,
            horario_inicio=time(10, 0),
            horario_fim=time(18, 0),
            numero_convidados=20,
            status='confirmada'
        )
        
        db_session.add(reserva)
        db_session.commit()
        
        assert reserva.id is not None
        assert reserva.cpf_associado == associado_adimplente.cpf
        assert reserva.status == 'confirmada'
    
    def test_criar_taxa_apos_reserva(
        self, db_session, associado_adimplente, churrasqueira
    ):
        """Should create taxa after reservation"""
        data_futura = date.today() + timedelta(days=7)
        
        # Criar reserva
        reserva = Reserva(
            nome=associado_adimplente.nome,
            email=associado_adimplente.email,
            telefone=associado_adimplente.telefone,
            cpf_associado=associado_adimplente.cpf,
            churrasqueira_id=churrasqueira.id,
            data_reserva=data_futura,
            horario_inicio=time(10, 0),
            horario_fim=time(18, 0),
            numero_convidados=20,
            status='confirmada'
        )
        db_session.add(reserva)
        db_session.commit()
        
        # Criar taxa
        taxa = Taxa(
            valor=30.00,
            tipo='RESERVA',
            status='pendente',
            data_vencimento=data_futura,
            reserva_id=reserva.id,
            associado_cpf=associado_adimplente.cpf
        )
        db_session.add(taxa)
        db_session.commit()
        
        assert taxa.id is not None
        assert taxa.reserva_id == reserva.id
        assert taxa.associado_cpf == associado_adimplente.cpf
        assert taxa.valor == 30.00


class TestReservaVerificarDisponibilidade:
    """Tests for reservation availability check"""
    
    def test_horario_disponivel(
        self, db_session, churrasqueira
    ):
        """Should detect available time slot"""
        data_teste = date.today() + timedelta(days=10)
        horario_inicio = time(10, 0)
        horario_fim = time(14, 0)
        
        disponivel = Reserva.verificar_disponibilidade(
            churrasqueira.id,
            data_teste,
            horario_inicio,
            horario_fim
        )
        
        # verificar_disponibilidade retorna tupla (bool, mensagem)
        assert disponivel[0] is True
    
    def test_horario_ocupado(
        self, db_session, associado_adimplente, churrasqueira
    ):
        """Should detect occupied time slot"""
        data_teste = date.today() + timedelta(days=10)
        
        # Criar reserva existente
        reserva_existente = Reserva(
            nome=associado_adimplente.nome,
            email=associado_adimplente.email,
            telefone=associado_adimplente.telefone,
            cpf_associado=associado_adimplente.cpf,
            churrasqueira_id=churrasqueira.id,
            data_reserva=data_teste,
            horario_inicio=time(10, 0),
            horario_fim=time(14, 0),
            numero_convidados=20,
            status='confirmada'
        )
        db_session.add(reserva_existente)
        db_session.commit()
        
        # Tentar reservar horário sobreposto
        disponivel = Reserva.verificar_disponibilidade(
            churrasqueira.id,
            data_teste,
            time(12, 0),  # Sobrepõe com 10h-14h
            time(16, 0)
        )
        
        # verificar_disponibilidade retorna tupla (bool, mensagem)
        assert disponivel[0] is False


class TestReservaComAssociado:
    """Tests for reservation with associado relationship"""
    
    def test_consultar_reserva_com_associado(
        self, db_session, associado_adimplente, reserva_futura
    ):
        """Should query reservation with associado data"""
        reserva = Reserva.query.filter_by(id=reserva_futura.id).first()
        associado = Associado.query.filter_by(cpf=reserva.cpf_associado).first()
        
        assert reserva is not None
        assert associado is not None
        assert reserva.cpf_associado == associado.cpf
        assert reserva.nome == associado.nome


class TestFluxoCompletoReserva:
    """Tests for complete reservation workflow"""
    
    def test_fluxo_reserva_adimplente_com_taxa(
        self, db_session, associado_adimplente, churrasqueira
    ):
        """Should complete full reservation flow for adimplente"""
        # 1. Verificar se associado pode reservar
        pode_reservar, _ = associado_adimplente.pode_fazer_reserva()
        assert pode_reservar is True
        
        # 2. Verificar disponibilidade
        data_futura = date.today() + timedelta(days=7)
        horario_inicio = time(10, 0)
        horario_fim = time(18, 0)
        
        disponivel = Reserva.verificar_disponibilidade(
            churrasqueira.id,
            data_futura,
            horario_inicio,
            horario_fim
        )
        assert disponivel[0] is True
        
        # 3. Criar reserva
        reserva = Reserva(
            nome=associado_adimplente.nome,
            email=associado_adimplente.email,
            telefone=associado_adimplente.telefone,
            cpf_associado=associado_adimplente.cpf,
            churrasqueira_id=churrasqueira.id,
            data_reserva=data_futura,
            horario_inicio=horario_inicio,
            horario_fim=horario_fim,
            numero_convidados=20,
            status='confirmada'
        )
        db_session.add(reserva)
        db_session.commit()
        
        # 4. Criar taxa
        taxa = Taxa(
            valor=30.00,
            tipo='RESERVA',
            status='pendente',
            data_vencimento=data_futura,
            reserva_id=reserva.id,
            associado_cpf=associado_adimplente.cpf
        )
        db_session.add(taxa)
        db_session.commit()
        
        # 5. Verificar estado final
        assert reserva.id is not None
        assert taxa.id is not None
        assert taxa.reserva_id == reserva.id
        
        # 6. Verificar relacionamentos
        taxas_associado = Taxa.query.filter_by(
            associado_cpf=associado_adimplente.cpf
        ).all()
        assert len(taxas_associado) == 1
        assert taxas_associado[0].status == 'pendente'
