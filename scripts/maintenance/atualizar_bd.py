import sqlite3
from datetime import datetime

# --- CONFIGURAÇÃO ---
# Confirme o nome exato do seu banco
NOME_DO_BANCO = "churrasqueira.db" 

def atualizar_tabela_seguro():
    print(f"--- Conectando ao banco '{'churrasqueira'}' para correção ---")
    
    try:
        conn = sqlite3.connect('churrasqueira.db')
        cursor = conn.cursor()

        # 1. Adiciona a coluna data_criacao (SEM DEFAULT para evitar o erro)
        try:
            print("Tentando adicionar coluna 'data_criacao'...")
            # Removemos o "DEFAULT CURRENT_TIMESTAMP" daqui
            cursor.execute("ALTER TABLE login_sistema ADD COLUMN data_criacao DATETIME")
            print("✅ Coluna 'data_criacao' adicionada!")
            
            # 2. Preenche os dados existentes com a data de hoje
            # Para não ficarem com valor NULL (vazio)
            data_hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(f"UPDATE login_sistema SET data_criacao = '{data_hoje}' WHERE data_criacao IS NULL")
            print("✅ Datas antigas preenchidas com sucesso.")
            
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("⚠️ A coluna 'data_criacao' já existe. Pulando...")
            else:
                print(f"❌ Erro ao criar data_criacao: {e}")

        # 3. Adiciona a coluna ultimo_login (Essa é tranquila pois aceita vazio)
        try:
            print("Tentando adicionar coluna 'ultimo_login'...")
            cursor.execute("ALTER TABLE login_sistema ADD COLUMN ultimo_login DATETIME")
            print("✅ Coluna 'ultimo_login' adicionada!")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("⚠️ A coluna 'ultimo_login' já existe.")
            else:
                print(f"❌ Erro ao criar ultimo_login: {e}")

        conn.commit()
        conn.close()
        print("\n--- Correção finalizada! ---")
        print("Tente fazer o login novamente.")

    except sqlite3.Error as e:
        print(f"❌ Erro crítico de conexão: {e}")

if __name__ == "__main__":
    atualizar_tabela_seguro()