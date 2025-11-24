from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from app.models import db, Associado
from app.services.webservice_sinsind import web_service_sinsind
import logging


class AssociadoService:
    """Serviço para gerenciamento de associados do SINT-IFESGO"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def buscar_por_cpf(self, cpf: str) -> Optional[Dict]:
        """Busca associado por CPF - primeiro no web service, depois no banco local"""
        # Limpar CPF
        cpf_limpo = self._limpar_cpf(cpf)
        
        # Tentar buscar no web service primeiro
        try:
            sucesso, dados_ws, mensagem = web_service_sinsind.consultar_associado(cpf_limpo)
            
            if sucesso and dados_ws:
                self.logger.info(f"Associado {cpf_limpo} encontrado no web service")
                return dados_ws
                
        except Exception as e:
            self.logger.warning(f"Erro ao consultar web service para CPF {cpf_limpo}: {str(e)}")
        
        # Fallback para banco local
        associado = Associado.query.filter_by(cpf=cpf_limpo).first()
        
        if associado:
            self.logger.info(f"Associado {cpf_limpo} encontrado no banco local")
            dados_local = associado.to_dict()
            dados_local['origem'] = 'banco_local'
            return dados_local
        
        return None
    
    def verificar_adimplencia(self, cpf: str) -> Tuple[bool, str]:
        """Verifica se associado está adimplente - primeiro no web service, depois no banco local"""
        # Tentar verificar no web service primeiro
        try:
            adimplente_ws, mensagem_ws = web_service_sinsind.verificar_adimplencia(cpf)
            
            # Se o web service responder, usar essa informação
            if mensagem_ws != "Web service desabilitado":
                return adimplente_ws, mensagem_ws
                
        except Exception as e:
            self.logger.warning(f"Erro ao verificar adimplência no web service para CPF {cpf}: {str(e)}")
        
        # Fallback para verificação local
        associado = self.buscar_por_cpf(cpf)
        
        if not associado:
            return False, "CPF não encontrado no cadastro de associados"
        
        if not associado.get('ativo', True):
            return False, "Associado inativo no sistema"
        
        # Verificar adimplência (compatível com ambos os formatos)
        adimplente = False
        if associado.get('adimplente') is not None:
            # Formato do web service
            adimplente = associado['adimplente']
        elif associado.get('status_adimplencia'):
            # Formato do banco local
            adimplente = associado['status_adimplencia'] == 'adimplente'
        
        if not adimplente:
            return False, "Associado inadimplente com taxa sindical. Regularize sua situação para fazer reservas."
        
        origem = associado.get('origem', 'banco_local')
        return True, f"Associado adimplente (verificado via {origem})"
    
    def criar_associado(self, dados: Dict) -> Dict:
        """Cria novo associado"""
        try:
            # Validar CPF
            cpf_limpo = self._limpar_cpf(dados['cpf'])
            cpf_valido, cpf_msg = Associado.validar_cpf(cpf_limpo)
            
            if not cpf_valido:
                return {
                    'sucesso': False,
                    'mensagem': cpf_msg
                }
            
            # Verificar se CPF já existe
            if self.buscar_por_cpf(cpf_limpo):
                return {
                    'sucesso': False,
                    'mensagem': 'CPF já cadastrado no sistema'
                }
            
            # Verificar se email já existe
            email_existe = Associado.query.filter_by(email=dados['email']).first()
            if email_existe:
                return {
                    'sucesso': False,
                    'mensagem': 'Email já cadastrado no sistema'
                }
            
            # Processar data de último pagamento
            data_ultimo_pagamento = None
            if dados.get('data_ultimo_pagamento'):
                try:
                    # Converter string para date
                    data_str = dados['data_ultimo_pagamento']
                    if isinstance(data_str, str):
                        data_ultimo_pagamento = datetime.strptime(data_str, '%Y-%m-%d').date()
                    elif isinstance(data_str, date):
                        data_ultimo_pagamento = data_str
                except ValueError:
                    pass  # Ignora erro de conversão, deixa como None
            
            # Criar associado
            novo_associado = Associado(
                cpf=cpf_limpo,
                nome=dados['nome'].strip(),
                email=dados['email'].strip(),
                telefone=dados.get('telefone', '').strip() or None,
                status_adimplencia=dados.get('status_adimplencia', 'adimplente'),
                data_ultimo_pagamento=data_ultimo_pagamento
            )
            
            db.session.add(novo_associado)
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Associado cadastrado com sucesso',
                'associado': novo_associado.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao cadastrar associado: {str(e)}'
            }
    
    def atualizar_status_adimplencia(self, cpf: str, status: str, data_pagamento: date = None) -> Dict:
        """Atualiza status de adimplência do associado"""
        try:
            cpf_limpo = self._limpar_cpf(cpf)
            associado = Associado.query.filter_by(cpf=cpf_limpo).first()
            
            if not associado:
                return {
                    'sucesso': False,
                    'mensagem': 'Associado não encontrado'
                }
            
            associado.status_adimplencia = status
            
            if status == 'adimplente' and data_pagamento:
                associado.data_ultimo_pagamento = data_pagamento
            
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': f'Status atualizado para {status}',
                'associado': associado.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao atualizar status: {str(e)}'
            }
    
    def listar_inadimplentes(self) -> List[Dict]:
        """Lista todos os associados inadimplentes"""
        associados = Associado.query.filter_by(
            status_adimplencia='inadimplente',
            ativo=True
        ).all()
        
        return [associado.to_dict() for associado in associados]
    
    def listar_todos(self, apenas_ativos: bool = True) -> List[Dict]:
        """Lista todos os associados"""
        query = Associado.query
        
        if apenas_ativos:
            query = query.filter_by(ativo=True)
        
        associados = query.all()
        return [associado.to_dict() for associado in associados]
    
    def buscar_por_email(self, email: str) -> Optional[Dict]:
        """Busca associado por email"""
        associado = Associado.query.filter_by(email=email.strip()).first()
        
        if associado:
            return associado.to_dict()
        
        return None
    
    def _limpar_cpf(self, cpf: str) -> str:
        """Remove formatação do CPF"""
        import re
        return re.sub(r'[^\d]', '', cpf)
    
    def desativar_associado(self, cpf: str, motivo: str = None) -> Dict:
        """Desativa um associado"""
        try:
            cpf_limpo = self._limpar_cpf(cpf)
            associado = Associado.query.filter_by(cpf=cpf_limpo).first()
            
            if not associado:
                return {
                    'sucesso': False,
                    'mensagem': 'Associado não encontrado'
                }
            
            associado.ativo = False
            
            if motivo:
                # Aqui poderia adicionar um campo de observações se necessário
                pass
            
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Associado desativado com sucesso'
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao desativar associado: {str(e)}'
            }
    
    def atualizar_associado(self, cpf_original: str, dados: Dict) -> Dict:
        """Atualiza dados de um associado existente"""
        try:
            # Buscar associado pelo CPF original
            cpf_limpo = self._limpar_cpf(cpf_original)
            associado = Associado.query.filter_by(cpf=cpf_limpo).first()
            
            if not associado:
                return {
                    'sucesso': False,
                    'mensagem': 'Associado não encontrado'
                }
            
            # Atualizar campos permitidos
            if 'nome' in dados and dados['nome'].strip():
                associado.nome = dados['nome'].strip()
            
            if 'email' in dados and dados['email'].strip():
                email = dados['email'].strip()
                
                # Verificar se email já existe (exceto o próprio associado)
                email_existe = Associado.query.filter(
                    Associado.email == email,
                    Associado.id != associado.id
                ).first()
                
                if email_existe:
                    return {
                        'sucesso': False,
                        'mensagem': 'Este email já está em uso por outro associado'
                    }
                
                associado.email = email
            
            if 'telefone' in dados:
                associado.telefone = dados['telefone'].strip() if dados['telefone'] else None
            
            if 'status_adimplencia' in dados:
                status = dados['status_adimplencia']
                if status in ['adimplente', 'inadimplente']:
                    associado.status_adimplencia = status
                    
                    # Se marcar como adimplente, atualizar data do pagamento
                    if status == 'adimplente':
                        associado.data_ultimo_pagamento = date.today()
            
            # CPF não deve ser alterado após criação por questões de integridade
            
            db.session.commit()
            
            return {
                'sucesso': True,
                'mensagem': 'Associado atualizado com sucesso',
                'associado': associado.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'sucesso': False,
                'mensagem': f'Erro ao atualizar associado: {str(e)}'
            }