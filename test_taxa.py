import sys
sys.path.insert(0, '.')

from app.models import db, Taxa
from app.container import container
from flask import Flask
from config import Config

# Criar app Flask básico
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Teste 1: Query direta
    print("=== TESTE 1: Query direta no banco ===")
    taxas = Taxa.query.all()
    print(f"Total de taxas (query direta): {len(taxas)}")
    for taxa in taxas:
        print(f"  Taxa #{taxa.id}: R$ {taxa.valor} - Status: {taxa.status} - CPF: {taxa.associado_cpf}")
    
    # Teste 2: Usando o service
    print("\n=== TESTE 2: Usando taxa_service ===")
    taxa_service = container.get_taxa_service()
    taxas_service = taxa_service.listar_todas_taxas()
    print(f"Total de taxas (service): {len(taxas_service)}")
    if taxas_service:
        for t in taxas_service:
            print(f"  Taxa: {t}")
    else:
        print("  Nenhuma taxa retornada pelo service!")
