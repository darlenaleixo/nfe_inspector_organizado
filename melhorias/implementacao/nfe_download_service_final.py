# -*- coding: utf-8 -*-
"""
Serviço de Download atualizado com implementação real dos webservices
"""

import os
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from sefaz_client_completo import SefazWebserviceClient
from sefaz.auth import CertificateManager
from core.config import ConfigManager
from core.utils import error_handler


@dataclass
class Cliente:
    """Representa um cliente com seus dados de acesso"""
    id: str
    cnpj: str
    razao_social: str
    certificado_path: str
    certificado_senha: str
    uf: str
    ambiente: int  # 1=Produção, 2=Homologação
    ativo: bool = True
    ultimo_download: Optional[str] = None
    observacoes: str = ""


@dataclass
class DownloadJob:
    """Representa um job de download de notas"""
    cliente_id: str
    tipo_nota: str  # 'nfe' ou 'nfse'
    data_inicio: str
    data_fim: str
    status: str = "pendente"  # pendente, executando, concluido, erro
    total_notas: int = 0
    notas_baixadas: int = 0
    notas_com_erro: int = 0
    erro_msg: str = ""
    criado_em: str = None
    finalizado_em: str = None
    detalhes: Dict[str, Any] = None


class ClienteManager:
    """Gerencia os dados dos clientes no banco SQLite"""
    
    def __init__(self, db_path: str = "clientes.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Inicializa o banco de dados SQLite"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id TEXT PRIMARY KEY,
                    cnpj TEXT UNIQUE NOT NULL,
                    razao_social TEXT NOT NULL,
                    certificado_path TEXT NOT NULL,
                    certificado_senha TEXT NOT NULL,
                    uf TEXT NOT NULL,
                    ambiente INTEGER NOT NULL,
                    ativo BOOLEAN DEFAULT TRUE,
                    ultimo_download TEXT,
                    observacoes TEXT DEFAULT '',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    atualizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS download_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id TEXT NOT NULL,
                    tipo_nota TEXT NOT NULL,
                    data_inicio TEXT NOT NULL,
                    data_fim TEXT NOT NULL,
                    status TEXT DEFAULT 'pendente',
                    total_notas INTEGER DEFAULT 0,
                    notas_baixadas INTEGER DEFAULT 0,
                    notas_com_erro INTEGER DEFAULT 0,
                    erro_msg TEXT DEFAULT '',
                    detalhes TEXT DEFAULT '{}',
                    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    finalizado_em TIMESTAMP,
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notas_baixadas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id TEXT NOT NULL,
                    chave_acesso TEXT NOT NULL,
                    tipo_nota TEXT NOT NULL,
                    numero_nota TEXT,
                    data_emissao TEXT,
                    valor_total REAL,
                    cnpj_emitente TEXT,
                    nome_emitente TEXT,
                    situacao TEXT,
                    xml_path TEXT,
                    manifestada BOOLEAN DEFAULT FALSE,
                    baixado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chave_acesso),
                    FOREIGN KEY (cliente_id) REFERENCES clientes (id)
                )
            """)
            
            # Índices para performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_notas_cliente ON notas_baixadas (cliente_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_notas_chave ON notas_baixadas (chave_acesso)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_cliente ON download_jobs (cliente_id)")
    
    def adicionar_cliente(self, cliente: Cliente) -> bool:
        """Adiciona um novo cliente"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO clientes 
                    (id, cnpj, razao_social, certificado_path, certificado_senha, 
                     uf, ambiente, ativo, ultimo_download, observacoes, atualizado_em)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    cliente.id, cliente.cnpj, cliente.razao_social,
                    cliente.certificado_path, cliente.certificado_senha,
                    cliente.uf, cliente.ambiente, cliente.ativo,
                    cliente.ultimo_download, cliente.observacoes
                ))
            return True
        except Exception as e:
            logging.error(f"Erro ao adicionar cliente {cliente.id}: {e}")
            return False
    
    def listar_clientes(self, apenas_ativos: bool = True) -> List[Cliente]:
        """Lista todos os clientes"""
        query = "SELECT * FROM clientes"
        if apenas_ativos:
            query += " WHERE ativo = TRUE"
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            return [Cliente(**dict(row)) for row in cursor.fetchall()]
    
    def obter_cliente(self, cliente_id: str) -> Optional[Cliente]:
        """Obtém um cliente específico"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
            row = cursor.fetchone()
            return Cliente(**dict(row)) if row else None
    
    def salvar_job(self, job: DownloadJob) -> int:
        """Salva um job de download no banco"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO download_jobs 
                (cliente_id, tipo_nota, data_inicio, data_fim, status, 
                 total_notas, notas_baixadas, notas_com_erro, erro_msg, detalhes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.cliente_id, job.tipo_nota, job.data_inicio, job.data_fim,
                job.status, job.total_notas, job.notas_baixadas, job.notas_com_erro,
                job.erro_msg, json.dumps(job.detalhes or {})
            ))
            return cursor.lastrowid


class NFeDownloadService:
    """Serviço principal para download de NFe/NFSe"""
    
    def __init__(self, pasta_saida: str = "downloads"):
        self.pasta_saida = pasta_saida
        self.cliente_manager = ClienteManager()
        self.config = ConfigManager()
        self.logger = logging.getLogger(__name__)
        
        # Criar pasta de saída se não existir
        os.makedirs(pasta_saida, exist_ok=True)
        
        # Configurações de timeout e retry
        self.timeout_requests = 60
        self.max_tentativas = 3
        self.intervalo_requests = 1  # segundos entre requests
    
    @error_handler
    def download_notas_cliente(self, cliente_id: str, data_inicio: str, 
                              data_fim: str, tipo_nota: str = "nfe",
                              manifestar_automatico: bool = False) -> DownloadJob:
        """
        Faz download das notas de um cliente específico
        
        Args:
            cliente_id: ID do cliente
            data_inicio: Data início no formato YYYY-MM-DD
            data_fim: Data fim no formato YYYY-MM-DD
            tipo_nota: Tipo da nota ('nfe' ou 'nfse')
            manifestar_automatico: Se deve manifestar ciência automaticamente
        """
        job = DownloadJob(
            cliente_id=cliente_id,
            tipo_nota=tipo_nota,
            data_inicio=data_inicio,
            data_fim=data_fim,
            criado_em=datetime.now().isoformat(),
            detalhes={}
        )
        
        try:
            # Buscar dados do cliente
            cliente = self.cliente_manager.obter_cliente(cliente_id)
            if not cliente:
                raise Exception(f"Cliente {cliente_id} não encontrado")
            
            if not cliente.ativo:
                raise Exception(f"Cliente {cliente_id} está inativo")
            
            job.status = "executando"
            self.logger.info(f"🔄 Iniciando download para {cliente.razao_social}")
            
            # Validar certificado
            cert_manager = CertificateManager(cliente.certificado_path, cliente.certificado_senha)
            
            # Criar pasta do cliente
            pasta_cliente = os.path.join(self.pasta_saida, cliente_id)
            os.makedirs(pasta_cliente, exist_ok=True)
            
            if tipo_nota.lower() == "nfe":
                job = self._download_nfe_completo(cliente, job, pasta_cliente, 
                                                cert_manager, manifestar_automatico)
            elif tipo_nota.lower() == "nfse":
                job = self._download_nfse(cliente, job, pasta_cliente)
            else:
                raise Exception(f"Tipo de nota não suportado: {tipo_nota}")
            
            job.status = "concluido"
            job.finalizado_em = datetime.now().isoformat()
            
            # Atualizar último download do cliente
            cliente.ultimo_download = job.finalizado_em
            self.cliente_manager.adicionar_cliente(cliente)
            
            # Salvar job no banco
            self.cliente_manager.salvar_job(job)
            
            self.logger.info(f"✅ Download concluído: {job.notas_baixadas}/{job.total_notas} notas")
            
        except Exception as e:
            job.status = "erro"
            job.erro_msg = str(e)
            job.finalizado_em = datetime.now().isoformat()
            self.logger.error(f"❌ Erro no download do cliente {cliente_id}: {e}")
            
            # Salvar job com erro
            self.cliente_manager.salvar_job(job)
        
        return job
    
    def _download_nfe_completo(self, cliente: Cliente, job: DownloadJob, 
                             pasta_cliente: str, cert_manager: CertificateManager,
                             manifestar_automatico: bool = False) -> DownloadJob:
        """Download completo de NFe com todas as etapas"""
        try:
            # Criar cliente webservice
            sefaz_client = SefazWebserviceClient(
                uf=cliente.uf,
                ambiente=cliente.ambiente,
                cert_manager=cert_manager,
                verificar_ssl=self.config.get_boolean('SEFAZ', 'verificar_ssl', True)
            )
            
            # Testar conectividade
            if not sefaz_client.testar_conectividade():
                raise Exception("Falha na conectividade com SEFAZ")
            
            self.logger.info("✅ Conectividade SEFAZ OK")
            
            # 1. Consultar manifestações
            self.logger.info("🔍 Consultando manifestações...")
            manifestacoes = sefaz_client.consultar_manifestacao_destinatario(
                cnpj=cliente.cnpj,
                data_inicio=job.data_inicio,
                data_fim=job.data_fim
            )
            
            job.total_notas = len(manifestacoes)
            job.detalhes['manifestacoes_encontradas'] = job.total_notas
            
            if job.total_notas == 0:
                self.logger.info("ℹ️ Nenhuma manifestação encontrada no período")
                return job
            
            # 2. Baixar XMLs das notas
            pasta_xml = os.path.join(pasta_cliente, "nfe")
            os.makedirs(pasta_xml, exist_ok=True)
            
            self.logger.info(f"📥 Baixando {job.total_notas} notas...")
            
            notas_baixadas = []
            notas_com_erro = []
            
            for i, manifestacao in enumerate(manifestacoes, 1):
                chave_acesso = manifestacao['chave_acesso']
                
                try:
                    self.logger.info(f"📄 [{i}/{job.total_notas}] {chave_acesso}")
                    
                    # Baixar XML
                    xml_content = sefaz_client.baixar_xml_nfe(
                        chave_acesso=chave_acesso,
                        cnpj_destinatario=cliente.cnpj
                    )
                    
                    if xml_content:
                        # Salvar arquivo XML
                        xml_filename = f"{chave_acesso}.xml"
                        xml_path = os.path.join(pasta_xml, xml_filename)
                        
                        with open(xml_path, 'w', encoding='utf-8') as f:
                            f.write(xml_content)
                        
                        # Registrar nota baixada
                        self._registrar_nota_baixada(
                            cliente_id=cliente.id,
                            chave_acesso=chave_acesso,
                            xml_path=xml_path,
                            manifestacao=manifestacao
                        )
                        
                        notas_baixadas.append(chave_acesso)
                        job.notas_baixadas += 1
                        
                        # Manifestar ciência se solicitado
                        if manifestar_automatico and not manifestacao.get('manifestada', False):
                            try:
                                sefaz_client.manifestar_ciencia(
                                    chave_acesso=chave_acesso,
                                    cnpj_destinatario=cliente.cnpj,
                                    tipo_manifestacao="210210"  # Ciência da Operação
                                )
                                self.logger.info(f"✓ Ciência manifestada: {chave_acesso}")
                            except Exception as e:
                                self.logger.warning(f"⚠️ Erro ao manifestar ciência: {e}")
                    else:
                        notas_com_erro.append(chave_acesso)
                        job.notas_com_erro += 1
                        self.logger.warning(f"⚠️ Não foi possível baixar: {chave_acesso}")
                
                except Exception as e:
                    notas_com_erro.append(chave_acesso)
                    job.notas_com_erro += 1
                    self.logger.error(f"❌ Erro ao baixar {chave_acesso}: {e}")
                
                # Intervalo entre requests
                if i < job.total_notas:
                    time.sleep(self.intervalo_requests)
            
            # Atualizar detalhes do job
            job.detalhes.update({
                'notas_baixadas_lista': notas_baixadas,
                'notas_com_erro_lista': notas_com_erro,
                'pasta_xml': pasta_xml
            })
            
        except Exception as e:
            raise Exception(f"Erro no download de NFe: {e}")
        
        return job
    
    def _download_nfse(self, cliente: Cliente, job: DownloadJob, pasta_cliente: str) -> DownloadJob:
        """Download específico de NFSe (implementação futura)"""
        job.erro_msg = "Download de NFSe ainda não implementado"
        raise Exception("Download de NFSe ainda não implementado")
    
    def _registrar_nota_baixada(self, cliente_id: str, chave_acesso: str, 
                               xml_path: str, manifestacao: Dict):
        """Registra uma nota baixada no banco com dados da manifestação"""
        try:
            with sqlite3.connect(self.cliente_manager.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO notas_baixadas 
                    (cliente_id, chave_acesso, tipo_nota, xml_path,
                     cnpj_emitente, nome_emitente, valor_total, data_emissao,
                     situacao, manifestada)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cliente_id, chave_acesso, 'nfe', xml_path,
                    manifestacao.get('cnpj_emitente', ''),
                    manifestacao.get('nome_emitente', ''),
                    manifestacao.get('valor_nf', 0.0),
                    manifestacao.get('data_recebimento', ''),
                    manifestacao.get('situacao_manifestacao', ''),
                    manifestacao.get('manifestada', False)
                ))
        except Exception as e:
            self.logger.error(f"Erro ao registrar nota baixada: {e}")
    
    def download_lote_clientes(self, clientes_ids: List[str], data_inicio: str, 
                              data_fim: str, max_workers: int = 3,
                              manifestar_automatico: bool = False) -> List[DownloadJob]:
        """
        Faz download em lote para múltiplos clientes (paralelo)
        """
        jobs = []
        
        self.logger.info(f"🚀 Iniciando download em lote: {len(clientes_ids)} clientes")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submeter jobs
            futures = {
                executor.submit(
                    self.download_notas_cliente, 
                    cliente_id, data_inicio, data_fim, "nfe", manifestar_automatico
                ): cliente_id 
                for cliente_id in clientes_ids
            }
            
            # Coletar resultados
            for future in as_completed(futures):
                cliente_id = futures[future]
                try:
                    job = future.result()
                    jobs.append(job)
                    
                    if job.status == "concluido":
                        self.logger.info(f"✅ {cliente_id}: {job.notas_baixadas} notas baixadas")
                    else:
                        self.logger.error(f"❌ {cliente_id}: {job.erro_msg}")
                        
                except Exception as e:
                    self.logger.error(f"❌ Erro no download do cliente {cliente_id}: {e}")
                    # Criar job de erro
                    error_job = DownloadJob(
                        cliente_id=cliente_id,
                        tipo_nota="nfe",
                        data_inicio=data_inicio,
                        data_fim=data_fim,
                        status="erro",
                        erro_msg=str(e),
                        finalizado_em=datetime.now().isoformat()
                    )
                    jobs.append(error_job)
        
        return jobs
    
    def obter_estatisticas_downloads(self) -> Dict[str, Any]:
        """Obtém estatísticas detalhadas dos downloads realizados"""
        with sqlite3.connect(self.cliente_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Estatísticas gerais
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_notas,
                    COUNT(DISTINCT cliente_id) as total_clientes,
                    SUM(valor_total) as valor_total_geral,
                    COUNT(CASE WHEN manifestada = 1 THEN 1 END) as notas_manifestadas
                FROM notas_baixadas
            """)
            stats_gerais = dict(cursor.fetchone())
            
            # Por tipo de nota
            cursor = conn.execute("""
                SELECT tipo_nota, COUNT(*) as quantidade
                FROM notas_baixadas
                GROUP BY tipo_nota
            """)
            por_tipo = {row['tipo_nota']: row['quantidade'] for row in cursor.fetchall()}
            
            # Por cliente
            cursor = conn.execute("""
                SELECT 
                    nb.cliente_id,
                    c.razao_social,
                    COUNT(*) as total_notas,
                    SUM(nb.valor_total) as valor_total,
                    MAX(nb.baixado_em) as ultimo_download
                FROM notas_baixadas nb
                LEFT JOIN clientes c ON nb.cliente_id = c.id
                GROUP BY nb.cliente_id
                ORDER BY total_notas DESC
            """)
            por_cliente = [dict(row) for row in cursor.fetchall()]
            
            # Jobs recentes
            cursor = conn.execute("""
                SELECT 
                    cliente_id, status, total_notas, notas_baixadas,
                    data_inicio, data_fim, criado_em
                FROM download_jobs
                ORDER BY criado_em DESC
                LIMIT 10
            """)
            jobs_recentes = [dict(row) for row in cursor.fetchall()]
            
            return {
                'geral': stats_gerais,
                'por_tipo': por_tipo,
                'por_cliente': por_cliente,
                'jobs_recentes': jobs_recentes
            }
    
    def limpar_dados_antigos(self, dias: int = 90):
        """Remove dados antigos do banco e arquivos"""
        data_limite = datetime.now() - timedelta(days=dias)
        data_limite_str = data_limite.isoformat()
        
        with sqlite3.connect(self.cliente_manager.db_path) as conn:
            # Remover notas antigas
            cursor = conn.execute("""
                DELETE FROM notas_baixadas 
                WHERE baixado_em < ?
            """, (data_limite_str,))
            
            notas_removidas = cursor.rowcount
            
            # Remover jobs antigos
            cursor = conn.execute("""
                DELETE FROM download_jobs 
                WHERE criado_em < ?
            """, (data_limite_str,))
            
            jobs_removidos = cursor.rowcount
            
        self.logger.info(f"🧹 Limpeza concluída: {notas_removidas} notas, {jobs_removidos} jobs removidos")