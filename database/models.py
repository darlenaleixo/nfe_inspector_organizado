<<<<<<< HEAD
# database/models.py

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
import os


@dataclass
class Empresa:
    id: Optional[int] = None
    cnpj: str = ""
    razao_social: str = ""
    nome_fantasia: str = ""
    uf: str = ""
    criado_em: str = ""

@dataclass
class NotaFiscal:
    id: Optional[int] = None
    empresa_id: int = 0
    chave_acesso: str = ""
    numero: str = ""
    serie: str = ""
    data_emissao: str = ""
    data_processamento: str = ""
    
    # Emissor
    cnpj_emissor: str = ""
    nome_emissor: str = ""
    uf_emissor: str = ""
    
    # Destinatário
    cnpj_destinatario: str = ""
    nome_destinatario: str = ""
    uf_destinatario: str = ""
    
    # Valores
    valor_produtos: float = 0.0
    valor_frete: float = 0.0
    valor_seguro: float = 0.0
    valor_desconto: float = 0.0
    valor_total: float = 0.0
    valor_icms: float = 0.0
    valor_ipi: float = 0.0
    valor_pis: float = 0.0
    valor_cofins: float = 0.0
    
    # Status
    status_sefaz: str = ""  # autorizada, rejeitada, cancelada
    codigo_status: str = ""
    motivo_status: str = ""
    
    # Tipo de pagamento
    forma_pagamento: str = ""
    condicao_pagamento: str = ""
    
    # Classificação IA
    risco_fiscal: float = 0.0
    nivel_risco: str = ""
    inconsistencias: int = 0
    
    # Metadados
    arquivo_origem: str = ""
    hash_arquivo: str = ""

@dataclass
class ItemNotaFiscal:
    id: Optional[int] = None
    nota_fiscal_id: int = 0
    numero_item: int = 0
    
    # Produto
    codigo_produto: str = ""
    descricao: str = ""
    ncm: str = ""
    cest: str = ""
    unidade: str = ""
    quantidade: float = 0.0
    valor_unitario: float = 0.0
    valor_total: float = 0.0
    
    # Impostos
    cfop: str = ""
    cst_icms: str = ""
    aliquota_icms: float = 0.0
    valor_icms: float = 0.0
    cst_pis: str = ""
    aliquota_pis: float = 0.0
    valor_pis: float = 0.0
    cst_cofins: str = ""
    aliquota_cofins: float = 0.0
    valor_cofins: float = 0.0
    
    # Sugestões IA
    ncm_sugerido: str = ""
    cfop_sugerido: str = ""
    cst_sugerido: str = ""
    confianca_ia: float = 0.0

class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "None"):
        # Se não especificar caminho, usar pasta 'database'
        if db_path is None:
            # Criar pasta 'database' se não existir
            db_folder = os.path.join(os.getcwd(), 'database')
            os.makedirs(db_folder, exist_ok=True)
            
            # Caminho completo do banco
            self.db_path = os.path.join(db_folder, 'nfe_data.db')
        else:
            self.db_path = db_path
            
        self.init_database()
        logging.info(f"✅ Banco de dados iniciado: {self.db_path}")
    
    def init_database(self):
        """Inicializa o banco de dados com todas as tabelas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela de empresas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS empresas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cnpj TEXT UNIQUE NOT NULL,
                        razao_social TEXT NOT NULL,
                        nome_fantasia TEXT,
                        uf TEXT,
                        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabela de notas fiscais
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notas_fiscais (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        empresa_id INTEGER,
                        chave_acesso TEXT UNIQUE NOT NULL,
                        numero TEXT NOT NULL,
                        serie TEXT NOT NULL,
                        data_emissao TEXT NOT NULL,
                        data_processamento TEXT DEFAULT CURRENT_TIMESTAMP,
                        
                        cnpj_emissor TEXT NOT NULL,
                        nome_emissor TEXT,
                        uf_emissor TEXT,
                        
                        cnpj_destinatario TEXT,
                        nome_destinatario TEXT,
                        uf_destinatario TEXT,
                        
                        valor_produtos REAL DEFAULT 0,
                        valor_frete REAL DEFAULT 0,
                        valor_seguro REAL DEFAULT 0,
                        valor_desconto REAL DEFAULT 0,
                        valor_total REAL DEFAULT 0,
                        valor_icms REAL DEFAULT 0,
                        valor_ipi REAL DEFAULT 0,
                        valor_pis REAL DEFAULT 0,
                        valor_cofins REAL DEFAULT 0,
                        
                        status_sefaz TEXT DEFAULT 'processando',
                        codigo_status TEXT,
                        motivo_status TEXT,
                        
                        forma_pagamento TEXT,
                        condicao_pagamento TEXT,
                        
                        risco_fiscal REAL DEFAULT 0,
                        nivel_risco TEXT DEFAULT 'baixo',
                        inconsistencias INTEGER DEFAULT 0,
                        
                        arquivo_origem TEXT,
                        hash_arquivo TEXT,
                        
                        FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                    )
                """)
                
                # Tabela de itens das notas fiscais
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS itens_notas_fiscais (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nota_fiscal_id INTEGER,
                        numero_item INTEGER NOT NULL,
                        
                        codigo_produto TEXT,
                        descricao TEXT NOT NULL,
                        ncm TEXT,
                        cest TEXT,
                        unidade TEXT,
                        quantidade REAL DEFAULT 0,
                        valor_unitario REAL DEFAULT 0,
                        valor_total REAL DEFAULT 0,
                        
                        cfop TEXT,
                        cst_icms TEXT,
                        aliquota_icms REAL DEFAULT 0,
                        valor_icms REAL DEFAULT 0,
                        cst_pis TEXT,
                        aliquota_pis REAL DEFAULT 0,
                        valor_pis REAL DEFAULT 0,
                        cst_cofins TEXT,
                        aliquota_cofins REAL DEFAULT 0,
                        valor_cofins REAL DEFAULT 0,
                        
                        ncm_sugerido TEXT,
                        cfop_sugerido TEXT,
                        cst_sugerido TEXT,
                        confianca_ia REAL DEFAULT 0,
                        
                        FOREIGN KEY (nota_fiscal_id) REFERENCES notas_fiscais (id)
                    )
                """)
                
                # Índices para performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_chave ON notas_fiscais (chave_acesso)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_data ON notas_fiscais (data_emissao)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_status ON notas_fiscais (status_sefaz)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_empresa ON notas_fiscais (empresa_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_itens_nf ON itens_notas_fiscais (nota_fiscal_id)")
                
                conn.commit()
                logging.info("✅ Base de dados inicializada com sucesso")
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inicializar banco de dados: {e}")
            raise
    
    def inserir_empresa(self, empresa: Empresa) -> int:
        """Insere uma empresa e retorna o ID (nova ou existente)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Primeiro verifica se empresa já existe
                cursor.execute("SELECT id FROM empresas WHERE cnpj = ?", (empresa.cnpj,))
                resultado = cursor.fetchone()
                
                if resultado:
                    # Empresa já existe, retorna ID existente
                    empresa_id = resultado[0]
                    logging.debug(f"Empresa já existe: CNPJ {empresa.cnpj}, ID {empresa_id}")
                    return empresa_id
                else:
                    # Empresa não existe, insere nova
                    cursor.execute("""
                    INSERT INTO empresas (cnpj, razao_social, nome_fantasia, uf, criado_em)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        empresa.cnpj,
                        empresa.razao_social,
                        empresa.nome_fantasia,
                        empresa.uf,
                        datetime.now().isoformat()
                    ))
                    
                    empresa_id = cursor.lastrowid
                    logging.info(f"✅ Nova empresa cadastrada: {empresa.razao_social} (ID: {empresa_id})")
                    return empresa_id
                    
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inserir empresa: {e}")
            return None

    def inserir_empresa_retorna_status(self, empresa: Empresa) -> tuple:
        """Insere empresa e retorna (ID, foi_nova_empresa), criando detalhes obrigatórios."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Verifica existência
                cursor.execute("SELECT id FROM empresas WHERE cnpj = ?", (empresa.cnpj,))
                row = cursor.fetchone()
                if row:
                    return row[0], False
                # Insere nova empresa
                cursor.execute("""
                    INSERT INTO empresas (cnpj, razao_social, nome_fantasia, uf, criado_em)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    empresa.cnpj,
                    empresa.razao_social,
                    empresa.nome_fantasia,
                    empresa.uf,
                    datetime.now().isoformat()
                ))
                empresa_id = cursor.lastrowid
                # Garante tabela detalhada
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS empresas_detalhadas (
                        id INTEGER PRIMARY KEY,
                        empresa_id INTEGER UNIQUE,
                        cidade TEXT, endereco TEXT, cep TEXT, telefone TEXT, email TEXT,
                        inscricao_estadual TEXT, regime_tributario TEXT, atividade_principal TEXT,
                        situacao_cadastral TEXT DEFAULT 'ATIVA', atualizado_em TEXT, criado_por TEXT,
                        ativa BOOLEAN DEFAULT 1, monitoramento BOOLEAN DEFAULT 1, alertas BOOLEAN DEFAULT 1,
                        FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                    )
                """)
                # Insere detalhes
                cursor.execute("""
                    INSERT INTO empresas_detalhadas (
                        empresa_id, situacao_cadastral, ativa, monitoramento, alertas, criado_por, atualizado_em
                    ) VALUES (?, 'ATIVA', 1, 1, 1, ?, ?)
                """, (
                    empresa_id,
                    'Processador',
                    datetime.now().isoformat()
                ))
                conn.commit()
                return empresa_id, True
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inserir empresa: {e}")
            return None, False



    def inserir_nota_fiscal(self, nota: NotaFiscal) -> int:
        """Insere uma nota fiscal e retorna o ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Converte dataclass para dicionário, excluindo ID
                dados = asdict(nota)
                dados.pop('id', None)
                
                # Monta query dinamicamente
                campos = list(dados.keys())
                placeholders = '?' * len(campos)
                valores = list(dados.values())
                
                cursor.execute(f"""
                    INSERT OR REPLACE INTO notas_fiscais 
                    ({', '.join(campos)}) 
                    VALUES ({', '.join(['?'] * len(campos))})
                """, valores)
                
                return cursor.lastrowid
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inserir nota fiscal: {e}")
            return None
    
    def inserir_item_nota_fiscal(self, item: ItemNotaFiscal) -> int:
        """Insere um item de nota fiscal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                dados = asdict(item)
                dados.pop('id', None)
                
                campos = list(dados.keys())
                valores = list(dados.values())
                
                cursor.execute(f"""
                    INSERT INTO itens_notas_fiscais 
                    ({', '.join(campos)}) 
                    VALUES ({', '.join(['?'] * len(campos))})
                """, valores)
                
                return cursor.lastrowid
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inserir item: {e}")
            return None
    
    def consultar_notas_fiscais(self, filtros: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Consulta notas fiscais com filtros opcionais"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Para acessar por nome da coluna
                cursor = conn.cursor()
                
                # Query base
                query = """
                    SELECT nf.*, e.razao_social as empresa_nome
                    FROM notas_fiscais nf
                    LEFT JOIN empresas e ON nf.empresa_id = e.id
                    WHERE 1=1
                """
                parametros = []
                
                # Aplica filtros dinamicamente
                if filtros:
                    if 'data_inicio' in filtros and filtros['data_inicio']:
                        query += " AND nf.data_emissao >= ?"
                        parametros.append(filtros['data_inicio'] + " 00:00:00")

                    if 'data_fim' in filtros and filtros['data_fim']:
                        query += " AND nf.data_emissao <= ?"
                        parametros.append(filtros['data_fim'] + " 23:59:59")
                    
                    if 'status_sefaz' in filtros and filtros['status_sefaz']:
                        query += " AND nf.status_sefaz = ?"
                        parametros.append(filtros['status_sefaz'])
                    
                    if 'forma_pagamento' in filtros and filtros['forma_pagamento']:
                        query += " AND LOWER(nf.forma_pagamento) LIKE ?"
                        parametros.append(f"%{filtros['forma_pagamento'].lower()}%")

                    
                    if 'empresa_id' in filtros and filtros['empresa_id']:
                        query += " AND nf.empresa_id = ?"
                        parametros.append(filtros['empresa_id'])
                    
                    if 'valor_min' in filtros and filtros['valor_min'] is not None:
                        query += " AND nf.valor_total >= ?"
                        parametros.append(filtros['valor_min'])
                    
                    if 'valor_max' in filtros and filtros['valor_max'] is not None:
                        query += " AND nf.valor_total <= ?"
                        parametros.append(filtros['valor_max'])
                    
                    if 'nivel_risco' in filtros and filtros['nivel_risco']:
                        query += " AND nf.nivel_risco = ?"
                        parametros.append(filtros['nivel_risco'])
                
                # Ordena por data mais recente
                query += " ORDER BY nf.data_emissao DESC, nf.id DESC"
                
                cursor.execute(query, parametros)
                resultados = cursor.fetchall()
                
                # Converte Row objects para dicionários
                return [dict(row) for row in resultados]
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao consultar notas fiscais: {e}")
            return []
    
    def obter_estatisticas(self, empresa_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtém estatísticas gerais das notas fiscais"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                where_clause = "WHERE empresa_id = ?" if empresa_id else ""
                params = [empresa_id] if empresa_id else []
                
                # Total de notas
                cursor.execute(f"SELECT COUNT(*) FROM notas_fiscais {where_clause}", params)
                total_notas = cursor.fetchone()[0]
                
                # Total por status
                cursor.execute(f"""
                    SELECT status_sefaz, COUNT(*) 
                    FROM notas_fiscais {where_clause}
                    GROUP BY status_sefaz
                """, params)
                status_counts = dict(cursor.fetchall())
                
                # Valor total
                cursor.execute(f"SELECT SUM(valor_total) FROM notas_fiscais {where_clause}", params)
                valor_total = cursor.fetchone()[0] or 0
                
                # Média de risco
                cursor.execute(f"SELECT AVG(risco_fiscal) FROM notas_fiscais {where_clause}", params)
                risco_medio = cursor.fetchone()[0] or 0
                
                return {
                    'total_notas': total_notas,
                    'status_counts': status_counts,
                    'valor_total': valor_total,
                    'risco_medio': risco_medio
                }
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def listar_empresas(self) -> List[Dict[str, Any]]:
        """Lista todas as empresas cadastradas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT e.*, 
                           COUNT(nf.id) as total_notas,
                           COALESCE(SUM(nf.valor_total), 0) as valor_total
                    FROM empresas e
                    LEFT JOIN notas_fiscais nf ON e.id = nf.empresa_id
                    GROUP BY e.id
                    ORDER BY e.razao_social
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao listar empresas: {e}")
            return []

    def backup_database(self, backup_path: str) -> bool:
        """Cria backup do banco de dados"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logging.info(f"✅ Backup criado: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"❌ Erro ao criar backup: {e}")
            return False
=======
# database/models.py

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
import os


@dataclass
class Empresa:
    id: Optional[int] = None
    cnpj: str = ""
    razao_social: str = ""
    nome_fantasia: str = ""
    uf: str = ""
    criado_em: str = ""

@dataclass
class NotaFiscal:
    id: Optional[int] = None
    empresa_id: int = 0
    chave_acesso: str = ""
    numero: str = ""
    serie: str = ""
    data_emissao: str = ""
    data_processamento: str = ""
    
    # Emissor
    cnpj_emissor: str = ""
    nome_emissor: str = ""
    uf_emissor: str = ""
    
    # Destinatário
    cnpj_destinatario: str = ""
    nome_destinatario: str = ""
    uf_destinatario: str = ""
    
    # Valores
    valor_produtos: float = 0.0
    valor_frete: float = 0.0
    valor_seguro: float = 0.0
    valor_desconto: float = 0.0
    valor_total: float = 0.0
    valor_icms: float = 0.0
    valor_ipi: float = 0.0
    valor_pis: float = 0.0
    valor_cofins: float = 0.0
    
    # Status
    status_sefaz: str = ""  # autorizada, rejeitada, cancelada
    codigo_status: str = ""
    motivo_status: str = ""
    
    # Tipo de pagamento
    forma_pagamento: str = ""
    condicao_pagamento: str = ""
    
    # Classificação IA
    risco_fiscal: float = 0.0
    nivel_risco: str = ""
    inconsistencias: int = 0
    
    # Metadados
    arquivo_origem: str = ""
    hash_arquivo: str = ""

@dataclass
class ItemNotaFiscal:
    id: Optional[int] = None
    nota_fiscal_id: int = 0
    numero_item: int = 0
    
    # Produto
    codigo_produto: str = ""
    descricao: str = ""
    ncm: str = ""
    cest: str = ""
    unidade: str = ""
    quantidade: float = 0.0
    valor_unitario: float = 0.0
    valor_total: float = 0.0
    
    # Impostos
    cfop: str = ""
    cst_icms: str = ""
    aliquota_icms: float = 0.0
    valor_icms: float = 0.0
    cst_pis: str = ""
    aliquota_pis: float = 0.0
    valor_pis: float = 0.0
    cst_cofins: str = ""
    aliquota_cofins: float = 0.0
    valor_cofins: float = 0.0
    
    # Sugestões IA
    ncm_sugerido: str = ""
    cfop_sugerido: str = ""
    cst_sugerido: str = ""
    confianca_ia: float = 0.0

class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "None"):
        # Se não especificar caminho, usar pasta 'database'
        if db_path is None:
            # Criar pasta 'database' se não existir
            db_folder = os.path.join(os.getcwd(), 'database')
            os.makedirs(db_folder, exist_ok=True)
            
            # Caminho completo do banco
            self.db_path = os.path.join(db_folder, 'nfe_data.db')
        else:
            self.db_path = db_path
            
        self.init_database()
        logging.info(f"✅ Banco de dados iniciado: {self.db_path}")
    
    def init_database(self):
        """Inicializa o banco de dados com todas as tabelas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela de empresas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS empresas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cnpj TEXT UNIQUE NOT NULL,
                        razao_social TEXT NOT NULL,
                        nome_fantasia TEXT,
                        uf TEXT,
                        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabela de notas fiscais
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notas_fiscais (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        empresa_id INTEGER,
                        chave_acesso TEXT UNIQUE NOT NULL,
                        numero TEXT NOT NULL,
                        serie TEXT NOT NULL,
                        data_emissao TEXT NOT NULL,
                        data_processamento TEXT DEFAULT CURRENT_TIMESTAMP,
                        
                        cnpj_emissor TEXT NOT NULL,
                        nome_emissor TEXT,
                        uf_emissor TEXT,
                        
                        cnpj_destinatario TEXT,
                        nome_destinatario TEXT,
                        uf_destinatario TEXT,
                        
                        valor_produtos REAL DEFAULT 0,
                        valor_frete REAL DEFAULT 0,
                        valor_seguro REAL DEFAULT 0,
                        valor_desconto REAL DEFAULT 0,
                        valor_total REAL DEFAULT 0,
                        valor_icms REAL DEFAULT 0,
                        valor_ipi REAL DEFAULT 0,
                        valor_pis REAL DEFAULT 0,
                        valor_cofins REAL DEFAULT 0,
                        
                        status_sefaz TEXT DEFAULT 'processando',
                        codigo_status TEXT,
                        motivo_status TEXT,
                        
                        forma_pagamento TEXT,
                        condicao_pagamento TEXT,
                        
                        risco_fiscal REAL DEFAULT 0,
                        nivel_risco TEXT DEFAULT 'baixo',
                        inconsistencias INTEGER DEFAULT 0,
                        
                        arquivo_origem TEXT,
                        hash_arquivo TEXT,
                        
                        FOREIGN KEY (empresa_id) REFERENCES empresas (id)
                    )
                """)
                
                # Tabela de itens das notas fiscais
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS itens_notas_fiscais (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nota_fiscal_id INTEGER,
                        numero_item INTEGER NOT NULL,
                        
                        codigo_produto TEXT,
                        descricao TEXT NOT NULL,
                        ncm TEXT,
                        cest TEXT,
                        unidade TEXT,
                        quantidade REAL DEFAULT 0,
                        valor_unitario REAL DEFAULT 0,
                        valor_total REAL DEFAULT 0,
                        
                        cfop TEXT,
                        cst_icms TEXT,
                        aliquota_icms REAL DEFAULT 0,
                        valor_icms REAL DEFAULT 0,
                        cst_pis TEXT,
                        aliquota_pis REAL DEFAULT 0,
                        valor_pis REAL DEFAULT 0,
                        cst_cofins TEXT,
                        aliquota_cofins REAL DEFAULT 0,
                        valor_cofins REAL DEFAULT 0,
                        
                        ncm_sugerido TEXT,
                        cfop_sugerido TEXT,
                        cst_sugerido TEXT,
                        confianca_ia REAL DEFAULT 0,
                        
                        FOREIGN KEY (nota_fiscal_id) REFERENCES notas_fiscais (id)
                    )
                """)
                
                # Índices para performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_chave ON notas_fiscais (chave_acesso)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_data ON notas_fiscais (data_emissao)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_status ON notas_fiscais (status_sefaz)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_nf_empresa ON notas_fiscais (empresa_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_itens_nf ON itens_notas_fiscais (nota_fiscal_id)")
                
                conn.commit()
                logging.info("✅ Base de dados inicializada com sucesso")
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inicializar banco de dados: {e}")
            raise
    
    def inserir_empresa(self, empresa: Empresa) -> int:
        """Insere uma empresa e retorna o ID (nova ou existente)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Primeiro verifica se empresa já existe
                cursor.execute("SELECT id FROM empresas WHERE cnpj = ?", (empresa.cnpj,))
                resultado = cursor.fetchone()
                
                if resultado:
                    # Empresa já existe, retorna ID existente
                    empresa_id = resultado[0]
                    logging.debug(f"Empresa já existe: CNPJ {empresa.cnpj}, ID {empresa_id}")
                    return empresa_id
                else:
                    # Empresa não existe, insere nova
                    cursor.execute("""
                    INSERT INTO empresas (cnpj, razao_social, nome_fantasia, uf, criado_em)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        empresa.cnpj,
                        empresa.razao_social,
                        empresa.nome_fantasia,
                        empresa.uf,
                        datetime.now().isoformat()
                    ))
                    
                    empresa_id = cursor.lastrowid
                    logging.info(f"✅ Nova empresa cadastrada: {empresa.razao_social} (ID: {empresa_id})")
                    return empresa_id
                    
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inserir empresa: {e}")
            return None

    def inserir_empresa_retorna_status(self, empresa: Empresa) -> tuple:
        """Insere empresa e retorna (ID, foi_nova_empresa), criando detalhes obrigatórios"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verifica se já existe
                cursor.execute("SELECT id FROM empresas WHERE cnpj = ?", (empresa.cnpj,))
                row = cursor.fetchone()
                
                if row:
                    return row[0], False
                else:
                    # Insere nova empresa
                    cursor.execute("""
                    INSERT INTO empresas (cnpj, razao_social, nome_fantasia, uf, criado_em)
                    VALUES (?, ?, ?, ?, ?)
                    """, (
                        empresa.cnpj,
                        empresa.razao_social,
                        empresa.nome_fantasia,
                        empresa.uf,
                        datetime.now().isoformat()
                    ))
                    empresa_id = cursor.lastrowid
                    
                    # ✅ CRÍTICO: Criar tabela empresas_detalhadas se não existir
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
                    
                    # ✅ CRÍTICO: Inserir registro em empresas_detalhadas
                    cursor.execute("""
                    INSERT INTO empresas_detalhadas (
                        empresa_id, situacao_cadastral, ativa, monitoramento, alertas, 
                        criado_por, atualizado_em
                    ) VALUES (?, 'ATIVA', 1, 1, 1, ?, ?)
                    """, (
                        empresa_id,
                        'Processador',
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    logging.info(f"✅ Nova empresa cadastrada com detalhes: {empresa.razao_social} (ID: {empresa_id})")
                    return empresa_id, True
                    
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inserir empresa com status: {e}")
            return None, False


    def inserir_nota_fiscal(self, nota: NotaFiscal) -> int:
        """Insere uma nota fiscal e retorna o ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Converte dataclass para dicionário, excluindo ID
                dados = asdict(nota)
                dados.pop('id', None)
                
                # Monta query dinamicamente
                campos = list(dados.keys())
                placeholders = '?' * len(campos)
                valores = list(dados.values())
                
                cursor.execute(f"""
                    INSERT OR REPLACE INTO notas_fiscais 
                    ({', '.join(campos)}) 
                    VALUES ({', '.join(['?'] * len(campos))})
                """, valores)
                
                return cursor.lastrowid
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inserir nota fiscal: {e}")
            return None
    
    def inserir_item_nota_fiscal(self, item: ItemNotaFiscal) -> int:
        """Insere um item de nota fiscal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                dados = asdict(item)
                dados.pop('id', None)
                
                campos = list(dados.keys())
                valores = list(dados.values())
                
                cursor.execute(f"""
                    INSERT INTO itens_notas_fiscais 
                    ({', '.join(campos)}) 
                    VALUES ({', '.join(['?'] * len(campos))})
                """, valores)
                
                return cursor.lastrowid
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao inserir item: {e}")
            return None
    
    def consultar_notas_fiscais(self, filtros: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Consulta notas fiscais com filtros opcionais"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row  # Para acessar por nome da coluna
                cursor = conn.cursor()
                
                # Query base
                query = """
                    SELECT nf.*, e.razao_social as empresa_nome
                    FROM notas_fiscais nf
                    LEFT JOIN empresas e ON nf.empresa_id = e.id
                    WHERE 1=1
                """
                parametros = []
                
                # Aplica filtros dinamicamente
                if filtros:
                    if 'data_inicio' in filtros and filtros['data_inicio']:
                        query += " AND nf.data_emissao >= ?"
                        parametros.append(filtros['data_inicio'] + " 00:00:00")

                    if 'data_fim' in filtros and filtros['data_fim']:
                        query += " AND nf.data_emissao <= ?"
                        parametros.append(filtros['data_fim'] + " 23:59:59")
                    
                    if 'status_sefaz' in filtros and filtros['status_sefaz']:
                        query += " AND nf.status_sefaz = ?"
                        parametros.append(filtros['status_sefaz'])
                    
                    if 'forma_pagamento' in filtros and filtros['forma_pagamento']:
                        query += " AND LOWER(nf.forma_pagamento) LIKE ?"
                        parametros.append(f"%{filtros['forma_pagamento'].lower()}%")

                    
                    if 'empresa_id' in filtros and filtros['empresa_id']:
                        query += " AND nf.empresa_id = ?"
                        parametros.append(filtros['empresa_id'])
                    
                    if 'valor_min' in filtros and filtros['valor_min'] is not None:
                        query += " AND nf.valor_total >= ?"
                        parametros.append(filtros['valor_min'])
                    
                    if 'valor_max' in filtros and filtros['valor_max'] is not None:
                        query += " AND nf.valor_total <= ?"
                        parametros.append(filtros['valor_max'])
                    
                    if 'nivel_risco' in filtros and filtros['nivel_risco']:
                        query += " AND nf.nivel_risco = ?"
                        parametros.append(filtros['nivel_risco'])
                
                # Ordena por data mais recente
                query += " ORDER BY nf.data_emissao DESC, nf.id DESC"
                
                cursor.execute(query, parametros)
                resultados = cursor.fetchall()
                
                # Converte Row objects para dicionários
                return [dict(row) for row in resultados]
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao consultar notas fiscais: {e}")
            return []
    
    def obter_estatisticas(self, empresa_id: Optional[int] = None) -> Dict[str, Any]:
        """Obtém estatísticas gerais das notas fiscais"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                where_clause = "WHERE empresa_id = ?" if empresa_id else ""
                params = [empresa_id] if empresa_id else []
                
                # Total de notas
                cursor.execute(f"SELECT COUNT(*) FROM notas_fiscais {where_clause}", params)
                total_notas = cursor.fetchone()[0]
                
                # Total por status
                cursor.execute(f"""
                    SELECT status_sefaz, COUNT(*) 
                    FROM notas_fiscais {where_clause}
                    GROUP BY status_sefaz
                """, params)
                status_counts = dict(cursor.fetchall())
                
                # Valor total
                cursor.execute(f"SELECT SUM(valor_total) FROM notas_fiscais {where_clause}", params)
                valor_total = cursor.fetchone()[0] or 0
                
                # Média de risco
                cursor.execute(f"SELECT AVG(risco_fiscal) FROM notas_fiscais {where_clause}", params)
                risco_medio = cursor.fetchone()[0] or 0
                
                return {
                    'total_notas': total_notas,
                    'status_counts': status_counts,
                    'valor_total': valor_total,
                    'risco_medio': risco_medio
                }
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao obter estatísticas: {e}")
            return {}
    
    def listar_empresas(self) -> List[Dict[str, Any]]:
        """Lista todas as empresas cadastradas"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT e.*, 
                           COUNT(nf.id) as total_notas,
                           COALESCE(SUM(nf.valor_total), 0) as valor_total
                    FROM empresas e
                    LEFT JOIN notas_fiscais nf ON e.id = nf.empresa_id
                    GROUP BY e.id
                    ORDER BY e.razao_social
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            logging.error(f"❌ Erro ao listar empresas: {e}")
            return []

    def backup_database(self, backup_path: str) -> bool:
        """Cria backup do banco de dados"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logging.info(f"✅ Backup criado: {backup_path}")
            return True
        except Exception as e:
            logging.error(f"❌ Erro ao criar backup: {e}")
            return False
>>>>>>> 62fc89a629eb88be57523fc82f480d488337ac8e
