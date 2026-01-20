import sqlite3

conn = sqlite3.connect('churrasqueira.db')
cursor = conn.cursor()

# Listar usuários atuais
print("=== Usuários no sistema ===")
cursor.execute('SELECT cpf, adm FROM login_sistema')
for row in cursor.fetchall():
    print(f"CPF: {row[0]} - Admin: {row[1]}")

print("\n=== Atualizando todos os usuários para admin ===")
cursor.execute('UPDATE login_sistema SET adm = 1')
conn.commit()

print("\n=== Usuários após atualização ===")
cursor.execute('SELECT cpf, adm FROM login_sistema')
for row in cursor.fetchall():
    print(f"CPF: {row[0]} - Admin: {row[1]}")

print("\n✓ Todos os usuários agora são administradores!")

conn.close()
