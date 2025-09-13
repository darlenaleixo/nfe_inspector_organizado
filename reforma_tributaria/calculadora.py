# reforma_tributaria/calculadora.py
from .config import ConfigReformaTributaria
from typing import Dict, Any
from decimal import Decimal, ROUND_HALF_UP

class CalculadoraReformaTributaria:
    """Calcula tributos CBS, IBS e IS"""
    
    def __init__(self, config: ConfigReformaTributaria):
        self.config = config
    
    def calcular_cbs(self, valor_produto: float, dados_produto: Dict[str, Any]) -> Dict[str, float]:
        """Calcula CBS baseado na configuração do ano"""
        if not self.config.cbs_ativo:
            return {'base_calculo': 0, 'aliquota': 0, 'valor': 0}
            
        base_calculo = Decimal(str(valor_produto))
        aliquota = Decimal(str(self.config.aliquota_cbs))
        
        # Aplicar reduções se houver
        if dados_produto.get('reducao_bc_cbs'):
            reducao = Decimal(str(dados_produto['reducao_bc_cbs']))
            base_calculo = base_calculo * (1 - reducao)
        
        valor_cbs = (base_calculo * aliquota).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return {
            'base_calculo': float(base_calculo),
            'aliquota': float(aliquota),
            'valor': float(valor_cbs)
        }
    
    def calcular_ibs(self, valor_produto: float, dados_produto: Dict[str, Any]) -> Dict[str, float]:
        """Calcula IBS baseado na configuração do ano"""
        if not self.config.ibs_ativo:
            return {'base_calculo': 0, 'aliquota': 0, 'valor': 0}
            
        base_calculo = Decimal(str(valor_produto))
        aliquota = Decimal(str(self.config.aliquota_ibs))
        
        # Aplicar reduções se houver
        if dados_produto.get('reducao_bc_ibs'):
            reducao = Decimal(str(dados_produto['reducao_bc_ibs']))
            base_calculo = base_calculo * (1 - reducao)
        
        valor_ibs = (base_calculo * aliquota).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return {
            'base_calculo': float(base_calculo),
            'aliquota': float(aliquota),
            'valor': float(valor_ibs)
        }
    
    def calcular_credito_compensacao(self, valor_cbs: float, valor_ibs: float) -> Dict[str, float]:
        """Calcula crédito de compensação com PIS/COFINS (2026)"""
        if not self.config.ano_vigencia == 2026:
            return {'credito_pis': 0, 'credito_cofins': 0}
            
        # Em 2026, CBS+IBS podem ser compensados com PIS+COFINS
        total_reforma = valor_cbs + valor_ibs
        
        return {
            'credito_pis': total_reforma * 0.165,  # Proporção típica PIS
            'credito_cofins': total_reforma * 0.835,  # Proporção típica COFINS
            'total_compensavel': total_reforma
        }