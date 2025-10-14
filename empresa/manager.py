# empresa/manager.py

import sqlite3
import logging
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from database.models import DatabaseManager, Empresa

@dataclass
class EmpresaCompleta:
    """Empresa com dados completos e metadados"""
    id: Optional[int] = None
    cnpj: str = ""
    razao_social: str = ""
    nome_fantasia: str = ""
    uf: str = ""
    cidade: str = ""
    endereco: str = ""
    cep: str = ""
    telefone: str = ""
    email: str = ""
    inscricao_estadual: str = ""
    regime_tributario: str = ""
    atividade_principal: str = ""
    situacao_cadastral: str = "ATIVA"
    
    # Metadados
    criado_em: str = ""
    atualizado_em: str = ""
    criado_por: str = "Sistema"
    total_nfes: int = 0
    valor_total_movimentado: float = 0.0
    ultimo_processamento: str = ""
    
    # Configurações
    ativa: bool = True
    monitoramento: bool = True
    alertas: bool = True

class GerenciadorEmpresas:
    """Gerenciador completo de empresas com CRUD e funcionalidades avançadas"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.init_extended_tables()
    
    def init_extended_tables(self):
        """Cria tabelas estendidas para empresas"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela empresas estendida
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresas_detalhadas (
                    id INTEGER PRIMARY KEY,
                    empresa_id INTEGER UNIQUE,
                    cidade TEXT,
                    endereco TEXT,
                    cep TEXT,
                    telefone TEXT,
                    email TEXT,
                    inscricao_estadual TEXT,
                    regime_tributario TEXT,
                    atividade_principal TEXT,
                    situacao_cadastral TEXT DEFAULT 'ATIVA',
                    atualizado_em TEXT,
                    criado_por TEXT DEFAULT 'Sistema',
                    ativa BOOLEAN DEFAULT 1,
                    monitoramento BOOLEAN DEFAULT 1,
                    alertas BOOLEAN DEFAULT 1,
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                )
                """)
                
                # Tabela de histórico de alterações
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresas_historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    empresa_id INTEGER,
                    campo_alterado TEXT,
                    valor_anterior TEXT,
                    valor_novo TEXT,
                    alterado_por TEXT,
                    alterado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                )
                """)
                
                # Tabela de configurações por empresa
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS empresas_config (
                    id INTEGER PRIMARY KEY,
                    empresa_id INTEGER UNIQUE,
                    auto_processar BOOLEAN DEFAULT 1,
                    nivel_alerta TEXT DEFAULT 'MEDIO',
                    email_notificacao TEXT,
                    dias_backup INTEGER DEFAULT 30,
                    config_json TEXT,
                    FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                )
                """)
                
                conn.commit()
                logging.info("✅ Tabelas estendidas de empresas criadas")
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao criar tabelas estendidas: {e}")
    
    def criar_empresa(self, dados: Dict[str, Any], criado_por: str = "Manual") -> Optional[int]:
        """Cria nova empresa com validações completas"""
        try:
            # Validar CNPJ
            cnpj_limpo = self._limpar_cnpj(dados.get('cnpj', ''))
            if not self._validar_cnpj(cnpj_limpo):
                raise ValueError(f"CNPJ inválido: {dados.get('cnpj')}")
            
            # Verificar se já existe
            if self._empresa_existe(cnpj_limpo):
                raise ValueError("Empresa já cadastrada")
            
            # Consultar dados da Receita Federal (opcional)
            dados_rf = self._consultar_receita_federal(cnpj_limpo)
            if dados_rf:
                dados.update(dados_rf)
            
            # Criar empresa base
            empresa_base = Empresa(
                cnpj=self._formatar_cnpj(cnpj_limpo),
                razao_social=dados.get('razao_social', '').strip()[:200],
                nome_fantasia=dados.get('nome_fantasia', '').strip()[:200],
                uf=dados.get('uf', '').strip()[:2].upper()
            )
            
            empresa_id = self.db_manager.inserir_empresa(empresa_base)
            if not empresa_id:
                raise Exception("Falha ao criar empresa base")
            
            # Criar registro detalhado
            self._criar_detalhes_empresa(empresa_id, dados, criado_por)
            
            # Criar configurações padrão
            self._criar_config_padrao(empresa_id)
            
            logging.info(f"✅ Empresa criada: {dados.get('razao_social')} (ID: {empresa_id})")
            return empresa_id
            
        except Exception as e:
            logging.error(f"❌ Erro ao criar empresa: {e}")
            raise
    
    def atualizar_empresa(self, empresa_id: int, dados: Dict[str, Any], 
                         alterado_por: str = "Manual") -> bool:
        """Atualiza empresa com histórico de alterações"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                cursor = conn.cursor()
                
                # Busca dados atuais para histórico
                empresa_atual = self.obter_empresa_completa(empresa_id)
                if not empresa_atual:
                    raise ValueError("Empresa não encontrada")
                
                # Atualiza empresa base se necessário
                if any(k in dados for k in ['razao_social', 'nome_fantasia', 'uf']):
                    update_base = []
                    params_base = []
                    
                    if 'razao_social' in dados:
                        update_base.append("razao_social = ?")
                        params_base.append(dados['razao_social'][:200])
                        self._registrar_alteracao(empresa_id, 'razao_social',
                                                empresa_atual.razao_social,
                                                dados['razao_social'], alterado_por)
                    
                    if 'nome_fantasia' in dados:
                        update_base.append("nome_fantasia = ?")
                        params_base.append(dados['nome_fantasia'][:200])
                        self._registrar_alteracao(empresa_id, 'nome_fantasia',
                                                empresa_atual.nome_fantasia,
                                                dados['nome_fantasia'], alterado_por)
                    
                    if 'uf' in dados:
                        update_base.append("uf = ?")
                        params_base.append(dados['uf'][:2].upper())
                        self._registrar_alteracao(empresa_id, 'uf',
                                                empresa_atual.uf,
                                                dados['uf'], alterado_por)
                    
                    if update_base:
                        params_base.append(empresa_id)
                        cursor.execute(f"""
                        UPDATE empresas 
                        SET {', '.join(update_base)}
                        WHERE id = ?
                        """, params_base)
                
                # Atualiza detalhes
                self._atualizar_detalhes_empresa(empresa_id, dados, alterado_por, cursor)
                
                conn.commit()
                logging.info(f"✅ Empresa {empresa_id} atualizada por {alterado_por}")
                return True
                
        except Exception as e:
            logging.error(f"❌ Erro ao atualizar empresa {empresa_id}: {e}")
            return False
    
    def excluir_empresa(self, empresa_id: int, excluido_por: str = "Manual") -> bool:
        """Marca empresa como excluída, mantendo dados e notas fiscais vinculadas"""
        try:
            # Usar timeout para evitar lock
            with sqlite3.connect(self.db_manager.db_path, timeout=30.0) as conn:
                conn.execute("PRAGMA journal_mode=WAL")  # Permite leituras concorrentes
                conn.execute("BEGIN IMMEDIATE")  # Lock exclusivo imediato
                
                cursor = conn.cursor()
                
                # Verificar se empresa existe
                cursor.execute("SELECT id, razao_social FROM empresas WHERE id = ?", (empresa_id,))
                empresa = cursor.fetchone()
                if not empresa:
                    conn.rollback()
                    raise ValueError("Empresa não encontrada")
                
                logging.info(f"Iniciando exclusão da empresa {empresa_id}: {empresa[1]}")
                
                # Verificar se tabela empresas tem campo ativa
                cursor.execute("PRAGMA table_info(empresas)")
                colunas_empresas = [col[1] for col in cursor.fetchall()]
                
                if 'ativa' in colunas_empresas:
                    cursor.execute("UPDATE empresas SET ativa = 0 WHERE id = ?", (empresa_id,))
                    logging.debug(f"Campo 'ativa' atualizado para empresa {empresa_id}")
                
                # Verificar se registro existe na tabela detalhada
                cursor.execute("SELECT empresa_id FROM empresas_detalhadas WHERE empresa_id = ?", (empresa_id,))
                detalhes_existe = cursor.fetchone()
                
                if detalhes_existe:
                    # Atualizar registro existente
                    cursor.execute("""
                    UPDATE empresas_detalhadas 
                    SET situacao_cadastral = 'EXCLUIDA',
                        ativa = 0,
                        atualizado_em = ?
                    WHERE empresa_id = ?
                    """, (datetime.now().isoformat(), empresa_id))
                    logging.debug(f"Registro detalhado atualizado para empresa {empresa_id}")
                else:
                    # Criar registro se não existir
                    cursor.execute("""
                    INSERT INTO empresas_detalhadas 
                    (empresa_id, situacao_cadastral, ativa, atualizado_em, criado_por)
                    VALUES (?, 'EXCLUIDA', 0, ?, ?)
                    """, (empresa_id, datetime.now().isoformat(), excluido_por))
                    logging.debug(f"Registro detalhado criado para empresa {empresa_id}")
                
                # Registrar no histórico
                cursor.execute("""
                INSERT INTO empresas_historico 
                (empresa_id, campo_alterado, valor_anterior, valor_novo, alterado_por, alterado_em)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (empresa_id, 'situacao_cadastral', 'ATIVA', 'EXCLUIDA', 
                    excluido_por, datetime.now().isoformat()))
                
                # Commit explícito
                conn.commit()
                
                logging.info(f"✅ Empresa {empresa_id} ({empresa[1]}) marcada como excluída por {excluido_por}")
                return True
                
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                logging.error(f"❌ Banco de dados travado ao excluir empresa {empresa_id}. Tentando novamente...")
                # Tentar novamente após pequena pausa
                import time
                time.sleep(0.5)
                return self._excluir_empresa_retry(empresa_id, excluido_por)
            else:
                logging.error(f"❌ Erro SQLite ao excluir empresa {empresa_id}: {e}")
                raise
                
        except Exception as e:
            logging.error(f"❌ Erro geral ao excluir empresa {empresa_id}: {e}")
            raise

    def _excluir_empresa_retry(self, empresa_id: int, excluido_por: str, tentativas: int = 3) -> bool:
        """Retry da exclusão em caso de database lock"""
        import time
        
        for tentativa in range(tentativas):
            try:
                logging.info(f"Tentativa {tentativa + 1} de exclusão da empresa {empresa_id}")
                
                # Forçar fechamento de conexões ociosas
                import gc
                gc.collect()
                
                with sqlite3.connect(self.db_manager.db_path, timeout=60.0) as conn:
                    conn.execute("PRAGMA busy_timeout = 60000")  # 60 segundos de timeout
                    conn.execute("PRAGMA journal_mode=WAL")
                    
                    cursor = conn.cursor()
                    
                    # Verificar se empresa existe
                    cursor.execute("SELECT id, razao_social FROM empresas WHERE id = ?", (empresa_id,))
                    empresa = cursor.fetchone()
                    if not empresa:
                        raise ValueError("Empresa não encontrada")
                    
                    # Marcar como excluída na tabela detalhada
                    cursor.execute("""
                    INSERT OR REPLACE INTO empresas_detalhadas 
                    (empresa_id, situacao_cadastral, ativa, atualizado_em, criado_por)
                    VALUES (?, 'EXCLUIDA', 0, ?, ?)
                    """, (empresa_id, datetime.now().isoformat(), excluido_por))
                    
                    # Registrar no histórico
                    cursor.execute("""
                    INSERT INTO empresas_historico 
                    (empresa_id, campo_alterado, valor_anterior, valor_novo, alterado_por)
                    VALUES (?, ?, ?, ?, ?)
                    """, (empresa_id, 'situacao_cadastral', 'ATIVA', 'EXCLUIDA', excluido_por))
                    
                    conn.commit()
                    
                    logging.info(f"✅ Empresa {empresa_id} excluída com sucesso (tentativa {tentativa + 1})")
                    return True
                    
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and tentativa < tentativas - 1:
                    wait_time = (tentativa + 1) * 0.5  # Espera progressiva
                    logging.warning(f"Database ainda travado. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logging.error(f"❌ Falha final na exclusão após {tentativa + 1} tentativas: {e}")
                    raise
                    
            except Exception as e:
                logging.error(f"❌ Erro na tentativa {tentativa + 1}: {e}")
                if tentativa == tentativas - 1:
                    raise
                time.sleep(0.5)
        
        return False

    def liberar_conexoes_db(self):
        """Força liberação de conexões SQLite"""
        try:
            import gc
            gc.collect()
            
            # Fechar conexão do db_manager se existir
            if hasattr(self.db_manager, '_connection') and self.db_manager._connection:
                self.db_manager._connection.close()
                self.db_manager._connection = None
                
            logging.debug("Conexões SQLite liberadas")
            
        except Exception as e:
            logging.warning(f"Erro ao liberar conexões: {e}")
    
    def obter_empresa_completa(self, empresa_id: int) -> Optional[EmpresaCompleta]:
        """Obtém empresa com todos os dados"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT
                    e.*,
                    ed.cidade, 
                    ed.endereco, 
                    ed.cep, 
                    ed.telefone, 
                    ed.email,
                    ed.inscricao_estadual,
                    ed.regime_tributario, 
                    ed.atividade_principal,
                    ed.situacao_cadastral, 
                    ed.atualizado_em, 
                    ed.criado_por,
                    COALESCE(ed.ativa, 1) as ativa,
                    COALESCE(ed.monitoramento, 1) as monitoramento,
                    COALESCE(ed.alertas, 1) as alertas,
                    COUNT(nf.id) as total_nfes,
                    COALESCE(SUM(nf.valor_total), 0) as valor_total_movimentado,
                    MAX(nf.data_processamento) as ultimo_processamento
                FROM empresas e
                LEFT JOIN empresas_detalhadas ed ON e.id = ed.empresa_id
                LEFT JOIN notas_fiscais nf ON e.id = nf.empresa_id
                WHERE e.id = ?
                GROUP BY e.id
                """, (empresa_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                data = dict(row)
                
                # Adicionar campos que podem estar ausentes
                data['inscricao_estadual'] = data.get('inscricao_estadual', '')
                data['criado_em'] = data.get('criado_em', '')
                
                # Converter valores para bool
                data['ativa'] = bool(data.get('ativa', 1))
                data['monitoramento'] = bool(data.get('monitoramento', 1)) 
                data['alertas'] = bool(data.get('alertas', 1))
                
                return EmpresaCompleta(**data)
                
        except Exception as e:
            logging.error(f"❌ Erro ao obter empresa {empresa_id}: {e}")
            return None
    
    def listar_empresas_completas(self, filtros: Dict[str, Any] = None) -> List[EmpresaCompleta]:
        """Lista empresas com filtros avançados"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                SELECT
                    e.*, 
                    ed.cidade, 
                    ed.endereco, 
                    ed.cep,
                    ed.telefone,
                    ed.email,
                    ed.inscricao_estadual,
                    ed.regime_tributario,
                    ed.atividade_principal,
                    ed.situacao_cadastral,
                    ed.atualizado_em,
                    ed.criado_por,
                    COALESCE(ed.ativa, 1) as ativa,
                    COALESCE(ed.monitoramento, 1) as monitoramento,
                    COALESCE(ed.alertas, 1) as alertas,
                    COUNT(nf.id) as total_nfes,
                    COALESCE(SUM(nf.valor_total), 0) as valor_total_movimentado,
                    MAX(nf.data_processamento) as ultimo_processamento
                FROM empresas e
                LEFT JOIN empresas_detalhadas ed ON e.id = ed.empresa_id
                LEFT JOIN notas_fiscais nf ON e.id = nf.empresa_id
                WHERE COALESCE(ed.ativa, 1) = 1 
                  AND COALESCE(ed.situacao_cadastral, 'ATIVA') != 'EXCLUIDA'
                """
                
                params = []

                if filtros:
                    if filtros.get('uf'):
                        query += " AND e.uf = ?"
                        params.append(filtros['uf'])

                    if filtros.get('ativa') is not None:
                        query += " AND COALESCE(ed.ativa, 1) = ?"
                        params.append(filtros['ativa'])

                    if filtros.get('situacao_cadastral'):
                        query += " AND ed.situacao_cadastral = ?"
                        params.append(filtros['situacao_cadastral'])
                        
                query += " GROUP BY e.id ORDER BY e.razao_social"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                empresas = []
                for row in rows:
                    data = dict(row)
                    # Adicionar campos que podem estar ausentes
                    data['inscricao_estadual'] = data.get('inscricao_estadual', '')
                    data['criado_em'] = data.get('criado_em', '')
                    
                    # Converter booleanos
                    data['ativa'] = bool(data.get('ativa', 1))
                    data['monitoramento'] = bool(data.get('monitoramento', 1))
                    data['alertas'] = bool(data.get('alertas', 1))
                    
                    empresas.append(EmpresaCompleta(**data))
                    
                return empresas
                
        except Exception as e:
            logging.error(f"❌ Erro ao listar empresas: {e}")
            return []
    
    def obter_historico_alteracoes(self, empresa_id: int) -> List[Dict[str, Any]]:
        """Obtém histórico de alterações da empresa"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT * FROM empresas_historico 
                WHERE empresa_id = ?
                ORDER BY alterado_em DESC
                """, (empresa_id,))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logging.error(f"❌ Erro ao obter histórico: {e}")
            return []
    
    def exportar_empresas(self, formato: str = 'csv') -> str:
        """Exporta lista de empresas"""
        try:
            empresas = self.listar_empresas_completas()
            
            if formato.lower() == 'csv':
                return self._exportar_csv(empresas)
            elif formato.lower() == 'json':
                return self._exportar_json(empresas)
            else:
                raise ValueError("Formato não suportado")
                
        except Exception as e:
            logging.error(f"❌ Erro ao exportar: {e}")
            raise
    
    def importar_empresas(self, arquivo_path: str, criado_por: str = "Import") -> Dict[str, int]:
        """Importa empresas de arquivo CSV/JSON"""
        try:
            if arquivo_path.endswith('.csv'):
                return self._importar_csv(arquivo_path, criado_por)
            elif arquivo_path.endswith('.json'):
                return self._importar_json(arquivo_path, criado_por)
            else:
                raise ValueError("Formato de arquivo não suportado")
                
        except Exception as e:
            logging.error(f"❌ Erro ao importar: {e}")
            raise
    
    # Funções auxiliares internas
    def _limpar_cnpj(self, cnpj: str) -> str:
        return ''.join(filter(str.isdigit, cnpj or ''))
    
    def _formatar_cnpj(self, cnpj_limpo: str) -> str:
        return f"{cnpj_limpo[:2]}.{cnpj_limpo[2:5]}.{cnpj_limpo[5:8]}/{cnpj_limpo[8:12]}-{cnpj_limpo[12:14]}"
    
    def _validar_cnpj(self, cnpj: str) -> bool:
        """Validação básica de CNPJ"""
        if len(cnpj) != 14:
            return False
        
        # Verificar se não são todos dígitos iguais
        if cnpj == cnpj[0] * 14:
            return False
        
        # Validação dos dígitos verificadores (algoritmo oficial)
        def calcular_digito(cnpj_base, pesos):
            soma = sum(int(cnpj_base[i]) * pesos[i] for i in range(len(pesos)))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto
        
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        
        digito1 = calcular_digito(cnpj[:12], pesos1)
        digito2 = calcular_digito(cnpj[:13], pesos2)
        
        return cnpj[-2:] == f"{digito1}{digito2}"
    
    def _empresa_existe(self, cnpj_limpo: str) -> bool:
        """Verifica se empresa já existe"""
        cnpj_formatado = self._formatar_cnpj(cnpj_limpo)
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM empresas WHERE cnpj = ?", (cnpj_formatado,))
            return cursor.fetchone() is not None
    
    def _consultar_receita_federal(self, cnpj: str) -> Optional[Dict[str, Any]]:
        """Consulta dados na Receita Federal (API pública)"""
        try:
            # API gratuita da ReceitaWS
            url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                dados = response.json()
                if dados.get('status') == 'OK':
                    return {
                        'razao_social': dados.get('nome', ''),
                        'nome_fantasia': dados.get('fantasia', ''),
                        'uf': dados.get('uf', ''),
                        'cidade': dados.get('municipio', ''),
                        'endereco': f"{dados.get('logradouro', '')} {dados.get('numero', '')}".strip(),
                        'cep': dados.get('cep', ''),
                        'telefone': dados.get('telefone', ''),
                        'email': dados.get('email', ''),
                        'atividade_principal': dados.get('atividade_principal', [{}])[0].get('text', ''),
                        'situacao_cadastral': dados.get('situacao', '')
                    }
        except:
            pass  # API não disponível, continua sem dados
        
        return None
    
    def _criar_detalhes_empresa(self, empresa_id: int, dados: Dict[str, Any], criado_por: str):
        """Cria registro detalhado da empresa"""
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO empresas_detalhadas (
                empresa_id, cidade, endereco, cep, telefone, email,
                inscricao_estadual, regime_tributario, atividade_principal,
                situacao_cadastral, atualizado_em, criado_por
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                empresa_id, dados.get('cidade', ''), dados.get('endereco', ''),
                dados.get('cep', ''), dados.get('telefone', ''), dados.get('email', ''),
                dados.get('inscricao_estadual', ''), dados.get('regime_tributario', ''),
                dados.get('atividade_principal', ''), dados.get('situacao_cadastral', 'ATIVA'),
                datetime.now().isoformat(), criado_por
            ))
    
    def _criar_config_padrao(self, empresa_id: int):
        """Cria configurações padrão para empresa"""
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO empresas_config (empresa_id, config_json)
            VALUES (?, ?)
            """, (empresa_id, json.dumps({
                'processamento_automatico': True,
                'alertas_email': True,
                'backup_dias': 30,
                'nivel_risco_maximo': 0.8
            })))
    
    def _registrar_alteracao(self, empresa_id: int, campo: str, valor_anterior: Any,
                           valor_novo: Any, alterado_por: str):
        """Registra alteração no histórico"""
        with sqlite3.connect(self.db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO empresas_historico 
            (empresa_id, campo_alterado, valor_anterior, valor_novo, alterado_por)
            VALUES (?, ?, ?, ?, ?)
            """, (empresa_id, campo, str(valor_anterior), str(valor_novo), alterado_por))
    
    def _atualizar_detalhes_empresa(self, empresa_id: int, dados: Dict[str, Any],
                                  alterado_por: str, cursor):
        """Atualiza detalhes da empresa"""
        campos_detalhes = [
            'cidade', 'endereco', 'cep', 'telefone', 'email',
            'inscricao_estadual', 'regime_tributario', 'atividade_principal',
            'situacao_cadastral', 'ativa', 'monitoramento', 'alertas'
        ]
        
        updates = []
        params = []
        
        for campo in campos_detalhes:
            if campo in dados:
                updates.append(f"{campo} = ?")
                params.append(dados[campo])
        
        if updates:
            updates.append("atualizado_em = ?")
            params.append(datetime.now().isoformat())
            params.append(empresa_id)
            
            cursor.execute(f"""
            UPDATE empresas_detalhadas 
            SET {', '.join(updates)}
            WHERE empresa_id = ?
            """, params)
    
    def _exportar_csv(self, empresas: List[EmpresaCompleta]) -> str:
        """Exporta empresas para CSV"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow([
            'CNPJ', 'Razão Social', 'Nome Fantasia', 'UF', 'Cidade',
            'Telefone', 'Email', 'Situação', 'Total NFe', 'Valor Total'
        ])
        
        # Dados
        for emp in empresas:
            writer.writerow([
                emp.cnpj, emp.razao_social, emp.nome_fantasia, emp.uf, emp.cidade,
                emp.telefone, emp.email, emp.situacao_cadastral,
                emp.total_nfes, f"R$ {emp.valor_total_movimentado:,.2f}"
            ])
        
        return output.getvalue()
    
    def _exportar_json(self, empresas: List[EmpresaCompleta]) -> str:
        """Exporta empresas para JSON"""
        return json.dumps([asdict(emp) for emp in empresas], 
                         indent=2, ensure_ascii=False, default=str)
    
    def _importar_csv(self, arquivo_path: str, criado_por: str) -> Dict[str, int]:
        """Importa empresas de CSV"""
        import csv
        
        resultados = {'sucesso': 0, 'erro': 0, 'duplicadas': 0}
        
        with open(arquivo_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                try:
                    if self._empresa_existe(self._limpar_cnpj(row.get('CNPJ', ''))):
                        resultados['duplicadas'] += 1
                        continue
                    
                    dados = {
                        'cnpj': row.get('CNPJ', ''),
                        'razao_social': row.get('Razão Social', ''),
                        'nome_fantasia': row.get('Nome Fantasia', ''),
                        'uf': row.get('UF', ''),
                        'cidade': row.get('Cidade', ''),
                        'telefone': row.get('Telefone', ''),
                        'email': row.get('Email', '')
                    }
                    
                    self.criar_empresa(dados, criado_por)
                    resultados['sucesso'] += 1
                    
                except Exception as e:
                    logging.error(f"Erro ao importar empresa {row}: {e}")
                    resultados['erro'] += 1
        
        return resultados

    def _importar_json(self, arquivo_path: str, criado_por: str) -> Dict[str, int]:
        """Importa empresas de JSON"""
        resultados = {'sucesso': 0, 'erro': 0, 'duplicadas': 0}
        
        try:
            with open(arquivo_path, 'r', encoding='utf-8') as file:
                empresas_data = json.load(file)
            
            for empresa_data in empresas_data:
                try:
                    if self._empresa_existe(self._limpar_cnpj(empresa_data.get('cnpj', ''))):
                        resultados['duplicadas'] += 1
                        continue
                    
                    self.criar_empresa(empresa_data, criado_por)
                    resultados['sucesso'] += 1
                    
                except Exception as e:
                    logging.error(f"Erro ao importar empresa {empresa_data}: {e}")
                    resultados['erro'] += 1
                    
        except Exception as e:
            logging.error(f"Erro ao ler arquivo JSON: {e}")
            raise
        
        return resultados
