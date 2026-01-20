"""
Dashboard Blueprint
Main application pages and navigation
"""

from flask import Blueprint, render_template, redirect, url_for, flash, session

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/inicio')
def inicio():
    """SINT-IFESGO system home page"""
    # Check if user is logged in
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado para acessar o sistema', 'warning')
        return redirect(url_for('auth.login'))
    
    try:
        return render_template('inicio.html')
    except Exception as e:
        print(f"\n!!! ERROR loading home page: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return render_template('inicio.html', erro=f"Erro ao carregar página: {str(e)}")


@dashboard_bp.route('/nova-reserva')
def nova_reserva():
    """New reservation page"""
    # Check if user is logged in
    if 'usuario_logado' not in session:
        flash('Você precisa estar logado para fazer uma reserva', 'warning')
        return redirect(url_for('auth.login'))
    
    # Pass logged user's CPF to template
    cpf_usuario = session.get('cpf', '')
    is_admin = session.get('is_admin', False)
    cpf_formatado = ''
    if cpf_usuario and len(cpf_usuario) == 11:
        cpf_formatado = f"{cpf_usuario[:3]}.{cpf_usuario[3:6]}.{cpf_usuario[6:9]}-{cpf_usuario[9:]}"
    
    return render_template('nova_reserva.html', cpf_usuario=cpf_usuario, cpf_formatado=cpf_formatado, is_admin=is_admin)
