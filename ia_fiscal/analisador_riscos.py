# ia_fiscal/analisador_riscos.py

import json
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from .config import config_ia

@dataclass
class RiscoFiscal:
    """Resultado da análise de risco fiscal"""
    score: float  # 0.0 a 1.0 (1.0 = alto risco)
    nivel: str   # "baixo", "medio", "alto", "critico"
    fatores: List[str]  # Fatores que contribuíram para o risco
    recomendacoes: List[str]  # Ações recomendadas
    confianca: float  # Confiança na análise

class AnalisadorRiscos:
    """Analisa riscos fiscais usando machine learning e regras de negócio"""
    
    def __init__(self):
        self.historico_fornecedores = {}
        self.padroes_cfop = {}
        self.municipios_risco = set()
        self._carregar_dados_historicos()
    
    def analisar_nfe(self, dados_nfe: Dict[str, Any]) -> RiscoFiscal:
        """Análise completa de risco fiscal de uma NFe"""
        
        fatores_risco = []
        scores = []
        
        # 1. Análise do valor da nota
        score_valor, fator_valor = self._analisar_valor(dados_nfe)
        if score_valor > 0:
            scores.append(score_valor)
            fatores_risco.append(fator_valor)
        
        # 2. Análise do fornecedor
        score_fornecedor, fator_fornecedor = self._analisar_fornecedor(dados_nfe)
        if score_fornecedor > 0:
            scores.append(score_fornecedor)
            fatores_risco.append(fator_fornecedor)
        
        # 3. Análise do CFOP
        score_cfop, fator_cfop = self._analisar_cfop(dados_nfe)
        if score_cfop > 0:
            scores.append(score_cfop)
            fatores_risco.append(fator_cfop)
        
        # 4. Análise temporal
        score_tempo, fator_tempo = self._analisar_prazo(dados_nfe)
        if score_tempo > 0:
            scores.append(score_tempo)
            fatores_risco.append(fator_tempo)
        
        # 5. Análise geográfica
        score_geo, fator_geo = self._analisar_geografia(dados_nfe)
        if score_geo > 0:
            scores.append(score_geo)
            fatores_risco.append(fator_geo)
        
        # Cálculo do score final ponderado
        if scores:
            score_final = np.average(scores, weights=[
                config_ia.risk_factors_weight.get("valor_alto", 0.3),
                config_ia.risk_factors_weight.get("fornecedor_novo", 0.2),
                config_ia.risk_factors_weight.get("cfop_incomum", 0.25),
                config_ia.risk_factors_weight.get("prazo_vencimento", 0.15),
                config_ia.risk_factors_weight.get("municipio_diferente", 0.1)
            ][:len(scores)])
        else:
            score_final = 0.0
        
        # Determina nível de risco
        if score_final >= 0.8:
            nivel = "critico"
        elif score_final >= 0.6:
            nivel = "alto"
        elif score_final >= 0.4:
            nivel = "medio"
        else:
            nivel = "baixo"
        
        # Gera recomendações
        recomendacoes = self._gerar_recomendacoes(fatores_risco, score_final)
        
        return RiscoFiscal(
            score=score_final,
            nivel=nivel,
            fatores=fatores_risco,
            recomendacoes=recomendacoes,
            confianca=min(len(scores) / 5.0, 1.0)  # Mais fatores = mais confiança
        )
    
    def _analisar_valor(self, dados_nfe: Dict[str, Any]) -> Tuple[float, str]:
        """Analisa se o valor da NFe é atípico"""
        valor = float(dados_nfe.get('valor_total', 0))
        
        # Valores muito altos são suspeitos
        if valor > 100000:  # Acima de 100k
            return 0.8, f"Valor muito alto: R$ {valor:,.2f}"
        elif valor > 50000:  # Acima de 50k
            return 0.5, f"Valor alto: R$ {valor:,.2f}"
        elif valor < 1:  # Valores muito baixos
            return 0.6, f"Valor suspeito: R$ {valor:,.2f}"
        
        return 0.0, ""
    
    def _analisar_fornecedor(self, dados_nfe: Dict[str, Any]) -> Tuple[float, str]:
        """Analisa histórico e características do fornecedor"""
        cnpj = dados_nfe.get('cnpj_emissor', '')
        
        if not cnpj:
            return 0.9, "CNPJ do emissor não informado"
        
        # Verifica se é fornecedor conhecido
        historico = self.historico_fornecedores.get(cnpj, {})
        
        if not historico:
            return 0.6, "Fornecedor novo (sem histórico)"
        
        # Analisa rejeições passadas
        taxa_rejeicao = historico.get('taxa_rejeicao', 0)
        if taxa_rejeicao > 0.3:  # Mais de 30% de rejeição
            return 0.7, f"Fornecedor com alta taxa de rejeição: {taxa_rejeicao:.1%}"
        
        return 0.0, ""
    
    def _analisar_cfop(self, dados_nfe: Dict[str, Any]) -> Tuple[float, str]:
        """Analisa se o CFOP é adequado para a operação"""
        cfop = dados_nfe.get('cfop', '')
        valor = float(dados_nfe.get('valor_total', 0))
        
        if not cfop:
            return 0.8, "CFOP não informado"
        
        # CFOPs de devolução com valores altos
        if cfop.startswith('14') or cfop.startswith('24'):  # Devoluções
            if valor > 10000:
                return 0.6, f"Devolução de valor alto: CFOP {cfop}, R$ {valor:,.2f}"
        
        # CFOPs de exportação sem validações extras
        if cfop.startswith('70'):  # Exportações
            return 0.3, f"Operação de exportação: CFOP {cfop}"
        
        return 0.0, ""
    
    def _analisar_prazo(self, dados_nfe: Dict[str, Any]) -> Tuple[float, str]:
        """Analisa prazos de emissão e vencimento"""
        try:
            data_emissao = datetime.strptime(dados_nfe.get('data_emissao', ''), '%Y-%m-%d')
            hoje = datetime.now()
            
            # NFe muito antiga sendo processada agora
            dias_atraso = (hoje - data_emissao).days
            if dias_atraso > 30:
                return 0.5, f"NFe antiga: {dias_atraso} dias de atraso"
            
            # NFe com data futura
            if data_emissao > hoje:
                return 0.8, "Data de emissão no futuro"
                
        except (ValueError, TypeError):
            return 0.4, "Data de emissão inválida"
        
        return 0.0, ""
    
    def _analisar_geografia(self, dados_nfe: Dict[str, Any]) -> Tuple[float, str]:
        """Analisa aspectos geográficos da operação"""
        uf_emissor = dados_nfe.get('uf_emissor', '')
        uf_destinatario = dados_nfe.get('uf_destinatario', '')
        
        # Operações interestaduais específicas
        if uf_emissor != uf_destinatario:
            # Estados com maior risco fiscal (exemplo)
            estados_risco = {'AC', 'AP', 'RR', 'TO'}
            if uf_emissor in estados_risco or uf_destinatario in estados_risco:
                return 0.3, f"Operação interestadual com estado de risco: {uf_emissor} → {uf_destinatario}"
        
        return 0.0, ""
    
    def _gerar_recomendacoes(self, fatores: List[str], score: float) -> List[str]:
        """Gera recomendações baseadas nos fatores de risco"""
        recomendacoes = []
        
        if score >= 0.8:
            recomendacoes.append("🔴 Revisar manualmente antes de autorizar")
            recomendacoes.append("Verificar documentação adicional do fornecedor")
        
        if score >= 0.6:
            recomendacoes.append("🟡 Validar campos obrigatórios cuidadosamente")
            recomendacoes.append("Confirmar dados do destinatário")
        
        if any("valor" in fator.lower() for fator in fatores):
            recomendacoes.append("Confirmar valor com documentação de origem")
        
        if any("fornecedor" in fator.lower() for fator in fatores):
            recomendacoes.append("Validar CNPJ e inscrição estadual do emissor")
        
        if any("cfop" in fator.lower() for fator in fatores):
            recomendacoes.append("Verificar adequação do CFOP à operação")
        
        return recomendacoes
    
    def _carregar_dados_historicos(self):
        """Carrega dados históricos para análise"""
        try:
            # Exemplo de estrutura de dados históricos
            self.historico_fornecedores = {
                "exemplo_cnpj": {
                    "total_nfes": 150,
                    "nfes_rejeitadas": 5,
                    "taxa_rejeicao": 0.033,
                    "valor_medio": 2500.00,
                    "cfops_comuns": ["5101", "5102", "6101"]
                }
            }
            
            self.padroes_cfop = {
                "5101": {"descricao": "Venda", "valor_medio": 1500.00},
                "5102": {"descricao": "Venda fora do estabelecimento", "valor_medio": 800.00}
            }
            
        except Exception as e:
            print(f"Erro ao carregar dados históricos: {e}")

    def treinar_modelo(self, dados_nfes: List[Dict[str, Any]]):
        """Treina o modelo com dados históricos"""
        # Implementar machine learning mais avançado aqui
        # Por exemplo, usando scikit-learn para classificação
        pass
    
    def atualizar_historico(self, dados_nfe: Dict[str, Any], resultado_processamento: str):
        """Atualiza histórico com resultado do processamento"""
        cnpj = dados_nfe.get('cnpj_emissor', '')
        if cnpj:
            if cnpj not in self.historico_fornecedores:
                self.historico_fornecedores[cnpj] = {
                    "total_nfes": 0,
                    "nfes_rejeitadas": 0,
                    "taxa_rejeicao": 0.0
                }
            
            self.historico_fornecedores[cnpj]["total_nfes"] += 1
            if resultado_processamento == "rejeitada":
                self.historico_fornecedores[cnpj]["nfes_rejeitadas"] += 1
            
            # Recalcula taxa de rejeição
            total = self.historico_fornecedores[cnpj]["total_nfes"]
            rejeitadas = self.historico_fornecedores[cnpj]["nfes_rejeitadas"]
            self.historico_fornecedores[cnpj]["taxa_rejeicao"] = rejeitadas / total
