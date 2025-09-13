# reforma_tributaria/tributos.py
from dataclasses import dataclass
from typing import Optional
from enum import Enum
from typing import Dict, Any, Optional

class TipoTributoReforma(Enum):
    """Novos tributos da Reforma Tributária"""
    CBS = "CBS"  # Contribuição sobre Bens e Serviços
    IBS = "IBS"  # Imposto sobre Bens e Serviços  
    IS = "IS"    # Imposto Seletivo

class CSTReforma(Enum):
    """Códigos de Situação Tributária dos novos tributos"""
    # Definições conforme Nota Técnica 2025.002
    TRIBUTADO_INTEGRALMENTE = "00"
    TRIBUTADO_COM_COBRANCA_ST = "10"
    ISENTO = "40"
    NAO_INCIDENCIA = "41"
    SUSPENSAO = "50"
    DIFERIMENTO = "51"
    ICMS_COBRADO_ANTERIORMENTE = "60"
    REDUCAO_BC = "20"
    ISENCAO = "30"
    NAO_TRIBUTADO = "90"

@dataclass
class DadosTributoReforma:
    """Estrutura para dados dos novos tributos"""
    tipo_tributo: TipoTributoReforma
    cst: str
    codigo_classificacao: str  # cClassTrib conforme NT
    base_calculo: float
    aliquota: float
    valor_tributo: float
    reducao_bc: Optional[float] = None
    motivo_desoneracao: Optional[str] = None