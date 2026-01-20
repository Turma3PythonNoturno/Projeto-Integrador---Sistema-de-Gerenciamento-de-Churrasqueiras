"""
Taxas Blueprint
Handles fee/payment management
"""

from flask import Blueprint

taxas_bp = Blueprint('taxas', __name__, url_prefix='/taxas')

# TODO: Move taxa routes from routes.py
# - /taxas (list)
# - /api/taxa/confirmar-pagamento
# - /api/taxa/marcar-paga
