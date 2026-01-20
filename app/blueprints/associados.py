"""
Associados Blueprint
Handles member/associado management
"""

from flask import Blueprint

associados_bp = Blueprint('associados', __name__, url_prefix='/associados')

# TODO: Move associado routes from routes.py
# - /associados (list)
# - /associado/novo
# - /api/associado/criar
# - /api/associado/importar-api
# - /api/associado/verificar/<cpf>
