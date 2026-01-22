"""
Reservations Blueprint  
Handles reservation management (list, create, edit, cancel)
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from datetime import datetime
from app.container import container
from app.models import Reserva, Churrasqueira
from app.utils import CPFUtils

reservas_bp = Blueprint('reservas', __name__)

# Get services from container
reserva_service = container.get_reserva_service()


@reservas_bp.route('/reservas')
def listar():
    """Page to list reservations - all for admin, only user's for associados"""
    try:
        # Check if user is logged in
        if 'usuario_logado' not in session:
            flash('Você precisa estar logado para ver reservas', 'warning')
            return redirect(url_for('auth.login'))
        
        # Atualizar status de reservas expiradas
        num_atualizadas = reserva_service.atualizar_status_expirados()
        print(f"Atualizadas {num_atualizadas} reservas")
        
        is_admin = session.get('is_admin', False)
        cpf_usuario = session.get('cpf')
        
        # Filtrar apenas reservas ativas (não mostrar concluídas/expiradas/canceladas)
        filtro_historico = request.args.get('historico', 'false') == 'true'
        
        # IMPORTANTE: Recarregar dados APÓS atualizar status
        # If admin, list all reservations
        if is_admin:
            # Recarregar do banco após atualização
            from app.models import db
            db.session.expire_all()  # Força recarregar do banco
            reservas_data = reserva_service.listar_todas_reservas()
            titulo = "Reservas da Churrasqueira" if not filtro_historico else "Histórico de Reservas"
        else:
            # If regular associado, list only their reservations
            from app.models import db
            db.session.expire_all()  # Força recarregar do banco
            reservas_objs = Reserva.query.filter_by(cpf_associado=cpf_usuario).order_by(
                Reserva.data_reserva.desc(), 
                Reserva.horario_inicio.desc()
            ).all()
            reservas_data = [r.to_dict() for r in reservas_objs]
            titulo = "Minhas Reservas" if not filtro_historico else "Meu Histórico"
        
        # Filtrar baseado no tipo de visualização
        if filtro_historico:
            # Mostrar apenas concluídas, expiradas e canceladas
            reservas_data = [r for r in reservas_data if r.get('status') in ['concluida', 'expirada', 'cancelada']]
        else:
            # Mostrar apenas ativas (pendente, confirmada, ativa)
            reservas_data = [r for r in reservas_data if r.get('status') in ['pendente', 'confirmada', 'ativa']]
        
        # Convert to template-compatible objects
        reservas = []
        for reserva_dict in reservas_data:
            # Create simple object with to_dict method
            class ReservaView:
                def __init__(self, data):
                    self._data = data
                    for key, value in data.items():
                        setattr(self, key, value)
                
                def to_dict(self):
                    return self._data
            
            reservas.append(ReservaView(reserva_dict))
        
        return render_template('lista_reservas.html', 
                             reservas=reservas, 
                             titulo=titulo, 
                             is_admin=is_admin,
                             filtro_historico=filtro_historico)
    except Exception as e:
        print(f"\n!!! ERROR LISTING RESERVATIONS: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return render_template('lista_reservas.html', 
                             reservas=[], 
                             titulo="Reservas",
                             is_admin=False,
                             erro=f"Erro ao carregar reservas: {str(e)}")


@reservas_bp.route('/api/verificar-disponibilidade')
def verificar_disponibilidade():
    """API to check time slot availability"""
    data_str = request.args.get('data')
    horario_inicio_str = request.args.get('horario_inicio')
    horario_fim_str = request.args.get('horario_fim')
    churrasqueira_id_str = request.args.get('churrasqueira_id')
    
    if not all([data_str, horario_inicio_str, horario_fim_str]):
        return jsonify({
            'disponivel': False, 
            'mensagem': 'Parâmetros obrigatórios: data, horario_inicio, horario_fim'
        }), 400
    
    try:
        resultado = reserva_service.verificar_disponibilidade(
            data_str, horario_inicio_str, horario_fim_str, churrasqueira_id_str
        )
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({
            'disponivel': False, 
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@reservas_bp.route('/api/reservas/disponiveis')
def listar_churrasqueiras_disponiveis():
    """Lista churrasqueiras disponíveis para um intervalo de data/horário."""
    data_str = request.args.get('data')
    inicio_str = request.args.get('inicio')
    fim_str = request.args.get('fim')

    if not all([data_str, inicio_str, fim_str]):
        return jsonify({
            'disponiveis': [],
            'mensagem': 'Parâmetros obrigatórios: data, inicio, fim'
        }), 400

    try:
        data_reserva = datetime.strptime(data_str, '%Y-%m-%d').date()
        horario_inicio = datetime.strptime(inicio_str, '%H:%M').time()
        horario_fim = datetime.strptime(fim_str, '%H:%M').time()
    except ValueError:
        return jsonify({
            'disponiveis': [],
            'mensagem': 'Formato inválido de data ou horário'
        }), 400

    # Buscar churrasqueiras ocupadas no intervalo
    reservas_conflitantes = Reserva.query.filter(
        Reserva.data_reserva == data_reserva,
        Reserva.status.in_(('ativa', 'pendente', 'paga', 'confirmada')),
        Reserva.horario_inicio < horario_fim,
        Reserva.horario_fim > horario_inicio
    ).all()

    ids_ocupadas = {r.churrasqueira_id for r in reservas_conflitantes}

    # Churrasqueiras livres
    churrasqueiras_livres = Churrasqueira.query.filter(~Churrasqueira.id.in_(ids_ocupadas)).all()

    disponiveis = [
        {
            'id': ch.id,
            'nome': ch.nome,
            'preco': float(ch.preco or 0)
        }
        for ch in churrasqueiras_livres
    ]

    return jsonify({
        'disponiveis': disponiveis,
        'mensagem': 'Churrasqueiras disponíveis retornadas com sucesso'
    })


@reservas_bp.route('/api/criar-reserva', methods=['POST'])
def criar_reserva():
    """API to create new reservation"""
    # Check if user is logged in
    if 'usuario_logado' not in session:
        return jsonify({
            'sucesso': False,
            'mensagem': 'Você precisa estar logado para fazer uma reserva'
        }), 401
    
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                'sucesso': False, 
                'mensagem': 'Dados JSON são obrigatórios'
            }), 400

        # IMPORTANT VALIDATION
        if "churrasqueira_id" not in dados or not str(dados["churrasqueira_id"]).strip():
            return jsonify({
                "sucesso": False,
                "mensagem": "Você deve selecionar uma churrasqueira."
            }), 400
        
        # Auto-fill associado CPF with logged user's CPF
        cpf_form = dados.get('cpf_associado', '')
        cpf_usuario = session.get('cpf')
        
        # Clean CPF (remove dots and dashes)
        if cpf_form:
            cpf_limpo = CPFUtils.limpar(str(cpf_form))
        elif cpf_usuario:
            cpf_limpo = CPFUtils.limpar(str(cpf_usuario))
        else:
            cpf_limpo = None
        
        if cpf_limpo:
            dados['cpf_associado'] = cpf_limpo
        
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


@reservas_bp.route('/api/cancelar-reserva/<int:reserva_id>', methods=['POST'])
def cancelar_reserva(reserva_id):
    """API to cancel a reservation"""
    # Check if user is logged in
    if 'usuario_logado' not in session:
        return jsonify({
            'sucesso': False,
            'mensagem': 'Você precisa estar logado para cancelar uma reserva'
        }), 401
    
    try:
        is_admin = session.get('is_admin', False)
        cpf_usuario = session.get('cpf')
        
        # Verificar se reserva existe
        reserva = Reserva.query.get(reserva_id)
        if not reserva:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Reserva não encontrada'
            }), 404
        
        # Verify reservation belongs to user (except if admin)
        if not is_admin:
            # Check if reservation belongs to logged user
            if reserva.cpf_associado != cpf_usuario:
                return jsonify({
                    'sucesso': False,
                    'mensagem': 'Você só pode cancelar suas próprias reservas'
                }), 403
        
        dados = request.get_json() or {}
        email_confirmacao = dados.get('email') if not is_admin else None
        
        resultado = reserva_service.cancelar_reserva(reserva_id, email_confirmacao, is_admin=is_admin)
        
        if resultado['sucesso']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'sucesso': False, 
            'mensagem': f'Erro interno: {str(e)}'
        }), 500


@reservas_bp.route('/api/listar-reservas', methods=['GET'])
def api_listar_reservas():
    """API to list all reservations"""
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


@reservas_bp.route('/api/reserva/<int:reserva_id>', methods=['GET'])
def obter_detalhes_reserva(reserva_id):
    """API to get reservation details"""
    # Check if user is logged in
    if 'usuario_logado' not in session:
        return jsonify({
            'sucesso': False,
            'mensagem': 'Você precisa estar logado para ver detalhes da reserva'
        }), 401
    
    try:
        is_admin = session.get('is_admin', False)
        cpf_usuario = session.get('cpf')
        
        # Get reservation from database
        reserva = Reserva.query.get(reserva_id)
        if not reserva:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Reserva não encontrada'
            }), 404
        
        # Verify reservation belongs to user (except if admin)
        if not is_admin and reserva.cpf_associado != cpf_usuario:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Você só pode ver detalhes das suas próprias reservas'
            }), 403
        
        # Return reservation details
        return jsonify({
            'sucesso': True,
            'reserva': reserva.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro interno: {str(e)}'
        }), 500
