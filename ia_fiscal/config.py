# ia_fiscal/config.py

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ConfigIAFiscal:
    """Configurações da Inteligência Artificial Fiscal"""
    
    # Análise de Riscos
    risk_threshold: float = 0.7  # Limite para alertar sobre riscos
    risk_factors_weight: Dict[str, float] = None
    
    # Detecção de Fraudes
    fraud_threshold: float = 0.8
    fraud_patterns_enabled: bool = True
    
    # Sugestões Tributárias
    suggestion_confidence: float = 0.6  # Confiança mínima para sugestões
    learning_enabled: bool = True  # Aprender com correções do usuário
    
    # Validação Inteligente
    auto_validation: bool = True
    validation_strictness: str = "medium"  # low, medium, high
    
    # Assistente Virtual
    chatbot_enabled: bool = True
    response_language: str = "pt-BR"
    
    def __post_init__(self):
        if self.risk_factors_weight is None:
            self.risk_factors_weight = {
                "valor_alto": 0.3,
                "fornecedor_novo": 0.2,
                "cfop_incomum": 0.25,
                "prazo_vencimento": 0.15,
                "municipio_diferente": 0.1
            }

# Configuração padrão
config_ia = ConfigIAFiscal()
