import sqlite3

conn = sqlite3.connect('churrasqueira.db')
cursor = conn.cursor()

# Mostrar associados antes
print("=== Associados ANTES ===")
cursor.execute('SELECT cpf, nome FROM associados')
for row in cursor.fetchall():
    print(f"CPF: {row[0]} - Nome: {row[1]}")

# Atualizar o nome para "Administrador"
print("\n=== Atualizando nome ===")
cursor.execute("UPDATE associados SET nome = 'Administrador' WHERE cpf = '12345678901'")
conn.commit()

# Mostrar associados depois
print("\n=== Associados DEPOIS ===")
cursor.execute('SELECT cpf, nome FROM associados')
for row in cursor.fetchall():
    print(f"CPF: {row[0]} - Nome: {row[1]}")

print("\n✓ Nome atualizado com sucesso!")

conn.close()
