# ia_fiscal/sugestor_tributario.py

import json
import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import unicodedata
from datetime import datetime
import logging


@dataclass
class SugestaoTributaria:
    """Resultado de uma sugestão tributária"""
    codigo: str
    descricao: str
    confianca: float  # 0.0 a 1.0
    razoes: List[str]  # Por que foi sugerido
    alternativas: List[Dict[str, Any]]  # Outras opções

@dataclass 
class ContextoOperacao:
    """Contexto da operação para melhorar sugestões"""
    tipo_empresa: str = "industria"  # industria, comercio, servicos
    regime_tributario: str = "simples"  # simples, lucro_presumido, lucro_real
    uf_origem: str = "SP"
    uf_destino: str = "SP"
    operacao_tipo: str = "venda"  # venda, compra, transferencia, devolucao
    valor_operacao: float = 0.0
    cliente_tipo: str = "pj"  # pj, pf, governo

class SugestorTributario:
    """Sistema inteligente de sugestões tributárias"""
    
    def __init__(self):
        self.base_ncm = self._carregar_base_ncm()
        self.base_cfop = self._carregar_base_cfop()
        self.base_cst = self._carregar_base_cst()
        self.historico_aprendizado = defaultdict(list)
        self.palavras_chave_ncm = self._construir_indice_palavras()
        
    def sugerir_ncm(self, descricao_produto: str, contexto: Optional[ContextoOperacao] = None) -> List[SugestaoTributaria]:
        """Sugere NCM baseado na descrição do produto"""
        
        if not descricao_produto or len(descricao_produto.strip()) < 3:
            return []
        
        descricao_limpa = self._limpar_texto(descricao_produto)
        palavras = descricao_limpa.split()
        
        # 1. Busca exata por palavras-chave
        candidatos_exatos = self._buscar_ncm_palavras_chave(palavras)
        
        # 2. Busca por similaridade semântica
        candidatos_similares = self._buscar_ncm_similaridade(descricao_limpa)
        
        # 3. Busca no histórico de aprendizado
        candidatos_historico = self._buscar_ncm_historico(descricao_limpa)
        
        # 4. Combina e pontua resultados
        todos_candidatos = {}
        
        # Pontuação por busca exata (peso maior)
        for ncm, score in candidatos_exatos.items():
            todos_candidatos[ncm] = todos_candidatos.get(ncm, 0) + score * 0.5
            
        # Pontuação por similaridade  
        for ncm, score in candidatos_similares.items():
            todos_candidatos[ncm] = todos_candidatos.get(ncm, 0) + score * 0.3
            
        # Pontuação por histórico (aprendizado)
        for ncm, score in candidatos_historico.items():
            todos_candidatos[ncm] = todos_candidatos.get(ncm, 0) + score * 0.2
        
        # 5. Aplica ajustes por contexto
        if contexto:
            todos_candidatos = self._ajustar_ncm_por_contexto(todos_candidatos, contexto)
        
        # 6. Ordena e formata resultados
        resultados_ordenados = sorted(todos_candidatos.items(), key=lambda x: x[1], reverse=True)
        
        sugestoes = []
        for ncm, score in resultados_ordenados[:5]:  # Top 5 sugestões
            info_ncm = self.base_ncm.get(ncm, {})
            razoes = self._gerar_razoes_ncm(ncm, descricao_limpa, score)
            alternativas = self._gerar_alternativas_ncm(ncm, resultados_ordenados[1:4])
            
            sugestoes.append(SugestaoTributaria(
                codigo=ncm,
                descricao=info_ncm.get('descricao', f'NCM {ncm}'),
                confianca=min(score, 1.0),
                razoes=razoes,
                alternativas=alternativas
            ))
            
        return sugestoes
    
    def sugerir_cfop(self, operacao_descricao: str, contexto: ContextoOperacao) -> List[SugestaoTributaria]:
        """Sugere CFOP baseado no tipo de operação e contexto"""
        
        # Determina tipo de operação por palavras-chave
        tipo_op = self._identificar_tipo_operacao(operacao_descricao, contexto)
        
        # Busca CFOPs adequados
        cfops_candidatos = {}
        
        # 1. CFOPs por tipo de operação
        for cfop, info in self.base_cfop.items():
            if tipo_op in info.get('tipos_operacao', []):
                score_base = 0.8
                
                # Ajusta score por contexto
                if contexto.uf_origem == contexto.uf_destino and cfop.startswith(('1', '5')):
                    score_base += 0.15  # Operação dentro do estado
                elif contexto.uf_origem != contexto.uf_destino and cfop.startswith(('2', '6')):
                    score_base += 0.15  # Operação interestadual
                
                # Ajusta por regime tributário
                if contexto.regime_tributario == 'simples' and 'simples' in info.get('regimes_adequados', []):
                    score_base += 0.1
                
                cfops_candidatos[cfop] = score_base
        
        # 2. Histórico de uso
        historico_cfop = self.historico_aprendizado.get(f"cfop_{contexto.tipo_empresa}_{tipo_op}", [])
        for item in historico_cfop[-10:]:  # Últimos 10 usos
            cfop_historico = item.get('cfop')
            if cfop_historico in cfops_candidatos:
                cfops_candidatos[cfop_historico] += 0.1
        
        # 3. Ordena e formata resultados
        resultados_ordenados = sorted(cfops_candidatos.items(), key=lambda x: x[1], reverse=True)
        
        sugestoes = []
        for cfop, score in resultados_ordenados[:3]:  # Top 3 CFOPs
            info_cfop = self.base_cfop.get(cfop, {})
            razoes = self._gerar_razoes_cfop(cfop, tipo_op, contexto)
            
            sugestoes.append(SugestaoTributaria(
                codigo=cfop,
                descricao=info_cfop.get('descricao', f'CFOP {cfop}'),
                confianca=min(score, 1.0),
                razoes=razoes,
                alternativas=[]
            ))
            
        return sugestoes
    
    def sugerir_cst(self, ncm: str, cfop: str, contexto: ContextoOperacao) -> List[SugestaoTributaria]:
        """Sugere CST baseado no NCM, CFOP e contexto da empresa"""
        
        csts_candidatos = {}
        
        # 1. CSTs por regime tributário
        if contexto.regime_tributario == 'simples':
            # Simples Nacional - CSTs específicos
            if contexto.tipo_empresa == 'industria':
                csts_candidatos.update({'102': 0.9, '103': 0.7, '300': 0.6})
            elif contexto.tipo_empresa == 'comercio':
                csts_candidatos.update({'102': 0.8, '500': 0.9})
            else:  # serviços
                csts_candidatos.update({'300': 0.9, '500': 0.7})
                
        elif contexto.regime_tributario in ['lucro_presumido', 'lucro_real']:
            # Regime normal - análise mais complexa
            info_ncm = self.base_ncm.get(ncm, {})
            info_cfop = self.base_cfop.get(cfop, {})
            
            # CST baseado na natureza do produto
            if 'isento' in info_ncm.get('caracteristicas', []):
                csts_candidatos.update({'40': 0.9, '41': 0.7})
            elif 'substituicao' in info_ncm.get('caracteristicas', []):
                csts_candidatos.update({'60': 0.9, '10': 0.6})
            else:
                csts_candidatos.update({'00': 0.8, '20': 0.6})
        
        # 2. Ajustes por CFOP
        if cfop.startswith(('14', '24')):  # Devoluções
            csts_candidatos = {'41': 0.9}  # Não incidência
        elif cfop in ['5949', '6949']:  # Outras saídas
            for cst in csts_candidatos:
                csts_candidatos[cst] *= 1.1  # Aumenta confiança
        
        # 3. Histórico de uso
        chave_historico = f"cst_{contexto.regime_tributario}_{contexto.tipo_empresa}"
        historico_cst = self.historico_aprendizado.get(chave_historico, [])
        for item in historico_cst[-5:]:  # Últimos 5 usos
            cst_historico = item.get('cst')
            if cst_historico in csts_candidatos:
                csts_candidatos[cst_historico] += 0.15
        
        # 4. Ordena e formata resultados
        resultados_ordenados = sorted(csts_candidatos.items(), key=lambda x: x[1], reverse=True)
        
        sugestoes = []
        for cst, score in resultados_ordenados[:3]:  # Top 3 CSTs
            info_cst = self.base_cst.get(cst, {})
            razoes = self._gerar_razoes_cst(cst, contexto, ncm, cfop)
            
            sugestoes.append(SugestaoTributaria(
                codigo=cst,
                descricao=info_cst.get('descricao', f'CST {cst}'),
                confianca=min(score, 1.0),
                razoes=razoes,
                alternativas=[]
            ))
            
        return sugestoes
    
    def aprender_correcao(self, original: Dict[str, str], corrigido: Dict[str, str], contexto: ContextoOperacao):
        """Aprende com correções do usuário para melhorar sugestões futuras"""
        
        timestamp = datetime.now().isoformat()
        
        # Registra correção de NCM
        if 'ncm' in original and 'ncm' in corrigido and original['ncm'] != corrigido['ncm']:
            chave = f"ncm_correcao_{contexto.tipo_empresa}"
            self.historico_aprendizado[chave].append({
                'timestamp': timestamp,
                'descricao': original.get('descricao', ''),
                'ncm_original': original['ncm'],
                'ncm_corrigido': corrigido['ncm'],
                'contexto': contexto.__dict__
            })
        
        # Registra correção de CFOP
        if 'cfop' in original and 'cfop' in corrigido and original['cfop'] != corrigido['cfop']:
            chave = f"cfop_{contexto.tipo_empresa}_{contexto.operacao_tipo}"
            self.historico_aprendizado[chave].append({
                'timestamp': timestamp,
                'cfop': corrigido['cfop'],
                'contexto': contexto.__dict__
            })
        
        # Registra correção de CST
        if 'cst' in original and 'cst' in corrigido and original['cst'] != corrigido['cst']:
            chave = f"cst_{contexto.regime_tributario}_{contexto.tipo_empresa}"
            self.historico_aprendizado[chave].append({
                'timestamp': timestamp,
                'cst': corrigido['cst'],
                'ncm': corrigido.get('ncm'),
                'cfop': corrigido.get('cfop')
            })
        
        # Limita histórico a últimas 100 entradas por tipo
        for chave in self.historico_aprendizado:
            if len(self.historico_aprendizado[chave]) > 100:
                self.historico_aprendizado[chave] = self.historico_aprendizado[chave][-100:]
    
    # === MÉTODOS AUXILIARES ===
    
    def _limpar_texto(self, texto: str) -> str:
        """Limpa e normaliza texto para análise"""
        if not texto:
            return ""
        
        # Remove acentos
        texto = unicodedata.normalize('NFD', texto)
        texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
        
        # Converte para minúsculas
        texto = texto.lower()
        
        # Remove caracteres especiais
        texto = re.sub(r'[^a-zA-Z0-9\s]', ' ', texto)
        
        # Remove espaços extras
        texto = ' '.join(texto.split())
        
        return texto
    
    def _buscar_ncm_palavras_chave(self, palavras: List[str]) -> Dict[str, float]:
        """Busca NCMs por palavras-chave"""
        candidatos = defaultdict(float)
        
        for palavra in palavras:
            if len(palavra) < 3:  # Ignora palavras muito curtas
                continue
                
            ncms_palavra = self.palavras_chave_ncm.get(palavra, [])
            for ncm, peso in ncms_palavra:
                candidatos[ncm] += peso / len(palavras)  # Normaliza por quantidade de palavras
        
        return dict(candidatos)
    
    def _buscar_ncm_similaridade(self, descricao: str) -> Dict[str, float]:
        """Busca NCMs por similaridade de texto"""
        candidatos = {}
        
        # Implementação simples de similaridade por sobreposição de palavras
        palavras_desc = set(descricao.split())
        
        for ncm, info in self.base_ncm.items():
            descricao_ncm = info.get('descricao', '').lower()
            palavras_ncm = set(descricao_ncm.split())
            
            if len(palavras_desc) > 0 and len(palavras_ncm) > 0:
                sobreposicao = len(palavras_desc.intersection(palavras_ncm))
                uniao = len(palavras_desc.union(palavras_ncm))
                similaridade = sobreposicao / uniao if uniao > 0 else 0
                
                if similaridade > 0.1:  # Threshold mínimo
                    candidatos[ncm] = similaridade
        
        return candidatos
    
    def _buscar_ncm_historico(self, descricao: str) -> Dict[str, float]:
        """Busca NCMs no histórico de aprendizado"""
        candidatos = defaultdict(float)
        
        for chave, historico in self.historico_aprendizado.items():
            if chave.startswith('ncm_'):
                for item in historico[-20:]:  # Últimos 20 registros
                    desc_historico = item.get('descricao', '').lower()
                    if descricao in desc_historico or desc_historico in descricao:
                        ncm = item.get('ncm_corrigido')
                        if ncm:
                            candidatos[ncm] += 0.1
        
        return dict(candidatos)
    
    def _identificar_tipo_operacao(self, descricao: str, contexto: ContextoOperacao) -> str:
        """Identifica tipo de operação por palavras-chave"""
        desc_lower = descricao.lower()
        
        if any(palavra in desc_lower for palavra in ['venda', 'saida', 'faturamento']):
            return 'venda'
        elif any(palavra in desc_lower for palavra in ['compra', 'aquisicao', 'entrada']):
            return 'compra'
        elif any(palavra in desc_lower for palavra in ['transferencia', 'remessa']):
            return 'transferencia'
        elif any(palavra in desc_lower for palavra in ['devolucao', 'retorno']):
            return 'devolucao'
        else:
            return contexto.operacao_tipo  # Usa contexto como fallback
    
    def _gerar_razoes_ncm(self, ncm: str, descricao: str, score: float) -> List[str]:
        """Gera explicações sobre por que o NCM foi sugerido"""
        razoes = []
        
        info_ncm = self.base_ncm.get(ncm, {})
        palavras_desc = set(descricao.split())
        palavras_ncm = set(info_ncm.get('descricao', '').lower().split())
        palavras_comuns = palavras_desc.intersection(palavras_ncm)
        
        if score > 0.7:
            razoes.append("Alta correspondência com descrição")
        elif score > 0.4:
            razoes.append("Boa correspondência com descrição")
        
        if palavras_comuns:
            razoes.append(f"Palavras-chave encontradas: {', '.join(list(palavras_comuns)[:3])}")
        
        if ncm in [item.get('ncm_corrigido') for hist in self.historico_aprendizado.values() for item in hist]:
            razoes.append("Usado anteriormente em produtos similares")
        
        return razoes
    
    def _gerar_razoes_cfop(self, cfop: str, tipo_op: str, contexto: ContextoOperacao) -> List[str]:
        """Gera explicações sobre por que o CFOP foi sugerido"""
        razoes = []
        
        if contexto.uf_origem == contexto.uf_destino:
            razoes.append("Operação dentro do mesmo estado")
        else:
            razoes.append(f"Operação interestadual: {contexto.uf_origem} → {contexto.uf_destino}")
        
        razoes.append(f"Adequado para: {tipo_op}")
        
        if contexto.regime_tributario == 'simples':
            razoes.append("Compatível com Simples Nacional")
        
        return razoes
    
    def _gerar_razoes_cst(self, cst: str, contexto: ContextoOperacao, ncm: str, cfop: str) -> List[str]:
        """Gera explicações sobre por que o CST foi sugerido"""
        razoes = []
        
        if contexto.regime_tributario == 'simples':
            razoes.append("Sugerido para empresas do Simples Nacional")
        
        if cst in ['40', '41']:
            razoes.append("Produto isento ou com não incidência")
        elif cst == '00':
            razoes.append("Tributação normal integral")
        elif cst in ['102', '103', '300', '500']:
            razoes.append("CST específico do Simples Nacional")
        
        return razoes
    
    def _carregar_base_ncm(self) -> Dict[str, Dict[str, Any]]:
        """Carrega base de dados de NCM"""
        # Base simplificada para demonstração
        # Em produção, carregaria de arquivo/banco de dados completo
        return {
            "22011000": {
                "descricao": "agua mineral natural",
                "caracteristicas": ["bebida", "natural"],
                "categoria": "alimentos_bebidas"
            },
            "84433210": {
                "descricao": "impressoras jato de tinta",
                "caracteristicas": ["eletronico", "escritorio"],
                "categoria": "equipamentos"
            },
            "61046200": {
                "descricao": "blusas de malha de algodao",
                "caracteristicas": ["vestuario", "algodao"],
                "categoria": "textil"
            },
            "39269090": {
                "descricao": "outras obras de plastico",
                "caracteristicas": ["plastico", "diversos"],
                "categoria": "plasticos"
            }
        }
    
    def _carregar_base_cfop(self) -> Dict[str, Dict[str, Any]]:
        """Carrega base de dados de CFOP"""
        return {
            "5101": {
                "descricao": "Venda de produção do estabelecimento",
                "tipos_operacao": ["venda"],
                "regimes_adequados": ["simples", "lucro_presumido", "lucro_real"]
            },
            "5102": {
                "descricao": "Venda de mercadoria adquirida ou recebida de terceiros",
                "tipos_operacao": ["venda"],
                "regimes_adequados": ["simples", "lucro_presumido", "lucro_real"]
            },
            "6101": {
                "descricao": "Venda de produção do estabelecimento (interestadual)",
                "tipos_operacao": ["venda"],
                "regimes_adequados": ["simples", "lucro_presumido", "lucro_real"]
            },
            "1102": {
                "descricao": "Compra para comercialização",
                "tipos_operacao": ["compra"],
                "regimes_adequados": ["simples", "lucro_presumido", "lucro_real"]
            },
            "5405": {
                "descricao": "Remessa para venda fora do estabelecimento",
                "tipos_operacao": ["transferencia"],
                "regimes_adequados": ["simples", "lucro_presumido", "lucro_real"]
            },
            "1411": {
                "descricao": "Devolução de venda de produção",
                "tipos_operacao": ["devolucao"],
                "regimes_adequados": ["simples", "lucro_presumido", "lucro_real"]
            }
        }
    
    def _carregar_base_cst(self) -> Dict[str, Dict[str, Any]]:
        """Carrega base de dados de CST"""
        return {
            "00": {
                "descricao": "Tributada integralmente",
                "aplicavel": ["lucro_presumido", "lucro_real"]
            },
            "10": {
                "descricao": "Tributada e com cobrança do ICMS por substituição tributária",
                "aplicavel": ["lucro_presumido", "lucro_real"]
            },
            "20": {
                "descricao": "Com redução de base de cálculo",
                "aplicavel": ["lucro_presumido", "lucro_real"]
            },
            "40": {
                "descricao": "Isenta",
                "aplicavel": ["simples", "lucro_presumido", "lucro_real"]
            },
            "41": {
                "descricao": "Não tributada",
                "aplicavel": ["simples", "lucro_presumido", "lucro_real"]
            },
            "102": {
                "descricao": "Tributada pelo Simples Nacional sem permissão de crédito",
                "aplicavel": ["simples"]
            },
            "103": {
                "descricao": "Isenção do ICMS no Simples Nacional",
                "aplicavel": ["simples"]
            },
            "300": {
                "descricao": "Imune - Simples Nacional",
                "aplicavel": ["simples"]
            },
            "500": {
                "descricao": "ICMS cobrado anteriormente por substituição tributária",
                "aplicavel": ["simples"]
            }
        }
    
    def _construir_indice_palavras(self) -> Dict[str, List[Tuple[str, float]]]:
        """Constrói índice de palavras-chave para NCM"""
        indice = defaultdict(list)
        
        for ncm, info in self.base_ncm.items():
            descricao = info.get('descricao', '')
            palavras = self._limpar_texto(descricao).split()
            
            for palavra in palavras:
                if len(palavra) >= 3:
                    peso = 1.0 / len(palavras)  # Peso inversamente proporcional ao tamanho
                    indice[palavra].append((ncm, peso))
        
        return dict(indice)
    
    def _ajustar_ncm_por_contexto(self, candidatos: Dict[str, float], contexto: ContextoOperacao) -> Dict[str, float]:
        """Ajusta pontuação de NCMs baseado no contexto da empresa"""
        ajustados = candidatos.copy()
        
        for ncm, score in candidatos.items():
            info_ncm = self.base_ncm.get(ncm, {})
            categoria = info_ncm.get('categoria', '')
            
            # Ajustes por tipo de empresa
            if contexto.tipo_empresa == 'comercio' and categoria in ['equipamentos', 'textil']:
                ajustados[ncm] *= 1.2
            elif contexto.tipo_empresa == 'industria' and categoria == 'alimentos_bebidas':
                ajustados[ncm] *= 1.1
            
            # Ajustes por valor da operação
            if contexto.valor_operacao > 10000 and categoria == 'equipamentos':
                ajustados[ncm] *= 1.1
        
        return ajustados
    
    def _gerar_alternativas_ncm(self, ncm_principal: str, outros_resultados: List[Tuple[str, float]]) -> List[Dict[str, Any]]:
        """Gera alternativas para o NCM sugerido"""
        alternativas = []
        
        for ncm, score in outros_resultados[:2]:  # 2 alternativas
            if ncm != ncm_principal:
                info = self.base_ncm.get(ncm, {})
                alternativas.append({
                    "codigo": ncm,
                    "descricao": info.get('descricao', f'NCM {ncm}'),
                    "confianca": min(score, 1.0)
                })
        
        return alternativas
