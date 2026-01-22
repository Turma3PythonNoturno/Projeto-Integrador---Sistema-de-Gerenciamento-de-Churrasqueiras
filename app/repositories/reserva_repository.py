from typing import List, Dict, Optional, Tuple
from datetime import date, time, datetime
from app.interfaces.reserva_interfaces import IReservaRepository
from app.entities.reserva import Reserva as ReservaEntity
from app.models import db, Reserva as ReservaModel


class ReservaRepository(IReservaRepository):
    """Repositório concreto para reservas usando SQLAlchemy"""
    
    def criar_reserva(self, reserva_data: Dict) -> Dict:
        """Cria uma nova reserva no banco de dados"""
        try:
            # Limpar CPF (remover pontos e traços) se fornecido
            cpf_associado = reserva_data.get('cpf_associado')
            if cpf_associado:
                cpf_associado = ''.join(filter(str.isdigit, str(cpf_associado)))
            
            nova_reserva = ReservaModel(
                nome=reserva_data['nome'],
                churrasqueira_id=reserva_data['churrasqueira_id'],  
                cpf_associado=cpf_associado,
                data_reserva=reserva_data['data_reserva'],
                horario_inicio=reserva_data['horario_inicio'],
                horario_fim=reserva_data['horario_fim'],
                email=reserva_data.get('email'),
                telefone=reserva_data.get('telefone'),
                numero_convidados=reserva_data.get('numero_convidados', 1),
                observacoes=reserva_data.get('observacoes'),
                status=reserva_data.get('status', 'ativa')
            )
            
            db.session.add(nova_reserva)
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Reserva criada com sucesso',
                'reserva_id': nova_reserva.id,
                'reserva': self._model_to_dict(nova_reserva)
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao criar reserva: {str(e)}'
            }
    
    def buscar_por_id(self, reserva_id: int) -> Optional[Dict]:
        """Busca reserva por ID"""
        try:
            reserva = ReservaModel.query.get(reserva_id)
            if reserva:
                return self._model_to_dict(reserva)
            return None
        except Exception:
            return None
    
    def listar_reservas_ativas(self, data_inicio: date, data_fim: date) -> List[Dict]:
        """Lista reservas ativas em um período"""
        try:
            reservas = ReservaModel.query.filter(
                ReservaModel.data_reserva >= data_inicio,
                ReservaModel.data_reserva <= data_fim,
                ReservaModel.status == 'ativa'
            ).order_by(ReservaModel.data_reserva, ReservaModel.horario_inicio).all()
            
            return [self._model_to_dict(reserva) for reserva in reservas]
        except Exception:
            return []
    
    def verificar_disponibilidade(self, data: date, inicio: time, fim: time, churrasqueira_id: Optional[int] = None) -> Tuple[bool, str]:
        """Verifica disponibilidade de horário.

        Se churrasqueira_id for fornecido, verifica APENAS aquele equipamento.
        Se não for, verifica se HÁ ALGUM equipamento livre (lógica original).
        """
        try:
            # Se foi especificada uma churrasqueira, a verificação é direta
            if churrasqueira_id:
                reservas_conflitantes = ReservaModel.query.filter(
                    ReservaModel.data_reserva == data,
                    ReservaModel.churrasqueira_id == churrasqueira_id,
                    ReservaModel.status.in_(('ativa', 'pendente', 'paga', 'confirmada')),
                    ReservaModel.horario_inicio < fim,
                    ReservaModel.horario_fim > inicio
                ).all()

                if reservas_conflitantes:
                    detalhes = []
                    for r in reservas_conflitantes:
                        detalhes.append(f"{r.horario_inicio.strftime('%H:%M')} - {r.horario_fim.strftime('%H:%M')} ({r.nome})")
                    return False, f"Churrasqueira ocupada neste horário: {'; '.join(detalhes)}"
                
                return True, "Horário disponível"

            # === Lógica para 'Qualquer Churrasqueira' (usada na busca inicial) ===
            
            # Buscar todas as churrasqueiras cadastradas
            from app.models import Churrasqueira

            todas_ids = [c.id for c in Churrasqueira.query.all()]

            # Reservas ativas/pagas/pendentes que conflitam no dia e horário
            reservas_conflitantes = ReservaModel.query.filter(
                ReservaModel.data_reserva == data,
                ReservaModel.status.in_(('ativa', 'pendente', 'paga', 'confirmada')),
                ReservaModel.horario_inicio < fim,
                ReservaModel.horario_fim > inicio
            ).all()

            # IDs das churrasqueiras que estão ocupadas nesse período
            ids_ocupadas = {r.churrasqueira_id for r in reservas_conflitantes}

            # Se existir ao menos uma churrasqueira livre -> disponível
            ids_disponiveis = [cid for cid in todas_ids if cid not in ids_ocupadas]

            if len(ids_disponiveis) > 0:
                return True, "Horário disponível"

            # Caso todas ocupadas, construir mensagem de conflito com detalhes
            mensagem = "Todos os equipamentos estão ocupados neste horário"
            if reservas_conflitantes:
                detalhes = []
                for r in reservas_conflitantes:
                    detalhes.append(f"{r.horario_inicio.strftime('%H:%M')} - {r.horario_fim.strftime('%H:%M')} ({r.nome})")
                mensagem = "Conflito: " + "; ".join(detalhes)

            return False, mensagem

        except Exception as e:
            return False, f"Erro ao verificar disponibilidade: {str(e)}"
    
    def cancelar_reserva(self, reserva_id: int) -> bool:
        """Cancela uma reserva e suas taxas associadas"""
        try:
            from app.models import Taxa
            
            reserva = ReservaModel.query.get(reserva_id)
            if reserva:
                # Cancelar taxas associadas (não deletar, apenas marcar como canceladas)
                taxas = Taxa.query.filter_by(reserva_id=reserva_id).all()
                for taxa in taxas:
                    if taxa.status in ['pendente', 'vencido']:
                        taxa.status = 'cancelado'
                
                # Cancelar a reserva
                reserva.status = 'cancelada'
                db.session.commit()
                return True
            return False
        except Exception as e:
            db.session.rollback()
            return False
    
    def obter_horarios_ocupados(self, data_reserva: date) -> List[Dict]:
        """Retorna lista de horários ocupados para uma data"""
        try:
            reservas = ReservaModel.query.filter(
                ReservaModel.data_reserva == data_reserva,
                ReservaModel.status == 'ativa'
            ).all()
            
            horarios_ocupados = []
            for reserva in reservas:
                horarios_ocupados.append({
                    'inicio': reserva.horario_inicio.strftime('%H:%M'),
                    'fim': reserva.horario_fim.strftime('%H:%M'),
                    'nome': reserva.nome
                })
            
            return horarios_ocupados
        except Exception:
            return []
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas das reservas"""
        try:
            # Total de reservas ativas
            total_ativas = ReservaModel.query.filter(
                ReservaModel.status == 'ativa',
                ReservaModel.data_reserva >= date.today()
            ).count()
            
            # Reservas do mês atual
            primeiro_dia_mes = date.today().replace(day=1)
            reservas_mes = ReservaModel.query.filter(
                ReservaModel.data_reserva >= primeiro_dia_mes,
                ReservaModel.status == 'ativa'
            ).count()
            
            # Horário mais popular
            horario_popular_query = db.session.query(
                ReservaModel.horario_inicio,
                db.func.count(ReservaModel.id).label('total')
            ).filter(
                ReservaModel.status == 'ativa'
            ).group_by(
                ReservaModel.horario_inicio
            ).order_by(
                db.func.count(ReservaModel.id).desc()
            ).first()
            
            horario_popular = horario_popular_query[0].strftime('%H:%M') if horario_popular_query else "N/A"
            
            return {
                'total_reservas_ativas': total_ativas,
                'reservas_mes_atual': reservas_mes,
                'horario_mais_popular': horario_popular
            }
        except Exception:
            return {
                'total_reservas_ativas': 0,
                'reservas_mes_atual': 0,
                'horario_mais_popular': 'N/A'
            }
    
    def _model_to_dict(self, reserva: ReservaModel) -> Dict:
        """Converte model do SQLAlchemy para dicionário"""
        return {
            'id': reserva.id,
            'nome': reserva.nome,
            'email': reserva.email,
            'telefone': reserva.telefone,
            'cpf_associado': reserva.cpf_associado or '',
            'churrasqueira_id': reserva.churrasqueira_id,
            'data_reserva': reserva.data_reserva.strftime('%d/%m/%Y'),
            'data_reserva_iso': reserva.data_reserva.strftime('%Y-%m-%d'),
            'horario_inicio': reserva.horario_inicio.strftime('%H:%M'),
            'horario_fim': reserva.horario_fim.strftime('%H:%M'),
            'numero_convidados': reserva.numero_convidados,
            'status': reserva.status,
            'status_display': 'Ativa' if reserva.status == 'ativa' else 'Cancelada',
            'data_criacao': reserva.data_criacao.strftime('%d/%m/%Y %H:%M'),
            'observacoes': reserva.observacoes or ''
        }