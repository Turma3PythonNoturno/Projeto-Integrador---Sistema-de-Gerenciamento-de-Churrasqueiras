from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from app.models import db, Associado


class AssociadoService:
    """Serviço para gerenciamento de associados do SINT-IFESGO"""
    
    def __init__(self):
        pass
    
    def buscar_por_cpf(self, cpf: str) -> Optional[Dict]:
        """Busca associado por CPF"""
        # Limpar CPF
        cpf_limpo = self._limpar_cpf(cpf)
        
        associado = Associado.query.filter_by(cpf=cpf_limpo).first()
        
        if associado:
            return associado.to_dict()
        
        return None
    
    def verificar_adimplencia(self, cpf: str) -> Tuple[bool, str]:
        """Verifica se associado está adimplente"""
        associado = self.buscar_por_cpf(cpf)
        
        if not associado:
            return False, "CPF não encontrado no cadastro de associados"
        
        if not associado['ativo']:
            return False, "Associado inativo no sistema"
        
        if associado['status_adimplencia'] != 'adimplente':
            return False, "Associado inadimplente com taxa sindical. Regularize sua situação para fazer reservas."
        
        return True, "Associado adimplente"
    
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
            
            # Criar associado
            novo_associado = Associado(
                cpf=cpf_limpo,
                nome=dados['nome'].strip(),
                email=dados['email'].strip(),
                telefone=dados.get('telefone', '').strip() or None,
                status_adimplencia=dados.get('status_adimplencia', 'adimplente'),
                data_ultimo_pagamento=dados.get('data_ultimo_pagamento')
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