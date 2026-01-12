import sqlite3

conn = sqlite3.connect('churrasqueira.db')
cursor = conn.cursor()

print('=== RESERVAS ===')
cursor.execute('SELECT * FROM reservas')
cols = [description[0] for description in cursor.description]
print(f'Colunas: {cols}')
for row in cursor.fetchall():
    print(f'Dados: {row}')

print('\n=== TAXAS ===')
cursor.execute('SELECT * FROM taxas')
cols = [description[0] for description in cursor.description]
print(f'Colunas: {cols}')
for row in cursor.fetchall():
    print(f'Dados: {row}')

conn.close()
