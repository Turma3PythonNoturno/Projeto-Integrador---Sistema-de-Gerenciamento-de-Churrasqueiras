"""
API Blueprint
Handles API endpoints for AJAX calls and external integration
"""

from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# TODO: Move API routes from routes.py
# - /api/verificar-disponibilidade
# - /api/criar-reserva
# - /api/cancelar-reserva
# - /api/listar-reservas
# - /api/estatisticas
# - /api/associado/criar
# - /api/associado/importar-api
# - /api/associado/verificar/<cpf>
# - /api/taxa/confirmar-pagamento
