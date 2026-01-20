"""
Sistema de Reserva de Churrasqueira - SINT-IFESGO
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from app.utils import CPFUtils
import os

# Flag global para evitar inicialização duplicada
_inicializado = False

app = Flask(__name__)
app.secret_key = 'bfdpython'

def create_app():
    """Factory function para criar e configurar a aplicação Flask."""
    app = Flask(
        __name__,
        template_folder='app/templates',
        static_folder='static'
    )
    
    app.config.from_object(Config)
    
    # Inicialização do DB
    from app.models import db
    db.init_app(app)

    # IMPORTANTE: importar todos os models antes do create_all()
    from app.models import (
        Associado,
        Churrasqueira,
        Reserva,
        LoginSistema
    )

    # Registro dos blueprints modularizados (Phase 2 - COMPLETO)
    # routes.py legado foi completamente substituído por blueprints
    from app.blueprints import auth_bp, dashboard_bp, reservas_bp, api_bp, associados_bp, taxas_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reservas_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(associados_bp)
    app.register_blueprint(taxas_bp)
    
    # Criar tabelas e inserir dados iniciais
    # No modo debug, o Flask executa o código duas vezes:
    # 1. No processo pai (reloader) - WERKZEUG_RUN_MAIN não existe
    # 2. No processo filho (principal) - WERKZEUG_RUN_MAIN = 'true'
    # Só queremos executar a inicialização no processo principal
    is_main_process = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    is_not_debug = not app.debug
    
    # Executar apenas se estamos no processo principal
    if is_main_process or is_not_debug:
        with app.app_context():
            # Criar tabelas primeiro
            db.create_all()
            
            # Verificar se já foi inicializado checando se existem logins (exceto admin padrão)
            # Isso evita duplicação mesmo se o módulo for recarregado
            logins_existentes = LoginSistema.query.filter(LoginSistema.cpf != '12345678901').count()
            ja_inicializado = logins_existentes > 0
            
            if ja_inicializado:
                # Já foi inicializado: garantir que o nome do associado admin esteja correto
                admin_assoc = Associado.query.filter_by(cpf='12345678901').first()
                if admin_assoc and admin_assoc.nome != 'Administrador':
                    admin_assoc.nome = 'Administrador'
                    db.session.commit()
                # Apenas criar tabelas se necessário e sair
                return app
            
            # Primeira inicialização - executar todo o processo
            print("Banco de dados criado com sucesso!")
            print(f"Local do banco: {app.config['SQLALCHEMY_DATABASE_URI']}")

            # Criar churrasqueiras padrão
            total_churrasqueiras = Churrasqueira.query.count()
            if total_churrasqueiras == 0:
                print("Criando churrasqueiras padrão...")
                lista = [
                    Churrasqueira(nome="Churrasqueira Bosque"),
                    Churrasqueira(nome="Churrasqueira Araguaia"),
                    Churrasqueira(nome="Churrasqueira Asufesgo"),
                    Churrasqueira(nome="Churrasqueira Sint-UFG"),
                    Churrasqueira(nome="Churrasqueira Sint-Ifes")
                ]
                db.session.add_all(lista)
                db.session.commit()
                print("Churrasqueiras cadastradas!")
            else:
                print(f"Banco já contém {total_churrasqueiras} churrasqueiras")

            # Criar associado teste
            total_associados = Associado.query.count()
            if total_associados == 0:
                print("Criando associado de teste...")
                associado_teste = Associado(
                    codigo='001',
                    cpf='12345678901',
                    nome='Administrador',
                    categoria='SERVIDOR',
                    situacao='FILIADO',
                    inadimplencia='NÃO',
                    email='admin@sint.com.br',
                    telefone='(62) 99999-9999',
                    ativo=True
                )
                db.session.add(associado_teste)
                db.session.commit()
                print("Associado de teste criado!")
            else:
                print(f"Banco já contém {total_associados} associado(s)")
            # Criar usuário administrador de teste se não existir
            admin_login = LoginSistema.query.filter_by(cpf='12345678901').first()
            if not admin_login:
                print("Criando usuário administrador de teste...")
                admin = LoginSistema(
                    cpf='12345678901',
                    adm=1  # Nível administrador
                )
                admin.definir_senha('admin123')  # Senha: admin123
                db.session.add(admin)
                db.session.commit()
                print("=" * 50)
                print("USUÁRIO ADMINISTRADOR CRIADO!")
                print("=" * 50)
                print("CPF: 123.456.789-01")
                print("Senha: admin123")
                print("Nível: Administrador")
                print("=" * 50)
            else:
                print("Usuário administrador já existe")
                print("CPF: 123.456.789-01 | Senha: admin123")
            
            # Sincronizar associados da API e criar logins
            # Verificar arquivo de controle para evitar sincronizar repetidamente
            sync_control_file = os.path.join(os.path.dirname(__file__), '.sync_done')
            
            if not os.path.exists(sync_control_file):
                print("\n" + "=" * 50)
                print("SINCRONIZANDO ASSOCIADOS DA API...")
                print("=" * 50)
                try:
                    from app.services.associado_service import AssociadoService
                    import requests
                    
                    associado_service = AssociadoService()
                    config = Config()
                    
                    # Buscar associados da API
                    payload = {
                        **config.WEB_SERVICE_CREDENTIALS,
                        "acao": "listar_associados"
                    }
                    
                    response = requests.post(
                        config.WEB_SERVICE_URL,
                        json=payload,
                        timeout=config.WEB_SERVICE_TIMEOUT,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    associados_criados = 0
                    logins_criados = 0
                    logins_atualizados = 0
                    batch_size = 100  # Fazer commit a cada 100 registros
                    contador = 0
                    
                    if response.status_code == 200:
                        data = response.json()
                        associados_raw = data.get('data', []) if data.get('status') == 'success' else data.get('associados', [])
                        
                        print(f"Total de associados encontrados na API: {len(associados_raw)}")
                        print("Sincronizando em lotes de 100 registros...")
                        
                        for assoc in associados_raw:
                            try:
                                # Limpar CPF
                                cpf_limpo = CPFUtils.limpar(assoc.get('cpf', ''))
                                
                                if len(cpf_limpo) != 11:
                                    continue  # CPF inválido, pular
                                
                                # Importar/atualizar associado no banco
                                resultado = associado_service.importar_da_api(assoc)
                                if resultado.get('acao') == 'criado':
                                    associados_criados += 1
                                
                                # Criar ou atualizar login
                                login_existente = LoginSistema.query.filter_by(cpf=cpf_limpo).first()
                                
                                if not login_existente:
                                    # Criar novo login
                                    # Senha = 4 primeiros dígitos do CPF
                                    senha = cpf_limpo[:4]
                                    
                                    novo_login = LoginSistema(
                                        cpf=cpf_limpo,
                                        adm=0  # Associado comum, não admin
                                    )
                                    novo_login.definir_senha(senha)
                                    db.session.add(novo_login)
                                    logins_criados += 1
                                else:
                                    # Login já existe, apenas garantir que não seja admin (exceto o admin padrão)
                                    if cpf_limpo != '12345678901' and login_existente.adm == 1:
                                        login_existente.adm = 0
                                        logins_atualizados += 1
                            
                            except Exception as e:
                                print(f"Erro ao processar associado {assoc.get('cpf', 'N/A')}: {str(e)}")
                                continue
                            
                            # Fazer commit a cada batch_size registros
                            contador += 1
                            if contador % batch_size == 0:
                                db.session.commit()
                                print(f"  ✓ {contador} registros processados...")
                        
                        # Commit final para registros restantes
                        db.session.commit()
                        
                        print(f"\n✓ Associados criados/atualizados: {associados_criados}")
                        print(f"✓ Logins criados: {logins_criados}")
                        print(f"✓ Logins atualizados: {logins_atualizados}")
                        print("\n" + "=" * 50)
                        print("SINCRONIZAÇÃO CONCLUÍDA!")
                        print("=" * 50)
                        print("\nRegra de login para associados:")
                        print("- Usuário: CPF (apenas números)")
                        print("- Senha: 4 primeiros dígitos do CPF")
                        print("=" * 50 + "\n")
                        
                        # Criar arquivo de controle
                        with open(sync_control_file, 'w') as f:
                            f.write('Sincronização concluída')
                    else:
                        print(f"Erro ao buscar associados da API: Status {response.status_code}")
                        print("Os associados serão sincronizados quando a API estiver disponível.")
                
                except Exception as e:
                    print(f"Erro ao sincronizar associados: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    db.session.rollback()
                    print("A aplicação continuará funcionando, mas os associados não foram sincronizados.")
            else:
                print("✓ Sincronização já realizada anteriormente. Pulando...")
    

    return app


# Criar app
app = create_app()


if __name__ == "__main__":
    print("Iniciando sistema de reserva de churrasqueira...")
    print("SINT-IFESGO - Sistema de Gestão de Reservas")
    print("Acesse: http://127.0.0.1:5000")
    print("Horário de funcionamento: 08:00 às 18:00h")

    app.run(debug=True, host='127.0.0.1', port=5000)
