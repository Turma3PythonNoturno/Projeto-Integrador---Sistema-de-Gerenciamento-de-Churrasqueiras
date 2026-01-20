"""
Authentication Blueprint
Handles login, logout, and password recovery
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, LoginSistema, Associado, TokenRecuperacaoSenha

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if 'usuario_logado' in session:
        return redirect(url_for('dashboard.inicio'))
    
    if request.method == 'POST':
        # 1. Get form data
        cpf_form = request.form.get('cpf_associado')
        senha_form = request.form.get('password')

        # 2. Clean CPF (Remove dots and dashes to match database)
        cpf_limpo = cpf_form.replace('.', '').replace('-', '')

        # 3. Find user in login table
        usuario_login = LoginSistema.query.filter_by(cpf=cpf_limpo).first()

        # 4. Validation: Check if user exists and password is correct
        if usuario_login and usuario_login.verificar_senha(senha_form):
            
            # --- LOGIN SUCCESS ---
            
            # Create session
            session['usuario_logado'] = True
            session['cpf'] = usuario_login.cpf
            session['is_admin'] = usuario_login.is_admin()

            # Get name through 'associado_obj' relationship created in Model
            # .split()[0] used to get only first name for menu
            nome_completo = usuario_login.associado_obj.nome
            session['nome_usuario'] = nome_completo.split()[0]

            flash(f'Bem-vindo(a), {session["nome_usuario"]}!', 'success')

            return redirect(url_for('dashboard.inicio'))
        
        else:
            flash('CPF ou senha incorretos.', 'danger')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Você saiu do sistema', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/esqueci-senha', methods=['GET', 'POST'])
def esqueci_senha():
    """Password recovery request page"""
    if request.method == 'POST':
        cpf_form = request.form.get('cpf')
        telefone_form = request.form.get('telefone')
        
        if not cpf_form or not telefone_form:
            flash('CPF e telefone são obrigatórios', 'danger')
            return render_template('esqueci_senha.html')
        
        # Clean CPF and phone
        cpf_limpo = cpf_form.replace('.', '').replace('-', '')
        telefone_limpo = telefone_form.replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
        
        # Check if associado exists
        associado = Associado.query.filter_by(cpf=cpf_limpo).first()
        if not associado:
            flash('CPF não encontrado no sistema', 'danger')
            return render_template('esqueci_senha.html')
        
        # Verify phone matches
        telefone_cadastrado = associado.telefone.replace('(', '').replace(')', '').replace(' ', '').replace('-', '') if associado.telefone else ''
        if telefone_cadastrado != telefone_limpo:
            flash('Telefone não corresponde ao cadastro', 'danger')
            return render_template('esqueci_senha.html')
        
        # Check if login exists
        login = LoginSistema.query.filter_by(cpf=cpf_limpo).first()
        if not login:
            flash('Usuário não possui login cadastrado', 'danger')
            return render_template('esqueci_senha.html')
        
        try:
            # Generate recovery token
            token_obj = TokenRecuperacaoSenha.criar_token(cpf_limpo)
            
            # TODO: Send email with recovery link
            # For now, display link on screen (development)
            link_recuperacao = url_for('auth.resetar_senha', token=token_obj.token, _external=True)
            
            # Prepare phone for WhatsApp (remove formatting)
            telefone_whatsapp = associado.telefone.replace('(', '').replace(')', '').replace(' ', '').replace('-', '') if associado.telefone else None
            
            # Return to page with generated link
            return render_template('esqueci_senha.html', 
                                 link_gerado=link_recuperacao,
                                 telefone_whatsapp=telefone_whatsapp,
                                 nome_associado=associado.nome,
                                 sucesso=True)
            
        except Exception as e:
            flash(f'Erro ao gerar token: {str(e)}', 'danger')
        
        return render_template('esqueci_senha.html')
    
    return render_template('esqueci_senha.html')


@auth_bp.route('/resetar-senha/<token>', methods=['GET', 'POST'])
def resetar_senha(token):
    """Password reset page with token"""
    # Find token in database
    token_obj = TokenRecuperacaoSenha.query.filter_by(token=token).first()
    
    if not token_obj:
        flash('Token inválido ou não encontrado', 'danger')
        return redirect(url_for('auth.login'))
    
    if not token_obj.is_valido():
        flash('Token expirado ou já utilizado. Solicite uma nova recuperação.', 'warning')
        return redirect(url_for('auth.esqueci_senha'))
    
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirma_senha = request.form.get('confirma_senha')
        
        # Validations
        if not nova_senha or not confirma_senha:
            flash('Preencha todos os campos', 'danger')
            return render_template('resetar_senha.html', token=token)
        
        if len(nova_senha) < 6:
            flash('A senha deve ter no mínimo 6 caracteres', 'danger')
            return render_template('resetar_senha.html', token=token)
        
        if nova_senha != confirma_senha:
            flash('As senhas não coincidem', 'danger')
            return render_template('resetar_senha.html', token=token)
        
        try:
            # Find user login
            login = LoginSistema.query.filter_by(cpf=token_obj.cpf).first()
            if not login:
                flash('Usuário não encontrado', 'danger')
                return redirect(url_for('auth.login'))
            
            # Update password
            login.definir_senha(nova_senha)
            
            # Mark token as used
            token_obj.marcar_como_usado()
            
            db.session.commit()
            
            flash('Senha alterada com sucesso! Faça login com sua nova senha.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao resetar senha: {str(e)}', 'danger')
            return render_template('resetar_senha.html', token=token)
    
    # GET - display form
    associado = Associado.query.filter_by(cpf=token_obj.cpf).first()
    return render_template('resetar_senha.html', token=token, nome=associado.nome if associado else 'Usuário')
