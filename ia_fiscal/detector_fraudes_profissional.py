
# ia_fiscal/detector_fraudes_profissional.py

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any
import hashlib

class DetectorFraudesProfissional:
    """Detector de fraudes com expertise contábil e fiscal"""
    
    def __init__(self):
        self.historico_analises = {}
        self.padroes_suspeitos = self._carregar_padroes_suspeitos()
        
    def detectar_inconsistencias(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, str]]:
        """Detecção profissional de inconsistências e fraudes"""
        
        inconsistencias = []
        
        # 1. ANÁLISE DE INTEGRIDADE DOCUMENTAL
        inconsistencias.extend(self._analisar_integridade_documental(dados_nfe))
        
        # 2. DETECÇÃO DE PADRÕES FRAUDULENTOS
        inconsistencias.extend(self._detectar_padroes_fraudulentos(dados_nfe))
        
        # 3. VALIDAÇÕES DE COMPLIANCE FISCAL
        inconsistencias.extend(self._validar_compliance_fiscal(dados_nfe))
        
        # 4. ANÁLISE COMPORTAMENTAL
        inconsistencias.extend(self._analisar_comportamento_fiscal(dados_nfe))
        
        return inconsistencias
    
    def _analisar_integridade_documental(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, str]]:
        """Análise de integridade documental"""
        inconsistencias = []
        
        # Validação de chave de acesso
        chave = dados_nfe.get('chave_acesso', '')
        if not self._validar_chave_acesso_tecnica(chave):
            inconsistencias.append({
                'severidade': 'CRÍTICA',
                'categoria': 'INTEGRIDADE_DOCUMENTAL',
                'codigo': 'ID001',
                'descricao': 'Chave de acesso NFe apresenta formato ou DV incorreto conforme MOC NFe',
                'impacto': 'Documento fiscal inválido. Não possui validade jurídica',
                'solucao_tecnica': 'Reemitir NFe com chave gerada corretamente pelo sistema emissor',
                'prazo_correcao': 'IMEDIATO',
                'responsavel_tecnico': 'Analista de Sistemas + Contador',
                'norma_referencia': 'Manual de Orientação do Contribuinte NFe v6.0 - Item 4.2'
            })
        
        # Análise de consistência entre campos relacionados
        cnpj = dados_nfe.get('cnpj_emissor', '')
        ie = dados_nfe.get('inscricao_estadual', '')
        uf = dados_nfe.get('uf', '')
        
        if not self._validar_consistencia_cnpj_ie_uf(cnpj, ie, uf):
            inconsistencias.append({
                'severidade': 'ALTA',
                'categoria': 'CONSISTÊNCIA_CADASTRAL',
                'codigo': 'ID002',
                'descricao': f'Inconsistência entre CNPJ {cnpj}, IE {ie} e UF {uf}',
                'impacto': 'Possível uso de documentos falsificados ou cadastro irregular',
                'solucao_tecnica': 'Validar dados cadastrais na SEFAZ e RFB. Corrigir cadastro mestre',
                'prazo_correcao': '24 horas',
                'responsavel_tecnico': 'Departamento Fiscal',
                'norma_referencia': 'Convênio ICMS 57/95'
            })
        
        return inconsistencias
    
    def _detectar_padroes_fraudulentos(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, str]]:
        """Detecção de padrões típicos de fraude fiscal"""
        inconsistencias = []
        
        cnpj = dados_nfe.get('cnpj_emissor', '')
        valor = dados_nfe.get('valor_total', 0)
        data_emissao = dados_nfe.get('data_emissao', '')
        
        # Padrão 1: Operações sequenciais com valores "redondos"
        if self._detectar_valores_redondos_suspeitos(valor):
            inconsistencias.append({
                'severidade': 'MÉDIA',
                'categoria': 'PADRÃO_SUSPEITO',
                'codigo': 'PS001', 
                'descricao': f'Valor exatamente R$ {valor:,.2f} pode indicar simulação de operação',
                'impacto': 'Padrão monitored pela Receita Federal em análises de risco',
                'solucao_tecnica': 'Verificar autenticidade da operação. Manter documentação probatória',
                'prazo_correcao': '7 dias',
                'responsavel_tecnico': 'Auditoria Interna',
                'norma_referencia': 'Portaria RFB 3.518/2011 - Análise de Risco'
            })
        
        # Padrão 2: Emissões concentradas em horários específicos
        if self._detectar_horario_suspeito(data_emissao):
            inconsistencias.append({
                'severidade': 'BAIXA',
                'categoria': 'PADRÃO_TEMPORAL',
                'codigo': 'PS002',
                'descricao': 'Emissão em horário pouco usual para atividade comercial normal',
                'impacto': 'Pode indicar automação suspeita ou emissão em lote',
                'solucao_tecnica': 'Verificar se operação condiz com funcionamento normal da empresa',
                'prazo_correcao': '15 dias',
                'responsavel_tecnico': 'Controladoria',
                'norma_referencia': 'Análise Comportamental SEFAZ'
            })
        
        # Padrão 3: CNPJ com histórico de irregularidades
        risco_cnpj = self._avaliar_risco_historico_cnpj(cnpj)
        if risco_cnpj == 'ALTO':
            inconsistencias.append({
                'severidade': 'ALTA',
                'categoria': 'HISTÓRICO_IRREGULAR',
                'codigo': 'PS003',
                'descricao': 'CNPJ apresenta histórico de irregularidades em análises anteriores',
                'impacto': 'Alto risco de envolvimento em esquema de sonegação ou fraude',
                'solucao_tecnica': 'Suspender operações. Realizar due diligence completa',
                'prazo_correcao': 'IMEDIATO',
                'responsavel_tecnico': 'Jurídico + Compliance',
                'norma_referencia': 'Lei 12.846/2013 - Lei Anticorrupção'
            })
        
        return inconsistencias
    
    def _validar_compliance_fiscal(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, str]]:
        """Validações específicas de compliance fiscal"""
        inconsistencias = []
        
        # Análise de risco SPED
        if self._risco_sped_fiscal(dados_nfe):
            inconsistencias.append({
                'severidade': 'MÉDIA',
                'categoria': 'COMPLIANCE_SPED',
                'codigo': 'CF001',
                'descricao': 'Operação pode gerar inconsistência no SPED Fiscal',
                'impacto': 'Questionamento em validação automática da RFB/SEFAZ',
                'solucao_tecnica': 'Verificar escrituração no Bloco C. Considerar necessidade de ajuste',
                'prazo_correcao': '30 dias',
                'responsavel_tecnico': 'Contador Responsável',
                'norma_referencia': 'Decreto 6.022/2007 - SPED Fiscal'
            })
        
        # Validação e-Social
        if self._impacto_esocial(dados_nfe):
            inconsistencias.append({
                'severidade': 'BAIXA',
                'categoria': 'COMPLIANCE_ESOCIAL', 
                'codigo': 'CF002',
                'descricao': 'Operação pode impactar obrigações do e-Social',
                'impacto': 'Necessidade de verificação de eventos trabalhistas relacionados',
                'solucao_tecnica': 'Conferir se há colaboradores envolvidos na operação (transporte, etc)',
                'prazo_correcao': '15 dias',
                'responsavel_tecnico': 'Departamento Pessoal',
                'norma_referencia': 'Decreto 8.373/2014 - e-Social'
            })
        
        return inconsistencias
    
    def _analisar_comportamento_fiscal(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, str]]:
        """Análise comportamental para detecção de anomalias"""
        inconsistencias = []
        
        cnpj = dados_nfe.get('cnpj_emissor', '')
        
        # Análise de crescimento súbito de faturamento
        crescimento = self._analisar_crescimento_faturamento(cnpj, dados_nfe)
        if crescimento > 300:  # Crescimento superior a 300%
            inconsistencias.append({
                'severidade': 'MÉDIA',
                'categoria': 'ANÁLISE_COMPORTAMENTAL',
                'codigo': 'AC001',
                'descricao': f'Crescimento de faturamento de {crescimento:.1f}% em relação ao histórico',
                'impacto': 'Padrão que pode atrair fiscalização por variação anormal de receita',
                'solucao_tecnica': 'Documentar razões do crescimento. Preparar justificativas técnicas',
                'prazo_correcao': '30 dias',
                'responsavel_tecnico': 'Controladoria + Contabilidade',
                'norma_referencia': 'IN RFB 1.131/2011 - Parâmetros de Fiscalização'
            })
        
        # Detecção de sazonalidade anormal
        if self._detectar_sazonalidade_anormal(dados_nfe):
            inconsistencias.append({
                'severidade': 'BAIXA',
                'categoria': 'SAZONALIDADE',
                'codigo': 'AC002',
                'descricao': 'Operação fora do padrão sazonal esperado para o setor',
                'impacto': 'Possível questionamento sobre autenticidade das operações',
                'solucao_tecnica': 'Manter documentação que comprove a genuinidade das operações',
                'prazo_correcao': '60 dias',
                'responsavel_tecnico': 'Análise de Negócios',
                'norma_referencia': 'Análise Setorial SEFAZ'
            })
        
        return inconsistencias
    
    # MÉTODOS AUXILIARES ESPECIALIZADOS
    
    def _validar_chave_acesso_tecnica(self, chave: str) -> bool:
        """Validação técnica da chave de acesso NFe"""
        if not chave or len(chave) != 44:
            return False
            
        try:
            # Extrair componentes da chave
            uf = chave[0:2]
            ano_mes = chave[2:6]  
            cnpj = chave[6:20]
            modelo = chave[20:22]
            serie = chave[22:25]
            numero = chave[25:34]
            tipo_emissao = chave[34:35]
            codigo_numerico = chave[35:43]
            dv = chave[43:44]
            
            # Validações básicas
            if not (uf.isdigit() and 11 <= int(uf) <= 53):
                return False
                
            if not (ano_mes.isdigit() and len(ano_mes) == 4):
                return False
                
            if not self._validar_cnpj_na_chave(cnpj):
                return False
                
            # Validar DV da chave
            return self._calcular_dv_chave(chave[:-1]) == dv
            
        except:
            return False
    
    def _calcular_dv_chave(self, chave_sem_dv: str) -> str:
        """Calcula dígito verificador da chave NFe"""
        pesos = "432987654329876543298765432987654329876543"
        soma = sum(int(chave_sem_dv[i]) * int(pesos[i]) for i in range(43))
        resto = soma % 11
        return str(0 if resto <= 1 else 11 - resto)
    
    def _validar_cnpj_na_chave(self, cnpj_chave: str) -> bool:
        """Valida CNPJ extraído da chave"""
        if len(cnpj_chave) != 14:
            return False
        return self._validar_cnpj_algoritmo(cnpj_chave)
    
    def _validar_cnpj_algoritmo(self, cnpj: str) -> bool:
        """Algoritmo de validação CNPJ"""
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
            
        pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
        pesos2 = [6,5,4,3,2,9,8,7,6,5,4,3,2]
        
        soma1 = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        dv1 = 0 if (soma1 % 11) < 2 else 11 - (soma1 % 11)
        
        soma2 = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        dv2 = 0 if (soma2 % 11) < 2 else 11 - (soma2 % 11)
        
        return cnpj[-2:] == f"{dv1}{dv2}"
    
    def _validar_consistencia_cnpj_ie_uf(self, cnpj: str, ie: str, uf: str) -> bool:
        """Valida consistência entre CNPJ, IE e UF"""
        # Lógica simplificada - em produção consultar bases oficiais
        if not cnpj or not uf:
            return False
            
        # UFs válidas
        ufs_validas = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG',
                      'PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']
        
        return uf in ufs_validas
    
    def _detectar_valores_redondos_suspeitos(self, valor: float) -> bool:
        """Detecta valores suspeitamente "redondos" """
        if valor <= 0:
            return False
            
        # Valores exatos múltiplos de 1000 acima de R$ 5.000
        if valor >= 5000 and valor % 1000 == 0:
            return True
            
        # Valores exatos múltiplos de 10000 
        if valor % 10000 == 0 and valor >= 10000:
            return True
            
        return False
    
    def _detectar_horario_suspeito(self, data_emissao: str) -> bool:
        """Detecta horários suspeitos de emissão"""
        try:
            if not data_emissao:
                return False
                
            # Extrair hora se disponível
            if 'T' in data_emissao:
                hora_str = data_emissao.split('T')[1][:2]
                hora = int(hora_str)
                
                # Emissões entre 22h e 6h são suspeitas
                return hora >= 22 or hora <= 6
                
        except:
            pass
            
        return False
    
    def _avaliar_risco_historico_cnpj(self, cnpj: str) -> str:
        """Avalia risco baseado no histórico do CNPJ"""
        # Em produção, consultar base histórica real
        cnpj_clean = re.sub(r'\D', '', cnpj)
        
        # Simular CNPJs com histórico de risco
        cnpjs_alto_risco = ['11111111000111', '22222222000222', '33333333000333']
        cnpjs_medio_risco = ['44444444000444', '55555555000555']
        
        if cnpj_clean in cnpjs_alto_risco:
            return 'ALTO'
        elif cnpj_clean in cnpjs_medio_risco:
            return 'MÉDIO'
        else:
            return 'BAIXO'
    
    def _risco_sped_fiscal(self, dados_nfe: Dict[str, Any]) -> bool:
        """Avalia risco de inconsistência no SPED"""
        # Validações básicas que podem impactar SPED
        cfop = dados_nfe.get('cfop', '')
        cst = dados_nfe.get('cst', '')
        
        # CFOPs que exigem atenção especial no SPED
        cfops_especiais = ['5905', '6905', '5949', '6949']
        return cfop in cfops_especiais
    
    def _impacto_esocial(self, dados_nfe: Dict[str, Any]) -> bool:
        """Avalia impacto no e-Social"""
        # CFOPs relacionados a prestação de serviços que podem envolver trabalhadores
        cfop = dados_nfe.get('cfop', '')
        cfops_servicos = ['5933', '6933', '5949', '6949']
        return cfop in cfops_servicos
    
    def _analisar_crescimento_faturamento(self, cnpj: str, dados_nfe: Dict[str, Any]) -> float:
        """Analisa crescimento de faturamento"""
        # Em produção, consultar histórico real
        valor_atual = dados_nfe.get('valor_total', 0)
        
        # Simular histórico
        valor_medio_historico = 10000  # R$ 10k média histórica
        
        if valor_medio_historico > 0:
            crescimento = ((valor_atual - valor_medio_historico) / valor_medio_historico) * 100
            return max(0, crescimento)
        
        return 0
    
    def _detectar_sazonalidade_anormal(self, dados_nfe: Dict[str, Any]) -> bool:
        """Detecta padrões sazonais anormais"""
        try:
            data_emissao = dados_nfe.get('data_emissao', '')
            if not data_emissao:
                return False
                
            mes = int(data_emissao[5:7])
            valor = dados_nfe.get('valor_total', 0)
            
            # Exemplo: vendas muito altas em fevereiro (mês historicamente baixo)
            if mes == 2 and valor > 50000:
                return True
                
        except:
            pass
            
        return False
    
    def _carregar_padroes_suspeitos(self) -> Dict:
        """Carrega padrões conhecidos de fraude"""
        return {
            'valores_redondos': [1000, 5000, 10000, 50000, 100000],
            'horarios_suspeitos': list(range(22, 24)) + list(range(0, 7)),
            'cfops_atencao': ['5905', '6905', '5949', '6949', '5933', '6933']
        }

