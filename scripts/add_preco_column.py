import sqlite3
import pathlib
import sys

# Tenta usar instance/app.db; se não existir, tenta churrasqueira.db
candidates = [pathlib.Path('instance/app.db'), pathlib.Path('churrasqueira.db')]
db = next((p for p in candidates if p.exists()), None)

if db is None:
    print('ERRO: nenhum banco encontrado (instance/app.db ou churrasqueira.db). Abra o app uma vez para gerar o banco ou aponte o caminho correto.')
    sys.exit(1)

print(f'Usando DB: {db.resolve()}')

conn = sqlite3.connect(db)
cur = conn.cursor()

cur.execute("PRAGMA table_info(churrasqueiras)")
cols = {row[1] for row in cur.fetchall()}

if 'preco' in cols:
    print('Coluna preco já existe, nada a fazer.')
else:
    cur.execute("ALTER TABLE churrasqueiras ADD COLUMN preco NUMERIC DEFAULT 30.00")
    print('Coluna preco adicionada com sucesso.')

# Atualiza valores padrão (Bosque=60, demais=30)
cur.execute("UPDATE churrasqueiras SET preco = 60.00 WHERE LOWER(nome) LIKE '%bosque%'")
cur.execute("UPDATE churrasqueiras SET preco = 30.00 WHERE LOWER(nome) NOT LIKE '%bosque%'")

conn.commit()
conn.close()
print('Preços atualizados (Bosque=60, demais=30).')
print('OK: esquema e preços ajustados.')
