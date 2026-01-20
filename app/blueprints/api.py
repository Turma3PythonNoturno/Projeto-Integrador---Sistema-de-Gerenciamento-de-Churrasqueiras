"""
API Blueprint
Handles API endpoints for AJAX calls and external integration
Note: Most API routes were moved to their respective blueprints:
- Reservation APIs → reservas_bp
- Associado APIs → associados_bp  
- Taxa APIs → taxas_bp
This contains shared/utility API endpoints
"""

from flask import Blueprint, jsonify
from app.container import container

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Get services from container
reserva_service = container.get_reserva_service()


@api_bp.route('/estatisticas')
def obter_estatisticas():
    """API to get statistics"""
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

