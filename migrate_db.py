"""
Script para migração do banco de dados
Adiciona novos campos à tabela de associados
"""

from app import create_app
from app.models import db

app = create_app()

with app.app_context():
    print("Iniciando migração do banco de dados...")
    
    # Recriar todas as tabelas (CUIDADO: isso apagará os dados!)
    print("\nAVISO: Este script irá RECRIAR todas as tabelas.")
    print("Todos os dados existentes serão PERDIDOS!")
    resposta = input("Deseja continuar? (digite 'SIM' para confirmar): ")
    
    if resposta == 'SIM':
        print("\nRecriando tabelas...")
        db.drop_all()
        db.create_all()
        print("✓ Tabelas recriadas com sucesso!")
        print("\nNovos campos adicionados à tabela de associados:")
        print("  - codigo")
        print("  - lotacao")
        print("  - categoria")
        print("  - situacao")
        print("  - inadimplencia")
        print("  - data_ultima_sincronizacao")
        print("\n✓ Migração concluída!")
    else:
        print("\nMigração cancelada.")
