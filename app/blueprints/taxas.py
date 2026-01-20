"""
Taxas Blueprint
Handles fee/payment management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.container import container

taxas_bp = Blueprint('taxas', __name__)

# Get services from container
taxa_service = container.get_taxa_service()


def verificar_admin():
    """Check if user is administrator"""
    if 'usuario_logado' not in session:
        return False
    return session.get('is_admin', False)


@taxas_bp.route('/taxas')
def listar():
    """List system fees (admin only)"""
    if not verificar_admin():
        flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
        return redirect(url_for('dashboard.inicio'))
    
    cpf_associado = request.args.get('cpf')  # Optional
    
    # List ALL fees, not just pending ones
    if cpf_associado:
        taxas = taxa_service.listar_por_associado(cpf_associado)
    else:
        taxas = taxa_service.listar_todas_taxas()
    
    print(f"\n=== DEBUG TAXAS ===")
    print(f"Total de taxas encontradas: {len(taxas)}")
    print(f"Taxas: {taxas}")
    
    # Calculate basic statistics for template
    total_recebido = sum(float(t.get('valor', 0)) for t in taxas if t.get('status') == 'pago')
    total_pendente = sum(float(t.get('valor', 0)) for t in taxas if t.get('status') == 'pendente')
    total_vencido = sum(float(t.get('valor', 0)) for t in taxas if t.get('status') == 'vencido')
    
    print(f"\n=== ESTATÍSTICAS CALCULADAS ===")
    print(f"Total Recebido: R$ {total_recebido}")
    print(f"Total Pendente: R$ {total_pendente}")
    print(f"Total Vencido: R$ {total_vencido}")
    print(f"Total de Taxas: {len(taxas)}")
    
    estatisticas = {
        'total_recebido': total_recebido,
        'total_pendente': total_pendente,
        'total_vencido': total_vencido,
        'total_taxas': len(taxas)
    }
    
    print(f"\n=== ANTES DO RENDER ===")
    print(f"Estatísticas sendo enviadas: {estatisticas}")
    print(f"Taxas sendo enviadas: {len(taxas)} itens")
    
    return render_template('taxas.html', 
                         taxas=taxas, 
                         estatisticas=estatisticas)


@taxas_bp.route('/api/taxa/confirmar-pagamento', methods=['POST'])
def confirmar_pagamento():
    """API to confirm fee payment"""
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Dados JSON são obrigatórios'
            }), 400
        
        taxa_id = dados.get('taxa_id')
        if not taxa_id:
            return jsonify({
                'sucesso': False,
                'mensagem': 'ID da taxa é obrigatório'
            }), 400
        
        resultado = taxa_service.confirmar_pagamento(taxa_id)
        
        if resultado['sucesso']:
            return jsonify(resultado)
        else:
            return jsonify(resultado), 400
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro interno: {str(e)}'
        }), 500
# - /api/taxa/marcar-paga
