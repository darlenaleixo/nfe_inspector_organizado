# reforma_tributaria/config.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

@dataclass
class ConfigReformaTributaria:
    """Configurações da Reforma Tributária por período"""
    ano_vigencia: int
    cbs_ativo: bool = False
    ibs_ativo: bool = False
    is_ativo: bool = False
    aliquota_cbs: float = 0.0
    aliquota_ibs: float = 0.0
    pis_cofins_extinto: bool = False
    icms_iss_extinto: bool = False
    
    @classmethod
    def get_config_por_ano(cls, ano: int) -> 'ConfigReformaTributaria':
        """Retorna configuração específica por ano"""
        configs = {
            2025: cls(2025),  # Preparação
            2026: cls(2026, True, True, False, 0.009, 0.001),  # Fase piloto
            2027: cls(2027, True, True, True, 0.087, 0.005, True),  # CBS integral
            2033: cls(2033, True, True, True, 0.265, 0.177, True, True)  # Sistema completo
        }
        return configs.get(ano, configs[2025])

