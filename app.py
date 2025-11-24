"""
Sistema de Reserva de Churrasqueira - SINT-IFESGO
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

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
        from app.models import Associado
        total_associados = Associado.query.count()
        if total_associados == 0:
            print("Criando associado de teste...")
            associado_teste = Associado(
                cpf='12345678901',
                nome='João da Silva Teste',
                email='joao.teste@sint.com.br',
                telefone='(62) 99999-9999',
                status_adimplencia='adimplente',
                ativo=True
            )
            db.session.add(associado_teste)
            db.session.commit()
            print("Associado de teste criado!")
        else:
            print(f"Banco já contém {total_associados} associado(s)")
    
    return app

# Criação da instância da aplicação
app = create_app()

if __name__ == "__main__":
    print("Iniciando sistema de reserva de churrasqueira...")
    print("SINT-IFESGO - Sistema de Gestão de Reservas")
    print("Acesse: http://127.0.0.1:5000")
    print("Horário de funcionamento: 08:00 às 18:00h")
    
    app.run(debug=True, host='127.0.0.1', port=5000)