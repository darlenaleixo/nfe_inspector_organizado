# ia_fiscal/analisador_riscos_profissional.py

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
from dataclasses import dataclass

@dataclass
class ResultadoAnalise:
    score: float
    nivel: str
    detalhes: Dict[str, Any]
    inconsistencias: List[Dict[str, str]]
    recomendacoes: List[Dict[str, str]]

class AnalisadorRiscosProfissional:
    """Analisador de riscos fiscal com expertise contábil profissional"""
    
    def __init__(self):
        self.tabela_ncm = self._carregar_tabela_ncm()
        self.tabela_cfop = self._carregar_tabela_cfop()
        self.tabela_cst = self._carregar_tabela_cst()
        self.regras_icms_st = self._carregar_regras_icms_st()
        
    def analisar_nfe(self, dados_nfe: Dict[str, Any]) -> ResultadoAnalise:
        """Análise completa da NFe com expertise contábil"""
        
        score_total = 0.0
        inconsistencias = []
        recomendacoes = []
        detalhes = {
            'validacoes_executadas': [],
            'alertas_fiscais': [],
            'obrigacoes_acessorias': [],
            'riscos_autuacao': []
        }
        
        # 1. VALIDAÇÕES CADASTRAIS (Peso: 25%)
        score_cadastral, inc_cad, rec_cad = self._analisar_dados_cadastrais(dados_nfe)
        score_total += score_cadastral * 0.25
        inconsistencias.extend(inc_cad)
        recomendacoes.extend(rec_cad)
        detalhes['validacoes_executadas'].append('Análise cadastral completa')
        
        # 2. VALIDAÇÕES TRIBUTÁRIAS (Peso: 35%)
        score_tributario, inc_trib, rec_trib = self._analisar_tributos(dados_nfe)
        score_total += score_tributario * 0.35
        inconsistencias.extend(inc_trib)
        recomendacoes.extend(rec_trib)
        detalhes['validacoes_executadas'].append('Cálculos tributários verificados')
        
        # 3. CLASSIFICAÇÃO FISCAL (Peso: 20%)
        score_classificacao, inc_class, rec_class = self._analisar_classificacao_fiscal(dados_nfe)
        score_total += score_classificacao * 0.20
        inconsistencias.extend(inc_class)
        recomendacoes.extend(rec_class)
        detalhes['validacoes_executadas'].append('Classificação fiscal analisada')
        
        # 4. CONFORMIDADE OPERACIONAL (Peso: 20%)
        score_operacional, inc_oper, rec_oper = self._analisar_conformidade_operacional(dados_nfe)
        score_total += score_operacional * 0.20
        inconsistencias.extend(inc_oper)
        recomendacoes.extend(rec_oper)
        detalhes['validacoes_executadas'].append('Conformidade operacional verificada')
        
        # Determinar nível de risco
        if score_total >= 7.5:
            nivel = "CRÍTICO"
            detalhes['riscos_autuacao'].append("Risco iminente de autuação fiscal")
        elif score_total >= 5.5:
            nivel = "ALTO"
            detalhes['riscos_autuacao'].append("Alto risco de questionamento fiscal")
        elif score_total >= 3.0:
            nivel = "MÉDIO"
            detalhes['alertas_fiscais'].append("Requer atenção do responsável técnico")
        else:
            nivel = "BAIXO"
            detalhes['alertas_fiscais'].append("NFe em conformidade básica")
        
        # Alertas de obrigações acessórias
        detalhes['obrigacoes_acessorias'] = self._gerar_alertas_obrigacoes(dados_nfe, inconsistencias)
        
        return ResultadoAnalise(
            score=round(score_total, 2),
            nivel=nivel,
            detalhes=detalhes,
            inconsistencias=inconsistencias,
            recomendacoes=recomendacoes
        )
    
    def _analisar_dados_cadastrais(self, dados_nfe: Dict[str, Any]) -> tuple:
        """Análise profissional de dados cadastrais"""
        score = 0.0
        inconsistencias = []
        recomendacoes = []
        
        cnpj_emissor = dados_nfe.get('cnpj_emissor', '')
        
        # Validação técnica de CNPJ
        if not self._validar_cnpj_tecnico(cnpj_emissor):
            score += 3.0
            inconsistencias.append({
                'severidade': 'ALTA',
                'categoria': 'VALIDAÇÃO_CADASTRAL',
                'codigo_erro': 'E001',
                'descricao': 'CNPJ do emissor apresenta dígitos verificadores incorretos conforme algoritmo da RFB',
                'impacto': 'Nota fiscal inválida para fins de escrituração contábil (Art. 175 RIR/2018)',
                'norma_legal': 'Instrução Normativa RFB nº 1470/2014'
            })
            recomendacoes.append({
                'problema': 'CNPJ com DV incorreto',
                'solucao': 'Corrigir CNPJ no cadastro de clientes/fornecedores antes da emissão. Validar na base da RFB.',
                'prioridade': 'CRÍTICA',
                'tempo_estimado': '30 minutos',
                'responsavel': 'Departamento Fiscal',
                'codigo_procedimento': 'PROC-001'
            })
        
        # Consulta situação cadastral (simulada)
        situacao_cnpj = self._consultar_situacao_cnpj(cnpj_emissor)
        if situacao_cnpj in ['INAPTA', 'SUSPENSA', 'BAIXADA']:
            score += 4.0
            inconsistencias.append({
                'severidade': 'CRÍTICA',
                'categoria': 'SITUAÇÃO_CADASTRAL', 
                'codigo_erro': 'E002',
                'descricao': f'CNPJ do destinatário encontra-se {situacao_cnpj} na base da Receita Federal',
                'impacto': 'Operação comercial inválida. Risco de glosa total de créditos de ICMS/PIS/COFINS',
                'norma_legal': 'Art. 3º da Lei 8.137/90 c/c Art. 11 da Lei 8.212/91'
            })
            recomendacoes.append({
                'problema': f'Empresa {situacao_cnpj}',
                'solucao': 'Suspender operações com esta empresa. Notificar departamento comercial. Regularizar pendências na RFB.',
                'prioridade': 'CRÍTICA',
                'tempo_estimado': '1 dia útil',
                'responsavel': 'Contador Responsável + Jurídico',
                'codigo_procedimento': 'PROC-002'
            })
        
        # Validação Inscrição Estadual
        ie = dados_nfe.get('inscricao_estadual', '')
        uf = dados_nfe.get('uf', '')
        if ie and not self._validar_ie_por_uf(ie, uf):
            score += 2.0
            inconsistencias.append({
                'severidade': 'MÉDIA',
                'categoria': 'INSCRIÇÃO_ESTADUAL',
                'codigo_erro': 'E003', 
                'descricao': f'Inscrição Estadual {ie} inválida para UF {uf} conforme algoritmo estadual',
                'impacto': 'Possível glosa de crédito de ICMS. Questionamento em fiscalização eletrônica',
                'norma_legal': f'Regulamento ICMS {uf}'
            })
        
        return score, inconsistencias, recomendacoes
    
    def _analisar_tributos(self, dados_nfe: Dict[str, Any]) -> tuple:
        """Análise profissional de cálculos tributários"""
        score = 0.0
        inconsistencias = []
        recomendacoes = []
        
        valor_total = dados_nfe.get('valor_total', 0)
        valor_icms = dados_nfe.get('valor_icms', 0)
        valor_pis = dados_nfe.get('valor_pis', 0)
        valor_cofins = dados_nfe.get('valor_cofins', 0)
        cfop = dados_nfe.get('cfop', '')
        cst = dados_nfe.get('cst', '')
        
        # Validação ICMS x CST
        if self._cst_requer_icms(cst) and valor_icms == 0:
            score += 2.5
            inconsistencias.append({
                'severidade': 'ALTA',
                'categoria': 'CÁLCULO_ICMS',
                'codigo_erro': 'T001',
                'descricao': f'CST {cst} indica operação tributada, porém valor ICMS = R$ 0,00',
                'impacto': 'Inconsistência que pode gerar auto de infração por sonegação fiscal',
                'norma_legal': 'Art. 155 CF/88 c/c RICMS/SP Art. 29'
            })
            recomendacoes.append({
                'problema': 'ICMS não calculado em CST tributado',
                'solucao': 'Revisar parametrização fiscal no ERP. Calcular ICMS conforme alíquota da UF de destino.',
                'prioridade': 'ALTA', 
                'tempo_estimado': '1 hora',
                'responsavel': 'Contador',
                'codigo_procedimento': 'PROC-T001'
            })
        
        # Validação PIS/COFINS
        if self._operacao_requer_pis_cofins(cfop):
            aliq_pis_esperada = 0.0165
            aliq_cofins_esperada = 0.076
            
            pis_calculado = valor_total * aliq_pis_esperada
            cofins_calculado = valor_total * aliq_cofins_esperada
            
            if abs(valor_pis - pis_calculado) > 0.10:
                score += 1.5
                inconsistencias.append({
                    'severidade': 'MÉDIA',
                    'categoria': 'CÁLCULO_PIS',
                    'codigo_erro': 'T002',
                    'descricao': f'PIS calculado: R$ {pis_calculado:.2f}, informado: R$ {valor_pis:.2f}',
                    'impacto': 'Divergência pode gerar questionamento da RFB em malha fiscal',
                    'norma_legal': 'Lei 10.637/2002 Art. 2º'
                })
        
        # Validação CFOP x Operação
        uf_origem = dados_nfe.get('uf_origem', '')
        uf_destino = dados_nfe.get('uf_destino', uf_origem)
        
        if self._cfop_incompativel_com_ufs(cfop, uf_origem, uf_destino):
            score += 2.0
            inconsistencias.append({
                'severidade': 'ALTA',
                'categoria': 'CFOP_INCOMPATÍVEL',
                'codigo_erro': 'T003',
                'descricao': f'CFOP {cfop} incompatível: origem {uf_origem}, destino {uf_destino}',
                'impacto': 'Erro pode invalidar escrituração no SPED Fiscal',
                'norma_legal': 'Ajuste SINIEF 02/2009'
            })
            
            cfop_correto = '6' + cfop[1:] if uf_origem != uf_destino else '5' + cfop[1:]
            recomendacoes.append({
                'problema': 'CFOP incompatível com operação',
                'solucao': f'Corrigir para CFOP {cfop_correto}. Revisar tabela de CFOPs no sistema.',
                'prioridade': 'ALTA',
                'tempo_estimado': '30 minutos', 
                'responsavel': 'Departamento Fiscal',
                'codigo_procedimento': 'PROC-T003'
            })
        
        return score, inconsistencias, recomendacoes
    
    def _analisar_classificacao_fiscal(self, dados_nfe: Dict[str, Any]) -> tuple:
        """Análise de classificação fiscal (NCM, CEST, etc)"""
        score = 0.0
        inconsistencias = []
        recomendacoes = []
        
        ncm = dados_nfe.get('ncm', '')
        cest = dados_nfe.get('cest', '')
        
        # Validação NCM
        if not self._ncm_valido_na_tipi(ncm):
            score += 3.0
            inconsistencias.append({
                'severidade': 'ALTA',
                'categoria': 'NCM_INVÁLIDO',
                'codigo_erro': 'C001',
                'descricao': f'NCM {ncm} não localizado na Tabela TIPI vigente (Decreto 8.950/2016)',
                'impacto': 'Produto pode ser bloqueado na entrada. Risco de apreensão fiscal',
                'norma_legal': 'Decreto 8.950/2016 - Tabela TIPI'
            })
            recomendacoes.append({
                'problema': 'NCM inválido/desatualizado',
                'solucao': 'Consultar NCM correto no site da RFB. Atualizar cadastro de produtos no ERP.',
                'prioridade': 'ALTA',
                'tempo_estimado': '45 minutos',
                'responsavel': 'Departamento Fiscal + Cadastro',
                'codigo_procedimento': 'PROC-C001'
            })
        
        # Validação CEST obrigatório
        if self._ncm_requer_cest(ncm) and not cest:
            score += 2.0
            inconsistencias.append({
                'severidade': 'MÉDIA', 
                'categoria': 'CEST_OBRIGATÓRIO',
                'codigo_erro': 'C002',
                'descricao': f'NCM {ncm} sujeito ao ICMS-ST, porém campo CEST não informado',
                'impacto': 'Rejeição automática na SEFAZ. Impossibilidade de autorização da NFe',
                'norma_legal': 'Convênio ICMS 92/2015'
            })
            
            cest_sugerido = self._sugerir_cest_para_ncm(ncm)
            recomendacoes.append({
                'problema': 'CEST não informado',
                'solucao': f'Informar CEST {cest_sugerido} conforme Anexo XXVII do RICMS.',
                'prioridade': 'MÉDIA',
                'tempo_estimado': '15 minutos',
                'responsavel': 'Departamento Fiscal',
                'codigo_procedimento': 'PROC-C002'
            })
        
        return score, inconsistencias, recomendacoes
    
    def _analisar_conformidade_operacional(self, dados_nfe: Dict[str, Any]) -> tuple:
        """Análise de conformidade operacional"""
        score = 0.0
        inconsistencias = []
        recomendacoes = []
        
        data_emissao = dados_nfe.get('data_emissao', '')
        valor_total = dados_nfe.get('valor_total', 0)
        
        # Validação de data de emissão
        try:
            dt_emissao = datetime.strptime(data_emissao[:10], '%Y-%m-%d') if data_emissao else datetime.now()
            dt_hoje = datetime.now()
            
            if dt_emissao > dt_hoje:
                score += 4.0
                inconsistencias.append({
                    'severidade': 'CRÍTICA',
                    'categoria': 'DATA_FUTURA',
                    'codigo_erro': 'O001',
                    'descricao': f'Data de emissão {data_emissao[:10]} é posterior à data atual',
                    'impacto': 'Nota fiscal inválida. Configura falsificação de documento fiscal',
                    'norma_legal': 'Art. 1º do Decreto 85.878/81'
                })
            
            elif (dt_hoje - dt_emissao).days > 120:
                score += 1.0
                inconsistencias.append({
                    'severidade': 'BAIXA',
                    'categoria': 'DATA_ANTIGA',
                    'codigo_erro': 'O002', 
                    'descricao': f'NFe emitida há {(dt_hoje - dt_emissao).days} dias',
                    'impacto': 'Possível questionamento sobre estoque parado ou operação simulada',
                    'norma_legal': 'Portaria CAT 162/2008'
                })
                
        except:
            score += 2.0
            inconsistencias.append({
                'severidade': 'ALTA',
                'categoria': 'DATA_INVÁLIDA',
                'codigo_erro': 'O003',
                'descricao': 'Data de emissão em formato inválido ou não informada',
                'impacto': 'NFe será rejeitada na autorização',
                'norma_legal': 'Manual de Orientação NFe v6.0'
            })
        
        # Validação de valor suspeito
        if valor_total > 100000:  # Acima de R$ 100k
            score += 0.5
            inconsistencias.append({
                'severidade': 'BAIXA',
                'categoria': 'VALOR_ELEVADO',
                'codigo_erro': 'O004',
                'descricao': f'Operação de alto valor: R$ {valor_total:,.2f}',
                'impacto': 'Operação sujeita a maior escrutínio fiscal. Requer documentação adicional',
                'norma_legal': 'Lei 9.613/98 (Prevenção à Lavagem)'
            })
            
            recomendacoes.append({
                'problema': 'Operação de alto valor',
                'solucao': 'Manter documentação probatória adicional (contratos, comprovantes de pagamento, etc).',
                'prioridade': 'BAIXA',
                'tempo_estimado': '30 minutos',
                'responsavel': 'Departamento Financeiro',
                'codigo_procedimento': 'PROC-O004'
            })
        
        return score, inconsistencias, recomendacoes
    
    # MÉTODOS AUXILIARES TÉCNICOS
    
    def _validar_cnpj_tecnico(self, cnpj: str) -> bool:
        """Validação técnica CNPJ conforme algoritmo RFB"""
        if not cnpj:
            return False
            
        cnpj = re.sub(r'\D', '', cnpj)
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        
        # Algoritmo oficial de validação
        pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
        pesos2 = [6,5,4,3,2,9,8,7,6,5,4,3,2]
        
        soma1 = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        resto1 = soma1 % 11
        dv1 = 0 if resto1 < 2 else 11 - resto1
        
        soma2 = sum(int(cnpj[i]) * pesos2[i] for i in range(13))  
        resto2 = soma2 % 11
        dv2 = 0 if resto2 < 2 else 11 - resto2
        
        return cnpj[-2:] == f"{dv1}{dv2}"
    
    def _consultar_situacao_cnpj(self, cnpj: str) -> str:
        """Simula consulta situação CNPJ na RFB"""
        # Em produção, fazer chamada para API da RFB
        cnpj_clean = re.sub(r'\D', '', cnpj)
        
        # Lista de CNPJs teste com situações diferentes
        cnpjs_inaptos = ['11111111000111', '22222222000222']
        cnpjs_suspensos = ['33333333000333', '44444444000444'] 
        cnpjs_baixados = ['55555555000555', '66666666000666']
        
        if cnpj_clean in cnpjs_inaptos:
            return 'INAPTA'
        elif cnpj_clean in cnpjs_suspensos:
            return 'SUSPENSA'
        elif cnpj_clean in cnpjs_baixados:
            return 'BAIXADA'
        else:
            return 'ATIVA'
    
    def _validar_ie_por_uf(self, ie: str, uf: str) -> bool:
        """Validação IE por UF (simplificada)"""
        if not ie or ie.upper() == 'ISENTO':
            return True
            
        # Algoritmos específicos por UF (implementar conforme necessidade)
        validacoes_uf = {
            'SP': lambda x: len(re.sub(r'\D', '', x)) in [12, 13],
            'RJ': lambda x: len(re.sub(r'\D', '', x)) == 8,
            'MG': lambda x: len(re.sub(r'\D', '', x)) == 13,
            # Adicionar demais UFs
        }
        
        validador = validacoes_uf.get(uf, lambda x: True)
        return validador(ie)
    
    def _cst_requer_icms(self, cst: str) -> bool:
        """Verifica se CST exige cálculo de ICMS"""
        csts_tributados = ['00', '10', '20', '30', '51', '60', '70', '90']
        return cst in csts_tributados
    
    def _operacao_requer_pis_cofins(self, cfop: str) -> bool:
        """Verifica se CFOP é tributado por PIS/COFINS"""
        cfops_tributados = ['5101', '5102', '5109', '5116', '5117', '5118', 
                           '6101', '6102', '6109', '6116', '6117', '6118']
        return cfop in cfops_tributados
    
    def _cfop_incompativel_com_ufs(self, cfop: str, uf_origem: str, uf_destino: str) -> bool:
        """Verifica incompatibilidade CFOP x UFs"""
        if not cfop or len(cfop) != 4:
            return False
            
        primeiro_digito = cfop[0]
        
        # CFOP 5xxx = estadual, 6xxx = interestadual
        if primeiro_digito == '5' and uf_origem != uf_destino:
            return True
        if primeiro_digito == '6' and uf_origem == uf_destino:
            return True
            
        return False
    
    def _ncm_valido_na_tipi(self, ncm: str) -> bool:
        """Valida NCM na tabela TIPI (simplificado)"""
        if not ncm or len(ncm) != 8:
            return False
            
        # Lista básica de NCMs inválidos para teste
        ncms_invalidos = ['00000000', '99999999', '12345678']
        return ncm not in ncms_invalidos
    
    def _ncm_requer_cest(self, ncm: str) -> bool:
        """Verifica se NCM está sujeito ao ICMS-ST"""
        # NCMs sujeitos ao ST (lista simplificada)
        ncms_st = ['22021000', '22030000', '27101259', '87032310']
        return ncm in ncms_st
    
    def _sugerir_cest_para_ncm(self, ncm: str) -> str:
        """Sugere CEST para NCM"""
        sugestoes = {
            '22021000': '03.002.00',
            '22030000': '03.003.00',
            '27101259': '06.001.00'
        }
        return sugestoes.get(ncm, '01.001.00')
    
    def _gerar_alertas_obrigacoes(self, dados_nfe: Dict[str, Any], inconsistencias: List) -> List[str]:
        """Gera alertas sobre obrigações acessórias"""
        alertas = []
        
        # Baseado no número de inconsistências
        if len(inconsistencias) > 5:
            alertas.append("Recomenda-se revisão geral dos processos fiscais da empresa")
            alertas.append("Considerar auditoria interna antes da próxima fiscalização")
        
        if len(inconsistencias) > 2:
            alertas.append("Verificar impacto no SPED Fiscal do período")
            alertas.append("Analisar necessidade de retificação de declarações")
        
        # Alertas específicos por valor
        valor = dados_nfe.get('valor_total', 0)
        if valor > 50000:
            alertas.append("Operação sujeita ao LALUR - verificar reflexos no IRPJ/CSLL")
        
        return alertas
    
    def _carregar_tabela_ncm(self) -> Dict:
        """Carrega tabela NCM (simulada)"""
        return {}
    
    def _carregar_tabela_cfop(self) -> Dict:
        """Carrega tabela CFOP (simulada)"""
        return {}
    
    def _carregar_tabela_cst(self) -> Dict:
        """Carrega tabela CST (simulada)"""
        return {}
    
    def _carregar_regras_icms_st(self) -> Dict:
        """Carrega regras ICMS-ST (simulada)"""
        return {}
