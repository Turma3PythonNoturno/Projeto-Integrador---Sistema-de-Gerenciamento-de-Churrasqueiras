from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class Boletim:
    """Entidade de domínio para Boletim Informativo"""
    
    titulo: str
    conteudo: str
    tipo: str = 'geral'  # geral, urgente, comunicado, evento
    prioridade: str = 'normal'  # baixa, normal, alta, critica
    data_publicacao: Optional[datetime] = None
    data_expiracao: Optional[datetime] = None
    ativo: bool = True
    autor: Optional[str] = None
    destinatarios: str = 'todos'  # todos, adimplentes, inadimplentes
    id: Optional[int] = None
    
    def __post_init__(self):
        """Inicialização pós-criação"""
        if self.data_publicacao is None:
            self.data_publicacao = datetime.utcnow()
    
    def is_ativo(self) -> bool:
        """Verifica se o boletim está ativo"""
        if not self.ativo:
            return False
        
        # Verifica se não expirou
        if self.data_expiracao and datetime.utcnow() > self.data_expiracao:
            return False
        
        return True
    
    def is_urgente(self) -> bool:
        """Verifica se é boletim urgente"""
        return self.prioridade in ['alta', 'critica'] or self.tipo == 'urgente'
    
    def deve_notificar_associado(self, status_adimplencia: str) -> bool:
        """Verifica se deve notificar associado baseado no status"""
        if self.destinatarios == 'todos':
            return True
        
        if self.destinatarios == 'adimplentes' and status_adimplencia == 'adimplente':
            return True
        
        if self.destinatarios == 'inadimplentes' and status_adimplencia == 'inadimplente':
            return True
        
        return False
    
    def resumo(self, max_chars: int = 100) -> str:
        """Retorna resumo do conteúdo"""
        if len(self.conteudo) <= max_chars:
            return self.conteudo
        
        return self.conteudo[:max_chars] + "..."
    
    def to_dict(self) -> dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'titulo': self.titulo,
            'conteudo': self.conteudo,
            'resumo': self.resumo(),
            'tipo': self.tipo,
            'prioridade': self.prioridade,
            'data_publicacao': self.data_publicacao.strftime('%d/%m/%Y %H:%M') if self.data_publicacao else '',
            'data_expiracao': self.data_expiracao.strftime('%d/%m/%Y %H:%M') if self.data_expiracao else None,
            'ativo': self.ativo,
            'is_ativo': self.is_ativo(),
            'is_urgente': self.is_urgente(),
            'autor': self.autor or 'SINT-IFESGO',
            'destinatarios': self.destinatarios,
            'classe_css': self._get_classe_css()
        }
    
    def _get_classe_css(self) -> str:
        """Retorna classe CSS baseada no tipo e prioridade"""
        if self.prioridade == 'critica':
            return 'alert-danger'
        elif self.prioridade == 'alta' or self.tipo == 'urgente':
            return 'alert-warning'
        elif self.tipo == 'evento':
            return 'alert-info'
        else:
            return 'alert-primary'