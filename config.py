"""
Configurações do Sistema de Reserva de Churrasqueira - SINT-IFESGO

Este módulo contém todas as configurações específicas para o sistema de reservas
do Sindicato dos Trabalhadores Técnico-Administrativos em Educação das Instituições
Federais de Ensino Superior do Estado de Goiás.

Configurações incluem:
- Parâmetros do Flask (chave secreta, banco de dados)
- Horários de funcionamento (08:00-18:00h)
- Valores de taxa de reserva (R$ 25,00)
- Informações organizacionais do SINT-IFESGO
- Limites e validações do sistema

Autor: Sistema SINT-IFESGO
Versão: 1.0
"""

import os
from pathlib import Path

# Diretório base do projeto (onde está localizado este arquivo)
basedir = Path(__file__).resolve().parent

class Config:
    """
    Classe de configuração principal do sistema SINT-IFESGO.
    
    Centraliza todas as configurações necessárias para o funcionamento
    do sistema de reserva de churrasqueira, incluindo configurações
    específicas do Flask, banco de dados, regras de negócio e
    informações organizacionais.
    """
    
    # =========================================================================
    # CONFIGURAÇÕES BÁSICAS DO FLASK
    # =========================================================================
    
    # Chave secreta para sessões e formulários (usar variável de ambiente em produção)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-churrasqueira-2024'
    
    # =========================================================================
    # CONFIGURAÇÕES DO BANCO DE DADOS
    # =========================================================================
    
    # URI do banco SQLite (usar PostgreSQL/MySQL em produção)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + str(basedir / 'churrasqueira.db')
    
    # Desabilitar rastreamento de modificações (economia de memória)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # =========================================================================
    # CONFIGURAÇÕES DE HORÁRIO DE FUNCIONAMENTO
    # =========================================================================
    
    HORARIOS_FUNCIONAMENTO = {
        'inicio': '08:00',        # Horário de abertura
        'fim': '18:00',           # Horário de fechamento (conforme solicitação)
        'intervalo_minimo': 2     # Duração mínima da reserva em horas
    }
    
    # =========================================================================
    # INFORMAÇÕES ORGANIZACIONAIS DO SINT-IFESGO
    # =========================================================================
    
    ORGANIZACAO = {
        'nome': 'SINT-IFESGO',
        'nome_completo': 'Sindicato dos Trabalhadores Técnico-Administrativos em Educação das Instituições Federais de Ensino Superior do Estado de Goiás',
        'email_contato': 'sint-ifesgo@sint-ifesgo.org.br',
        'telefone': '+55 62 99226-3174'
    }
    
    # =========================================================================
    # CONFIGURAÇÕES FINANCEIRAS - TAXA DE RESERVA
    # =========================================================================
    
    TAXA_RESERVA = {
        'valor': 25.00,  # Valor da taxa de reserva em reais (R$ 25,00)
        'prazo_pagamento_horas': 24,  # Prazo para confirmação do pagamento (24h)
        'forma_pagamento': ['PIX', 'Transferência', 'Dinheiro']  # Formas aceitas
    }
    
    # =========================================================================
    # LIMITES E VALIDAÇÕES DO SISTEMA
    # =========================================================================
    
    # Antecedência máxima para reservas (30 dias)
    MAX_DIAS_ANTECEDENCIA = 30
    
    # Antecedência mínima para reservas (1 dia)
    MIN_DIAS_ANTECEDENCIA = 1

    # Duração máxima de uma reserva (8 horas)
    MAX_DURATION_HOURS = 8
    
    # Duração mínima de uma reserva (4 horas)
    MIN_DURATION_HOURS = 4