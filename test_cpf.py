import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Importar diretamente do app.py
from app import create_app
from app.models import db, Associado, Taxa

app = create_app()

with app.app_context():
    print("=== TESTANDO CPF ===")
    
    # Listar todos os associados
    print("\nTODOS OS ASSOCIADOS:")
    associados = Associado.query.all()
    for a in associados:
        print(f"  ID: {a.id} | CPF: '{a.cpf}' | Nome: {a.nome}")
    
    # Pegar a taxa
    print("\nTAXA:")
    taxa = Taxa.query.first()
    if taxa:
        print(f"  ID: {taxa.id}")
        print(f"  CPF original: '{taxa.associado_cpf}'")
        print(f"  Tipo do CPF: {type(taxa.associado_cpf)}")
        
        # Limpar CPF
        cpf_limpo = taxa.associado_cpf.replace('.', '').replace('-', '') if taxa.associado_cpf else None
        print(f"  CPF limpo: '{cpf_limpo}'")
        print(f"  Tipo do CPF limpo: {type(cpf_limpo)}")
        
        # Buscar associado
        print("\nBUSCANDO ASSOCIADO:")
        associado = Associado.query.filter_by(cpf=cpf_limpo).first()
        print(f"  Resultado: {associado}")
        if associado:
            print(f"  Nome: {associado.nome}")
        else:
            print("  NENHUM ASSOCIADO ENCONTRADO!")
            
            # Tentar buscar com CPF formatado
            print("\nTentando com CPF formatado:")
            associado2 = Associado.query.filter_by(cpf=taxa.associado_cpf).first()
            print(f"  Resultado: {associado2}")
            if associado2:
                print(f"  Nome: {associado2.nome}")
