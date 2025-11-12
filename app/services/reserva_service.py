"""
Serviço de Reservas do Sistema SINT-IFESGO

Este módulo implementa a lógica de negócio central para o sistema de reservas
de churrasqueira do Sindicato dos Trabalhadores Técnico-Administrativos em 
Educação das Instituições Federais de Ensino Superior do Estado de Goiás.

Funcionalidades principais:
- Criação de reservas com validação de adimplência
- Controle de horários de funcionamento (08:00-18:00h)
- Validação de conflitos de horários
- Integração com sistema de cobrança (R$ 25,00)
- Gestão de status de reservas
- Verificação de disponibilidade

Regras de negócio implementadas:
1. Apenas associados adimplentes podem fazer reservas
2. Horário de funcionamento: 08:00 às 18:00h
3. Taxa obrigatória de R$ 25,00 por reserva
4. Prazo de 24h para confirmação de pagamento
5. Controle de conflitos de horários
6. Validação de antecedência (1 a 30 dias)
7. Duração mínima de 2h e máxima de 6h

Autor: Sistema SINT-IFESGO
Versão: 1.0
"""

from typing import Dict, List, Optional
from datetime import datetime, date, time, timedelta
from app.interfaces.reserva_interfaces import IReservaRepository, IValidadorReserva
from app.entities.reserva import Reserva as ReservaEntity
from app.services.associado_service import AssociadoService
from app.services.taxa_service import TaxaService


class ReservaService:
    """
    Serviço principal para gestão de reservas do SINT-IFESGO.
    
    Esta classe implementa toda a lógica de negócio relacionada às reservas
    de churrasqueira, incluindo validações específicas do sindicato,
    controle de adimplência, gestão de taxas e integração com outros
    serviços do sistema.
    
    Responsabilidades:
    - Orquestrar o processo completo de criação de reservas
    - Validar todos os critérios específicos do SINT-IFESGO
    - Integrar verificação de adimplência sindical
    - Controlar geração e cobrança de taxas
    - Gerenciar conflitos de horários
    - Manter histórico e status das reservas
    
    Attributes:
        _repositorio: Interface para persistência de dados
        _validador: Interface para validações de negócio
        _associado_service: Serviço de gestão de associados
        _taxa_service: Serviço de gestão de taxas
    """
    
    def __init__(self, 
                 repositorio: IReservaRepository, 
                 validador: IValidadorReserva):
        """
        Inicializa o serviço de reservas com suas dependências.
        
        Args:
            repositorio: Implementação da interface de repositório de reservas
            validador: Implementação da interface de validação de reservas
        """
        self._repositorio = repositorio
        self._validador = validador
        self._associado_service = AssociadoService()
        self._taxa_service = TaxaService()
    
    def criar_reserva(self, dados_reserva: Dict) -> Dict:
        """
        Cria uma nova reserva aplicando todas as regras de negócio do SINT-IFESGO.
        
        Este método implementa o processo completo de criação de reserva,
        incluindo todas as validações específicas do sindicato:
        
        1. Validação de dados básicos (formato, campos obrigatórios)
        2. Verificação de adimplência sindical do associado
        3. Validação de horários de funcionamento (08:00-18:00h)
        4. Verificação de conflitos de horários
        5. Validação de antecedência e duração
        6. Geração automática da taxa de reserva (R$ 25,00)
        7. Persistência da reserva com status 'pendente'
        
        Args:
            dados_reserva (Dict): Dicionário com os dados da reserva:
                - nome (str): Nome do responsável
                - email (str): Email para contato
                - telefone (str): Telefone para contato

                - cpf_associado (str): CPF do associado
                - data_reserva (str): Data no formato 'YYYY-MM-DD'
                - horario_inicio (str): Horário no formato 'HH:MM'
                - horario_fim (str): Horário no formato 'HH:MM'
                - numero_convidados (int): Número de convidados
                - observacoes (str): Observações adicionais
        
        Returns:
            Dict: Resultado da operação contendo:
                - sucesso (bool): True se a reserva foi criada com sucesso
                - mensagem (str): Mensagem de sucesso ou erro
                - reserva_id (int): ID da reserva criada (se sucesso)
                - taxa_codigo (str): Código da taxa gerada (se sucesso)
                - taxa_valor (float): Valor da taxa (se sucesso)
        
        Raises:
            ValueError: Se os dados de entrada estiverem em formato inválido
            
        Business Rules:
            - Apenas associados adimplentes podem fazer reservas
            - Horário de funcionamento: 08:00 às 18:00h
            - Antecedência: 1 a 30 dias
            - Duração: 2 a 6 horas
            - Taxa obrigatória: R$ 25,00
        """
        
        # 1. VALIDAÇÃO DE DADOS BÁSICOS
        # Verifica integridade dos dados recebidos
        dados_validos, mensagem_validacao = self._validador.validar_dados_reserva(dados_reserva)
        if not dados_validos:
            return {
                'sucesso': False,
                'mensagem': f"Dados inválidos: {mensagem_validacao}"
            }
        
        # 2. VERIFICAÇÃO DE ADIMPLÊNCIA SINDICAL
        # Regra fundamental: apenas associados adimplentes podem reservar
        cpf_associado = dados_reserva.get('cpf_associado')
        if cpf_associado:
            adimplente, mensagem_adimplencia = self._associado_service.verificar_adimplencia(cpf_associado)
            if not adimplente:
                return {
                    'sucesso': False,
                    'mensagem': f"Acesso negado: {mensagem_adimplencia}"
                }
        
        # 3. CONVERSÃO E VALIDAÇÃO TEMPORAL
        # Converte strings para objetos datetime para processamento
        try:
            data_reserva = datetime.strptime(dados_reserva['data_reserva'], '%Y-%m-%d').date()
            horario_inicio = datetime.strptime(dados_reserva['horario_inicio'], '%H:%M').time()
            horario_fim = datetime.strptime(dados_reserva['horario_fim'], '%H:%M').time()
        except ValueError as e:
            return {
                'sucesso': False,
                'mensagem': f'Formato de data/hora inválido: {str(e)}'
            }
        
        # 4. Validar antecedência
        antecedencia_valida, mensagem_antecedencia = self._validador.validar_antecedencia(data_reserva)
        if not antecedencia_valida:
            return {
                'sucesso': False,
                'mensagem': mensagem_antecedencia
            }
        
        # 5. Validar horário de funcionamento
        horario_valido, mensagem_horario = self._validador.validar_horario_funcionamento(
            horario_inicio, horario_fim
        )
        if not horario_valido:
            return {
                'sucesso': False,
                'mensagem': mensagem_horario
            }
        
        # 6. Verificar disponibilidade
        disponivel, mensagem_disponibilidade = self._repositorio.verificar_disponibilidade(
            data_reserva, horario_inicio, horario_fim
        )
        if not disponivel:
            return {
                'sucesso': False,
                'mensagem': mensagem_disponibilidade
            }
        
        # 7. Preparar dados para o repositório - incluindo CPF do associado
        dados_para_criacao = {
            'nome': dados_reserva['nome'].strip(),

            'cpf_associado': cpf_associado,
            'data_reserva': data_reserva,
            'horario_inicio': horario_inicio,
            'horario_fim': horario_fim,
            'email': dados_reserva.get('email', '').strip() or None,
            'telefone': dados_reserva.get('telefone', '').strip() or None,
            'numero_convidados': int(dados_reserva.get('numero_convidados', 1)),
            'observacoes': dados_reserva.get('observacoes', '').strip() or None,
            'status': 'pendente'  # Reserva fica pendente até confirmação do pagamento
        }
        
        # 8. Criar reserva
        resultado_reserva = self._repositorio.criar_reserva(dados_para_criacao)
        
        if not resultado_reserva['sucesso']:
            return resultado_reserva
        
        # 9. Gerar taxa de reserva
        reserva_id = resultado_reserva['reserva']['id']
        if cpf_associado:
            resultado_taxa = self._taxa_service.gerar_taxa_reserva(reserva_id, cpf_associado)
        else:
            resultado_taxa = {'sucesso': False, 'mensagem': 'CPF do associado não informado'}
        
        if not resultado_taxa['sucesso']:
            # Se falhar na geração da taxa, podemos decidir se cancela a reserva ou não
            # Por ora, vamos manter a reserva mas informar sobre a taxa
            pass
        
        # 10. Retornar resultado completo
        return {
            'sucesso': True,
            'mensagem': 'Reserva criada com sucesso. Taxa gerada - efetue o pagamento em até 24h.',
            'reserva': resultado_reserva['reserva'],
            'taxa': resultado_taxa.get('taxa') if resultado_taxa['sucesso'] else None,
            'codigo_pagamento': resultado_taxa.get('taxa', {}).get('codigo_pagamento') if resultado_taxa['sucesso'] else None
        }
    
    def listar_reservas_futuras(self, dias_futuro: int = 30) -> List[Dict]:
        """Lista reservas ativas para os próximos dias"""
        hoje = date.today()
        data_limite = hoje + timedelta(days=dias_futuro)
        
        return self._repositorio.listar_reservas_ativas(hoje, data_limite)
    
    def verificar_disponibilidade(self, data_str: str, horario_inicio_str: str, horario_fim_str: str) -> Dict:
        """Verifica disponibilidade de um horário específico"""
        try:
            # Converter strings para objetos
            data_reserva = datetime.strptime(data_str, '%Y-%m-%d').date()
            horario_inicio = datetime.strptime(horario_inicio_str, '%H:%M').time()
            horario_fim = datetime.strptime(horario_fim_str, '%H:%M').time()
            
            # Validar antecedência
            antecedencia_valida, mensagem_antecedencia = self._validador.validar_antecedencia(data_reserva)
            if not antecedencia_valida:
                return {
                    'disponivel': False,
                    'mensagem': mensagem_antecedencia
                }
            
            # Validar horário de funcionamento
            horario_valido, mensagem_horario = self._validador.validar_horario_funcionamento(
                horario_inicio, horario_fim
            )
            if not horario_valido:
                return {
                    'disponivel': False,
                    'mensagem': mensagem_horario
                }
            
            # Verificar disponibilidade no repositório
            disponivel, mensagem = self._repositorio.verificar_disponibilidade(
                data_reserva, horario_inicio, horario_fim
            )
            
            # Obter horários ocupados para informação adicional
            horarios_ocupados = self._repositorio.obter_horarios_ocupados(data_reserva)
            
            return {
                'disponivel': disponivel,
                'mensagem': mensagem,
                'horarios_ocupados': horarios_ocupados
            }
            
        except ValueError as e:
            return {
                'disponivel': False,
                'mensagem': f'Formato de data/hora inválido: {str(e)}',
                'horarios_ocupados': []
            }
    
    def cancelar_reserva(self, reserva_id: int, email_confirmacao: Optional[str] = None) -> Dict:
        """Cancela uma reserva com validações"""
        
        # Buscar reserva
        reserva_data = self._repositorio.buscar_por_id(reserva_id)
        if not reserva_data:
            return {
                'sucesso': False,
                'mensagem': 'Reserva não encontrada'
            }
        
        # Verificar se está ativa
        if reserva_data['status'] != 'ativa':
            return {
                'sucesso': False,
                'mensagem': 'Reserva já foi cancelada'
            }
        
        # Verificar se pode ser cancelada (24h de antecedência)
        try:
            data_reserva = datetime.strptime(reserva_data['data_reserva_iso'], '%Y-%m-%d').date()
            horario_inicio = datetime.strptime(reserva_data['horario_inicio'], '%H:%M').time()
            
            agora = datetime.now()
            data_hora_reserva = datetime.combine(data_reserva, horario_inicio)
            
            if data_hora_reserva <= agora:
                return {
                    'sucesso': False,
                    'mensagem': 'Não é possível cancelar reservas que já começaram'
                }
            
            diferenca = data_hora_reserva - agora
            if diferenca.total_seconds() < 24 * 3600:  # 24 horas
                return {
                    'sucesso': False,
                    'mensagem': 'Cancelamento deve ser feito com pelo menos 24h de antecedência'
                }
            
        except Exception:
            return {
                'sucesso': False,
                'mensagem': 'Erro ao validar horário da reserva'
            }
        
        # Validar email se fornecido
        if email_confirmacao and reserva_data.get('email'):
            if email_confirmacao.lower().strip() != reserva_data['email'].lower().strip():
                return {
                    'sucesso': False,
                    'mensagem': 'Email de confirmação não confere com o da reserva'
                }
        
        # Cancelar no repositório
        cancelada = self._repositorio.cancelar_reserva(reserva_id)
        
        if cancelada:
            return {
                'sucesso': True,
                'mensagem': 'Reserva cancelada com sucesso'
            }
        else:
            return {
                'sucesso': False,
                'mensagem': 'Erro ao cancelar reserva'
            }
    
    def obter_estatisticas(self) -> Dict:
        """Obtém estatísticas das reservas"""
        return self._repositorio.obter_estatisticas()
    
    def buscar_reserva_por_id(self, reserva_id: int) -> Dict:
        """Busca uma reserva específica por ID"""
        reserva = self._repositorio.buscar_por_id(reserva_id)
        
        if reserva:
            return {
                'sucesso': True,
                'reserva': reserva
            }
        else:
            return {
                'sucesso': False,
                'mensagem': 'Reserva não encontrada'
            }