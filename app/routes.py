from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, get_flashed_messages
from datetime import datetime, date, time, timedelta
from app.container import container
from app.models import db, Reserva, LoginSistema, Associado, TokenRecuperacaoSenha

routes = Blueprint('routes', __name__)

# Obter serviços do container
reserva_service = container.get_reserva_service()
associado_service = container.get_associado_service()
taxa_service = container.get_taxa_service()

@routes.route('/', methods=['GET', 'POST'])
def login():
    if 'usuario_logado' in session:
        return redirect(url_for('routes.inicio'))
    
    if request.method == 'POST':
        # 1. Pega os dados do HTML
        cpf_form = request.form.get('cpf_associado')
        senha_form = request.form.get('password')

        # 2. Limpeza do CPF (Remove pontos e traçõs para bater com o banco)
        cpf_limpo = cpf_form.replace('.', '').replace('-', '')

        # 3. Busca o usuário da tabela de login.
        usuario_login = LoginSistema.query.filter_by(cpf=cpf_limpo).first()

        # 4. Validação: Verifica se o usuário existe e se a senha está correta.
        if usuario_login and usuario_login.verificar_senha(senha_form):
            
            # --- LOGIN SUCESSO---

            #Criamos a "Sessão".
            session['usuario_logado'] = True
            session['cpf'] = usuario_login.cpf
            session['is_admin'] = usuario_login.is_admin()

            #Pega o nome através do relacionamento 'associado_obj' criado no Model
            #o .split([0]) usado para pegar somente o primeiro nome para usar no menu.
            nome_completo = usuario_login.associado_obj.nome
            session['nome_usuario'] = nome_completo.split()[0]

            flash(f'Bem-vindo(a), {session["nome_usuario"]}!', 'success')

            return redirect(url_for('routes.inicio'))
        
        else:
            flash('CPF ou senha incorretos.', 'danger')

    return render_template('login.html')

@routes.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema', 'info')
    return redirect(url_for('routes.login'))


@routes.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    """Página para solicitar recuperação de senha"""
    if request.method == 'POST':
        cpf_form = request.form.get('cpf')
        telefone_form = request.form.get('telefone')
        
        if not cpf_form or not telefone_form:
            flash('CPF e telefone são obrigatórios', 'danger')
            return render_template('esqueci_senha.html')
        
        # Limpa o CPF e telefone
        cpf_limpo = cpf_form.replace('.', '').replace('-', '')
        telefone_limpo = telefone_form.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
        
        # Verifica se o associado existe
        associado = Associado.query.filter_by(cpf=cpf_limpo).first()
        if not associado:
            flash('CPF não encontrado no sistema', 'danger')
            return render_template('esqueci_senha.html')
        
        # Verifica se o telefone está correto
        telefone_cadastrado = associado.telefone.replace('(', '').replace(')', '').replace(' ', '').replace('-', '') if associado.telefone else ''
        if telefone_cadastrado != telefone_limpo:
            flash('Telefone não corresponde ao cadastro', 'danger')
            return render_template('esqueci_senha.html')
        
        # Verifica se existe login cadastrado
        login = LoginSistema.query.filter_by(cpf=cpf_limpo).first()
        if not login:
            flash('Usuário não possui login cadastrado', 'danger')
            return render_template('esqueci_senha.html')
        
        try:
            # Gera token de recuperação
            token_obj = TokenRecuperacaoSenha.criar_token(cpf_limpo)
            
            # TODO: Enviar email com link de recuperação
            # Por enquanto, vamos exibir o link na tela (desenvolvimento)
            link_recuperacao = url_for('routes.resetar_senha', token=token_obj.token, _external=True)
            
            # Preparar telefone para WhatsApp (remove formatação)
            telefone_whatsapp = associado.telefone.replace('(', '').replace(')', '').replace(' ', '').replace('-', '') if associado.telefone else None
            
            # Retorna para a página com o link gerado
            return render_template('esqueci_senha.html', 
                                 link_gerado=link_recuperacao,
                                 telefone_whatsapp=telefone_whatsapp,
                                 nome_associado=associado.nome,
                                 sucesso=True)
            
        except Exception as e:
            flash(f'Erro ao gerar token: {str(e)}', 'danger')
        
        return render_template('esqueci_senha.html')
    
    return render_template('esqueci_senha.html')


@routes.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def resetar_senha(token):
    """Página para resetar senha com token"""
    # Busca o token no banco
    token_obj = TokenRecuperacaoSenha.query.filter_by(token=token).first()
    
    if not token_obj:
        flash('Token inválido ou não encontrado', 'danger')
        return redirect(url_for('routes.login'))
    
    if not token_obj.is_valido():
        flash('Token expirado ou já utilizado. Solicite uma nova recuperação.', 'warning')
        return redirect(url_for('routes.esqueci_senha'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirma_senha = request.form.get('confirma_senha')
        
        # Validações
        if not nova_senha or not confirma_senha:
            flash('Preencha todos os campos', 'danger')
            return render_template('resetar_senha.html', token=token)
        
        if len(nova_senha) < 6:
            flash('A senha deve ter no mínimo 6 caracteres', 'danger')
            return render_template('resetar_senha.html', token=token)
        
        if nova_senha != confirma_senha:
            flash('As senhas não coincidem', 'danger')
            return render_template('resetar_senha.html', token=token)
        
        try:
            # Busca o login do usuário
            login = LoginSistema.query.filter_by(cpf=token_obj.cpf).first()
            if not login:
                flash('Usuário não encontrado', 'danger')
                return redirect(url_for('routes.login'))
            
            # Atualiza a senha
            login.definir_senha(nova_senha)
            
            # Marca o token como usado
            token_obj.marcar_como_usado()
            
            db.session.commit()
            
            flash('Senha alterada com sucesso! Faça login com sua nova senha.', 'success')
            return redirect(url_for('routes.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao resetar senha: {str(e)}', 'danger')
            return render_template('resetar_senha.html', token=token)
    
    # GET - exibe o formulário
    associado = Associado.query.filter_by(cpf=token_obj.cpf).first()
    return render_template('resetar_senha.html', token=token, nome=associado.nome if associado else 'Usuário')


@routes.route('/inicio')
def inicio():
    """Página inicial do sistema SINT-IFESGO"""
    try:
        return render_template('inicio.html')
    except Exception as e:
        print(f"\n!!! ERRO ao carregar página inicial: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return render_template('inicio.html', erro=f"Erro ao carregar página: {str(e)}")


@routes.route('/nova-reserva')
def nova_reserva():
    """Página para fazer nova reserva"""
    return render_template('nova_reserva.html')


@routes.route('/reservas')
def listar_reservas():
    """Página para listar todas as reservas"""
    try:
        # Listar TODAS as reservas, não apenas futuras
        reservas_data = reserva_service.listar_todas_reservas()
        
        print(f"\n=== DEBUG RESERVAS ===")
        print(f"Total de reservas encontradas: {len(reservas_data)}")
        for r in reservas_data:
            print(f"Reserva: {r.get('nome')} - {r.get('data_reserva')}")
        print(f"=== FIM DEBUG ===\n")
        
        # Converter para objetos compatíveis com template
        reservas = []
        for reserva_dict in reservas_data:
            # Criar um objeto simples que tem o método to_dict
            class ReservaView:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)
                
                def to_dict(self):
                    return reserva_dict
            
            reservas.append(ReservaView(reserva_dict))
        
        return render_template('lista_reservas.html', reservas=reservas)
    except Exception as e:
        print(f"\n!!! ERRO AO LISTAR RESERVAS: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return render_template('lista_reservas.html', 
                             reservas=[], 
                             erro=f"Erro ao carregar reservas: {str(e)}")


@routes.route('/api/verificar-disponibilidade')
def verificar_disponibilidade():
    """API para verificar disponibilidade de horários"""
    data_str = request.args.get('data')
    horario_inicio_str = request.args.get('horario_inicio')
    horario_fim_str = request.args.get('horario_fim')
    
    if not all([data_str, horario_inicio_str, horario_fim_str]):
        return jsonify({
            'disponivel': False, 
            'mensagem': 'Parâmetros obrigatórios: data, horario_inicio, horario_fim'
        }), 400
    
    try:
        resultado = reserva_service.verificar_disponibilidade(
            data_str, horario_inicio_str, horario_fim_str
        )
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'disponivel': False, 
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@routes.route('/api/criar-reserva', methods=['POST'])
def criar_reserva():
    """API para criar nova reserva"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                'sucesso': False, 
                'mensagem': 'Dados JSON são obrigatórios'
            }), 400
        
        resultado = reserva_service.criar_reserva(dados)
        
        if resultado['sucesso']:
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'sucesso': False, 
            'mensagem': f'Erro interno do servidor: {str(e)}'
        }), 500


@routes.route('/api/cancelar-reserva/<int:reserva_id>', methods=['POST'])
def cancelar_reserva(reserva_id):
    """API para cancelar uma reserva"""
    try:
        dados = request.get_json() or {}
        email_confirmacao = dados.get('email')
        
        resultado = reserva_service.cancelar_reserva(reserva_id, email_confirmacao)
        
        if resultado['sucesso']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'sucesso': False, 
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@routes.route('/api/listar-reservas', methods=['GET'])
def api_listar_reservas():
    """API para listar todas as reservas"""
    try:
        reservas = reserva_service.listar_reservas_futuras()
        return jsonify({
            'sucesso': True,
            'reservas': reservas
        })
    except Exception as e:
        return jsonify({
            'sucesso': False, 
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@routes.route('/api/estatisticas')
def obter_estatisticas():
    """API para obter estatísticas"""
    try:
        stats = reserva_service.obter_estatisticas()
        return jsonify({
            'sucesso': True,
            'estatisticas': stats
        })
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao obter estatísticas: {str(e)}'
        }), 500


@routes.route('/testar-bd')
def testar_bd():
    """Rota para testar o banco de dados"""
    try:
        # Buscar todas as reservas existentes usando o modelo SQLAlchemy
        reservas = Reserva.query.all()
        
        # Se não há reservas, criar uma de teste
        if len(reservas) == 0:
            reserva_teste = Reserva(
                nome="Maria Silva",

                data_reserva=date.today() + timedelta(days=1),
                horario_inicio=time(14, 0),
                horario_fim=time(18, 0),
                email="maria@email.com",
                numero_convidados=8,
                observacoes="Aniversário da família"
            )
            
            db.session.add(reserva_teste)
            db.session.commit()
            
            return "Banco funcionando! Reserva de teste criada com sucesso!"
        else:
            detalhes = "<br>".join([
                f"• {r.nome} - {r.data_reserva.strftime('%d/%m/%Y')} "
                f"das {r.horario_inicio} às {r.horario_fim}" 
                for r in reservas
            ])
            return f"Banco funcionando! Total de reservas: {len(reservas)}<br><br><strong>Reservas:</strong><br>{detalhes}"
        
    except Exception as e:
        return f"Erro no banco: {str(e)}"


@routes.route('/estatisticas')
def pagina_estatisticas():
    """Página de estatísticas"""
    try:
        stats = reserva_service.obter_estatisticas()
        return render_template('estatisticas.html', stats=stats)
    except Exception as e:
        return render_template('estatisticas.html', 
                             stats={}, 
                             erro=f"Erro ao carregar estatísticas: {str(e)}")


# === NOVAS ROTAS SINT-IFESGO ===

@routes.route('/associados')
def listar_associados():
    """Lista todos os associados - busca da API"""
    try:
        # Buscar dados da API
        import requests
        from config import Config
        
        config = Config()
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
        
        associados = []
        if response.status_code == 200:
            data = response.json()
            associados_raw = data.get('data', []) if data.get('status') == 'success' else data.get('associados', [])
            
            # Padronizar dados
            for assoc in associados_raw:
                cpf_limpo = ''.join(filter(str.isdigit, assoc.get('cpf', '')))
                inadimplencia = str(assoc.get('inadimplencia', 'SIM') or 'SIM').upper()
                
                associados.append({
                    'id': assoc.get('id'),
                    'codigo': assoc.get('codigo', ''),
                    'cpf': cpf_limpo,
                    'cpf_formatado': f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}" if len(cpf_limpo) == 11 else cpf_limpo,
                    'nome': assoc.get('nome', ''),
                    'lotacao': assoc.get('lotacao', ''),
                    'categoria': assoc.get('categoria', ''),
                    'situacao': assoc.get('situacao', ''),
                    'inadimplencia': inadimplencia,
                    'status_adimplencia': 'adimplente' if inadimplencia == 'NÃO' else 'inadimplente',
                    'status_display': 'Adimplente' if inadimplencia == 'NÃO' else 'Inadimplente',
                    'pode_reservar': inadimplencia == 'NÃO'
                })
        
        # Calcular estatísticas
        total = len(associados)
        adimplentes = len([a for a in associados if a['inadimplencia'] == 'NÃO'])
        inadimplentes = total - adimplentes
        
        estatisticas = {
            'total_associados': total,
            'adimplentes': adimplentes,
            'inadimplentes': inadimplentes,
            'percentual_adimplencia': round((adimplentes / total * 100) if total > 0 else 0, 1)
        }
        
        print(f"\n=== ASSOCIADOS DA API ===")
        print(f"Total: {total}")
        print(f"Adimplentes: {adimplentes}")
        print(f"Inadimplentes: {inadimplentes}")
        print(f"=== FIM ===\n")
        
        return render_template('associados.html', 
                             associados=associados, 
                             estatisticas=estatisticas)
    except Exception as e:
        print(f"\n!!! ERRO: {str(e)}\n")
        import traceback
        traceback.print_exc()
        
        # Estatísticas vazias em caso de erro
        estatisticas_vazia = {
            'total_associados': 0,
            'adimplentes': 0, 
            'inadimplentes': 0,
            'percentual_adimplencia': 0
        }
        return render_template('associados.html', 
                             associados=[], 
                             estatisticas=estatisticas_vazia,
                             erro=f"Erro ao carregar associados: {str(e)}")


@routes.route('/associado/novo')
def novo_associado():
    """Página para cadastrar novo associado"""
    return render_template('novo_associado.html')


@routes.route('/api/associado/criar', methods=['POST'])
def criar_associado():
    """API para criar novo associado"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Dados JSON são obrigatórios'
            }), 400
        
        resultado = associado_service.criar_associado(dados)
        
        if resultado['sucesso']:
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro interno do servidor: {str(e)}'
        }), 500


@routes.route('/api/associado/importar-api', methods=['POST'])
def importar_associado_api():
    """API para importar associados da API externa"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Dados JSON são obrigatórios'
            }), 400
        
        # Se for uma lista de associados
        if isinstance(dados, list):
            importados = 0
            atualizados = 0
            erros = []
            
            for associado_api in dados:
                try:
                    resultado = associado_service.importar_da_api(associado_api)
                    if resultado['sucesso']:
                        if resultado.get('acao') == 'criado':
                            importados += 1
                        else:
                            atualizados += 1
                except Exception as e:
                    erros.append(f"CPF {associado_api.get('cpf')}: {str(e)}")
            
            return jsonify({
                'sucesso': True,
                'importados': importados,
                'atualizados': atualizados,
                'erros': erros,
                'mensagem': f'{importados} novos associados importados, {atualizados} atualizados'
            })
        else:
            # Um único associado
            resultado = associado_service.importar_da_api(dados)
            return jsonify(resultado)
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao importar: {str(e)}'
        }), 500


@routes.route('/api/associado/verificar/<cpf>')
def verificar_associado(cpf):
    """API para verificar status de associado"""
    try:
        associado = associado_service.buscar_por_cpf(cpf)
        
        if not associado:
            return jsonify({
                'encontrado': False,
                'mensagem': 'CPF não encontrado no cadastro de associados'
            }), 404
        
        adimplente, mensagem = associado_service.verificar_adimplencia(cpf)
        
        return jsonify({
            'encontrado': True,
            'associado': associado,
            'adimplente': adimplente,
            'mensagem': mensagem
        })
        
    except Exception as e:
        return jsonify({
            'encontrado': False,
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@routes.route('/taxas')
def listar_taxas():
    """Lista taxas do sistema"""
    cpf_associado = request.args.get('cpf')  # Opcional
    
    # Lista TODAS as taxas, não apenas as pendentes
    if cpf_associado:
        taxas = taxa_service.listar_por_associado(cpf_associado)
    else:
        taxas = taxa_service.listar_todas_taxas()
    
    print(f"\n=== DEBUG TAXAS ===")
    print(f"Total de taxas encontradas: {len(taxas)}")
    print(f"Taxas: {taxas}")
    
    # Calcular estatísticas básicas para o template
    total_recebido = sum(float(t.get('valor', 0)) for t in taxas if t.get('status') == 'pago')
    total_pendente = sum(float(t.get('valor', 0)) for t in taxas if t.get('status') == 'pendente')
    total_vencido = sum(float(t.get('valor', 0)) for t in taxas if t.get('status') == 'vencido')
    
    print(f"\n=== ESTATÍSTICAS CALCULADAS ===")
    print(f"Total Recebido: R$ {total_recebido}")
    print(f"Total Pendente: R$ {total_pendente}")
    print(f"Total Vencido: R$ {total_vencido}")
    print(f"Total de Taxas: {len(taxas)}")
    
    estatisticas = {
        'total_recebido': total_recebido,
        'total_pendente': total_pendente,
        'total_vencido': total_vencido,
        'total_taxas': len(taxas)
    }
    
    print(f"\n=== ANTES DO RENDER ===")
    print(f"Estatísticas sendo enviadas: {estatisticas}")
    print(f"Taxas sendo enviadas: {len(taxas)} itens")
    
    return render_template('taxas.html', 
                         taxas=taxas, 
                         cpf_filtro=cpf_associado,
                         estatisticas=estatisticas)


@routes.route('/api/taxa/confirmar-pagamento-old', methods=['POST'])
def confirmar_pagamento_taxa_old():
    """API para confirmar pagamento de taxa (versão antiga)"""
    try:
        dados = request.get_json()
        
        if not dados or not dados.get('taxa_id'):
            return jsonify({
                'sucesso': False,
                'mensagem': 'ID da taxa é obrigatório'
            }), 400
        
        taxa_id = dados['taxa_id']
        codigo_transacao = dados.get('codigo_transacao')
        
        resultado = taxa_service.confirmar_pagamento(taxa_id, codigo_transacao)
        
        if resultado['sucesso']:
            return jsonify(resultado), 200
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro interno do servidor: {str(e)}'
        }), 500


@routes.route('/minha-conta/<cpf>')
def minha_conta(cpf):
    """Página da conta do associado"""
    try:
        # Buscar dados do associado
        associado = associado_service.buscar_por_cpf(cpf)
        
        if not associado:
            return render_template('erro.html', 
                                 mensagem="CPF não encontrado no sistema"), 404
        
        # Buscar reservas do associado
        # TODO: Implementar método no reserva_service para buscar por CPF
        
        # Buscar taxas do associado
        taxas = taxa_service.listar_por_associado(cpf)
        
        return render_template('minha_conta.html', 
                             associado=associado,
                             taxas=taxas)
        
    except Exception as e:
        return render_template('erro.html',
                             mensagem=f"Erro ao carregar conta: {str(e)}"), 500


# === ROTAS API PARA OS TEMPLATES ADMINISTRATIVOS ===

@routes.route('/api/associado/buscar', methods=['GET'])
def api_buscar_associado():
    """API para buscar associado por CPF"""
    cpf = request.args.get('cpf', '').strip()
    if not cpf:
        return jsonify({'sucesso': False, 'mensagem': 'CPF é obrigatório'}), 400
    
    try:
        associado = associado_service.buscar_por_cpf(cpf)
        if not associado:
            return jsonify({'sucesso': False, 'mensagem': 'Associado não encontrado'}), 404
        
        return jsonify({'sucesso': True, 'associado': associado})
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@routes.route('/api/associado/listar', methods=['GET'])
def api_listar_associados():
    """API para listar todos os associados com filtros"""
    try:
        # Parâmetros de filtro
        status = request.args.get('status', '')  # adimplente, inadimplente
        busca = request.args.get('busca', '')    # busca por nome/cpf
        
        associados = associado_service.listar_todos()
        
        # Aplicar filtros se necessário
        if status:
            associados = [a for a in associados if a.get('status_adimplencia') == status]
        
        if busca:
            busca_lower = busca.lower()
            associados = [a for a in associados 
                         if busca_lower in a.get('nome', '').lower() or 
                            busca_lower in a.get('cpf', '')]
        
        return jsonify({'sucesso': True, 'associados': associados})
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@routes.route('/api/associado/estatisticas', methods=['GET'])
def api_estatisticas_associados():
    """API para obter estatísticas de associados"""
    try:
        associados = associado_service.listar_todos()
        
        total = len(associados)
        adimplentes = len([a for a in associados if a.get('status_adimplencia') == 'adimplente'])
        inadimplentes = total - adimplentes
        
        stats = {
            'total_associados': total,
            'adimplentes': adimplentes,
            'inadimplentes': inadimplentes,
            'percentual_adimplencia': round((adimplentes / total * 100) if total > 0 else 0, 1)
        }
        
        return jsonify({'sucesso': True, 'estatisticas': stats})
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@routes.route('/api/associado/buscar/<cpf>', methods=['GET'])
def api_buscar_associado_por_cpf(cpf):
    """API para buscar associado por CPF específico"""
    try:
        associado_dict = associado_service.buscar_por_cpf(cpf)
        
        if not associado_dict:
            return jsonify({'sucesso': False, 'mensagem': 'Associado não encontrado'}), 404
            
        return jsonify({'sucesso': True, 'associado': associado_dict})
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@routes.route('/api/associado/detalhes/<cpf>', methods=['GET'])
def api_detalhes_associado(cpf):
    """API para obter detalhes completos do associado"""
    try:
        associado_dict = associado_service.buscar_por_cpf(cpf)
        
        if not associado_dict:
            return jsonify({'sucesso': False, 'mensagem': 'Associado não encontrado'}), 404
        
        # Garantir que todos os campos estejam presentes
        detalhes = {
            'cpf': associado_dict.get('cpf', ''),
            'cpf_formatado': associado_dict.get('cpf_formatado', associado_dict.get('cpf', '')),
            'nome': associado_dict.get('nome', ''),
            'email': associado_dict.get('email', ''),
            'telefone': associado_dict.get('telefone', ''),
            'status_adimplencia': associado_dict.get('status_adimplencia', 'inadimplente'),
            'status_display': 'Adimplente' if associado_dict.get('status_adimplencia') == 'adimplente' else 'Inadimplente',
            'data_cadastro': associado_dict.get('data_cadastro', 'Não disponível'),
            'data_ultimo_pagamento': associado_dict.get('data_ultimo_pagamento', 'Nunca'),
            'pode_reservar': associado_dict.get('adimplente', False) or associado_dict.get('status_adimplencia') == 'adimplente',
            'ativo': associado_dict.get('ativo', True),
            'categoria': associado_dict.get('categoria', ''),
            'lotacao': associado_dict.get('lotacao', ''),
            'situacao': associado_dict.get('situacao', associado_dict.get('situacao_sindical', '')),
            'origem': associado_dict.get('origem', 'desconhecida')
        }
        
        return jsonify({'sucesso': True, 'detalhes': detalhes})
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@routes.route('/api/associado/marcar-adimplente/<cpf>', methods=['POST'])
def api_marcar_adimplente(cpf):
    """API para marcar associado como adimplente"""
    try:
        # Buscar o associado
        associado_dict = associado_service.buscar_por_cpf(cpf)
        
        if not associado_dict:
            return jsonify({'sucesso': False, 'mensagem': 'Associado não encontrado'}), 404
        
        # Atualizar status (implementar no service depois se necessário)
        # Por enquanto retorna sucesso
        return jsonify({
            'sucesso': True, 
            'mensagem': 'Status de adimplência atualizado com sucesso'
        })
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@routes.route('/api/associado/atualizar/<cpf>', methods=['POST'])
def api_atualizar_associado(cpf):
    """API para atualizar dados de um associado"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({'sucesso': False, 'mensagem': 'Dados não fornecidos'}), 400
        
        resultado = associado_service.atualizar_associado(cpf, dados)
        
        if resultado['sucesso']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@routes.route('/api/taxa/confirmar-pagamento', methods=['POST'])
def api_confirmar_pagamento_taxa():
    """API para confirmar pagamento de taxa"""
    dados = request.get_json()
    if not dados or not dados.get('taxa_id'):
        return jsonify({'sucesso': False, 'mensagem': 'ID da taxa é obrigatório'}), 400
    
    try:
        resultado = taxa_service.confirmar_pagamento(
            dados['taxa_id'],
            dados.get('codigo_transacao', f"MANUAL_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        )
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@routes.route('/api/taxa/detalhes/<int:taxa_id>', methods=['GET'])
def api_detalhes_taxa(taxa_id):
    """API para obter detalhes de uma taxa"""
    try:
        taxa_obj = taxa_service.obter_por_id(taxa_id)
        if taxa_obj:
            return jsonify({
                'sucesso': True,
                'taxa': taxa_obj
            })
        else:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Taxa não encontrada'
            }), 404
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao buscar taxa: {str(e)}'
        }), 500


@routes.route('/api/taxa/estatisticas', methods=['GET'])
def api_estatisticas_taxas():
    """API para obter estatísticas de taxas"""
    try:
        # Buscar todas as taxas (implementação combinada)
        taxas_pendentes = taxa_service.listar_taxas_pendentes()
        taxas_vencidas = taxa_service.listar_taxas_vencidas()
        todas_taxas = taxas_pendentes + taxas_vencidas
        
        total_taxas = len(todas_taxas)
        pagas = len([t for t in todas_taxas if t.get('status') == 'pago'])
        pendentes = len([t for t in todas_taxas if t.get('status') == 'pendente'])
        vencidas = len([t for t in todas_taxas if t.get('status') == 'vencido'])
        
        valor_total = sum(t.get('valor', 0) for t in todas_taxas)
        valor_arrecadado = sum(t.get('valor', 0) for t in todas_taxas if t.get('status') == 'pago')
        
        stats = {
            'total_taxas': total_taxas,
            'taxas_pagas': pagas,
            'taxas_pendentes': pendentes,
            'taxas_vencidas': vencidas,
            'valor_total': valor_total,
            'valor_arrecadado': valor_arrecadado,
            'valor_pendente': valor_total - valor_arrecadado,
            'taxa_arrecadacao': round((valor_arrecadado / valor_total * 100) if valor_total > 0 else 0, 1)
        }
        
        return jsonify({'sucesso': True, 'estatisticas': stats})
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500


@routes.route('/api/taxa/relatorio', methods=['GET'])
def api_relatorio_taxas():
    """API para gerar relatório de taxas"""
    try:
        periodo = request.args.get('periodo')  # Formato: YYYY-MM
        
        # Buscar todas as taxas
        from app.models import Taxa
        query = Taxa.query
        
        if periodo:
            # Filtrar por período
            try:
                ano, mes = periodo.split('-')
                query = query.filter(
                    db.extract('year', Taxa.data_vencimento) == int(ano),
                    db.extract('month', Taxa.data_vencimento) == int(mes)
                )
            except:
                pass
        
        taxas = query.order_by(Taxa.data_vencimento.desc()).all()
        
        # Gerar relatório HTML simples
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Relatório de Taxas - SINT-IFESGO</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2d5016; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #2d5016; color: white; }}
                .pago {{ color: green; }}
                .pendente {{ color: orange; }}
                .vencido {{ color: red; }}
            </style>
        </head>
        <body>
            <h1>Relatório de Taxas - SINT-IFESGO</h1>
            <p>Período: {periodo if periodo else 'Todos'}</p>
            <p>Total de taxas: {len(taxas)}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Código</th>
                        <th>Associado</th>
                        <th>Tipo</th>
                        <th>Valor</th>
                        <th>Vencimento</th>
                        <th>Status</th>
                        <th>Pagamento</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for taxa in taxas:
            html += f"""
                    <tr>
                        <td>{taxa.codigo_pagamento}</td>
                        <td>{taxa.associado_cpf}</td>
                        <td>{taxa.tipo}</td>
                        <td>R$ {taxa.valor:.2f}</td>
                        <td>{taxa.data_vencimento.strftime('%d/%m/%Y')}</td>
                        <td class="{taxa.status}">{taxa.status.upper()}</td>
                        <td>{taxa.data_pagamento.strftime('%d/%m/%Y') if taxa.data_pagamento else '-'}</td>
                    </tr>
            """
        
        html += """
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return html
    except Exception as e:
        return f"<h1>Erro ao gerar relatório</h1><p>{str(e)}</p>", 500


@routes.route('/api/taxa/verificar-vencimentos', methods=['GET'])
def api_verificar_vencimentos():
    """API para verificar e atualizar taxas vencidas"""
    try:
        from app.models import Taxa
        from datetime import date
        
        hoje = date.today()
        
        # Buscar taxas pendentes que venceram
        taxas_vencidas = Taxa.query.filter(
            Taxa.status == 'pendente',
            Taxa.data_vencimento < hoje
        ).all()
        
        # Atualizar status para vencido
        processadas = 0
        for taxa in taxas_vencidas:
            taxa.status = 'vencido'
            processadas += 1
        
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'vencidas': len(taxas_vencidas),
            'processadas': processadas,
            'mensagem': f'{processadas} taxa(s) marcada(s) como vencida(s)'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'sucesso': False, 'mensagem': str(e)}), 500




@routes.route('/api/upload-midia', methods=['POST'])
def api_upload_midia():
    """API para upload de mídias para boletins"""
    try:
        if 'arquivo' not in request.files:
            return jsonify({'sucesso': False, 'mensagem': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return jsonify({'sucesso': False, 'mensagem': 'Nenhum arquivo selecionado'}), 400
        
        # Verificar tipo de arquivo
        tipos_permitidos = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
        filename = arquivo.filename or ''
        extensao = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if extensao not in tipos_permitidos:
            return jsonify({'sucesso': False, 'mensagem': 'Tipo de arquivo não permitido'}), 400
        
        # Salvar arquivo (implementação simplificada)
        from datetime import datetime
        import os
        
        # Criar nome único para o arquivo
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f"{timestamp}_{arquivo.filename}"
        
        # Definir caminho (criar pasta se não existir)
        upload_path = os.path.join(os.getcwd(), 'static', 'uploads')
        os.makedirs(upload_path, exist_ok=True)
        
        caminho_arquivo = os.path.join(upload_path, nome_arquivo)
        arquivo.save(caminho_arquivo)
        
        # Retornar URL relativa
        url_arquivo = f"/static/uploads/{nome_arquivo}"
        
        return jsonify({
            'sucesso': True,
            'url': url_arquivo,
            'nome_original': arquivo.filename,
            'nome_salvo': nome_arquivo
        })
        
    except Exception as e:
        return jsonify({'sucesso': False, 'mensagem': f'Erro no upload: {str(e)}'}), 500


@routes.route('/api/webservice/status')
def api_webservice_status():
    """API para verificar status do web service externo"""
    try:
        from app.services.webservice_sinsind import web_service_sinsind
        status = web_service_sinsind.status_servico()
        
        return jsonify({
            'sucesso': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': str(e)
        }), 500


@routes.route('/api/webservice/test/<cpf>')
def api_webservice_test(cpf):
    """API para testar consulta no web service externo"""
    try:
        from app.services.webservice_sinsind import web_service_sinsind
        sucesso, dados, mensagem = web_service_sinsind.consultar_associado(cpf)
        
        return jsonify({
            'sucesso': sucesso,
            'dados': dados,
            'mensagem': mensagem
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': str(e)
        }), 500


@routes.route('/webservice')
def webservice():
    """Página de administração do web service"""
    return render_template('webservice.html')