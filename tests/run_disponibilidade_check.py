from datetime import date, time, timedelta
import sys, os
# Garantir que o diretório do projeto esteja no PYTHONPATH quando executado como script
sys.path.insert(0, os.getcwd())

# Importar create_app diretamente do módulo app.py para evitar conflito com o pacote 'app'
import importlib.util
spec = importlib.util.spec_from_file_location('app_main', os.path.join(os.getcwd(), 'app.py'))
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
create_app = app_module.create_app
from app.models import db, Reserva, Churrasqueira
from app.repositories.reserva_repository import ReservaRepository

app = create_app()

with app.app_context():
    repo = ReservaRepository()

    # Garantir que existam 3 churrasqueiras
    churras = Churrasqueira.query.all()
    if len(churras) < 3:
        # limpar e criar 3
        Churrasqueira.query.delete()
        db.session.commit()
        for i in range(1, 4):
            db.session.add(Churrasqueira(nome=f"Churrasqueira {i}"))
        db.session.commit()
        churras = Churrasqueira.query.all()

    print('Churrasqueiras:', [c.nome for c in churras])

    # Escolher data futura
    dia = date.today() + timedelta(days=5)

    # Limpar reservas desse dia
    Reserva.query.filter(Reserva.data_reserva == dia).delete()
    db.session.commit()

    # Criar uma reserva na churrasqueira 1
    r1 = Reserva(
        nome="Teste 1",
        churrasqueira_id=churras[0].id,
        data_reserva=dia,
        horario_inicio=time(8, 0),
        horario_fim=time(14, 0),
        status='ativa'
    )
    db.session.add(r1)
    db.session.commit()

    # Verificar disponibilidade para o mesmo horário - deve ser True (há churrasqueiras livres)
    disponivel, msg = repo.verificar_disponibilidade(dia, time(8, 0), time(14, 0))
    print('Após 1 reserva -> disponivel:', disponivel, msg)

    # Agora criar reservas nas outras churrasqueiras (2 e 3)
    r2 = Reserva(
        nome="Teste 2",
        churrasqueira_id=churras[1].id,
        data_reserva=dia,
        horario_inicio=time(8, 0),
        horario_fim=time(14, 0),
        status='ativa'
    )
    r3 = Reserva(
        nome="Teste 3",
        churrasqueira_id=churras[2].id,
        data_reserva=dia,
        horario_inicio=time(8, 0),
        horario_fim=time(14, 0),
        status='ativa'
    )
    db.session.add(r2)
    db.session.add(r3)
    db.session.commit()

    # Agora todas as churrasqueiras ocupadas -> deve retornar False
    disponivel2, msg2 = repo.verificar_disponibilidade(dia, time(8, 0), time(14, 0))
    print('Após 3 reservas -> disponivel:', disponivel2, msg2)
