"""
Reservations Blueprint  
Handles reservation management (list, create, edit, cancel)
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.container import container
from app.models import Reserva, Churrasqueira
from app.utils import CPFUtils
from datetime import datetime

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
        
        is_admin = session.get('is_admin', False)
        cpf_usuario = session.get('cpf')
        
        # If admin, list all reservations
        if is_admin:
            reservas_data = reserva_service.listar_todas_reservas()
            titulo = "Reservas da Churrasqueira"
        else:
            # If regular associado, list only their reservations
            reservas_objs = Reserva.query.filter_by(cpf_associado=cpf_usuario).order_by(
                Reserva.data_reserva.desc(), 
                Reserva.horario_inicio.desc()
            ).all()
            reservas_data = [r.to_dict() for r in reservas_objs]
            titulo = "Minhas Reservas"
        
        print(f"\n=== DEBUG RESERVAS ===")
        print(f"Usuário: {cpf_usuario} | Admin: {is_admin}")
        print(f"Total de reservas encontradas: {len(reservas_data)}")
        for r in reservas_data:
            print(f"Reserva: {r.get('nome')} - {r.get('data_reserva')} - CPF: {r.get('cpf_associado')}")
        print(f"=== FIM DEBUG ===\n")
        
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
        
        return render_template('lista_reservas.html', reservas=reservas, titulo=titulo, is_admin=is_admin)
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
        
        # Get user info
        is_admin = session.get('is_admin', False)
        cpf_usuario = session.get('cpf')
        
        # Auto-fill associado CPF with logged user's CPF
        cpf_form = dados.get('cpf_associado', '')
        
        # Clean CPF (remove dots and dashes)
        if cpf_form:
            cpf_limpo = CPFUtils.limpar(str(cpf_form))
        elif cpf_usuario:
            cpf_limpo = CPFUtils.limpar(str(cpf_usuario))
        else:
            cpf_limpo = None
        
        if cpf_limpo:
            dados['cpf_associado'] = cpf_limpo
        
        # Validação: usuários normais só podem fazer reservas no seu próprio CPF
        # Admin pode fazer reservas para qualquer CPF
        if not is_admin and cpf_limpo != cpf_usuario:
            return jsonify({
                "sucesso": False,
                "mensagem": "Você só pode fazer reservas no seu próprio CPF. Para fazer reservas para outro CPF, contate o administrador."
            }), 403
        
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
        
        # Verify reservation belongs to user (except if admin)
        if not is_admin:
            reserva = Reserva.query.get(reserva_id)
            if not reserva:
                return jsonify({
                    'sucesso': False,
                    'mensagem': 'Reserva não encontrada'
                }), 404
            
            # Check if reservation belongs to logged user
            if reserva.cpf_associado != cpf_usuario:
                return jsonify({
                    'sucesso': False,
                    'mensagem': 'Você só pode cancelar suas próprias reservas'
                }), 403
        
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


@reservas_bp.route('/reservas/disponiveis', methods=['GET'])
def churrasqueiras_disponiveis():
    """API to get available grills for a given date and time range"""
    try:
        data_str = request.args.get("data")
        inicio_str = request.args.get("inicio")
        fim_str = request.args.get("fim")

        print(f"\n=== DEBUG /disponiveis ===")
        print(f"data_str: {data_str}")
        print(f"inicio_str: {inicio_str}")
        print(f"fim_str: {fim_str}")

        if not data_str or not inicio_str or not fim_str:
            print("Erro: Parâmetros insuficientes")
            return jsonify({"erro": "Parâmetros insuficientes"}), 400

        # Convert strings to proper formats
        data = datetime.strptime(data_str, "%Y-%m-%d").date()
        inicio = datetime.strptime(inicio_str, "%H:%M").time()
        fim = datetime.strptime(fim_str, "%H:%M").time()

        print(f"data: {data}, inicio: {inicio}, fim: {fim}")

        # Get all grills
        todas = Churrasqueira.query.all()
        ids_todas = [c.id for c in todas]
        
        print(f"Total de churrasqueiras: {len(todas)}")
        for c in todas:
            print(f"  - ID {c.id}: {c.nome}")

        # Find conflicting reservations
        conflitos = Reserva.query.filter(
            Reserva.data_reserva == data,
            Reserva.status.in_(('ativa', 'pendente', 'paga')),
            Reserva.horario_inicio < fim,
            Reserva.horario_fim > inicio
        ).all()

        ids_ocupadas = [r.churrasqueira_id for r in conflitos]
        
        print(f"Reservas em conflito: {len(conflitos)}")
        for r in conflitos:
            print(f"  - Churrasqueira {r.churrasqueira_id}: {r.horario_inicio} - {r.horario_fim}")

        # Filter available grills
        ids_disponiveis = [cid for cid in ids_todas if cid not in ids_ocupadas]
        
        print(f"Churrasqueiras disponíveis (IDs): {ids_disponiveis}")

        disponiveis = Churrasqueira.query.filter(
            Churrasqueira.id.in_(ids_disponiveis)
        ).all() if ids_disponiveis else []

        resposta = {
            "disponiveis": [
                {"id": c.id, "nome": c.nome}
                for c in disponiveis
            ],
            "total": len(disponiveis)
        }
        
        print(f"Resposta: {resposta}")
        print(f"=== FIM DEBUG ===\n")
        
        return jsonify(resposta)

    except Exception as e:
        print(f"ERRO em /disponiveis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "erro": f"Erro ao buscar churrasqueiras disponíveis: {str(e)}"
        }), 500
