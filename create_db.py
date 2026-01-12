from app import app, db

# Importa os models para garantir que sejam criados no banco
from app.models import Churrasqueira, Reserva, Usuario  # coloque todos os models existentes

with app.app_context():
    db.create_all()
    print("Banco de dados criado com sucesso!")
