"""
Serviço de Integração com Web Service Externo (SINSIND)

Este módulo gerencia a integração com o web service do sindicato para
consulta de dados dos associados em tempo real.

Funcionalidades:
- Consulta de associados por CPF
- Verificação de adimplência
- Cache de respostas para otimização
- Fallback para banco local em caso de falha

Autor: Sistema SINT-IFESGO
Versão: 1.0
"""

import requests
import json
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from config import Config

class WebServiceSINSIND:
    """
    Cliente para integração com o web service do SINSIND.
    
    Gerencia consultas de associados, verificação de adimplência
    e cache de respostas para otimização de performance.
    """
    
    def __init__(self):
        """Inicializa o cliente do web service."""
        self.config = Config()
        self.base_url = self.config.WEB_SERVICE_URL
        self.credentials = self.config.WEB_SERVICE_CREDENTIALS
        self.timeout = self.config.WEB_SERVICE_TIMEOUT
        self.enabled = self.config.WEB_SERVICE_ENABLED
        
        # Cache simples em memória (em produção, usar Redis)
        self._cache = {}
        self._cache_ttl = timedelta(minutes=5)  # Cache por 5 minutos
        
        # Logger para debugging
        self.logger = logging.getLogger(__name__)
    
    def _is_cache_valid(self, cpf: str) -> bool:
        """Verifica se o cache para um CPF ainda é válido."""
        if cpf not in self._cache:
            return False
        
        cached_time = self._cache[cpf].get('timestamp')
        if not cached_time:
            return False
        
        return datetime.now() - cached_time < self._cache_ttl
    
    def _get_from_cache(self, cpf: str) -> Optional[Dict]:
        """Recupera dados do cache se válidos."""
        if self._is_cache_valid(cpf):
            return self._cache[cpf]['data']
        return None
    
    def _set_cache(self, cpf: str, data: Dict) -> None:
        """Armazena dados no cache."""
        self._cache[cpf] = {
            'data': data,
            'timestamp': datetime.now()
        }
    
    def consultar_associado(self, cpf: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Consulta dados de um associado no web service.
        
        Args:
            cpf (str): CPF do associado (apenas números)
            
        Returns:
            Tuple[bool, Optional[Dict], str]: (sucesso, dados, mensagem)
        """
        
        # Verificar se o serviço está habilitado
        if not self.enabled:
            return False, None, "Web service desabilitado"
        
        # Limpar CPF (apenas números)
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        if len(cpf_limpo) != 11:
            return False, None, "CPF deve conter 11 dígitos"
        
        # Verificar cache primeiro
        cached_data = self._get_from_cache(cpf_limpo)
        if cached_data:
            return True, cached_data, "Dados do cache"
        
        try:
            # Preparar payload para requisição
            payload = {
                **self.credentials,
                "cpf": cpf_limpo,
                "acao": "consultar_associado"
            }
            
            # Fazer requisição HTTP POST
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            # Verificar status da resposta
            if response.status_code != 200:
                return False, None, f"Erro HTTP {response.status_code}"
            
            # Tentar fazer parse do JSON
            try:
                data = response.json()
            except json.JSONDecodeError:
                return False, None, "Resposta inválida do servidor"
            
            # Verificar formato da resposta do web service SINSIND
            if data.get('status') == 'success':
                # Formato do SINSIND: {"status": "success", "data": [...]}
                dados_array = data.get('data', [])
                if not dados_array:
                    return False, None, "Associado não encontrado no web service"
                
                # Pegar primeiro resultado (deveria ser único por CPF)
                associado_data = dados_array[0]
                
            elif data.get('sucesso'):
                # Formato alternativo: {"sucesso": true, "associado": {...}}
                associado_data = data.get('associado', {})
                if not associado_data:
                    return False, None, "Associado não encontrado"
                    
            else:
                # Erro na consulta
                if data.get('status') == 'error':
                    mensagem = data.get('message', 'Erro no web service')
                else:
                    mensagem = data.get('mensagem', 'Erro desconhecido')
                return False, None, mensagem
            
            # Padronizar dados do SINSIND para compatibilidade
            # O SINSIND retorna: inadimplencia: "NÃO"/"SIM", situacao: "NÃO FILIADO"/"FILIADO"
            inadimplencia = str(associado_data.get('inadimplencia', 'SIM') or 'SIM').upper()
            situacao = str(associado_data.get('situacao', '') or '').upper()
            
            # Associado é considerado adimplente se:
            # 1. Não tem inadimplência (inadimplencia = "NÃO")
            # 2. Está filiado ou é aposentado (categoria específica)
            categoria = str(associado_data.get('categoria', '') or '').upper()
            lotacao = str(associado_data.get('lotacao', '') or '').upper()
            
            adimplente = (inadimplencia == 'NÃO')  # Sem inadimplência
            
            dados_padronizados = {
                'cpf': cpf_limpo,
                'cpf_formatado': f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}",
                'nome': associado_data.get('nome', ''),
                'email': associado_data.get('email', ''),  # Web service pode não ter
                'telefone': associado_data.get('telefone', ''),  # Web service pode não ter
                'adimplente': adimplente,
                'status_adimplencia': 'adimplente' if adimplente else 'inadimplente',
                'categoria': categoria,
                'lotacao': lotacao,
                'situacao_sindical': situacao,
                'inadimplencia_sindical': inadimplencia,
                'data_ultimo_pagamento': associado_data.get('data_ultimo_pagamento'),
                'ativo': True,  # Se está no web service, considera ativo
                'origem': 'web_service_sinsind'
            }
            
            # Armazenar no cache
            self._set_cache(cpf_limpo, dados_padronizados)
            
            return True, dados_padronizados, "Consulta realizada com sucesso"
            
        except requests.exceptions.Timeout:
            return False, None, "Timeout na conexão com o web service"
        except requests.exceptions.ConnectionError:
            return False, None, "Erro de conexão com o web service"
        except requests.exceptions.RequestException as e:
            return False, None, f"Erro na requisição: {str(e)}"
        except Exception as e:
            self.logger.error(f"Erro inesperado na consulta: {str(e)}")
            return False, None, "Erro interno do sistema"
    
    def verificar_adimplencia(self, cpf: str) -> Tuple[bool, str]:
        """
        Verifica apenas o status de adimplência de um associado.
        
        Args:
            cpf (str): CPF do associado
            
        Returns:
            Tuple[bool, str]: (adimplente, mensagem)
        """
        sucesso, dados, mensagem = self.consultar_associado(cpf)
        
        if not sucesso:
            return False, mensagem
        
        if not dados:
            return False, "Dados não disponíveis"
        
        adimplente = dados.get('adimplente', False)
        status_msg = "Associado adimplente" if adimplente else "Associado inadimplente"
        
        return adimplente, status_msg
    
    def limpar_cache(self) -> None:
        """Limpa todo o cache."""
        self._cache.clear()
    
    def status_servico(self) -> Dict:
        """
        Verifica o status do web service.
        
        Returns:
            Dict: Informações sobre o status do serviço
        """
        if not self.enabled:
            return {
                'disponivel': False,
                'mensagem': 'Web service desabilitado na configuração',
                'cache_entries': len(self._cache)
            }
        
        try:
            # Teste simples de conectividade
            response = requests.get(
                self.base_url,
                timeout=5,
                headers={'User-Agent': 'SINT-IFESGO-Sistema/1.0'}
            )
            
            return {
                'disponivel': True,
                'status_code': response.status_code,
                'mensagem': 'Web service respondendo',
                'cache_entries': len(self._cache),
                'url': self.base_url
            }
            
        except Exception as e:
            return {
                'disponivel': False,
                'mensagem': f'Web service indisponível: {str(e)}',
                'cache_entries': len(self._cache),
                'url': self.base_url
            }


# Instância global do web service
web_service_sinsind = WebServiceSINSIND()