# Conformidade com Reforma Tributária - Base de Código

Para preparar seu sistema NFe para a **Reforma Tributária Brasileira** e o novo modelo **IVA Dual**, é necessário implementar uma base sólida que suporte os novos tributos IBS, CBS e IS que entrarão em vigor gradualmente a partir de 2026.

## Cronograma de Implementação

### 2025
- **Julho**: Início dos testes nos sistemas autorizadores (já iniciado)
- **Outubro**: Ambiente de produção preparado para novos campos

### 2026 (Fase Piloto)
- **CBS**: 0,9% (substituirá PIS/COFINS gradualmente)
- **IBS**: 0,1% (substituirá ICMS/ISS gradualmente)
- Valores compensáveis com PIS/COFINS existentes

### 2027-2032 (Transição Gradual)
- Extinção progressiva dos tributos atuais
- Aumento gradual de CBS e IBS
- Implementação do Imposto Seletivo (IS)

### 2033
- Sistema IVA Dual totalmente implementado
- Extinção completa: PIS, COFINS, ICMS, ISS, IPI

## Estrutura de Código para Implementação

### 1. Módulo de Configuração da Reforma Tributária

```python
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

# reforma_tributaria/tributos.py
from enum import Enum
from typing import Dict, Any

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
```

### 2. Validadores para Novos Campos NFe

```python
# reforma_tributaria/validadores.py
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
```

### 3. Gerador de XML com Novos Campos

```python
# reforma_tributaria/xml_generator.py
from xml.etree.ElementTree import Element, SubElement
from typing import Dict, Any

class GeradorXMLReformaTributaria:
    """Gera XML com novos campos da Reforma Tributária"""
    
    def __init__(self, config: ConfigReformaTributaria):
        self.config = config
    
    def adicionar_grupo_ibs_cbs_is(self, item_elem: Element, dados_item: Dict[str, Any]):
        """Adiciona grupo de IBS/CBS/IS ao item da NFe"""
        
        if self.config.cbs_ativo or self.config.ibs_ativo or self.config.is_ativo:
            # Grupo principal dos novos tributos
            grupo_reforma = SubElement(item_elem, "impostoReforma")
            
            if self.config.cbs_ativo:
                self._adicionar_cbs(grupo_reforma, dados_item.get('cbs', {}))
                
            if self.config.ibs_ativo:
                self._adicionar_ibs(grupo_reforma, dados_item.get('ibs', {}))
                
            if self.config.is_ativo:
                self._adicionar_is(grupo_reforma, dados_item.get('is', {}))
    
    def _adicionar_cbs(self, parent: Element, dados_cbs: Dict[str, Any]):
        """Adiciona grupo CBS"""
        cbs_elem = SubElement(parent, "CBS")
        
        # Campos obrigatórios conforme NT
        SubElement(cbs_elem, "CST").text = dados_cbs.get('cst', '00')
        SubElement(cbs_elem, "cClassTrib").text = dados_cbs.get('class_trib', '')
        
        if dados_cbs.get('base_calculo'):
            SubElement(cbs_elem, "vBC").text = f"{dados_cbs['base_calculo']:.2f}"
        if dados_cbs.get('aliquota'):
            SubElement(cbs_elem, "pCBS").text = f"{dados_cbs['aliquota']:.4f}"
        if dados_cbs.get('valor'):
            SubElement(cbs_elem, "vCBS").text = f"{dados_cbs['valor']:.2f}"
    
    def _adicionar_ibs(self, parent: Element, dados_ibs: Dict[str, Any]):
        """Adiciona grupo IBS"""
        ibs_elem = SubElement(parent, "IBS")
        
        # Campos obrigatórios conforme NT
        SubElement(ibs_elem, "CST").text = dados_ibs.get('cst', '00')
        SubElement(ibs_elem, "cClassTrib").text = dados_ibs.get('class_trib', '')
        
        if dados_ibs.get('base_calculo'):
            SubElement(ibs_elem, "vBC").text = f"{dados_ibs['base_calculo']:.2f}"
        if dados_ibs.get('aliquota'):
            SubElement(ibs_elem, "pIBS").text = f"{dados_ibs['aliquota']:.4f}"
        if dados_ibs.get('valor'):
            SubElement(ibs_elem, "vIBS").text = f"{dados_ibs['valor']:.2f}"
    
    def _adicionar_is(self, parent: Element, dados_is: Dict[str, Any]):
        """Adiciona grupo IS (Imposto Seletivo)"""
        is_elem = SubElement(parent, "IS")
        
        SubElement(is_elem, "CST").text = dados_is.get('cst', '00')
        SubElement(is_elem, "cClassTrib").text = dados_is.get('class_trib', '')
        
        if dados_is.get('base_calculo'):
            SubElement(is_elem, "vBC").text = f"{dados_is['base_calculo']:.2f}"
        if dados_is.get('aliquota'):
            SubElement(is_elem, "pIS").text = f"{dados_is['aliquota']:.4f}"
        if dados_is.get('valor'):
            SubElement(is_elem, "vIS").text = f"{dados_is['valor']:.2f}"
```

### 4. Calculadora de Tributos da Reforma

```python
# reforma_tributaria/calculadora.py
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
```

### 5. Tabelas de Classificação Tributária

```python
# reforma_tributaria/tabelas.py
from typing import Dict, List, Optional
import json

class TabelasReformaTributaria:
    """Gerencia tabelas de classificação tributária dos novos tributos"""
    
    def __init__(self):
        self.tabela_classificacao = self._carregar_tabela_classificacao()
    
    def _carregar_tabela_classificacao(self) -> Dict[str, Any]:
        """Carrega tabela de classificação tributária (RT 2024.001)"""
        # Esta tabela deve ser mantida atualizada conforme publicações oficiais
        return {
            "0000.00.00": {"descricao": "Produtos em geral", "observacoes": ""},
            "0100.00.00": {"descricao": "Produtos alimentícios", "observacoes": ""},
            "0200.00.00": {"descricao": "Produtos farmacêuticos", "observacoes": ""},
            # ... continuar conforme tabela oficial
        }
    
    def obter_classificacao_por_ncm(self, ncm: str, cest: Optional[str] = None) -> Optional[str]:
        """Sugere classificação tributária baseada em NCM/CEST"""
        # Lógica de mapeamento NCM -> Classificação Tributária
        # Deve ser implementada conforme mapeamentos oficiais
        pass
    
    def validar_codigo_classificacao(self, codigo: str) -> bool:
        """Valida se código de classificação existe na tabela oficial"""
        return codigo in self.tabela_classificacao
    
    def obter_sugestoes_classificacao(self, descricao_produto: str) -> List[str]:
        """Sugere códigos de classificação baseado na descrição do produto"""
        # Implementar lógica de IA/ML para sugestão inteligente
        pass
```

### 6. Monitor de Atualizações Legislativas

```python
# reforma_tributaria/monitor.py
import requests
from datetime import datetime
from typing import List, Dict, Any

class MonitorAtualizacoesRT:
    """Monitora atualizações das Notas Técnicas da Reforma Tributária"""
    
    def __init__(self):
        self.url_portal_nfe = "https://www.nfe.fazenda.gov.br/portal/"
        self.ultima_verificacao = None
    
    def verificar_novas_notas_tecnicas(self) -> List[Dict[str, Any]]:
        """Verifica se há novas Notas Técnicas publicadas"""
        # Implementar scraping ou API para verificar atualizações
        pass
    
    def baixar_tabela_classificacao_atualizada(self) -> bool:
        """Baixa versão mais recente da tabela de classificação"""
        # Implementar download automático das tabelas oficiais
        pass
    
    def notificar_mudancas_legislativas(self, mudancas: List[str]):
        """Notifica usuários sobre mudanças relevantes"""
        # Integrar com sistema de notificações
        pass
```

### 7. Integração com Interface Principal

```python
# main.py - Integração
from reforma_tributaria.config import ConfigReformaTributaria
from reforma_tributaria.calculadora import CalculadoraReformaTributaria
from reforma_tributaria.validadores import ValidadorReformaTributaria

def inicializar_reforma_tributaria():
    """Inicializa módulos da Reforma Tributária no sistema principal"""
    ano_atual = datetime.now().year
    config_rt = ConfigReformaTributaria.get_config_por_ano(ano_atual)
    
    calculadora = CalculadoraReformaTributaria(config_rt)
    validador = ValidadorReformaTributaria(config_rt)
    
    return config_rt, calculadora, validador

# No início da aplicação
if __name__ == "__main__":
    start_scheduler()
    
    # Inicializar Reforma Tributária
    config_rt, calc_rt, valid_rt = inicializar_reforma_tributaria()
    
    main()
```

## Próximos Passos de Implementação

1. **Implementar estruturas base** (config, tributos, validadores)
2. **Criar testes unitários** para cada módulo
3. **Integrar com geração de XML** existente
4. **Implementar calculadora de tributos**
5. **Criar interface para configuração** dos novos tributos
6. **Desenvolver sistema de atualização** automática das tabelas
7. **Implementar dashboard** de conformidade com Reforma Tributária

Esta base fornece a estrutura necessária para que seu sistema esteja preparado para as mudanças da Reforma Tributária, mantendo compatibilidade com o sistema atual e permitindo transição gradual conforme cronograma oficial.