# ia_fiscal/detector_fraudes.py

import re
from typing import Dict, List, Any, Tuple
from datetime import datetime
from .config import config_ia
import logging


class DetectorFraudes:
    """Detecta fraudes e inconsistências em documentos fiscais"""
    
    def __init__(self):
        self.padroes_fraude = self._carregar_padroes_fraude()
    
    def detectar_inconsistencias(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detecta todas as inconsistências na NFe"""
        
        inconsistencias = []
        
        # 1. Validações de CNPJ/CPF
        inconsistencias.extend(self._validar_documentos(dados_nfe))
        
        # 2. Validações de valores
        inconsistencias.extend(self._validar_valores(dados_nfe))
        
        # 3. Validações de datas
        inconsistencias.extend(self._validar_datas(dados_nfe))
        
        # 4. Validações de produtos
        inconsistencias.extend(self._validar_produtos(dados_nfe))
        
        # 5. Validações de impostos
        inconsistencias.extend(self._validar_impostos(dados_nfe))
        
        # 6. Padrões suspeitos conhecidos
        inconsistencias.extend(self._detectar_padroes_suspeitos(dados_nfe))
        
        return inconsistencias
    
    def _validar_documentos(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida CNPJs, CPFs e inscrições estaduais"""
        problemas = []
        
        # Validar CNPJ do emissor
        cnpj_emissor = dados_nfe.get('cnpj_emissor', '')
        if not self._validar_cnpj(cnpj_emissor):
            problemas.append({
                "tipo": "documento_invalido",
                "severidade": "alta",
                "campo": "cnpj_emissor",
                "valor": cnpj_emissor,
                "descricao": "CNPJ do emissor inválido",
                "sugestao": "Verificar dígitos verificadores do CNPJ"
            })
        
        # Validar documento do destinatário
        doc_dest = dados_nfe.get('documento_destinatario', '')
        tipo_doc = dados_nfe.get('tipo_documento_destinatario', 'cnpj')
        
        if tipo_doc == 'cnpj' and not self._validar_cnpj(doc_dest):
            problemas.append({
                "tipo": "documento_invalido",
                "severidade": "alta", 
                "campo": "documento_destinatario",
                "valor": doc_dest,
                "descricao": "CNPJ do destinatário inválido"
            })
        elif tipo_doc == 'cpf' and not self._validar_cpf(doc_dest):
            problemas.append({
                "tipo": "documento_invalido",
                "severidade": "alta",
                "campo": "documento_destinatario", 
                "valor": doc_dest,
                "descricao": "CPF do destinatário inválido"
            })
        
        return problemas
    
    def _validar_valores(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida consistência entre valores"""
        problemas = []
        
        try:
            valor_produtos = float(dados_nfe.get('valor_produtos', 0))
            valor_total = float(dados_nfe.get('valor_total', 0))
            valor_impostos = float(dados_nfe.get('valor_impostos', 0))
            
            # Valor total deve ser produtos + impostos (aproximadamente)
            diferenca_esperada = abs(valor_total - (valor_produtos + valor_impostos))
            if diferenca_esperada > 0.10:  # Diferença maior que 10 centavos
                problemas.append({
                    "tipo": "calculo_inconsistente",
                    "severidade": "media",
                    "campo": "valor_total",
                    "descricao": f"Inconsistência nos valores: Total={valor_total}, Produtos+Impostos={valor_produtos + valor_impostos}",
                    "sugestao": "Recalcular valor total"
                })
            
            # Valores negativos
            if valor_total < 0:
                problemas.append({
                    "tipo": "valor_negativo",
                    "severidade": "alta",
                    "campo": "valor_total",
                    "valor": valor_total,
                    "descricao": "Valor total não pode ser negativo"
                })
                
        except (ValueError, TypeError):
            problemas.append({
                "tipo": "valor_invalido",
                "severidade": "alta",
                "campo": "valores",
                "descricao": "Valores contêm caracteres não numéricos"
            })
        
        return problemas
    
    def _validar_datas(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida consistência de datas"""
        problemas = []
        
        try:
            data_emissao_str = dados_nfe.get('data_emissao', '')
            data_emissao = datetime.strptime(data_emissao_str, '%Y-%m-%d')
            hoje = datetime.now()
            
            # Data no futuro
            if data_emissao > hoje:
                problemas.append({
                    "tipo": "data_futura",
                    "severidade": "alta",
                    "campo": "data_emissao",
                    "valor": data_emissao_str,
                    "descricao": "Data de emissão no futuro",
                    "sugestao": "Verificar data de emissão"
                })
            
            # Data muito antiga (mais de 1 ano)
            if (hoje - data_emissao).days > 365:
                problemas.append({
                    "tipo": "data_antiga",
                    "severidade": "media",
                    "campo": "data_emissao",
                    "valor": data_emissao_str,
                    "descricao": f"NFe muito antiga: {(hoje - data_emissao).days} dias"
                })
                
        except (ValueError, TypeError):
            problemas.append({
                "tipo": "data_invalida",
                "severidade": "alta",
                "campo": "data_emissao",
                "descricao": "Formato de data inválido"
            })
        
        return problemas
    
    def _validar_produtos(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida dados dos produtos/serviços"""
        problemas = []
        
        itens = dados_nfe.get('itens', [])
        if not itens:
            problemas.append({
                "tipo": "sem_itens",
                "severidade": "alta",
                "campo": "itens",
                "descricao": "NFe sem itens"
            })
            return problemas
        
        for i, item in enumerate(itens):
            # NCM obrigatório para produtos
            ncm = item.get('ncm', '')
            if not ncm or len(ncm) != 8:
                problemas.append({
                    "tipo": "ncm_invalido",
                    "severidade": "media",
                    "campo": f"item[{i}].ncm",
                    "valor": ncm,
                    "descricao": f"NCM inválido no item {i+1}"
                })
            
            # Quantidade não pode ser zero ou negativa
            quantidade = float(item.get('quantidade', 0))
            if quantidade <= 0:
                problemas.append({
                    "tipo": "quantidade_invalida",
                    "severidade": "alta",
                    "campo": f"item[{i}].quantidade",
                    "valor": quantidade,
                    "descricao": f"Quantidade inválida no item {i+1}"
                })
        
        return problemas
    
    def _validar_impostos(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Valida cálculos de impostos"""
        problemas = []
        
        itens = dados_nfe.get('itens', [])
        for i, item in enumerate(itens):
            # Validar ICMS
            icms_cst = item.get('icms_cst', '')
            icms_aliquota = float(item.get('icms_aliquota', 0))
            
            # CST 00 deve ter alíquota > 0
            if icms_cst == '00' and icms_aliquota == 0:
                problemas.append({
                    "tipo": "imposto_inconsistente",
                    "severidade": "media",
                    "campo": f"item[{i}].icms",
                    "descricao": f"Item {i+1}: CST 00 sem alíquota de ICMS"
                })
            
            # CST 40, 41, 50 não devem ter alíquota
            if icms_cst in ['40', '41', '50'] and icms_aliquota > 0:
                problemas.append({
                    "tipo": "imposto_inconsistente",
                    "severidade": "media", 
                    "campo": f"item[{i}].icms",
                    "descricao": f"Item {i+1}: CST {icms_cst} não deve ter alíquota"
                })
        
        return problemas
    
    def _detectar_padroes_suspeitos(self, dados_nfe: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detecta padrões conhecidos de fraude"""
        problemas = []
        
        # Padrão: Notas de valor redondo muito específico
        valor_total = float(dados_nfe.get('valor_total', 0))
        if valor_total in [999.99, 9999.99, 99999.99]:
            problemas.append({
                "tipo": "padrao_suspeito",
                "severidade": "media",
                "campo": "valor_total",
                "valor": valor_total,
                "descricao": "Valor suspeito: valor exato comum em fraudes"
            })
        
        # Padrão: Sequência de notas do mesmo fornecedor
        cnpj = dados_nfe.get('cnpj_emissor', '')
        if cnpj in self.padroes_fraude.get('cnpjs_suspeitos', set()):
            problemas.append({
                "tipo": "fornecedor_suspeito",
                "severidade": "alta",
                "campo": "cnpj_emissor", 
                "valor": cnpj,
                "descricao": "Fornecedor em lista de suspeitos"
            })
        
        return problemas
    
    def _validar_cnpj(self, cnpj):
        """Valida CNPJ usando algoritmo oficial"""
        try:
            # CORREÇÃO: Converter para string primeiro
            if cnpj is None:
                return False
                
            cnpj_str = str(cnpj)  # Converter para string
            
            # Remove caracteres não numéricos
            cnpj = re.sub(r'[^0-9]', '', cnpj_str)
            
            # Verifica se tem 14 dígitos
            if len(cnpj) != 14:
                return False
            
            # Verifica se todos os dígitos são iguais
            if cnpj == cnpj[0] * 14:
                return False
            
            # Calcula primeiro dígito verificador
            soma = 0
            peso = 5
            for i in range(12):
                soma += int(cnpj[i]) * peso
                peso -= 1
                if peso < 2:
                    peso = 9
            
            resto = soma % 11
            dv1 = 0 if resto < 2 else 11 - resto
            
            # Calcula segundo dígito verificador
            soma = 0
            peso = 6
            for i in range(13):
                soma += int(cnpj[i]) * peso
                peso -= 1
                if peso < 2:
                    peso = 9
            
            resto = soma % 11
            dv2 = 0 if resto < 2 else 11 - resto
            
            # Verifica se os dígitos verificadores estão corretos
            return cnpj[-2:] == f"{dv1}{dv2}"
            
        except Exception as e:
            logging.error(f"Erro na validação CNPJ: {e}")
            return False
    
    def _validar_cpf(self, cpf: str) -> bool:
        """Valida CPF com dígitos verificadores"""
        if not cpf:
            return False
            
        # Remove caracteres não numéricos
        cpf = re.sub(r'[^0-9]', '', cpf)
        
        if len(cpf) != 11:
            return False
        
        # Verifica se todos os dígitos são iguais
        if cpf == cpf[0] * 11:
            return False
        
        # Cálculo dos dígitos verificadores
        def calcular_digito(cpf_parcial, peso_inicial):
            soma = sum(int(cpf_parcial[i]) * (peso_inicial - i) for i in range(len(cpf_parcial)))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto
        
        # Primeiro dígito
        digito1 = calcular_digito(cpf[:9], 10)
        if int(cpf[9]) != digito1:
            return False
        
        # Segundo dígito
        digito2 = calcular_digito(cpf[:10], 11)
        return int(cpf[10]) == digito2
    
    def _carregar_padroes_fraude(self) -> Dict[str, Any]:
        """Carrega padrões conhecidos de fraude"""
        return {
            "cnpjs_suspeitos": set([
                # Lista de CNPJs conhecidamente problemáticos
            ]),
            "valores_suspeitos": [999.99, 9999.99, 99999.99],
            "cfops_alertas": ["5949", "6949"]  # CFOPs genéricos
        }
