# -*- coding: utf-8 -*-
import os
import logging
import json
import pandas as pd
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from core.parser import parse_nfe_nfce_xml
from core.validator import validar_com_xsd
from core.utils import error_handler, CacheManager

class NFeProcessor:
    """
    Classe para processar múltiplos XMLs de NFe/NFCe em uma pasta,
    gerar relatórios e calcular resumos, utilizando um sistema de cache.
    """
    def __init__(self, pasta_xml: str, pasta_saida: str):
        self.pasta_xml = pasta_xml
        self.pasta_saida = pasta_saida
        self.dados_processados: List[Dict[str, Any]] = []
        self.chaves_canceladas: set = set()
        self.resumos: Dict[str, Any] = {}
        self.estatisticas = {
            "total_arquivos": 0, "notas_processadas_sucesso": 0,
            "arquivos_com_erro": 0, "arquivos_invalidos_xsd": 0,
            "notas_canceladas": 0, "carregados_do_cache": 0,
        }
        self.cache = CacheManager()
        self.regras_fiscais = self._carregar_regras_fiscais()

    def _carregar_regras_fiscais(self) -> Dict:
        """Carrega as regras de alíquotas do arquivo JSON."""
        caminho_regras = 'regras_fiscais.json'
        if os.path.exists(caminho_regras):
            try:
                with open(caminho_regras, 'r', encoding='utf-8') as f:
                    logging.info("Arquivo de regras fiscais encontrado e carregado.")
                    return json.load(f)
            except Exception as e:
                logging.error(f"Erro ao carregar o arquivo de regras fiscais: {e}")
        logging.warning("Arquivo 'regras_fiscais.json' não encontrado. A auditoria de alíquotas será pulada.")
        return {}

    def _coletar_chaves_canceladas(self) -> set:
        """Varre XMLs de evento e retorna o conjunto de chaves de NFes canceladas."""
        logging.info("Coleta de chaves canceladas (simulada).")
        return set()

    def processar_pasta(self):
        """Processa todos os XMLs na pasta especificada em paralelo, utilizando cache."""
        logging.info(f"Iniciando processamento da pasta: {self.pasta_xml}")
        
        self.chaves_canceladas = self._coletar_chaves_canceladas()
        self.estatisticas["notas_canceladas"] = len(self.chaves_canceladas)

        lista_arquivos_xml = [os.path.join(root, f) for root, _, files in os.walk(self.pasta_xml) for f in files if f.lower().endswith(".xml") and "evt" not in f.lower()]
        self.estatisticas["total_arquivos"] = len(lista_arquivos_xml)
        
        logging.info(f"Encontrados {len(lista_arquivos_xml)} arquivos XML para processar.")
        
        processados = 0
        with ThreadPoolExecutor() as executor:
            future_to_file = {executor.submit(self._processar_arquivo_individual, fp): fp for fp in lista_arquivos_xml}
            for future in as_completed(future_to_file):
                resultado = future.result()
                if resultado:
                    self.dados_processados.extend(resultado)
                    processados += 1
        
        self.estatisticas["notas_processadas_sucesso"] = processados
        logging.info(f"Processamento concluído. {processados} notas processadas com sucesso ({self.estatisticas['carregados_do_cache']} carregadas do cache).")

    def _processar_arquivo_individual(self, fp: str) -> List[Dict[str, Any]] | None:
        """Valida e processa um único arquivo XML, utilizando o cache."""
        dados_cacheados = self.cache.get(fp)
        if dados_cacheados is not None:
            self.estatisticas["carregados_do_cache"] += 1
            return dados_cacheados

        is_valido, erro_xsd = validar_com_xsd(fp)
        if not is_valido:
            logging.warning(f"Falha na validação XSD para {os.path.basename(fp)}: {erro_xsd}")
            self.estatisticas["arquivos_invalidos_xsd"] += 1
            return None

        with error_handler(f"processamento de {os.path.basename(fp)}"):
            dados = parse_nfe_nfce_xml(fp, self.chaves_canceladas)
            if dados:
                self.cache.set(fp, dados)
                return dados
            else:
                self.estatisticas["arquivos_com_erro"] += 1
                return None
        return None

    def calcular_resumos(self):
        """Calcula todos os resumos e análises após o processamento dos dados."""
        if not self.dados_processados:
            logging.warning("Nenhum dado processado para calcular resumos.")
            return

        logging.info("Calculando resumos e análises...")
        self._calcular_resumos_pandas()

    def _calcular_resumos_pandas(self):
        """Calcula resumos usando a biblioteca pandas para alta performance."""
        df = pd.DataFrame(self.dados_processados)
        df_autorizadas = df[df['status'] == 'Autorizada'].copy()

        df_autorizadas['valor_total_nf'] = pd.to_numeric(df_autorizadas['valor_total_nf'], errors='coerce').fillna(0)
        df_autorizadas['item_valor_total'] = pd.to_numeric(df_autorizadas['item_valor_total'], errors='coerce').fillna(0)

        self.resumos['total_vendas'] = df_autorizadas.drop_duplicates(subset=['chave_acesso'])['valor_total_nf'].sum()
        self.resumos['total_itens_vendidos'] = len(df_autorizadas)
        
        pagamentos_soma = {}
        pagamentos_flat = df_autorizadas.drop_duplicates(subset=['chave_acesso'])['pagamentos'].str.split('; ').explode()
        for pag in pagamentos_flat.dropna():
            if '=' in pag:
                tipo, valor_str = pag.split('=', 1)
                try:
                    valor = float(valor_str)
                    pagamentos_soma[tipo] = pagamentos_soma.get(tipo, 0.0) + valor
                except (ValueError, TypeError):
                    continue
        self.resumos['formas_pagamento'] = pagamentos_soma

        self.resumos['top_produtos'] = df_autorizadas.groupby('item_descricao')['item_valor_total'].sum().nlargest(10).to_dict()
        self.resumos['notas_faltantes'] = self._verificar_sequencia_notas(df_autorizadas)
        
        self._gerar_analises_avancadas_pandas()
        self._calcular_apuracao_impostos_pandas()
        self._gerar_livros_fiscais_pandas()
        self._auditar_aliquotas_pandas() # <-- Nova chamada

    def _verificar_sequencia_notas(self, df: pd.DataFrame) -> Dict[str, List[int]]:
        """Verifica se há notas faltando na sequência numérica por emitente e série."""
        faltantes = {}
        df_notas_unicas = df.drop_duplicates(subset=['chave_acesso'])
        if 'numero_nf' not in df_notas_unicas.columns: return {}
        
        for (emit_cnpj, serie), grupo in df_notas_unicas.groupby(['emit_cnpj', 'serie']):
            numeros = sorted(pd.to_numeric(grupo['numero_nf'], errors='coerce').dropna().unique())
            if not numeros: continue
            
            primeiro, ultimo = int(numeros[0]), int(numeros[-1])
            sequencia_completa = set(range(primeiro, ultimo + 1))
            notas_faltantes = sorted(list(sequencia_completa - set(numeros)))
            if notas_faltantes:
                faltantes[f"Emitente {emit_cnpj} - Série {serie}"] = notas_faltantes
        return faltantes

    def _gerar_analises_avancadas_pandas(self):
        """Gera análises como sazonalidade e top CFOPs."""
        df_autorizadas = pd.DataFrame([d for d in self.dados_processados if d.get('status') == 'Autorizada'])
        if df_autorizadas.empty:
            self.resumos.update({'vendas_por_mes': {}, 'top_cfops': {}})
            return
            
        df_autorizadas['data_emissao'] = pd.to_datetime(df_autorizadas['data_emissao'], errors='coerce')
        df_autorizadas.dropna(subset=['data_emissao'], inplace=True)
        
        df_autorizadas['valor_total_nf'] = pd.to_numeric(df_autorizadas['valor_total_nf'], errors='coerce').fillna(0)

        vendas_por_mes = df_autorizadas.groupby(pd.Grouper(key='data_emissao', freq='M'))['valor_total_nf'].sum()
        self.resumos['vendas_por_mes'] = {f"{idx.year}-{idx.month:02d}": val for idx, val in vendas_por_mes.items()}
        
        if 'item_cfop' in df_autorizadas.columns:
            self.resumos['top_cfops'] = df_autorizadas['item_cfop'].value_counts().nlargest(10).to_dict()
        else:
            self.resumos['top_cfops'] = {}

    def _calcular_apuracao_impostos_pandas(self):
        """Agrupa os totais de impostos por CFOP para apuração fiscal."""
        df = pd.DataFrame(self.dados_processados)
        colunas_impostos = ['icms_vicms', 'icms_vicmsst', 'ipi_vipi', 'pis_vpis', 'cofins_vcofins']
        
        for col in colunas_impostos:
            if col not in df.columns:
                df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df[colunas_impostos] = df[colunas_impostos].fillna(0)
        
        if 'item_cfop' in df.columns:
            self.resumos['apuracao_impostos'] = df.groupby('item_cfop')[colunas_impostos].sum().to_dict('index')
        else:
            self.resumos['apuracao_impostos'] = {}

    def _gerar_livros_fiscais_pandas(self):
        """Cria resumos de Entradas e Saídas baseados nos CFOPs (Pré-Livros Fiscais)."""
        df = pd.DataFrame(self.dados_processados)
        if 'item_cfop' not in df.columns or df.empty:
            self.resumos['livro_entradas'] = {}
            self.resumos['livro_saidas'] = {}
            return

        df['item_cfop'] = df['item_cfop'].astype(str)
        
        def classificar_cfop(cfop):
            if cfop.startswith(('1', '2', '3')): return 'Entrada'
            if cfop.startswith(('5', '6', '7')): return 'Saída'
            return 'Indefinido'
            
        df['tipo_operacao'] = df['item_cfop'].apply(classificar_cfop)

        colunas_fiscais = ['item_valor_total', 'icms_vbc', 'icms_vicms', 'icms_vicmsst', 'ipi_vipi', 'pis_vpis', 'cofins_vcofins']
        for col in colunas_fiscais:
            if col not in df.columns: df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        resumo_fiscal = df.groupby(['tipo_operacao', 'item_cfop'])[colunas_fiscais].sum()
        
        if 'Entrada' in resumo_fiscal.index:
            self.resumos['livro_entradas'] = resumo_fiscal.loc['Entrada'].to_dict('index')
        else:
            self.resumos['livro_entradas'] = {}
            
        if 'Saída' in resumo_fiscal.index:
            self.resumos['livro_saidas'] = resumo_fiscal.loc['Saída'].to_dict('index')
        else:
            self.resumos['livro_saidas'] = {}

    def _auditar_aliquotas_pandas(self):
        """Compara as alíquotas de ICMS dos itens com as regras definidas."""
        if not self.regras_fiscais or 'aliquotas_icms_por_ncm' not in self.regras_fiscais:
            self.resumos['auditoria_aliquotas'] = []
            return
            
        df = pd.DataFrame([d for d in self.dados_processados if d.get('status') == 'Autorizada'])
        if df.empty or 'item_ncm' not in df.columns or 'icms_picms' not in df.columns:
            self.resumos['auditoria_aliquotas'] = []
            return
        
        regras_ncm = self.regras_fiscais['aliquotas_icms_por_ncm']
        padrao = self.regras_fiscais.get('aliquota_icms_padrao', 0.0)

        df['icms_picms'] = pd.to_numeric(df['icms_picms'], errors='coerce').fillna(0)
        df['aliquota_esperada'] = df['item_ncm'].apply(lambda ncm: regras_ncm.get(str(ncm), padrao))
        
        # Compara alíquotas, considerando uma pequena tolerância para arredondamento
        divergencias = df[abs(df['icms_picms'] - df['aliquota_esperada']) > 0.01].copy()
        
        if not divergencias.empty:
            colunas_relatorio = ['numero_nf', 'item_descricao', 'item_ncm', 'icms_picms', 'aliquota_esperada']
            self.resumos['auditoria_aliquotas'] = divergencias[colunas_relatorio].to_dict('records')
        else:
            self.resumos['auditoria_aliquotas'] = []

    def gerar_relatorios(self):
        """Chama o módulo gerador para criar todos os ficheiros de relatório."""
        from reports.generator import gerar_todos_relatorios
        gerar_todos_relatorios(self.pasta_saida, self.dados_processados, self.resumos, self.estatisticas)

