"""
Associados Blueprint
Handles member/associado management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.container import container
from app.utils import CPFUtils
import requests
from config import Config

associados_bp = Blueprint('associados', __name__)

# Get services from container
associado_service = container.get_associado_service()


def verificar_admin():
    """Check if user is administrator"""
    if 'usuario_logado' not in session:
        return False
    return session.get('is_admin', False)


@associados_bp.route('/associados')
def listar():
    """List all associados - fetch from API (admin only)"""
    if not verificar_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('dashboard.inicio'))
    
    try:
        # Fetch data from API
        config = Config()
        payload = {
            **config.WEB_SERVICE_CREDENTIALS,
            "acao": "listar_associados"
        }
        
        response = requests.post(
            config.WEB_SERVICE_URL,
            json=payload,
            timeout=config.WEB_SERVICE_TIMEOUT,
            headers={'Content-Type': 'application/json'}
        )
        
        associados = []
        if response.status_code == 200:
            data = response.json()
            associados_raw = data.get('data', []) if data.get('status') == 'success' else data.get('associados', [])
            
            # Standardize data
            for assoc in associados_raw:
                cpf_limpo = CPFUtils.limpar(assoc.get('cpf', ''))
                inadimplencia = str(assoc.get('inadimplencia', 'SIM') or 'SIM').upper()
                
                associados.append({
                    'id': assoc.get('id'),
                    'codigo': assoc.get('codigo', ''),
                    'cpf': cpf_limpo,
                    'cpf_formatado': CPFUtils.formatar(cpf_limpo),
                    'nome': assoc.get('nome', ''),
                    'lotacao': assoc.get('lotacao', ''),
                    'categoria': assoc.get('categoria', ''),
                    'situacao': assoc.get('situacao', ''),
                    'inadimplencia': inadimplencia,
                    'status_adimplencia': 'adimplente' if inadimplencia == 'NÃO' else 'inadimplente',
                    'status_display': 'Adimplente' if inadimplencia == 'NÃO' else 'Inadimplente',
                    'pode_reservar': inadimplencia == 'NÃO'
                })
        
        # Calculate statistics
        total = len(associados)
        adimplentes = len([a for a in associados if a['inadimplencia'] == 'NÃO'])
        inadimplentes = total - adimplentes
        
        estatisticas = {
            'total_associados': total,
            'adimplentes': adimplentes,
            'inadimplentes': inadimplentes,
            'percentual_adimplencia': round((adimplentes / total * 100) if total > 0 else 0, 1)
        }
        
        print(f"\n=== ASSOCIADOS DA API ===")
        print(f"Total: {total}")
        print(f"Adimplentes: {adimplentes}")
        print(f"Inadimplentes: {inadimplentes}")
        print(f"=== FIM ===\n")
        
        return render_template('associados.html', 
                             associados=associados, 
                             estatisticas=estatisticas)
    except Exception as e:
        print(f"\n!!! ERRO: {str(e)}\n")
        import traceback
        traceback.print_exc()
        
        # Empty statistics in case of error
        estatisticas_vazia = {
            'total_associados': 0,
            'adimplentes': 0, 
            'inadimplentes': 0,
            'percentual_adimplencia': 0
        }
        return render_template('associados.html', 
                             associados=[], 
                             estatisticas=estatisticas_vazia,
                             erro=f"Erro ao carregar associados: {str(e)}")


@associados_bp.route('/associado/novo')
def novo():
    """Page to register new associado"""
    return render_template('novo_associado.html')


@associados_bp.route('/api/associado/criar', methods=['POST'])
def criar():
    """API to create new associado"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Dados JSON são obrigatórios'
            }), 400
        
        resultado = associado_service.criar_associado(dados)
        
        if resultado['sucesso']:
            return jsonify(resultado), 201
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro interno do servidor: {str(e)}'
        }), 500


@associados_bp.route('/api/associado/importar-api', methods=['POST'])
def importar_api():
    """API to import associados from external API"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Dados JSON são obrigatórios'
            }), 400
        
        # If it's a list of associados
        if isinstance(dados, list):
            importados = 0
            atualizados = 0
            erros = []
            
            for associado_api in dados:
                try:
                    resultado = associado_service.importar_da_api(associado_api)
                    if resultado['sucesso']:
                        if resultado.get('acao') == 'criado':
                            importados += 1
                        else:
                            atualizados += 1
                except Exception as e:
                    erros.append(f"CPF {associado_api.get('cpf')}: {str(e)}")
            
            return jsonify({
                'sucesso': True,
                'importados': importados,
                'atualizados': atualizados,
                'erros': erros,
                'mensagem': f'{importados} novos associados importados, {atualizados} atualizados'
            })
        else:
            # Single associado
            resultado = associado_service.importar_da_api(dados)
            return jsonify(resultado)
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao importar: {str(e)}'
        }), 500


@associados_bp.route('/api/associado/verificar/<cpf>')
def verificar(cpf):
    """API to verify associado status"""
    try:
        associado = associado_service.buscar_por_cpf(cpf)
        
        if not associado:
            return jsonify({
                'encontrado': False,
                'mensagem': 'CPF não encontrado no cadastro de associados'
            }), 404
        
        adimplente, mensagem = associado_service.verificar_adimplencia(cpf)
        
        return jsonify({
            'encontrado': True,
            'associado': associado,
            'adimplente': adimplente,
            'mensagem': mensagem
        })
        
    except Exception as e:
        return jsonify({
            'encontrado': False,
            'mensagem': f'Erro interno: {str(e)}'
        }), 500
