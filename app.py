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
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='static')
    
    app.config.from_object(Config)
    
    # Inicialização das extensões do Flask
    from app.models import db
    db.init_app(app)
    
    # Registro dos blueprints
    from app.routes import routes
    app.register_blueprint(routes)
    
    # Criação das tabelas do banco
    with app.app_context():
        db.create_all()
        print("Banco de dados criado com sucesso!")
        print(f"Local do banco: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        # Verificar e criar associado de teste se necessário
        from app.models import Associado, LoginSistema
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

# Criação da instância da aplicação
app = create_app()

if __name__ == "__main__":
    print("Iniciando sistema de reserva de churrasqueira...")
    print("SINT-IFESGO - Sistema de Gestão de Reservas")
    print("Acesse: http://127.0.0.1:5000")
    print("Horário de funcionamento: 08:00 às 18:00h")
    
    app.run(debug=True, host='127.0.0.1', port=5000)