"""
Reservations Blueprint  
Handles reservation management (list, create, edit, cancel)
"""

from flask import Blueprint

reservas_bp = Blueprint('reservas', __name__, url_prefix='/reservas')

# TODO: Move reservation routes from routes.py
# - /reservas (list)
# - /api/criar-reserva
# - /api/cancelar-reserva
# - /api/verificar-disponibilidade
# - /api/listar-reservas
