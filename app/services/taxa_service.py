from typing import Dict, List, Optional, Tuple
from datetime import datetime, date, timedelta
from decimal import Decimal
import re
from app.models import db, Taxa
from config import Config


class TaxaService:
    """Serviço para gerenciamento de taxas de reserva"""
    
    def __init__(self):
        self.config = Config()
    
    def _limpar_cpf(self, cpf: str) -> str:
        """Remove formatação do CPF"""
        if not cpf:
            return cpf
        return re.sub(r'[^\d]', '', cpf)
    
    def gerar_taxa_reserva(self, reserva_id: int, cpf_associado: str, valor: Optional[Decimal] = None) -> Dict:
        """Gera uma nova taxa de reserva
        
        Args:
            reserva_id: ID da reserva
            cpf_associado: CPF do associado
            valor: Valor opcional da taxa (usa padrão da config se não fornecido)
        """
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
            
            # Se não foi fornecido valor, buscar o preço da churrasqueira
            if valor is None:
                from app.models import Reserva, Churrasqueira
                reserva = Reserva.query.get(reserva_id)
                if reserva and reserva.churrasqueira:
                    valor = Decimal(str(reserva.churrasqueira.preco))
                else:
                    valor = Decimal(str(self.config.TAXA_RESERVA['valor']))
            else:
                valor = Decimal(str(valor))
            
            # Criar nova taxa (limpar CPF para manter consistência com banco de associados)
            nova_taxa = Taxa(
                valor=valor,
                tipo='reserva',
                status='pendente',
                data_vencimento=date.today() + timedelta(days=1),  # 24h para pagamento
                reserva_id=reserva_id,
                associado_cpf=self._limpar_cpf(cpf_associado)
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
    
    def obter_por_id(self, taxa_id: int) -> Optional[Dict]:
        """Obtém uma taxa pelo ID"""
        taxa = Taxa.query.get(taxa_id)
        if taxa:
            return taxa.to_dict()
        return None
    
    def listar_todas_taxas(self, cpf_associado: Optional[str] = None) -> List[Dict]:
        """Lista todas as taxas do sistema"""
        query = Taxa.query
        
        if cpf_associado:
            query = query.filter_by(associado_cpf=cpf_associado)
        
        taxas = query.all()
        print(f"\n=== DEBUG taxa_service.listar_todas_taxas ===")
        print(f"Total de taxas encontradas: {len(taxas)}")
        for taxa in taxas:
            print(f"  Taxa #{taxa.id}: R$ {taxa.valor} - Status: {taxa.status} - CPF: {taxa.associado_cpf}")
        
        result = [taxa.to_dict() for taxa in taxas]
        print(f"Resultado convertido para dict: {len(result)} itens")
        return result
    
    def listar_taxas_pendentes(self, cpf_associado: Optional[str] = None) -> List[Dict]:
        """Lista taxas pendentes, opcionalmente filtradas por associado"""
        query = Taxa.query.filter_by(status='pendente')
        
        if cpf_associado:
            query = query.filter_by(associado_cpf=cpf_associado)
        
        taxas = query.all()
        return [taxa.to_dict() for taxa in taxas]
    
    def atualizar_taxas_vencidas(self) -> int:
        """Atualiza automaticamente o status de taxas vencidas
        
        Returns:
            Número de taxas atualizadas
        """
        hoje = date.today()
        atualizadas = 0
        
        # Buscar taxas pendentes com data de vencimento passada
        taxas_vencidas = Taxa.query.filter(
            Taxa.status == 'pendente',
            Taxa.data_vencimento < hoje
        ).all()
        
        # Atualizar status para vencido
        for taxa in taxas_vencidas:
            taxa.status = 'vencido'
            atualizadas += 1
        
        if atualizadas > 0:
            db.session.commit()
        
        return atualizadas
    
    def listar_taxas_vencidas(self) -> List[Dict]:
        """Lista taxas vencidas"""
        # Atualizar status primeiro
        self.atualizar_taxas_vencidas()
        
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
    
    def verificar_vencimentos(self) -> Dict:
        """Verifica e atualiza status de taxas vencidas"""
        try:
            hoje = date.today()
            
            # Buscar taxas pendentes com vencimento no passado
            taxas_vencidas = Taxa.query.filter(
                Taxa.status == 'pendente',
                Taxa.data_vencimento < hoje
            ).all()
            
            processadas = 0
            for taxa in taxas_vencidas:
                taxa.marcar_como_vencida()
                processadas += 1
            
            if processadas > 0:
                db.session.commit()
            
            # Contar total de taxas vencidas
            total_vencidas = Taxa.query.filter_by(status='vencido').count()
            
            return {
                'sucesso': True,
                'mensagem': f'{processadas} taxa(s) marcada(s) como vencida(s)',
                'processadas': processadas,
                'vencidas': total_vencidas
            }
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao verificar vencimentos: {str(e)}',
                'processadas': 0,
                'vencidas': 0
            }
    
    def gerar_relatorio(self, periodo: Optional[str] = None) -> Dict:
        """Gera relatório de taxas em formato CSV
        
        Args:
            periodo: String no formato YYYY-MM para filtrar por mês/ano
        """
        try:
            query = Taxa.query
            
            # Filtrar por período se fornecido
            if periodo:
                try:
                    from datetime import datetime as dt
                    mes_ano = dt.strptime(periodo, '%Y-%m')
                    data_inicio = mes_ano.date()
                    # Próximo mês
                    if mes_ano.month == 12:
                        data_fim = data_inicio.replace(year=mes_ano.year + 1, month=1)
                    else:
                        data_fim = data_inicio.replace(month=mes_ano.month + 1)
                    
                    query = query.filter(
                        Taxa.data_criacao >= datetime.combine(data_inicio, datetime.min.time()),
                        Taxa.data_criacao < datetime.combine(data_fim, datetime.min.time())
                    )
                except ValueError:
                    return {
                        'sucesso': False,
                        'mensagem': 'Formato de período inválido. Use YYYY-MM'
                    }
            
            taxas = query.all()
            
            # Gerar CSV com encoding UTF-8 explícito
            linhas = ['ID,CPF Associado,Tipo,Valor,Status,Data Vencimento,Data Criacao,Reserva ID\n']
            
            for taxa in taxas:
                linha = f'{taxa.id},{taxa.associado_cpf},{taxa.tipo},R$ {taxa.valor:.2f},{taxa.status},'
                linha += f'{taxa.data_vencimento.strftime("%d/%m/%Y") if taxa.data_vencimento else "N/A"},'
                linha += f'{taxa.data_criacao.strftime("%d/%m/%Y %H:%M") if taxa.data_criacao else "N/A"},'
                linha += f'{taxa.reserva_id or "N/A"}\n'
                linhas.append(linha)
            
            conteudo = ''.join(linhas)
            # Garantir encoding UTF-8
            conteudo = conteudo.encode('utf-8').decode('utf-8')
            
            return {
                'sucesso': True,
                'conteudo': conteudo,
                'total_linhas': len(taxas)
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao gerar relatório: {str(e)}'
            }
    
    def gerar_comprovante(self, taxa_id: int) -> Dict:
        """Gera comprovante de pagamento em formato texto/HTML"""
        try:
            taxa = Taxa.query.get(taxa_id)
            
            if not taxa:
                return {
                    'sucesso': False,
                    'mensagem': 'Taxa não encontrada'
                }
            
            # Gerar HTML do comprovante
            html = f"""
            <html>
            <head>
                <meta charset="utf-8">
                <title>Comprovante de Taxa</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; }}
                    .section {{ margin: 20px 0; padding: 10px; }}
                    .label {{ font-weight: bold; }}
                    table {{ width: 100%; border-collapse: collapse; }}
                    td {{ padding: 8px; border: 1px solid #ddd; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>COMPROVANTE DE TAXA</h2>
                    <p>SINT-IFESGO - Sistema de Reserva de Churrasqueira</p>
                </div>
                
                <div class="section">
                    <p><span class="label">ID da Taxa:</span> {taxa.id}</p>
                    <p><span class="label">CPF do Associado:</span> {taxa.associado_cpf}</p>
                    <p><span class="label">Tipo:</span> {taxa.tipo.upper()}</p>
                    <p><span class="label">Valor:</span> R$ {taxa.valor:.2f}</p>
                    <p><span class="label">Status:</span> {taxa.status.upper()}</p>
                    <p><span class="label">Data de Vencimento:</span> {taxa.data_vencimento.strftime("%d/%m/%Y") if taxa.data_vencimento else "N/A"}</p>
                    <p><span class="label">Data de Criação:</span> {taxa.data_criacao.strftime("%d/%m/%Y %H:%M") if taxa.data_criacao else "N/A"}</p>
                    <p><span class="label">Código de Pagamento:</span> {taxa.codigo_pagamento or "N/A"}</p>
                </div>
                
                <div class="section" style="margin-top: 40px; text-align: center; color: #666; font-size: 12px;">
                    <p>Documento gerado automaticamente pelo sistema SINT-IFESGO</p>
                    <p>Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}</p>
                </div>
            </body>
            </html>
            """
            
            return {
                'sucesso': True,
                'conteudo': html
            }
            
        except Exception as e:
            return {
                'sucesso': False,
                'mensagem': f'Erro ao gerar comprovante: {str(e)}'
            }