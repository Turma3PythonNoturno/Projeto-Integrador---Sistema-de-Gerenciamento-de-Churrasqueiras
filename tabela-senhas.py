import sqlite3
from werkzeug.security import generate_password_hash

NOME_DO_BANCO = "churrasqueira.db"  # <--- COLOQUE O NOME DO SEU BANCO AQUI

def criar_user_inicial():
    print("Criando o usuário adm inicial...")

    conn = sqlite3.connect('churrasqueira.db')
    cursor = conn.cursor()

    cursor.execute("INSERT INTO associados (codigo, cpf, nome) VALUES ('002', '02748489101', 'Thiago')")
    conn.commit()
    conn.close

def criar_tabela_relacional():
    print(f"--- Conectando ao banco '{'churrasqueira.db'}' ---")
    
    conn = sqlite3.connect('churrasqueira.db')
    
    # Habilita suporte a chaves estrangeiras no SQLite (por padrão vem desligado)
    conn.execute("PRAGMA foreign_keys = ON")
    cursor = conn.cursor()

    # 1. CRIAÇÃO DA NOVA TABELA COM RELACIONAMENTO
    # - cpf: É a chave que liga com a tabela 'associados'
    # - adm: Usaremos 0 para 'Usuário Comum' e 1 para 'Admin'
    sql_tabela = """
    CREATE TABLE IF NOT EXISTS login_sistema (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cpf TEXT NOT NULL UNIQUE,
        senha_hash TEXT NOT NULL,
        adm INTEGER DEFAULT 0,
        FOREIGN KEY(cpf) REFERENCES associados(cpf) ON DELETE CASCADE
    );
    """
    # Obs: ON DELETE CASCADE significa que se deletar o associado, o login some junto.
    
    try:
        cursor.execute(sql_tabela)
        print("✅ Tabela 'login_sistema' criada com sucesso.")
        print("   -> Colunas: id, cpf (FK), senha_hash, adm")

        # 2. PERGUNTA SE QUER CRIAR UM LOGIN AGORA
        resp = input("\nDeseja criar um login para um CPF existente? (s/n): ").lower()
        
        if resp == 's':
            cpf_alvo = input("Digite o CPF do associado (com ou sem pontuação): ")
            senha_plana = input("Crie uma senha: ")
            e_admin = input("É administrador? (s/n): ").lower()
            
            # Tratamento dos dados
            cpf_limpo = cpf_alvo.replace(".", "").replace("-", "")
            is_adm = 1 if e_admin == 's' else 0
            senha_cripto = generate_password_hash(senha_plana)

            # Inserção vinculada
            sql_insert = """
            INSERT INTO login_sistema (cpf, senha_hash, adm) 
            VALUES (?, ?, ?)
            """
            
            cursor.execute(sql_insert, (cpf_limpo, senha_cripto, is_adm))
            conn.commit()
            print(f"✅ Login criado para o CPF {cpf_limpo}!")

    except sqlite3.IntegrityError as e:
        print(f"❌ Erro de Integridade: {e}")
        print("Dica: Verifique se o CPF existe na tabela 'associados' ou se já tem login.")
    except sqlite3.Error as e:
        print(f"❌ Erro SQL: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    criar_user_inicial()
    criar_tabela_relacional()
    