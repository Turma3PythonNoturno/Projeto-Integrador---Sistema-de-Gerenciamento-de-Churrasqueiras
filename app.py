"""
Sistema de Reserva de Churrasqueira - SINT-IFESGO
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

def create_app():
    """Factory function para criar e configurar a aplicação Flask."""
    app = Flask(
        __name__,
        template_folder='app/templates',
        static_folder='static'
    )
    
    app.config.from_object(Config)
    
    # Inicialização do DB
    from app.models import db
    db.init_app(app)

    # IMPORTANTE: importar todos os models antes do create_all()
    from app.models import (
        Associado,
        Churrasqueira,
        Reserva
    )

    # Registro dos blueprints
    from app.routes import routes
    app.register_blueprint(routes)
    
    # Criar tabelas e inserir dados iniciais
    with app.app_context():
        db.create_all()
        print("Banco de dados criado com sucesso!")
        print(f"Local do banco: {app.config['SQLALCHEMY_DATABASE_URI']}")

        # Criar churrasqueiras padrão
        total_churrasqueiras = Churrasqueira.query.count()
        if total_churrasqueiras == 0:
            print("Criando churrasqueiras padrão...")
            lista = [
                Churrasqueira(nome="Churrasqueira 1"),
                Churrasqueira(nome="Churrasqueira 2"),
                Churrasqueira(nome="Churrasqueira 3"),
            ]
            db.session.add_all(lista)
            db.session.commit()
            print("Churrasqueiras cadastradas!")
        else:
            print(f"Banco já contém {total_churrasqueiras} churrasqueiras")

        # Criar associado teste
        total_associados = Associado.query.count()
        if total_associados == 0:
            print("Criando associado de teste...")
            associado_teste = Associado(
                codigo='001',
                cpf='12345678901',
                nome='João da Silva Teste',
                categoria='SERVIDOR',
                situacao='FILIADO',
                inadimplencia='NÃO',
                email='joao.teste@sint.com.br',
                telefone='(62) 99999-9999',
                ativo=True
            )
            db.session.add(associado_teste)
            db.session.commit()
            print("Associado de teste criado!")
        else:
            print(f"Banco já contém {total_associados} associado(s)")

    return app


# Criar app
app = create_app()


if __name__ == "__main__":
    print("Iniciando sistema de reserva de churrasqueira...")
    print("SINT-IFESGO - Sistema de Gestão de Reservas")
    print("Acesse: http://127.0.0.1:5000")
    print("Horário de funcionamento: 08:00 às 18:00h")

    app.run(debug=True, host='127.0.0.1', port=5000)
