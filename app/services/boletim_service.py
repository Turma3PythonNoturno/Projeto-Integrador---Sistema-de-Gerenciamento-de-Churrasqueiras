from typing import Dict, List, Optional
from datetime import datetime, date, timedelta
from app.models import db, Boletim, Associado


class BoletimService:
    """Serviço para gerenciamento de boletins informativos"""
    
    def __init__(self):
        pass
    
    def criar_boletim(self, dados: Dict) -> Dict:
        """Cria novo boletim informativo"""
        try:
            # Validar dados obrigatórios
            if not dados.get('titulo') or not dados.get('conteudo'):
                return {
                    'sucesso': False,
                    'mensagem': 'Título e conteúdo são obrigatórios'
                }
            
            # Processar data de expiração se fornecida
            data_expiracao = None
            if dados.get('data_expiracao'):
                try:
                    data_expiracao = datetime.strptime(dados['data_expiracao'], '%Y-%m-%d %H:%M')
                except ValueError:
                    return {
                        'sucesso': False,
                        'mensagem': 'Formato de data de expiração inválido (use YYYY-MM-DD HH:MM)'
                    }
            
            # Criar boletim
            novo_boletim = Boletim(
                titulo=dados['titulo'].strip(),
                conteudo=dados['conteudo'].strip(),
                tipo=dados.get('tipo', 'geral'),
                prioridade=dados.get('prioridade', 'normal'),
                data_expiracao=data_expiracao,
                autor=dados.get('autor', 'SINT-IFESGO'),
                destinatarios=dados.get('destinatarios', 'todos')
            )
            
            db.session.add(novo_boletim)
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Boletim criado com sucesso',
                'boletim': novo_boletim.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao criar boletim: {str(e)}'
            }
    
    def listar_boletins_ativos(self, cpf_associado: Optional[str] = None) -> List[Dict]:
        """Lista boletins ativos, opcionalmente filtrados para um associado específico"""
        # Buscar boletins ativos
        boletins = Boletim.query.filter_by(ativo=True).order_by(
            Boletim.prioridade.desc(),
            Boletim.data_publicacao.desc()
        ).all()
        
        # Filtrar boletins válidos (não expirados)
        boletins_validos = [b for b in boletins if b.is_ativo()]
        
        # Se CPF fornecido, filtrar por destinatário
        if cpf_associado:
            associado = Associado.query.filter_by(cpf=cpf_associado).first()
            if associado:
                status_adimplencia = associado.status_adimplencia
                boletins_validos = [
                    b for b in boletins_validos 
                    if b.deve_notificar_associado(status_adimplencia)
                ]
        
        return [boletim.to_dict() for boletim in boletins_validos]
    
    def buscar_por_id(self, boletim_id: int) -> Optional[Dict]:
        """Busca boletim por ID"""
        boletim = Boletim.query.get(boletim_id)
        
        if boletim:
            return boletim.to_dict()
        
        return None
    
    def atualizar_boletim(self, boletim_id: int, dados: Dict) -> Dict:
        """Atualiza boletim existente"""
        try:
            boletim = Boletim.query.get(boletim_id)
            
            if not boletim:
                return {
                    'sucesso': False,
                    'mensagem': 'Boletim não encontrado'
                }
            
            # Atualizar campos se fornecidos
            if dados.get('titulo'):
                boletim.titulo = dados['titulo'].strip()
            
            if dados.get('conteudo'):
                boletim.conteudo = dados['conteudo'].strip()
            
            if dados.get('tipo'):
                boletim.tipo = dados['tipo']
            
            if dados.get('prioridade'):
                boletim.prioridade = dados['prioridade']
            
            if dados.get('destinatarios'):
                boletim.destinatarios = dados['destinatarios']
            
            if 'ativo' in dados:
                boletim.ativo = bool(dados['ativo'])
            
            # Processar data de expiração
            if dados.get('data_expiracao'):
                try:
                    boletim.data_expiracao = datetime.strptime(dados['data_expiracao'], '%Y-%m-%d %H:%M')
                except ValueError:
                    return {
                        'sucesso': False,
                        'mensagem': 'Formato de data de expiração inválido'
                    }
            
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Boletim atualizado com sucesso',
                'boletim': boletim.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao atualizar boletim: {str(e)}'
            }
    
    def desativar_boletim(self, boletim_id: int) -> Dict:
        """Desativa um boletim"""
        try:
            boletim = Boletim.query.get(boletim_id)
            
            if not boletim:
                return {
                    'sucesso': False,
                    'mensagem': 'Boletim não encontrado'
                }
            
            boletim.ativo = False
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Boletim desativado com sucesso'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao desativar boletim: {str(e)}'
            }
    
    def listar_boletins_urgentes(self) -> List[Dict]:
        """Lista apenas boletins urgentes ativos"""
        boletins = Boletim.query.filter(
            Boletim.ativo == True,
            db.or_(
                Boletim.prioridade.in_(['alta', 'critica']),
                Boletim.tipo == 'urgente'
            )
        ).order_by(Boletim.data_publicacao.desc()).all()
        
        # Filtrar apenas os válidos (não expirados)
        boletins_validos = [b for b in boletins if b.is_ativo()]
        
        return [boletim.to_dict() for boletim in boletins_validos]
    
    def criar_boletim_automatico_reserva(self, tipo_evento: str, detalhes: Dict) -> Dict:
        """Cria boletim automático relacionado a reservas"""
        templates = {
            'churrasqueira_disponivel': {
                'titulo': 'Churrasqueira Disponível para Reserva',
                'conteudo': 'A churrasqueira está disponível para reserva. Faça já a sua reserva pelo sistema online.',
                'tipo': 'comunicado',
                'prioridade': 'normal'
            },
            'manutencao_programada': {
                'titulo': 'Manutenção Programada da Churrasqueira',
                'conteudo': f"A churrasqueira estará indisponível para manutenção no dia {detalhes.get('data', 'a definir')}. Pedimos compreensão.",
                'tipo': 'comunicado',
                'prioridade': 'alta'
            },
            'lembrete_pagamento': {
                'titulo': 'Lembrete: Taxa Sindical',
                'conteudo': 'Lembramos que a taxa sindical deve estar em dia para fazer reservas da churrasqueira.',
                'tipo': 'comunicado',
                'prioridade': 'normal',
                'destinatarios': 'inadimplentes'
            }
        }
        
        template = templates.get(tipo_evento)
        if not template:
            return {
                'sucesso': False,
                'mensagem': 'Tipo de boletim automático não encontrado'
            }
        
        return self.criar_boletim(template)
    
    def expirar_boletins_antigos(self) -> Dict:
        """Desativa automaticamente boletins expirados"""
        try:
            agora = datetime.utcnow()
            
            # Buscar boletins ativos com data de expiração passada
            boletins_expirados = Boletim.query.filter(
                Boletim.ativo == True,
                Boletim.data_expiracao < agora
            ).all()
            
            count = 0
            for boletim in boletins_expirados:
                boletim.ativo = False
                count += 1
            
            if count > 0:
                db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': f'{count} boletins expirados foram desativados'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao expirar boletins: {str(e)}'
            }
    
    def estatisticas(self) -> Dict:
        """Retorna estatísticas dos boletins"""
        total_boletins = Boletim.query.count()
        boletins_ativos = Boletim.query.filter_by(ativo=True).count()
        boletins_urgentes = Boletim.query.filter(
            Boletim.ativo == True,
            db.or_(
                Boletim.prioridade.in_(['alta', 'critica']),
                Boletim.tipo == 'urgente'
            )
        ).count()
        
        return {
            'total_boletins': total_boletins,
            'boletins_ativos': boletins_ativos,
            'boletins_urgentes': boletins_urgentes,
            'boletins_inativos': total_boletins - boletins_ativos
        }