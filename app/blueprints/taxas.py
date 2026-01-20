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


@taxas_bp.route('/api/taxa/verificar-vencimentos', methods=['GET'])
def verificar_vencimentos():
    """API to check for expired fees and mark them as overdue"""
    if not verificar_admin():
        return jsonify({
            'sucesso': False,
            'mensagem': 'Acesso negado'
        }), 403
    
    try:
        resultado = taxa_service.verificar_vencimentos()
        return jsonify(resultado)
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao verificar vencimentos: {str(e)}'
        }), 500


@taxas_bp.route('/api/taxa/relatorio')
def gerar_relatorio():
    """API to generate fee report (CSV or PDF)"""
    if not verificar_admin():
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard.inicio'))
    
    try:
        periodo = request.args.get('periodo')  # Format: YYYY-MM
        
        resultado = taxa_service.gerar_relatorio(periodo)
        
        if resultado.get('sucesso'):
            # Return CSV content with proper UTF-8 encoding
            from flask import Response
            conteudo = resultado.get('conteudo', '')
            # Converter para bytes com encoding UTF-8
            conteudo_bytes = conteudo.encode('utf-8')
            return Response(
                conteudo_bytes,
                mimetype='text/csv; charset=utf-8',
                headers={
                    'Content-Disposition': f'attachment; filename="relatorio_taxas_{periodo or "completo"}.csv"',
                    'Content-Type': 'text/csv; charset=utf-8'
                }
            )
        else:
            flash('Erro ao gerar relatório', 'danger')
            return redirect(url_for('taxas.listar'))
            
    except Exception as e:
        flash(f'Erro: {str(e)}', 'danger')
        return redirect(url_for('taxas.listar'))


@taxas_bp.route('/api/taxa/comprovante/<int:taxa_id>')
def gerar_comprovante(taxa_id):
    """API to generate payment receipt"""
    if not verificar_admin():
        flash('Acesso negado', 'danger')
        return redirect(url_for('dashboard.inicio'))
    
    try:
        resultado = taxa_service.gerar_comprovante(taxa_id)
        
        if resultado.get('sucesso'):
            # Return PDF content
            from flask import Response
            return Response(
                resultado.get('conteudo', b''),
                mimetype='application/pdf',
                headers={'Content-Disposition': f'attachment; filename="comprovante_taxa_{taxa_id}.pdf"'}
            )
        else:
            flash('Erro ao gerar comprovante', 'danger')
            return redirect(url_for('taxas.listar'))
            
    except Exception as e:
        flash(f'Erro: {str(e)}', 'danger')
        return redirect(url_for('taxas.listar'))
