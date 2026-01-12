"""
Sistema de Reserva de Churrasqueira - SINT-IFESGO
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

app = Flask(__name__)
app.secret_key = 'bfdpython'

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
        Reserva,
        LoginSistema
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
                Churrasqueira(nome="Churrasqueira Bosque"),
                Churrasqueira(nome="Churrasqueira Araguaia"),
                Churrasqueira(nome="Churrasqueira Asufesgo"),
                Churrasqueira(nome="Churrasqueira Sint-UFG"),
                Churrasqueira(nome="Churrasqueira Sint-Ifes")
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
        # Criar usuário administrador de teste se não existir
        admin_login = LoginSistema.query.filter_by(cpf='12345678901').first()
        if not admin_login:
            print("Criando usuário administrador de teste...")
            admin = LoginSistema(
                cpf='12345678901',
                adm=1  # Nível administrador
            )
            admin.definir_senha('admin123')  # Senha: admin123
            db.session.add(admin)
            db.session.commit()
            print("=" * 50)
            print("USUÁRIO ADMINISTRADOR CRIADO!")
            print("=" * 50)
            print("CPF: 123.456.789-01")
            print("Senha: admin123")
            print("Nível: Administrador")
            print("=" * 50)
        else:
            print("Usuário administrador já existe")
            print("CPF: 123.456.789-01 | Senha: admin123")
    

    return app


# Criar app
app = create_app()


if __name__ == "__main__":
    print("Iniciando sistema de reserva de churrasqueira...")
    print("SINT-IFESGO - Sistema de Gestão de Reservas")
    print("Acesse: http://127.0.0.1:5000")
    print("Horário de funcionamento: 08:00 às 18:00h")

    app.run(debug=True, host='127.0.0.1', port=5000)
