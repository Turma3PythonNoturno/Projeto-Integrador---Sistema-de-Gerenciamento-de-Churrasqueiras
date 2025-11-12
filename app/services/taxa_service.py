from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
from app.models import db, Taxa
from config import Config


class TaxaService:
    """Serviço para gerenciamento de taxas de reserva"""
    
    def __init__(self):
        self.config = Config()
    
    def gerar_taxa_reserva(self, reserva_id: int, cpf_associado: str) -> Dict:
        """Gera uma nova taxa de reserva"""
        try:
            # Verificar se já existe taxa para esta reserva
            taxa_existente = Taxa.query.filter_by(
                reserva_id=reserva_id,
                tipo='reserva'
            ).first()
            
            if taxa_existente:
                return {
                    'sucesso': False,
                    'mensagem': 'Já existe uma taxa gerada para esta reserva'
                }
            
            # Criar nova taxa
            nova_taxa = Taxa(
                valor=Decimal(str(self.config.TAXA_RESERVA['valor'])),
                tipo='reserva',
                status='pendente',
                data_vencimento=date.today() + timedelta(days=1),  # 24h para pagamento
                reserva_id=reserva_id,
                associado_cpf=cpf_associado
            )
            
            # Gerar código de pagamento
            nova_taxa.gerar_codigo_pagamento()
            
            db.session.add(nova_taxa)
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Taxa gerada com sucesso',
                'taxa': nova_taxa.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao gerar taxa: {str(e)}'
            }
    
    def confirmar_pagamento(self, taxa_id: int, codigo_transacao: Optional[str] = None) -> Dict:
        """Confirma o pagamento de uma taxa"""
        try:
            taxa = Taxa.query.get(taxa_id)
            
            if not taxa:
                return {
                    'sucesso': False,
                    'mensagem': 'Taxa não encontrada'
                }
            
            pode_pagar, mensagem = taxa.pode_ser_paga()
            if not pode_pagar:
                return {
                    'sucesso': False,
                    'mensagem': mensagem
                }
            
            # Marcar como paga
            taxa.marcar_como_paga(
                data_pagamento=datetime.utcnow(),
                codigo_transacao=codigo_transacao
            )
            
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Pagamento confirmado com sucesso',
                'taxa': taxa.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao confirmar pagamento: {str(e)}'
            }
    
    def buscar_por_codigo(self, codigo_pagamento: str) -> Optional[Dict]:
        """Busca taxa por código de pagamento"""
        taxa = Taxa.query.filter_by(codigo_pagamento=codigo_pagamento).first()
        
        if taxa:
            return taxa.to_dict()
        
        return None
    
    def listar_taxas_pendentes(self, cpf_associado: Optional[str] = None) -> List[Dict]:
        """Lista taxas pendentes, opcionalmente filtradas por associado"""
        query = Taxa.query.filter_by(status='pendente')
        
        if cpf_associado:
            query = query.filter_by(associado_cpf=cpf_associado)
        
        taxas = query.all()
        return [taxa.to_dict() for taxa in taxas]
    
    def listar_taxas_vencidas(self) -> List[Dict]:
        """Lista taxas vencidas"""
        hoje = date.today()
        
        # Buscar taxas pendentes com data de vencimento passada
        taxas_vencidas = Taxa.query.filter(
            Taxa.status == 'pendente',
            Taxa.data_vencimento < hoje
        ).all()
        
        # Atualizar status para vencido
        for taxa in taxas_vencidas:
            taxa.marcar_como_vencida()
        
        if taxas_vencidas:
            db.session.commit()
        
        # Retornar todas as taxas vencidas
        taxas_vencidas_todas = Taxa.query.filter_by(status='vencido').all()
        return [taxa.to_dict() for taxa in taxas_vencidas_todas]
    
    def buscar_por_reserva(self, reserva_id: int) -> Optional[Dict]:
        """Busca taxa por ID da reserva"""
        taxa = Taxa.query.filter_by(reserva_id=reserva_id, tipo='reserva').first()
        
        if taxa:
            return taxa.to_dict()
        
        return None
    
    def cancelar_taxa(self, taxa_id: int, motivo: str) -> Dict:
        """Cancela uma taxa"""
        try:
            taxa = Taxa.query.get(taxa_id)
            
            if not taxa:
                return {
                    'sucesso': False,
                    'mensagem': 'Taxa não encontrada'
                }
            
            if taxa.is_paga():
                return {
                    'sucesso': False,
                    'mensagem': 'Não é possível cancelar taxa já paga'
                }
            
            taxa.cancelar(motivo)
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Taxa cancelada com sucesso'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao cancelar taxa: {str(e)}'
            }
    
    def verificar_pagamento_reserva(self, reserva_id: int) -> Tuple[bool, str]:
        """Verifica se a taxa da reserva foi paga"""
        taxa = self.buscar_por_reserva(reserva_id)
        
        if not taxa:
            return False, "Taxa de reserva não encontrada"
        
        if taxa['status'] == 'pago':
            return True, "Reserva paga"
        
        if taxa['status'] == 'vencido':
            return False, "Taxa de reserva vencida"
        
        if taxa['status'] == 'cancelado':
            return False, "Taxa de reserva cancelada"
        
        return False, "Pagamento pendente"
    
    def listar_por_associado(self, cpf_associado: str) -> List[Dict]:
        """Lista todas as taxas de um associado"""
        taxas = Taxa.query.filter_by(associado_cpf=cpf_associado).all()
        return [taxa.to_dict() for taxa in taxas]
    
    def relatorio_financeiro(self, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> Dict:
        """Gera relatório financeiro das taxas"""
        query = Taxa.query
        
        if data_inicio:
            query = query.filter(Taxa.data_criacao >= datetime.combine(data_inicio, datetime.min.time()))
        
        if data_fim:
            query = query.filter(Taxa.data_criacao <= datetime.combine(data_fim, datetime.max.time()))
        
        taxas = query.all()
        
        total_arrecadado = sum(float(taxa.valor) for taxa in taxas if taxa.status == 'pago')
        total_pendente = sum(float(taxa.valor) for taxa in taxas if taxa.status == 'pendente')
        total_vencido = sum(float(taxa.valor) for taxa in taxas if taxa.status == 'vencido')
        
        return {
            'periodo': {
                'inicio': data_inicio.strftime('%d/%m/%Y') if data_inicio else 'Início',
                'fim': data_fim.strftime('%d/%m/%Y') if data_fim else 'Hoje'
            },
            'resumo': {
                'total_arrecadado': total_arrecadado,
                'total_pendente': total_pendente,
                'total_vencido': total_vencido,
                'total_geral': total_arrecadado + total_pendente + total_vencido
            },
            'detalhes': {
                'taxas_pagas': len([t for t in taxas if t.status == 'pago']),
                'taxas_pendentes': len([t for t in taxas if t.status == 'pendente']),
                'taxas_vencidas': len([t for t in taxas if t.status == 'vencido']),
                'taxas_canceladas': len([t for t in taxas if t.status == 'cancelado'])
            }
        }