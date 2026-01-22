"""
Taxas Blueprint
Handles fee/payment management
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from app.container import container
from app.services.qrcode_service import QRCodeService
from io import BytesIO

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
    
    # Atualizar status de taxas vencidas
    taxa_service.atualizar_taxas_vencidas()
    
    cpf_associado = request.args.get('cpf')  # Optional
    
    # List ALL fees, not just pending ones
    if cpf_associado:
        taxas = taxa_service.listar_por_associado(cpf_associado)
    else:
        taxas = taxa_service.listar_todas_taxas()
    
    # Calculate basic statistics for template
    total_recebido = sum(float(t.get('valor', 0)) for t in taxas if t.get('status') == 'pago')
    total_pendente = sum(float(t.get('valor', 0)) for t in taxas if t.get('status') == 'pendente')
    total_vencido = sum(float(t.get('valor', 0)) for t in taxas if t.get('status') == 'vencido')
    
    estatisticas = {
        'total_recebido': total_recebido,
        'total_pendente': total_pendente,
        'total_vencido': total_vencido,
        'total_taxas': len(taxas)
    }
    
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


@taxas_bp.route('/api/taxa/detalhes/<int:taxa_id>', methods=['GET'])
def obter_detalhes_taxa(taxa_id):
    """API to get fee details"""
    if not verificar_admin():
        return jsonify({
            'sucesso': False,
            'mensagem': 'Acesso negado'
        }), 403
    
    try:
        from app.models import Taxa
        
        taxa = Taxa.query.get(taxa_id)
        if not taxa:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Taxa não encontrada'
            }), 404
        
        return jsonify({
            'sucesso': True,
            'taxa': taxa.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao obter detalhes: {str(e)}'
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


@taxas_bp.route('/api/taxa/qrcode/<int:taxa_id>')
def obter_qrcode(taxa_id):
    """API to get QR code for fee payment (PNG image)"""
    try:
        taxa = taxa_service.obter_por_id(taxa_id)
        
        if not taxa:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Taxa não encontrada'
            }), 404
        
        # Buscar churrasqueira para pegar o preço correto
        from app.models import db, Taxa
        taxa_obj = Taxa.query.get(taxa_id)
        
        if not taxa_obj:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Taxa não encontrada'
            }), 404
        
        # Gerar QR code
        resultado = QRCodeService.gerar_qrcode_pix(
            valor=taxa_obj.valor,
            taxa_id=taxa_id,
            descricao=f"Reserva de Churrasqueira - Taxa #{taxa_id}"
        )
        
        if resultado.get('sucesso'):
            # Retornar imagem PNG diretamente
            return send_file(
                BytesIO(resultado.get('qrcode_bytes')),
                mimetype='image/png',
                as_attachment=False,
                download_name=f'qrcode_taxa_{taxa_id}.png'
            )
        else:
            return jsonify({
                'sucesso': False,
                'mensagem': resultado.get('mensagem')
            }), 500
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao gerar QR code: {str(e)}'
        }), 500


@taxas_bp.route('/api/taxa/qrcode-json/<int:taxa_id>')
def obter_qrcode_json(taxa_id):
    """API to get QR code data as JSON (for modal display with base64 image)"""
    try:
        taxa = taxa_service.obter_por_id(taxa_id)
        
        if not taxa:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Taxa não encontrada'
            }), 404
        
        from app.models import Taxa
        taxa_obj = Taxa.query.get(taxa_id)
        
        if not taxa_obj:
            return jsonify({
                'sucesso': False,
                'mensagem': 'Taxa não encontrada'
            }), 404
        
        # Gerar QR code
        resultado = QRCodeService.gerar_qrcode_pix(
            valor=taxa_obj.valor,
            taxa_id=taxa_id,
            descricao=f"Reserva de Churrasqueira - Taxa #{taxa_id}"
        )
        
        if resultado.get('sucesso'):
            return jsonify({
                'sucesso': True,
                'taxa_id': taxa_id,
                'valor': str(taxa_obj.valor),
                'descricao': f"Reserva de Churrasqueira",
                'qrcode_base64': resultado.get('qrcode_base64'),
                'pix_data': resultado.get('pix_data')
            })
        else:
            return jsonify({
                'sucesso': False,
                'mensagem': resultado.get('mensagem')
            }), 500
            
    except Exception as e:
        return jsonify({
            'sucesso': False,
            'mensagem': f'Erro ao gerar QR code: {str(e)}'
        }), 500
