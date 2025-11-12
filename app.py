"""
Sistema de Reserva de Churrasqueira - SINT-IFESGO

Este módulo é o ponto de entrada principal da aplicação Flask que gerencia
o sistema de reservas de churrasqueira para associados do Sindicato dos 
Trabalhadores Técnico-Administrativos em Educação das Instituições Federais 
de Ensino Superior do Estado de Goiás (SINT-IFESGO).

Funcionalidades principais:
- Gestão de associados com validação de CPF
- Verificação de adimplência com taxa sindical
- Sistema de reservas com controle de horários (08:00-18:00h)
- Cobrança de taxa de reserva (R$ 25,00)
- Sistema de boletins informativos
- Controle de pagamentos com prazo de 24h

Autor: Sistema SINT-IFESGO
Data de criação: 2024
Versão: 1.0
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

def create_app():
    """
    Factory function para criar e configurar a aplicação Flask.
    
    Esta função implementa o padrão Application Factory, criando uma instância
    da aplicação Flask com todas as configurações necessárias para o sistema
    de reservas do SINT-IFESGO.
    
    Returns:
        Flask: Instância configurada da aplicação Flask
        
    Configurações aplicadas:
    - Template folder: app/templates (templates HTML do sistema)
    - Static folder: static (arquivos CSS, JS, imagens)
    - Configurações do banco de dados SQLite
    - Inicialização das extensões (SQLAlchemy)
    - Registro dos blueprints de rotas
    - Criação automática das tabelas do banco
    """
    # Criação da instância Flask com pastas customizadas
    app = Flask(__name__, 
                template_folder='app/templates',  # Templates HTML do sistema
                static_folder='static')           # Arquivos estáticos (CSS, JS)
    
    # Carregamento das configurações específicas do SINT-IFESGO
    app.config.from_object(Config)
    
    # Inicialização das extensões do Flask
    from app.models import db
    db.init_app(app)  # SQLAlchemy para ORM do banco de dados
    
    # Registro dos blueprints (rotas organizadas)
    from app.routes import routes
    app.register_blueprint(routes)
    
    # Criação automática das tabelas do banco de dados
    with app.app_context():
        db.create_all()
        print("Banco de dados criado com sucesso!")
        print(f"Local do banco: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    return app

# Criação da instância da aplicação usando o padrão Factory
app = create_app()

if __name__ == "__main__":
    """
    Ponto de entrada da aplicação quando executada diretamente.
    
    Configurações de execução:
    - Debug mode: Habilitado para desenvolvimento
    - Host: 127.0.0.1 (localhost apenas)
    - Porta: 5000 (padrão Flask)
    
    Para produção, desabilitar debug e configurar host/porta apropriados.
    """
    print("Iniciando sistema de reserva de churrasqueira...")
    print("SINT-IFESGO - Sistema de Gestão de Reservas")
    print("Acesse: http://127.0.0.1:5000")
    print("Horário de funcionamento: 08:00 às 18:00h")
    
    # Execução da aplicação Flask
    app.run(debug=True, host='127.0.0.1', port=5000)