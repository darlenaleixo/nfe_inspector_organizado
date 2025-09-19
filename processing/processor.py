# processing/processor.py - VERSÃO INTEGRADA COM BI

import os
import xml.etree.ElementTree as ET
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import sqlite3
from database.models import DatabaseManager, Empresa, NotaFiscal, ItemNotaFiscal

# Importa módulos já existentes
try:
    from ia_fiscal.analisador_riscos import AnalisadorRiscos, RiscoFiscal
    from ia_fiscal.detector_fraudes import DetectorFraudes
    from ia_fiscal.sugestor_tributario import SugestorTributario, ContextoOperacao
except ImportError:
    logging.warning("Módulos de IA Fiscal não disponíveis")
    AnalisadorRiscos = None
    DetectorFraudes = None
    SugestorTributario = None

try:
    from reforma_tributaria.calculadora import CalculadoraReformaTributaria
    from reforma_tributaria.config import ConfigReformaTributaria
except ImportError:
    logging.warning("Módulos de Reforma Tributária não disponíveis")
    CalculadoraReformaTributaria = None

class NFeProcessorBI:
    """Processador NFe integrado com Business Intelligence"""
    
    def __init__(self, pasta_xml: str, pasta_saida: str, db_path: str = "nfe_data.db"):
        self.pasta_xml = pasta_xml
        self.pasta_saida = pasta_saida
        
        # Inicializa banco de dados
        self.db_manager = DatabaseManager(db_path)
        
        # Inicializa módulos de IA (se disponíveis)
        self.analisador_riscos = AnalisadorRiscos() if AnalisadorRiscos else None
        self.detector_fraudes = DetectorFraudes() if DetectorFraudes else None
        self.sugestor_tributario = SugestorTributario() if SugestorTributario else None
        
        # Inicializa Reforma Tributária (se disponível)
        if CalculadoraReformaTributaria:
            config_rt = ConfigReformaTributaria.get_config_por_ano(datetime.now().year)
            self.calculadora_rt = CalculadoraReformaTributaria(config_rt)
        else:
            self.calculadora_rt = None
        
        # Estatísticas do processamento
        self.estatisticas = {
            "arquivos_processados": 0,
            "nfes_inseridas": 0,
            "empresas_cadastradas": 0,
            "erros_processamento": 0,
            "tempo_processamento": 0,
            "analises_ia_realizadas": 0
        }
        
        logging.info("✅ NFeProcessorBI inicializado")
    
    def processar_pasta(self) -> Dict[str, Any]:
        """Processa todos os XMLs da pasta e salva no banco"""
        
        inicio = datetime.now()
        logging.info(f"🚀 Iniciando processamento da pasta: {self.pasta_xml}")
        
        if not os.path.exists(self.pasta_xml):
            raise FileNotFoundError(f"Pasta não encontrada: {self.pasta_xml}")
        
        # Lista todos os arquivos XML
        arquivos_xml = [f for f in os.listdir(self.pasta_xml) if f.endswith('.xml')]
        
        if not arquivos_xml:
            logging.warning("❌ Nenhum arquivo XML encontrado")
            return self.estatisticas
        
        logging.info(f"📄 Encontrados {len(arquivos_xml)} arquivo(s) XML")
        
        # Processa cada arquivo
        for i, arquivo in enumerate(arquivos_xml, 1):
            try:
                caminho_arquivo = os.path.join(self.pasta_xml, arquivo)
                logging.info(f"📤 Processando [{i}/{len(arquivos_xml)}]: {arquivo}")
                
                # Processa o arquivo individual
                resultado = self._processar_arquivo_xml(caminho_arquivo)
                
                if resultado:
                    self.estatisticas["arquivos_processados"] += 1
                    self.estatisticas["nfes_inseridas"] += 1
                    logging.info(f"✅ {arquivo} processado com sucesso")
                else:
                    self.estatisticas["erros_processamento"] += 1
                    logging.error(f"❌ Erro ao processar {arquivo}")
                    
            except Exception as e:
                self.estatisticas["erros_processamento"] += 1
                logging.error(f"❌ Erro crítico ao processar {arquivo}: {e}")
                continue
        
        # Finaliza processamento
        fim = datetime.now()
        self.estatisticas["tempo_processamento"] = (fim - inicio).total_seconds()
        
        logging.info(f"🎯 Processamento concluído em {self.estatisticas['tempo_processamento']:.1f}s")
        logging.info(f"📊 Estatísticas: {self.estatisticas}")
        
        return self.estatisticas
    
    def _processar_arquivo_xml(self, caminho_arquivo: str) -> bool:
        """Processa um arquivo XML individual"""
        
        try:
            # 1. Calcula hash do arquivo
            hash_arquivo = self._calcular_hash_arquivo(caminho_arquivo)
            
            # 2. Verifica se já foi processado
            if self._arquivo_ja_processado(hash_arquivo):
                logging.info(f"⏭️ Arquivo já processado: {os.path.basename(caminho_arquivo)}")
                return True
            
            # 3. Parse do XML
            dados_nfe = self._parse_xml_nfe(caminho_arquivo)
            if not dados_nfe:
                return False
            
            # 4. Cadastra/busca empresa
            empresa_id = self._processar_empresa(dados_nfe['empresa_dados'])
            if not empresa_id:
                logging.error("Erro ao processar empresa")
                return False
            
            # 5. Análise de IA Fiscal
            analise_ia = self._executar_analise_ia(dados_nfe)
            
            # 6. Cálculos da Reforma Tributária
            calculos_rt = self._executar_calculos_reforma(dados_nfe)
            
            # 7. Monta objeto NotaFiscal
            nota_fiscal = self._montar_nota_fiscal(
                dados_nfe, empresa_id, hash_arquivo, 
                caminho_arquivo, analise_ia, calculos_rt
            )
            
            # 8. Insere no banco
            nota_id = self.db_manager.inserir_nota_fiscal(nota_fiscal)
            if not nota_id:
                return False
            
            # 9. Insere itens da nota
            for item_dados in dados_nfe.get('itens', []):
                item = self._montar_item_nota(item_dados, nota_id, analise_ia)
                self.db_manager.inserir_item_nota_fiscal(item)
            
            logging.info(f"💾 NFe salva no banco: ID={nota_id}")
            return True
            
        except Exception as e:
            logging.error(f"Erro ao processar XML: {e}")
            return False
    
    def _parse_xml_nfe(self, caminho_arquivo: str) -> Optional[Dict[str, Any]]:
        """Faz parse do XML da NFe - VERSÃO CORRIGIDA"""
        
        try:
            tree = ET.parse(caminho_arquivo)
            root = tree.getroot()
            
            # Remove namespaces para facilitar navegação
            for elem in root.iter():
                if '}' in elem.tag:
                    elem.tag = elem.tag.split('}')[1]
            
            # Extrai dados principais
            inf_nfe = root.find('.//infNFe')
            if inf_nfe is None:
                logging.error("Elemento infNFe não encontrado")
                return None
            
            # Dados da NFe
            ide = inf_nfe.find('ide')
            emit = inf_nfe.find('emit')
            dest = inf_nfe.find('dest')
            total = inf_nfe.find('total')
            
            if not emit:
                logging.error("Dados do emissor não encontrados")
                return None
            
            # Extração melhorada dos dados do emissor
            cnpj_emit = emit.find('CNPJ')
            nome_emit = emit.find('xNome')
            fantasia_emit = emit.find('xFant')
            endereco_emit = emit.find('enderEmit')
            
            empresa_dados = {
                'cnpj': cnpj_emit.text.strip() if cnpj_emit is not None else '',
                'razao_social': nome_emit.text.strip() if nome_emit is not None else 'Nome não informado',
                'nome_fantasia': fantasia_emit.text.strip() if fantasia_emit is not None else '',
                'uf': endereco_emit.find('UF').text.strip() if endereco_emit and endereco_emit.find('UF') is not None else ''
            }
            
            # Dados da NFe completos
            dados = {
                'chave_acesso': inf_nfe.get('Id', '').replace('NFe', ''),
                'numero': ide.find('nNF').text if ide and ide.find('nNF') is not None else '',
                'serie': ide.find('serie').text if ide and ide.find('serie') is not None else '',
                'data_emissao': self._converter_data_nfe(ide.find('dhEmi').text if ide and ide.find('dhEmi') is not None else ''),
                
                # Emissor
                'cnpj_emissor': empresa_dados['cnpj'],
                'nome_emissor': empresa_dados['razao_social'],
                'uf_emissor': empresa_dados['uf'],
                
                # Destinatário (corrigido)
                'cnpj_destinatario': self._extrair_documento_destinatario(dest),
                'nome_destinatario': dest.find('xNome').text if dest and dest.find('xNome') is not None else '',
                'uf_destinatario': dest.find('enderDest/UF').text if dest and dest.find('enderDest/UF') is not None else '',
                
                # Valores (corrigidos)
                'valor_produtos': float(total.find('ICMSTot/vProd').text) if total and total.find('ICMSTot/vProd') is not None else 0.0,
                'valor_frete': float(total.find('ICMSTot/vFrete').text) if total and total.find('ICMSTot/vFrete') is not None else 0.0,
                'valor_seguro': float(total.find('ICMSTot/vSeg').text) if total and total.find('ICMSTot/vSeg') is not None else 0.0,
                'valor_desconto': float(total.find('ICMSTot/vDesc').text) if total and total.find('ICMSTot/vDesc') is not None else 0.0,
                'valor_total': float(total.find('ICMSTot/vNF').text) if total and total.find('ICMSTot/vNF') is not None else 0.0,
                'valor_icms': float(total.find('ICMSTot/vICMS').text) if total and total.find('ICMSTot/vICMS') is not None else 0.0,
                'valor_ipi': float(total.find('ICMSTot/vIPI').text) if total and total.find('ICMSTot/vIPI') is not None else 0.0,
                'valor_pis': float(total.find('ICMSTot/vPIS').text) if total and total.find('ICMSTot/vPIS') is not None else 0.0,
                'valor_cofins': float(total.find('ICMSTot/vCOFINS').text) if total and total.find('ICMSTot/vCOFINS') is not None else 0.0,
                
                # Status e pagamento
                'status_sefaz': 'autorizada',  # Assume autorizada se chegou até aqui
                'forma_pagamento': self._extrair_forma_pagamento(inf_nfe) or 'Não informado',
                
                # Dados da empresa para cadastro
                'empresa_dados': empresa_dados,
                
                # Itens
                'itens': self._extrair_itens(inf_nfe)
            }
            
            return dados
            
        except ET.ParseError as e:
            logging.error(f"Erro ao fazer parse do XML: {e}")
            return None
        except Exception as e:
            logging.error(f"Erro inesperado ao processar XML: {e}")
            return None

    def _extrair_documento_destinatario(self, dest) -> str:
        """Extrai documento do destinatário (CNPJ ou CPF)"""
        if not dest:
            return ''
        
        cnpj = dest.find('CNPJ')
        if cnpj is not None:
            return cnpj.text.strip()
        
        cpf = dest.find('CPF')
        if cpf is not None:
            return cpf.text.strip()
        
        return ''
    
    def _extrair_itens(self, inf_nfe) -> List[Dict[str, Any]]:
        """Extrai itens da NFe"""
        itens = []
        
        for i, det in enumerate(inf_nfe.findall('det'), 1):
            prod = det.find('prod')
            imposto = det.find('imposto')
            
            if prod is None:
                continue
            
            item = {
                'numero_item': i,
                'codigo_produto': prod.find('cProd').text if prod.find('cProd') is not None else '',
                'descricao': prod.find('xProd').text if prod.find('xProd') is not None else '',
                'ncm': prod.find('NCM').text if prod.find('NCM') is not None else '',
                'cest': prod.find('CEST').text if prod.find('CEST') is not None else '',
                'unidade': prod.find('uCom').text if prod.find('uCom') is not None else '',
                'quantidade': float(prod.find('qCom').text) if prod.find('qCom') is not None else 0.0,
                'valor_unitario': float(prod.find('vUnCom').text) if prod.find('vUnCom') is not None else 0.0,
                'valor_total': float(prod.find('vProd').text) if prod.find('vProd') is not None else 0.0,
                'cfop': prod.find('CFOP').text if prod.find('CFOP') is not None else '',
            }
            
            # Impostos (simplificado - ICMS)
            if imposto:
                icms = imposto.find('.//ICMS')
                if icms:
                    for icms_tipo in icms:
                        item.update({
                            'cst_icms': icms_tipo.find('CST').text if icms_tipo.find('CST') is not None else (icms_tipo.find('CSOSN').text if icms_tipo.find('CSOSN') is not None else ''),
                            'aliquota_icms': float(icms_tipo.find('pICMS').text) if icms_tipo.find('pICMS') is not None else 0.0,
                            'valor_icms': float(icms_tipo.find('vICMS').text) if icms_tipo.find('vICMS') is not None else 0.0,
                        })
                        break
            
            itens.append(item)
        
        return itens
    
    def _executar_analise_ia(self, dados_nfe: Dict[str, Any]) -> Dict[str, Any]:
        """Executa análise de IA Fiscal nos dados da NFe"""
        
        if not self.analisador_riscos or not self.detector_fraudes:
            return {'risco_fiscal': 0.0, 'nivel_risco': 'baixo', 'inconsistencias': 0}
        
        try:
            self.estatisticas["analises_ia_realizadas"] += 1
            
            # Análise de riscos
            risco = self.analisador_riscos.analisar_nfe(dados_nfe)
            
            # Detecção de inconsistências
            inconsistencias = self.detector_fraudes.detectar_inconsistencias(dados_nfe)
            
            return {
                'risco_fiscal': risco.score,
                'nivel_risco': risco.nivel,
                'inconsistencias': len(inconsistencias)
            }
            
        except Exception as e:
            logging.error(f"Erro na análise de IA: {e}")
            return {'risco_fiscal': 0.0, 'nivel_risco': 'baixo', 'inconsistencias': 0}
    
    def _executar_calculos_reforma(self, dados_nfe: Dict[str, Any]) -> Dict[str, Any]:
        """Executa cálculos da Reforma Tributária"""
        
        if not self.calculadora_rt:
            return {}
        
        try:
            # Cálculos básicos CBS/IBS
            valor_produtos = dados_nfe.get('valor_produtos', 0.0)
            
            cbs = self.calculadora_rt.calcular_cbs(valor_produtos, {})
            ibs = self.calculadora_rt.calcular_ibs(valor_produtos, {})
            
            return {
                'cbs_valor': cbs.get('valor', 0.0),
                'ibs_valor': ibs.get('valor', 0.0),
                'rt_aplicavel': cbs.get('valor', 0.0) > 0 or ibs.get('valor', 0.0) > 0
            }
            
        except Exception as e:
            logging.error(f"Erro nos cálculos da Reforma Tributária: {e}")
            return {}
    
    def _processar_empresa(self, empresa_dados: Dict[str, Any]) -> Optional[int]:
        """Cadastra ou busca empresa no banco, logando apenas na criação."""
        try:
            cnpj_raw = empresa_dados.get('cnpj', '').strip()
            if not cnpj_raw:
                logging.error("CNPJ da empresa não informado")
                return None

            # Limpa e formata CNPJ
            cnpj_limpo = ''.join(filter(str.isdigit, cnpj_raw))
            if len(cnpj_limpo) != 14:
                logging.warning(f"CNPJ inválido: {cnpj_raw}")
                return None

            # Formata CNPJ: XX.XXX.XXX/XXXX-XX
            cnpj_formatado = f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/" \
                            f"{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"

            # Verifica se a empresa já existe
            cursor = sqlite3.connect(self.db_manager.db_path).cursor()
            cursor.execute("SELECT id, criado_em FROM empresas WHERE cnpj = ?", (cnpj_formatado,))
            row = cursor.fetchone()

            if row:
                empresa_id, criado_em = row
                logging.debug(f"Empresa já existe (ID: {empresa_id}, Cadastrada em {criado_em[:10]})")
            else:
                # Cria nova empresa
                empresa = Empresa(
                    cnpj=cnpj_formatado,
                    razao_social=empresa_dados.get('razao_social', '').strip()[:200],
                    nome_fantasia=empresa_dados.get('nome_fantasia', '').strip()[:200],
                    uf=empresa_dados.get('uf', '').strip()[:2].upper(),
                    criado_em=datetime.now().isoformat()
                )
                # DEPOIS - conta apenas empresas REALMENTE novas
                empresa_id, eh_empresa_nova = self.db_manager.inserir_empresa_retorna_status(empresa)
                if empresa_id:
                    if eh_empresa_nova:
                        self.estatisticas["empresas_cadastradas"] += 1
                        logging.info(f"✅ Nova empresa criada: {empresa.razao_social} (ID: {empresa_id})")
                    else:
                        logging.debug(f"Empresa já existente: {empresa.razao_social} (ID: {empresa_id})")


            return empresa_id

        except Exception as e:
            logging.error(f"Erro ao processar empresa: {e}")
            return None
    
    def _montar_nota_fiscal(self, dados_nfe: Dict, empresa_id: int, hash_arquivo: str, 
        caminho_arquivo: str, analise_ia: Dict, calculos_rt: Dict) -> NotaFiscal:
        """Monta objeto NotaFiscal para inserção no banco"""
        
        return NotaFiscal(
            empresa_id=empresa_id,
            chave_acesso=dados_nfe['chave_acesso'],
            numero=dados_nfe['numero'],
            serie=dados_nfe['serie'],
            data_emissao=dados_nfe['data_emissao'],
            data_processamento=datetime.now().isoformat(),
            
            # Emissor
            cnpj_emissor=dados_nfe['cnpj_emissor'],
            nome_emissor=dados_nfe['nome_emissor'],
            uf_emissor=dados_nfe['uf_emissor'],
            
            # Destinatário
            cnpj_destinatario=dados_nfe['cnpj_destinatario'],
            nome_destinatario=dados_nfe['nome_destinatario'],
            uf_destinatario=dados_nfe['uf_destinatario'],
            
            # Valores
            valor_produtos=dados_nfe['valor_produtos'],
            valor_frete=dados_nfe['valor_frete'],
            valor_seguro=dados_nfe['valor_seguro'],
            valor_desconto=dados_nfe['valor_desconto'],
            valor_total=dados_nfe['valor_total'],
            valor_icms=dados_nfe['valor_icms'],
            valor_ipi=dados_nfe['valor_ipi'],
            valor_pis=dados_nfe['valor_pis'],
            valor_cofins=dados_nfe['valor_cofins'],
            
            # Status
            status_sefaz=dados_nfe['status_sefaz'],
            
            # Pagamento
            forma_pagamento=dados_nfe.get('forma_pagamento', 'Não informado'),
            condicao_pagamento=dados_nfe.get('condicao_pagamento', ''),
            
            # IA
            risco_fiscal=analise_ia['risco_fiscal'],
            nivel_risco=analise_ia['nivel_risco'],
            inconsistencias=analise_ia['inconsistencias'],
            
            # Metadados
            arquivo_origem=os.path.basename(caminho_arquivo),
            hash_arquivo=hash_arquivo
        )
    
    def _montar_item_nota(self, item_dados: Dict, nota_fiscal_id: int, analise_ia: Dict) -> ItemNotaFiscal:
        """Monta objeto ItemNotaFiscal"""
        
        # Sugestões da IA (se disponível)
        sugestoes = {}
        if self.sugestor_tributario:
            try:
                contexto = ContextoOperacao()  # Contexto básico
                ncm_sugestoes = self.sugestor_tributario.sugerir_ncm(item_dados.get('descricao', ''), contexto)
                if ncm_sugestoes:
                    sugestoes = {
                        'ncm_sugerido': ncm_sugestoes[0].codigo,
                        'confianca_ia': ncm_sugestoes[0].confianca
                    }
            except:
                pass
        
        return ItemNotaFiscal(
            nota_fiscal_id=nota_fiscal_id,
            numero_item=item_dados['numero_item'],
            
            # Produto
            codigo_produto=item_dados['codigo_produto'],
            descricao=item_dados['descricao'],
            ncm=item_dados['ncm'],
            cest=item_dados['cest'],
            unidade=item_dados['unidade'],
            quantidade=item_dados['quantidade'],
            valor_unitario=item_dados['valor_unitario'],
            valor_total=item_dados['valor_total'],
            
            # Impostos
            cfop=item_dados['cfop'],
            cst_icms=item_dados.get('cst_icms', ''),
            aliquota_icms=item_dados.get('aliquota_icms', 0.0),
            valor_icms=item_dados.get('valor_icms', 0.0),
            
            # Sugestões IA
            ncm_sugerido=sugestoes.get('ncm_sugerido', ''),
            confianca_ia=sugestoes.get('confianca_ia', 0.0)
        )
    
    # === MÉTODOS AUXILIARES ===
    
    def _calcular_hash_arquivo(self, caminho_arquivo: str) -> str:
        """Calcula hash MD5 do arquivo"""
        hash_md5 = hashlib.md5()
        with open(caminho_arquivo, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _arquivo_ja_processado(self, hash_arquivo: str) -> bool:
        """Verifica se arquivo já foi processado"""
        # Consulta simples no banco para verificar se hash existe
        try:
            with self.db_manager.db_manager.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM notas_fiscais WHERE hash_arquivo = ?", (hash_arquivo,))
                return cursor.fetchone() is not None
        except:
            return False
    
    def _converter_data_nfe(self, data_str: str) -> str:
        """Converte data da NFe para formato padrão"""
        try:
            # Remove timezone se existir
            if 'T' in data_str:
                data_str = data_str.split('T')[0]
            elif ' ' in data_str:
                data_str = data_str.split(' ')[0]
            
            # Já está no formato YYYY-MM-DD
            return data_str
        except:
            return datetime.now().strftime('%Y-%m-%d')
    
    def _extrair_forma_pagamento(self, inf_nfe) -> str:
        """Extrai forma de pagamento, cobrindo <pag> e <pgtos>."""
        try:
            # Tenta tag singular
            pag = inf_nfe.find('.//pag')
            if pag is None:
                # Tenta tag plural (alguns layouts usam pgtos/pagto)
                pag = inf_nfe.find('.//pgtos')
            if pag is None:
                return 'Não informado'
            
            # Dentro de <pgtos> ou <pag> pode ter múltiplos <pagto> ou <detPag>
            # Procuramos primeiro tPag em todos os descendentes
            tPag_elem = pag.find('.//tPag') or pag.find('.//detPag/tPag')
            if tPag_elem is None or not tPag_elem.text:
                return 'Não informado'
            
            codigo = tPag_elem.text.strip()
            tipos = {
                '01': 'Dinheiro',
                '02': 'Cheque',
                '03': 'Cartão de Crédito',
                '04': 'Cartão de Débito',
                '05': 'Crédito Loja',
                '10': 'Vale Alimentação',
                '11': 'Vale Refeição',
                '12': 'Vale Presente',
                '13': 'Vale Combustível',
                '15': 'Boleto Bancário',
                '17': 'PIX',
                '18': 'Transferência',
                '90': 'Sem Pagamento',
                '99': 'Outros'
            }
            return tipos.get(codigo, f'Código {codigo}')
        except Exception:
            return 'Não informado'

    
    def obter_dashboard_manager(self) -> DatabaseManager:
        """Retorna DatabaseManager para uso no Dashboard"""
        return self.db_manager
    
    def obter_estatisticas(self) -> Dict[str, Any]:
        """Retorna estatísticas do processamento"""
        return self.estatisticas.copy()
    
      # === MÉTODOS DE COMPATIBILIDADE COM GUI ANTIGA ===
    
    def calcular_resumos(self):
        """Método de compatibilidade - resumos já calculados no processar_pasta()"""
        logging.info("Resumos já calculados durante o processamento")
        return True
    
    def gerar_relatorios(self):
        """Método de compatibilidade - gera relatórios básicos"""
        try:
            if not hasattr(self, 'estatisticas') or not self.estatisticas:
                logging.warning("Nenhuma estatística disponível para relatório")
                return False
            
            # Cria relatório texto simples
            relatorio_path = os.path.join(self.pasta_saida, "relatorio_processamento.txt")
            
            os.makedirs(self.pasta_saida, exist_ok=True)
            
            with open(relatorio_path, 'w', encoding='utf-8') as f:
                f.write("=== RELATÓRIO DE PROCESSAMENTO NFe ===\n\n")
                f.write(f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                f.write(f"Pasta processada: {self.pasta_xml}\n\n")
                
                f.write("ESTATÍSTICAS:\n")
                for chave, valor in self.estatisticas.items():
                    f.write(f"• {chave.replace('_', ' ').title()}: {valor}\n")
                
                if hasattr(self, 'db_manager'):
                    f.write("\nDADOS NO BANCO:\n")
                    stats_db = self.db_manager.obter_estatisticas()
                    f.write(f"• Total NFe no banco: {stats_db.get('total_notas', 0)}\n")
                    f.write(f"• Valor total: R$ {stats_db.get('valor_total', 0):,.2f}\n")
                    f.write(f"• Risco médio: {stats_db.get('risco_medio', 0):.1%}\n")
            
            logging.info(f"✅ Relatório salvo: {relatorio_path}")
            return True
            
        except Exception as e:
            logging.error(f"Erro ao gerar relatório: {e}")
            return False
    
    # Método alternativo para GUI
    def processar_pasta_gui(self):
        """Método específico para GUI - processa e armazena estatísticas"""
        self.estatisticas = self.processar_pasta()
        return self.estatisticas
