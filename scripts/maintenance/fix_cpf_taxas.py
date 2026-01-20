import sqlite3
import re

def limpar_cpf(cpf):
    """Remove formatação do CPF"""
    if not cpf:
        return cpf
    return re.sub(r'[^\d]', '', cpf)

conn = sqlite3.connect('churrasqueira.db')
cursor = conn.cursor()

print('=== ATUALIZANDO CPFs NAS TAXAS ===\n')

# Buscar todas as taxas com CPF formatado
cursor.execute('SELECT id, associado_cpf FROM taxas')
taxas = cursor.fetchall()

for taxa_id, cpf_original in taxas:
    cpf_limpo = limpar_cpf(cpf_original)
    if cpf_original != cpf_limpo:
        cursor.execute('UPDATE taxas SET associado_cpf = ? WHERE id = ?', (cpf_limpo, taxa_id))
        print(f'Taxa ID {taxa_id}: "{cpf_original}" -> "{cpf_limpo}"')
    else:
        print(f'Taxa ID {taxa_id}: CPF já está limpo ("{cpf_original}")')

conn.commit()

print('\n=== VERIFICANDO RESULTADO ===\n')
cursor.execute('SELECT id, associado_cpf, valor FROM taxas')
for row in cursor:
    print(f'Taxa ID: {row[0]} | CPF: "{row[1]}" | Valor: R$ {row[2]}')

conn.close()
print('\n✅ Atualização concluída!')
