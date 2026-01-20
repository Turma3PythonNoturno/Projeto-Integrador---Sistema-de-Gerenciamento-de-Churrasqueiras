"""
Pytest Configuration and Shared Fixtures
Sistema de Reserva de Churrasqueiras - SINT-IFESGO
"""

import pytest
from datetime import datetime, date, time, timedelta
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from app.models import db, Associado, Reserva, Churrasqueira, LoginSistema, Taxa
from config import Config


class TestConfig(Config):
    """Test-specific configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SECRET_KEY = 'test-secret-key'
    SERVER_NAME = 'localhost.localdomain'


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    test_app = Flask(__name__)
    test_app.config.from_object(TestConfig)
    test_app.secret_key = 'test-secret-key'
    
    db.init_app(test_app)
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()


@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture(scope='function')
def runner(app):
    """Create CLI runner"""
    return app.test_cli_runner()


@pytest.fixture(scope='function')
def db_session(app):
    """Create database session for testing"""
    with app.app_context():
        # Clear all tables before each test
        db.session.remove()
        db.drop_all()
        db.create_all()
        
        yield db.session
        
        # Cleanup
        db.session.remove()
        db.drop_all()


@pytest.fixture
def associado_adimplente(db_session):
    """Create an adimplente (compliant) associado"""
    associado = Associado(
        cpf='12345678901',
        codigo='001',
        nome='João da Silva',
        lotacao='Departamento de TI',
        categoria='EFETIVO',
        situacao='FILIADO',
        inadimplencia='NÃO',
        email='joao.silva@example.com',
        telefone='(62) 98765-4321',
        data_ultimo_pagamento=date.today(),
        ativo=True
    )
    db_session.add(associado)
    db_session.commit()
    return associado


@pytest.fixture
def associado_inadimplente(db_session):
    """Create an inadimplente (non-compliant) associado"""
    associado = Associado(
        cpf='98765432100',
        codigo='002',
        nome='Maria Santos',
        lotacao='Departamento de RH',
        categoria='EFETIVO',
        situacao='FILIADO',
        inadimplencia='SIM',
        email='maria.santos@example.com',
        telefone='(62) 91234-5678',
        data_ultimo_pagamento=date.today() - timedelta(days=90),
        ativo=True
    )
    db_session.add(associado)
    db_session.commit()
    return associado


@pytest.fixture
def churrasqueira(db_session):
    """Create a churrasqueira"""
    churrasco = Churrasqueira(
        nome='Churrasqueira Bosque',
        descricao='Churrasqueira localizada no bosque do campus',
        capacidade=30,
        foto_url='/static/uploads/bosque.jpg'
    )
    db_session.add(churrasco)
    db_session.commit()
    return churrasco


@pytest.fixture
def login_admin(db_session, associado_adimplente):
    """Create admin login"""
    login = LoginSistema(
        cpf=associado_adimplente.cpf,
        adm=True
    )
    login.definir_senha('admin123')
    db_session.add(login)
    db_session.commit()
    return login


@pytest.fixture
def login_usuario(db_session, associado_adimplente):
    """Create regular user login"""
    login = LoginSistema(
        cpf=associado_adimplente.cpf,
        adm=False
    )
    login.definir_senha('user123')
    db_session.add(login)
    db_session.commit()
    return login


@pytest.fixture
def reserva_futura(db_session, associado_adimplente, churrasqueira):
    """Create a future reservation"""
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
    return reserva


@pytest.fixture
def taxa_pendente(db_session, associado_adimplente, reserva_futura):
    """Create a pending taxa"""
    taxa = Taxa(
        valor=30.00,
        tipo='RESERVA',
        status='pendente',
        data_vencimento=date.today() + timedelta(days=7),
        reserva_id=reserva_futura.id,
        associado_cpf=associado_adimplente.cpf
    )
    db_session.add(taxa)
    db_session.commit()
    return taxa


@pytest.fixture
def authenticated_client(client, login_usuario, associado_adimplente):
    """Create authenticated client session"""
    with client.session_transaction() as session:
        session['cpf'] = associado_adimplente.cpf
        session['nome'] = associado_adimplente.nome
        session['email'] = associado_adimplente.email
    return client


@pytest.fixture
def admin_client(client, login_admin, associado_adimplente):
    """Create authenticated admin client session"""
    with client.session_transaction() as session:
        session['cpf'] = associado_adimplente.cpf
        session['nome'] = associado_adimplente.nome
        session['email'] = associado_adimplente.email
        session['is_admin'] = True
    return client


# Helper functions for tests
@pytest.fixture
def sample_cpf():
    """Return a valid CPF for testing"""
    return '12345678901'


@pytest.fixture
def sample_cpf_formatado():
    """Return a formatted CPF for testing"""
    return '123.456.789-01'


@pytest.fixture
def data_hoje():
    """Return today's date"""
    return date.today()


@pytest.fixture
def data_futura():
    """Return a future date (7 days ahead)"""
    return date.today() + timedelta(days=7)


@pytest.fixture
def horario_manha():
    """Return morning time"""
    return time(8, 0)


@pytest.fixture
def horario_tarde():
    """Return afternoon time"""
    return time(14, 0)
