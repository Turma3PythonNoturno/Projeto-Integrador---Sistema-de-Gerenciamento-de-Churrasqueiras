import sqlite3

conn = sqlite3.connect('churrasqueira.db')
cursor = conn.cursor()

# Adicionar o associado com o CPF que está na taxa
cpf = '06676668696'  # CPF limpo (sem formatação)
cursor.execute('''
    INSERT INTO associados (codigo, cpf, nome, categoria, situacao, inadimplencia, email, telefone, ativo)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
''', ('002', cpf, 'Maria Santos', 'SERVIDOR', 'FILIADO', 'NÃO', 'maria@example.com', '(62) 98888-8888', 1))

conn.commit()

print(f'✅ Associado adicionado: Maria Santos - CPF: {cpf}')

# Verificar
print('\n=== TODOS OS ASSOCIADOS ===')
cursor.execute('SELECT id, cpf, nome FROM associados')
for row in cursor.fetchall():
    print(f'ID: {row[0]} | CPF: "{row[1]}" | Nome: {row[2]}')

conn.close()
