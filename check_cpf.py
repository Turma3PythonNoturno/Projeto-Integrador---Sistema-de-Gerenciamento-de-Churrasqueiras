import sqlite3

conn = sqlite3.connect('churrasqueira.db')
cursor = conn.cursor()

print('=== ASSOCIADOS ===')
for row in cursor.execute('SELECT id, cpf, nome FROM associados'):
    print(f'ID: {row[0]} | CPF: "{row[1]}" | Nome: {row[2]}')

print('\n=== TAXAS ===')
for row in cursor.execute('SELECT id, associado_cpf, valor FROM taxas'):
    print(f'ID: {row[0]} | CPF: "{row[1]}" | Valor: {row[2]}')

conn.close()
