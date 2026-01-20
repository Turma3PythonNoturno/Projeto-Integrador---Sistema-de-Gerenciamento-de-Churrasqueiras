"""
Blueprints Module - Modularized Routes
Sistema de Reserva de Churrasqueiras - SINT-IFESGO
"""

from flask import Blueprint

# Import all blueprints
from app.blueprints.auth import auth_bp
from app.blueprints.dashboard import dashboard_bp
from app.blueprints.reservas import reservas_bp
from app.blueprints.associados import associados_bp
from app.blueprints.taxas import taxas_bp
from app.blueprints.api import api_bp

# Export all blueprints for registration
__all__ = [
    'auth_bp',
    'dashboard_bp', 
    'reservas_bp',
    'associados_bp',
    'taxas_bp',
    'api_bp'
]
