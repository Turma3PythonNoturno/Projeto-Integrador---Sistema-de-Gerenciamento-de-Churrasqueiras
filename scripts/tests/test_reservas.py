from app import create_app
from app.models import db, Reserva

app = create_app()

with app.app_context():
    reservas = Reserva.query.all()
    print(f'\nTotal de reservas no banco: {len(reservas)}\n')
    
    if reservas:
        for r in reservas:
            print(f'ID: {r.id}')
            print(f'Nome: {r.nome}')
            print(f'CPF: {r.cpf_associado}')
            print(f'Data: {r.data_reserva}')
            print(f'Horário: {r.horario_inicio} - {r.horario_fim}')
            print(f'Status: {r.status}')
            print('-' * 50)
    else:
        print('Nenhuma reserva encontrada no banco de dados!')
        print('O banco foi recriado, então as reservas antigas foram perdidas.')
