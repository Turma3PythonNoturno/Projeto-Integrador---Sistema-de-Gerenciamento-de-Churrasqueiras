from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, date, time, timedelta
from app.container import container
from app.models import db, Reserva

routes = Blueprint('routes', __name__)

# Obter serviços do container
reserva_service = container.get_reserva_service()
associado_service = container.get_associado_service()
taxa_service = container.get_taxa_service()
boletim_service = container.get_boletim_service()


@routes.route('/')
def inicio():
    """Página inicial do sistema SINT-IFESGO"""
    try:
        # Buscar boletins urgentes para exibir na página inicial
        boletins_urgentes = boletim_service.listar_boletins_urgentes()
        return render_template('inicio.html', boletins_urgentes=boletins_urgentes)
    except Exception as e:
        return render_template('inicio.html', boletins_urgentes=[], 
                             erro=f"Erro ao carregar boletins: {str(e)}")


@routes.route('/nova-reserva')
def nova_reserva():
    """Página para fazer nova reserva"""
    return render_template('nova_reserva.html')


@routes.route('/reservas')
def listar_reservas():
    """Página para listar todas as reservas"""
    try:
        reservas_data = reserva_service.listar_reservas_futuras()
        
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
    """Lista todos os associados"""
    try:
        associados = associado_service.listar_todos()
        return render_template('associados.html', associados=associados)
    except Exception as e:
        return render_template('associados.html', 
                             associados=[], 
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


@routes.route('/boletins')
def listar_boletins():
    """Página para listar boletins informativos"""
    try:
        boletins_data = boletim_service.listar_boletins_ativos()
        
        return render_template('boletins.html', 
                             boletins=boletins_data,
                             titulo="Boletins Informativos")
    except Exception as e:
        return render_template('boletins.html', 
                             boletins=[], 
                             erro=f"Erro ao carregar boletins: {str(e)}")


@routes.route('/admin/boletim/novo')
def novo_boletim():
    """Página para criar novo boletim (admin)"""
    return render_template('novo_boletim.html')


@routes.route('/api/boletim/criar', methods=['POST'])
def criar_boletim():
    """API para criar novo boletim"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Dados JSON são obrigatórios'
            }), 400
        
        resultado = boletim_service.criar_boletim(dados)
        
        if resultado['sucesso']:
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro interno do servidor: {str(e)}'
        }), 500


@routes.route('/taxas')
def listar_taxas():
    """Lista taxas do sistema"""
    try:
        cpf_associado = request.args.get('cpf')  # Opcional
        
        if cpf_associado:
            taxas = taxa_service.listar_por_associado(cpf_associado)
        else:
            taxas = taxa_service.listar_taxas_pendentes()
        
        return render_template('taxas.html', taxas=taxas, cpf_filtro=cpf_associado)
    except Exception as e:
        return render_template('taxas.html', 
                             taxas=[], 
                             erro=f"Erro ao carregar taxas: {str(e)}")


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
        
        # Buscar boletins para o associado
        boletins = boletim_service.listar_boletins_ativos(cpf)
        
        return render_template('minha_conta.html', 
                             associado=associado,
                             taxas=taxas,
                             boletins=boletins)
        
    except Exception as e:
        return render_template('erro.html',
                             mensagem=f"Erro ao carregar conta: {str(e)}"), 500


# === ROTAS API PARA OS TEMPLATES ADMINISTRATIVOS ===

@routes.route('/api/boletim/buscar', methods=['GET'])
def api_buscar_boletim():
    """API para buscar boletim por ID"""
    boletim_id = request.args.get('id', type=int)
    if not boletim_id:
        return jsonify({'sucesso': False, 'mensagem': 'ID do boletim é obrigatório'}), 400
    
    boletim = boletim_service.buscar_por_id(boletim_id)
    if not boletim:
        return jsonify({'sucesso': False, 'mensagem': 'Boletim não encontrado'}), 404
    
    return jsonify({'sucesso': True, 'boletim': boletim})


@routes.route('/api/boletim/editar', methods=['POST'])
def api_editar_boletim():
    """API para editar boletim"""
    dados = request.get_json()
    if not dados or not dados.get('id'):
        return jsonify({'sucesso': False, 'mensagem': 'Dados incompletos'}), 400
    
    resultado = boletim_service.atualizar_boletim(dados['id'], dados)
    return jsonify(resultado)


@routes.route('/api/boletim/excluir', methods=['POST'])
def api_excluir_boletim():
    """API para excluir (desativar) boletim"""
    dados = request.get_json()
    if not dados or not dados.get('id'):
        return jsonify({'sucesso': False, 'mensagem': 'ID do boletim é obrigatório'}), 400
    
    resultado = boletim_service.desativar_boletim(dados['id'])
    return jsonify(resultado)


@routes.route('/api/boletim/estatisticas', methods=['GET'])
def api_estatisticas_boletim():
    """API para obter estatísticas de boletins"""
    stats = boletim_service.estatisticas()
    return jsonify({'sucesso': True, 'estatisticas': stats})


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