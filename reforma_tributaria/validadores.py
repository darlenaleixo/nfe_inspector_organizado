# reforma_tributaria/validadores.py
from .config import ConfigReformaTributaria
from typing import List, Dict, Any
import re

class ValidadorReformaTributaria:
    """Validações específicas dos novos campos da Reforma Tributária"""
    
    def __init__(self, config: ConfigReformaTributaria):
        self.config = config
    
    def validar_grupo_ibs_cbs(self, dados_item: Dict[str, Any]) -> List[str]:
        """Valida grupo de IBS/CBS conforme NT 2025.002"""
        erros = []
        
        if not self.config.cbs_ativo and not self.config.ibs_ativo:
            return erros
            
        # Validações obrigatórias quando CBS/IBS ativo
        if self.config.cbs_ativo:
            if not dados_item.get('cbs_cst'):
                erros.append("CBS CST é obrigatório quando CBS ativo")
            if not dados_item.get('cbs_class_trib'):
                erros.append("CBS Código de Classificação Tributária obrigatório")
                
        if self.config.ibs_ativo:
            if not dados_item.get('ibs_cst'):
                erros.append("IBS CST é obrigatório quando IBS ativo")
            if not dados_item.get('ibs_class_trib'):
                erros.append("IBS Código de Classificação Tributária obrigatório")
                
        return erros
    
    def validar_codigo_classificacao(self, codigo: str, tipo_tributo: str) -> bool:
        """Valida formato do código de classificação tributária"""
        # Formato: NNNN.NN.NN conforme RT 2024.001
        padrao = r'^\d{4}\.\d{2}\.\d{2}$'
        return bool(re.match(padrao, codigo))
    
    def validar_municipio_fato_gerador(self, dados_nfe: Dict[str, Any]) -> List[str]:
        """Valida novo campo cMunFG específico para ICMS"""
        erros = []
        
        # Conforme NT: cMunFG agora é específico para ICMS
        if not dados_nfe.get('cMunFG_ICMS'):
            erros.append("Código do Município de Fato Gerador do ICMS obrigatório")
            
        # Novo campo para IBS pode ser necessário
        if self.config.ibs_ativo and not dados_nfe.get('cMunFG_IBS'):
            erros.append("Código do Município de Fato Gerador do IBS obrigatório quando IBS ativo")
            
        return erros