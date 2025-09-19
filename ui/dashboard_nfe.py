# ui/dashboard_nfe.py - VERSÃO CORRIGIDA COMPLETA

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import threading
import logging
import sqlite3


from database.models import DatabaseManager

# Imports seguros com tratamento de erro
try:
    from ia_fiscal.analisador_riscos import AnalisadorRiscos
except ImportError:
    AnalisadorRiscos = None

try:
    from processing.processor import NFeProcessorBI
except ImportError:
    NFeProcessorBI = None

class DashboardNFe(tk.Toplevel):
    """Dashboard interativo para análise de NFe"""
    
    def __init__(self, parent, db_manager: DatabaseManager):
        super().__init__(parent)
        self.db_manager = db_manager
        self.title("Dashboard NFe - Business Intelligence")
        self.geometry("1400x800")
        
        # Variáveis de filtro
        self.filtros = {}
        self.dados_atuais = []
        
        self.setup_interface()
        self.carregar_dados_iniciais()
    
    def setup_interface(self):
        """Configura a interface do dashboard"""
        
        # Painel principal com notebooks (abas)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 1: Lista de Notas Fiscais
        self.frame_lista = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_lista, text="📊 Notas Fiscais")
        self.setup_aba_lista()
        
        # Aba 2: Estatísticas
        self.frame_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_stats, text="📈 Estatísticas")
        self.setup_aba_estatisticas()
        
        # Aba 3: Empresas
        self.frame_empresas = ttk.Frame(self.notebook)
        self.notebook.add(self.frame_empresas, text="🏢 Empresas")
        self.setup_aba_empresas()
    
    def setup_aba_lista(self):
        """Configura aba de listagem de notas fiscais"""
        
        # Painel de filtros
        filtros_frame = ttk.LabelFrame(self.frame_lista, text="🔍 Filtros", padding="10")
        filtros_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Primeira linha de filtros
        linha1 = ttk.Frame(filtros_frame)
        linha1.pack(fill=tk.X, pady=5)
        
        # Filtro por data
        ttk.Label(linha1, text="Data início:").pack(side=tk.LEFT, padx=(0, 5))
        self.data_inicio = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ttk.Entry(linha1, textvariable=self.data_inicio, width=12).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(linha1, text="Data fim:").pack(side=tk.LEFT, padx=(0, 5))
        self.data_fim = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(linha1, textvariable=self.data_fim, width=12).pack(side=tk.LEFT, padx=(0, 15))
        
        # Filtro por status
        ttk.Label(linha1, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_var = tk.StringVar()
        combo_status = ttk.Combobox(linha1, textvariable=self.status_var, width=15, 
                                   values=["Todos", "autorizada", "rejeitada", "cancelada", "processando"])
        combo_status.set("Todos")
        combo_status.pack(side=tk.LEFT, padx=(0, 15))
        
        # Segunda linha de filtros
        linha2 = ttk.Frame(filtros_frame)
        linha2.pack(fill=tk.X, pady=5)
        
        # Filtro por forma de pagamento
        ttk.Label(linha2, text="Pagamento:").pack(side=tk.LEFT, padx=(0, 5))
        self.pagamento_var = tk.StringVar()
        combo_pagamento = ttk.Combobox(linha2, textvariable=self.pagamento_var, width=15,
                                      values=["Todos", "Dinheiro", "Cartão", "Boleto", "PIX", "Transferência"])
        combo_pagamento.set("Todos")
        combo_pagamento.pack(side=tk.LEFT, padx=(0, 15))
        
        # Filtro por valor
        ttk.Label(linha2, text="Valor mín:").pack(side=tk.LEFT, padx=(0, 5))
        self.valor_min = tk.StringVar()
        ttk.Entry(linha2, textvariable=self.valor_min, width=10).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(linha2, text="Valor máx:").pack(side=tk.LEFT, padx=(0, 5))
        self.valor_max = tk.StringVar()
        ttk.Entry(linha2, textvariable=self.valor_max, width=10).pack(side=tk.LEFT, padx=(0, 15))
        
        # Botões de ação
        ttk.Button(linha2, text="🔍 Filtrar", command=self.aplicar_filtros).pack(side=tk.LEFT, padx=15)
        ttk.Button(linha2, text="🗑️ Limpar", command=self.limpar_filtros).pack(side=tk.LEFT, padx=5)
        ttk.Button(linha2, text="📄 Exportar", command=self.exportar_dados).pack(side=tk.LEFT, padx=5)
        ttk.Button(linha2, text="📁 Importar XMLs", command=self.importar_xmls).pack(side=tk.LEFT, padx=5)
        
        # TreeView para lista de notas fiscais
        self.setup_treeview()
        
        # Painel de informações selecionada
        info_frame = ttk.LabelFrame(self.frame_lista, text="ℹ️ Detalhes da Nota Selecionada", padding="10")
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.info_text = tk.Text(info_frame, height=6, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar_info = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar_info.set)
        self.info_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_info.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_treeview(self):
        """Configura a TreeView para mostrar as notas fiscais"""
        
        # Frame para a TreeView com scrollbar
        tree_frame = ttk.Frame(self.frame_lista)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Colunas da TreeView
        colunas = (
            "chave_acesso", "numero", "data_emissao", "emissor", "destinatario",
            "valor_total", "status_sefaz", "forma_pagamento", "nivel_risco"
        )
        
        self.tree = ttk.Treeview(tree_frame, columns=colunas, show="tree headings", height=15)
        
        # Configurar cabeçalhos
        self.tree.heading("#0", text="ID")
        self.tree.column("#0", width=50, minwidth=50)
        
        self.tree.heading("chave_acesso", text="Chave de Acesso")
        self.tree.column("chave_acesso", width=200, minwidth=150)
        
        self.tree.heading("numero", text="Número")
        self.tree.column("numero", width=80, minwidth=60)
        
        self.tree.heading("data_emissao", text="Data Emissão")
        self.tree.column("data_emissao", width=100, minwidth=80)
        
        self.tree.heading("emissor", text="Emissor")
        self.tree.column("emissor", width=200, minwidth=150)
        
        self.tree.heading("destinatario", text="Destinatário")
        self.tree.column("destinatario", width=200, minwidth=150)
        
        self.tree.heading("valor_total", text="Valor Total")
        self.tree.column("valor_total", width=100, minwidth=80)
        
        self.tree.heading("status_sefaz", text="Status")
        self.tree.column("status_sefaz", width=100, minwidth=80)
        
        self.tree.heading("forma_pagamento", text="Pagamento")
        self.tree.column("forma_pagamento", width=100, minwidth=80)
        
        self.tree.heading("nivel_risco", text="Risco")
        self.tree.column("nivel_risco", width=80, minwidth=60)
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_h = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Posicionamento
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Evento de seleção
        self.tree.bind("<<TreeviewSelect>>", self.on_select_nota)
        
        # Contexto menu (clique direito)
        self.tree.bind("<Button-3>", self.mostrar_menu_contexto)
    
    def setup_aba_estatisticas(self):
        """Configura aba de estatísticas"""
        
        # Cards de resumo
        cards_frame = ttk.Frame(self.frame_stats)
        cards_frame.pack(fill=tk.X, pady=10)
        
        # Card 1: Total de Notas
        card1 = ttk.LabelFrame(cards_frame, text="📊 Total de Notas", padding="10")
        card1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.label_total_notas = ttk.Label(card1, text="0", font=("Arial", 20, "bold"))
        self.label_total_notas.pack()
        
        # Card 2: Valor Total
        card2 = ttk.LabelFrame(cards_frame, text="💰 Valor Total", padding="10")
        card2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.label_valor_total = ttk.Label(card2, text="R$ 0,00", font=("Arial", 20, "bold"))
        self.label_valor_total.pack()
        
        # Card 3: Risco Médio
        card3 = ttk.LabelFrame(cards_frame, text="⚠️ Risco Médio", padding="10")
        card3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.label_risco_medio = ttk.Label(card3, text="0%", font=("Arial", 20, "bold"))
        self.label_risco_medio.pack()
        
        # Gráficos (placeholder para futura implementação)
        graficos_frame = ttk.LabelFrame(self.frame_stats, text="📈 Análises", padding="10")
        graficos_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(graficos_frame, text="🚧 Gráficos interativos em desenvolvimento...", 
                 font=("Arial", 12)).pack(pady=50)
    
    def setup_aba_empresas(self):
        """Configura aba de empresas"""
        
        # Lista de empresas
        empresas_frame = ttk.LabelFrame(self.frame_empresas, text="🏢 Empresas Cadastradas", padding="10")
        empresas_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # TreeView para empresas
        colunas_empresas = ("cnpj", "razao_social", "uf", "total_notas", "valor_total")
        
        self.tree_empresas = ttk.Treeview(empresas_frame, columns=colunas_empresas, show="headings", height=10)
        
        self.tree_empresas.heading("cnpj", text="CNPJ")
        self.tree_empresas.column("cnpj", width=150)
        
        self.tree_empresas.heading("razao_social", text="Razão Social")
        self.tree_empresas.column("razao_social", width=300)
        
        self.tree_empresas.heading("uf", text="UF")
        self.tree_empresas.column("uf", width=50)
        
        self.tree_empresas.heading("total_notas", text="Total NFe")
        self.tree_empresas.column("total_notas", width=100)
        
        self.tree_empresas.heading("valor_total", text="Valor Total")
        self.tree_empresas.column("valor_total", width=150)
        
        scrollbar_empresas = ttk.Scrollbar(empresas_frame, orient=tk.VERTICAL, command=self.tree_empresas.yview)
        self.tree_empresas.configure(yscrollcommand=scrollbar_empresas.set)
        
        self.tree_empresas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_empresas.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Botões para empresas
        btn_frame = ttk.Frame(self.frame_empresas)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="🔄 Atualizar", command=self.carregar_empresas).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="📊 Ver Notas", command=self.filtrar_por_empresa).pack(side=tk.LEFT, padx=5)
    
    # === MÉTODOS DE DADOS ===
    
    def carregar_dados_iniciais(self):
        """Carrega dados iniciais do dashboard"""
        self.aplicar_filtros()
        self.carregar_empresas()
        self.atualizar_estatisticas()
    
    def aplicar_filtros(self):
        """Aplica filtros e atualiza a TreeView"""
       
        filtros = {}
        
        # Filtros de data
        if self.data_inicio.get():
            filtros['data_inicio'] = self.data_inicio.get()
        
        if self.data_fim.get():
            filtros['data_fim'] = self.data_fim.get()
        
        # Filtros de status
        if self.status_var.get() and self.status_var.get() != "Todos":
            filtros['status_sefaz'] = self.status_var.get()

        if self.pagamento_var.get() and self.pagamento_var.get() != "Todos":
            filtros['forma_pagamento'] = self.pagamento_var.get()
        
        # Filtros de valor
        if self.valor_min.get():
            try:
                filtros['valor_min'] = float(self.valor_min.get())
            except ValueError:
                pass

        if self.valor_max.get():
            try:
                filtros['valor_max'] = float(self.valor_max.get())
            except ValueError:
                pass
        
        # CONSULTA COM FILTRO DE EMPRESAS ATIVAS
        self.dados_atuais = self.consultar_nfe_empresas_ativas(filtros)
        
        self.atualizar_treeview()
        self.atualizar_estatisticas()

    def consultar_nfe_empresas_ativas(self, filtros: dict = None) -> list:
        """Consulta NFe apenas de empresas ativas (não excluídas)"""
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                query = """
                SELECT nf.*, e.razao_social    AS nome_emissor,
                        e.cnpj              AS cnpj_emissor,
                        e.uf                AS uf_emissor
                FROM notas_fiscais nf
                INNER JOIN empresas e
                    ON nf.empresa_id = e.id
                LEFT JOIN empresas_detalhadas ed
                    ON e.id = ed.empresa_id
                WHERE COALESCE(ed.ativa, 1) = 1
                AND COALESCE(ed.situacao_cadastral, 'ATIVA') != 'EXCLUIDA'
                """

                params = []

                if filtros:
                    if filtros.get('data_inicio'):
                        query += " AND DATE(nf.data_emissao) >= ?"
                        params.append(filtros['data_inicio'])
                    if filtros.get('data_fim'):
                        query += " AND DATE(nf.data_emissao) <= ?"
                        params.append(filtros['data_fim'])
                    if filtros.get('status_sefaz'):
                        query += " AND nf.status_sefaz = ?"
                        params.append(filtros['status_sefaz'])
                    if filtros.get('forma_pagamento'):
                        query += " AND nf.forma_pagamento = ?"
                        params.append(filtros['forma_pagamento'])
                    if filtros.get('valor_min'):
                        query += " AND nf.valor_total >= ?"
                        params.append(filtros['valor_min'])
                    if filtros.get('valor_max'):
                        query += " AND nf.valor_total <= ?"
                        params.append(filtros['valor_max'])

                query += " ORDER BY nf.data_emissao DESC"
                cursor.execute(query, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logging.error(f"❌ Erro ao consultar NFe de empresas ativas: {e}")
            return []

    def carregar_empresas(self):
        """Carrega lista de empresas ATIVAS na aba Empresas"""
        for item in self.tree_empresas.get_children():
            self.tree_empresas.delete(item)

        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute("""
                SELECT e.cnpj,
                    e.razao_social,
                    e.uf,
                    COUNT(nf.id)             AS total_nfes,
                    COALESCE(SUM(nf.valor_total), 0) AS valor_total
                FROM empresas e
                LEFT JOIN empresas_detalhadas ed
                    ON e.id = ed.empresa_id
                LEFT JOIN notas_fiscais nf
                    ON e.id = nf.empresa_id
                WHERE COALESCE(ed.ativa, 1) = 1
                AND COALESCE(ed.situacao_cadastral, 'ATIVA') != 'EXCLUIDA'
                GROUP BY e.id, e.cnpj, e.razao_social, e.uf
                ORDER BY e.razao_social
                """)

                empresas = cursor.fetchall()
                for emp in empresas:
                    self.tree_empresas.insert('', tk.END, values=(
                        emp['cnpj'],
                        emp['razao_social'],
                        emp['uf'],
                        emp['total_nfes'],
                        f"R$ {emp['valor_total']:,.2f}"
                    ))

        except Exception as e:
            logging.error(f"❌ Erro ao carregar empresas ativas: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar empresas:\n{e}")


    def filtrar_por_empresa(self):
        """Filtra notas por empresa selecionada (apenas ativas)"""
        sel = self.tree_empresas.selection()
        if not sel:
            return

        cnpj = self.tree_empresas.item(sel[0])['values'][0]
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                SELECT nf.*, e.razao_social AS nome_emissor
                FROM notas_fiscais nf
                INNER JOIN empresas e
                    ON nf.empresa_id = e.id
                LEFT JOIN empresas_detalhadas ed
                    ON e.id = ed.empresa_id
                WHERE e.cnpj = ?
                AND COALESCE(ed.ativa, 1) = 1
                AND COALESCE(ed.situacao_cadastral, 'ATIVA') != 'EXCLUIDA'
                ORDER BY nf.data_emissao DESC
                """, (cnpj,))
                self.dados_atuais = [dict(row) for row in cursor.fetchall()]
                self.atualizar_treeview()
                self.atualizar_estatisticas()
        except Exception as e:
            logging.error(f"❌ Erro ao filtrar por empresa: {e}")
            messagebox.showerror("Erro", f"Erro ao filtrar:\n{e}")

    def atualizar_treeview(self):
        """Atualiza dados na TreeView"""
        
        # Limpa dados anteriores
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Adiciona novos dados
        for i, nota in enumerate(self.dados_atuais):
            # Define cor baseada no status
            if nota.get('status_sefaz') == 'autorizada':
                tags = ('autorizada',)
            elif nota.get('status_sefaz') == 'rejeitada':
                tags = ('rejeitada',)
            else:
                tags = ('pendente',)
            
            # Trunca textos longos
            chave = nota.get('chave_acesso', '')
            chave_display = chave[:20] + "..." if len(chave) > 20 else chave
            
            emissor = nota.get('nome_emissor', '') or nota.get('cnpj_emissor', '')
            emissor_display = emissor[:30] + "..." if len(emissor) > 30 else emissor
            
            dest = nota.get('nome_destinatario', '') or nota.get('cnpj_destinatario', '')
            dest_display = dest[:30] + "..." if len(dest) > 30 else dest
            
            self.tree.insert("", tk.END, 
                           text=str(i + 1),
                           values=(
                               chave_display,
                               nota.get('numero', ''),
                               nota.get('data_emissao', ''),
                               emissor_display,
                               dest_display,
                               f"R$ {nota.get('valor_total', 0):,.2f}",
                               nota.get('status_sefaz', ''),
                               nota.get('forma_pagamento', 'Não informado'),
                               nota.get('nivel_risco', '')
                           ),
                           tags=tags)
        
        # Configura cores das tags
        self.tree.tag_configure('autorizada', foreground='green')
        self.tree.tag_configure('rejeitada', foreground='red')
        self.tree.tag_configure('pendente', foreground='orange')
    
    def atualizar_estatisticas(self):
        """Atualiza os cards de estatísticas"""
        
        if self.dados_atuais:
            total_notas = len(self.dados_atuais)
            valor_total = sum(nota.get('valor_total', 0) for nota in self.dados_atuais)
            risco_medio = sum(nota.get('risco_fiscal', 0) for nota in self.dados_atuais) / total_notas if total_notas > 0 else 0
        else:
            total_notas = 0
            valor_total = 0
            risco_medio = 0
        
        self.label_total_notas.config(text=str(total_notas))
        self.label_valor_total.config(text=f"R$ {valor_total:,.2f}")
        self.label_risco_medio.config(text=f"{risco_medio:.1%}")
                 
    def on_select_nota(self, event):
        """Evento chamado quando uma nota é selecionada"""
        
        selection = self.tree.selection()
        if selection:
            try:
                item_index = int(self.tree.item(selection[0])['text']) - 1
                if 0 <= item_index < len(self.dados_atuais):
                    nota = self.dados_atuais[item_index]
                    self.mostrar_detalhes_nota(nota)
            except (ValueError, IndexError):
                pass
    
    def mostrar_detalhes_nota(self, nota: Dict[str, Any]):
        """Mostra detalhes da nota selecionada"""
        
        detalhes = f"""📄 NOTA FISCAL SELECIONADA

🔑 Chave: {nota.get('chave_acesso', 'N/A')}
📊 Número/Série: {nota.get('numero', 'N/A')}/{nota.get('serie', 'N/A')}
📅 Data Emissão: {nota.get('data_emissao', 'N/A')}
📈 Status: {nota.get('status_sefaz', 'N/A').upper()}

💼 EMISSOR:
• CNPJ: {nota.get('cnpj_emissor', 'N/A')}
• Nome: {nota.get('nome_emissor', 'N/A')}
• UF: {nota.get('uf_emissor', 'N/A')}

👤 DESTINATÁRIO:
• CNPJ/CPF: {nota.get('cnpj_destinatario', 'N/A')}
• Nome: {nota.get('nome_destinatario', 'N/A')}
• UF: {nota.get('uf_destinatario', 'N/A')}

💰 VALORES:
• Produtos: R$ {nota.get('valor_produtos', 0):,.2f}
• ICMS: R$ {nota.get('valor_icms', 0):,.2f}
• Total: R$ {nota.get('valor_total', 0):,.2f}

💳 PAGAMENTO: {nota.get('forma_pagamento', 'N/A')}

⚠️ ANÁLISE IA:
• Nível de Risco: {nota.get('nivel_risco', 'baixo').upper()}
• Score: {nota.get('risco_fiscal', 0):.2%}
• Inconsistências: {nota.get('inconsistencias', 0)}
"""
        
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, detalhes)
        self.info_text.config(state=tk.DISABLED)
    
    def limpar_filtros(self):
        """Limpa todos os filtros"""
        self.data_inicio.set((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        self.data_fim.set(datetime.now().strftime("%Y-%m-%d"))
        self.status_var.set("Todos")
        self.pagamento_var.set("Todos")
        self.valor_min.set("")
        self.valor_max.set("")
        self.aplicar_filtros()
    
    def exportar_dados(self):
        """Exporta dados filtrados para CSV"""
        if not self.dados_atuais:
            messagebox.showwarning("Aviso", "Nenhum dado para exportar")
            return
        
        arquivo = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if arquivo:
            try:
                import csv
                with open(arquivo, 'w', newline='', encoding='utf-8') as csvfile:
                    if self.dados_atuais:
                        fieldnames = self.dados_atuais[0].keys()
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(self.dados_atuais)
                
                messagebox.showinfo("Sucesso", f"Dados exportados para: {arquivo}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar: {e}")
    
    def importar_xmls(self):
        """Importa novos arquivos XML"""
        pasta = filedialog.askdirectory(title="Selecione pasta com arquivos XML")
        if pasta:
            self.processar_xmls_thread(pasta)
    
    def processar_xmls_thread(self, pasta_xml):
        """Processa XMLs em thread separada - VERSÃO CORRIGIDA"""
        
        def processar():
            try:
                if NFeProcessorBI is None:
                    messagebox.showerror("Erro", "Módulo de processamento não disponível")
                    return
                
                # Mostra mensagem inicial
                messagebox.showinfo("Processamento", f"Iniciando processamento de XMLs em:\n{pasta_xml}")
                
                # Cria processador e processa
                processor = NFeProcessorBI(pasta_xml, "relatorios_temp")
                estatisticas = processor.processar_pasta()
                
                # Mostra resultado detalhado
                msg = f"""✅ Processamento concluído!

📊 ESTATÍSTICAS:
• Arquivos processados: {estatisticas.get('arquivos_processados', 0)}
• NFe inseridas no banco: {estatisticas.get('nfes_inseridas', 0)}
• Empresas cadastradas: {estatisticas.get('empresas_cadastradas', 0)}
• Análises de IA realizadas: {estatisticas.get('analises_ia_realizadas', 0)}
• Erros encontrados: {estatisticas.get('erros_processamento', 0)}
• Tempo total: {estatisticas.get('tempo_processamento', 0):.1f} segundos

🎯 Os dados foram salvos no banco e já estão disponíveis para consulta!"""
                
                messagebox.showinfo("Sucesso", msg)
                
                # Atualiza dashboard após processamento
                self.after(100, self.aplicar_filtros)
                self.after(200, self.carregar_empresas)
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao processar XMLs:\n\n{str(e)}")
        
        # Executa em thread separada para não travar a interface
        thread = threading.Thread(target=processar, daemon=True)
        thread.start()
    
    def filtrar_por_empresa(self):
        """Filtra notas por empresa selecionada"""
        selection = self.tree_empresas.selection()
        if selection:
            cnpj = self.tree_empresas.item(selection[0])['values'][0]
            
            # Implementa filtro por empresa
            filtros = {'cnpj_emissor': cnpj}
            self.dados_atuais = self.db_manager.consultar_notas_fiscais(filtros)
            self.atualizar_treeview()
            self.atualizar_estatisticas()
            
            # Muda para aba de notas fiscais
            self.notebook.select(0)
            
            messagebox.showinfo("Filtro Aplicado", f"Exibindo notas da empresa:\nCNPJ: {cnpj}")
    
    def mostrar_menu_contexto(self, event):
        """Mostra menu de contexto no clique direito"""
        
        # Identifica item clicado
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
            # Cria menu de contexto
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="📋 Copiar Chave", command=self.copiar_chave)
            menu.add_command(label="📄 Ver XML", command=self.ver_xml_original)
            menu.add_command(label="🔍 Análise IA", command=self.executar_analise_ia)
            menu.add_separator()
            menu.add_command(label="❌ Excluir", command=self.excluir_nota)
            
            menu.tk_popup(event.x_root, event.y_root)
    
    def copiar_chave(self):
        """Copia chave de acesso para clipboard"""
        selection = self.tree.selection()
        if selection:
            # Pega a chave completa dos dados, não da visualização truncada
            item_index = int(self.tree.item(selection[0])['text']) - 1
            if 0 <= item_index < len(self.dados_atuais):
                chave = self.dados_atuais[item_index].get('chave_acesso', '')
                if chave:
                    self.clipboard_clear()
                    self.clipboard_append(chave)
                    messagebox.showinfo("Copiado", f"Chave copiada:\n{chave}")
    
    def ver_xml_original(self):
        """Abre XML original (se disponível)"""
        messagebox.showinfo("Info", "Funcionalidade em desenvolvimento")
    
    def executar_analise_ia(self):
        """Executa nova análise de IA na nota selecionada"""
        messagebox.showinfo("Info", "Re-análise de IA em desenvolvimento")
    
    def excluir_nota(self):
        """Exclui nota selecionada"""
        if messagebox.askyesno("Confirmar", "Deseja excluir esta nota fiscal do banco de dados?"):
            messagebox.showinfo("Info", "Funcionalidade de exclusão em desenvolvimento")

    def setup_aba_lista(self):
        """Configura aba de listagem de notas fiscais - COM FILTRO POR EMPRESA"""
        
        # Painel de filtros
        filtros_frame = ttk.LabelFrame(self.frame_lista, text="🔍 Filtros", padding="10")
        filtros_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Primeira linha de filtros
        linha1 = ttk.Frame(filtros_frame)
        linha1.pack(fill=tk.X, pady=5)
        
        # NOVO: Filtro por empresa
        ttk.Label(linha1, text="Empresa:").pack(side=tk.LEFT, padx=(0, 5))
        self.empresa_var = tk.StringVar()
        self.combo_empresa = ttk.Combobox(linha1, textvariable=self.empresa_var, width=40, state="readonly")
        self.combo_empresa.pack(side=tk.LEFT, padx=(0, 15))
        
        # Filtro por data
        ttk.Label(linha1, text="Data início:").pack(side=tk.LEFT, padx=(0, 5))
        self.data_inicio = tk.StringVar(value=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        ttk.Entry(linha1, textvariable=self.data_inicio, width=12).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(linha1, text="Data fim:").pack(side=tk.LEFT, padx=(0, 5))
        self.data_fim = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        ttk.Entry(linha1, textvariable=self.data_fim, width=12).pack(side=tk.LEFT, padx=(0, 15))
        
        # Segunda linha de filtros
        linha2 = ttk.Frame(filtros_frame)
        linha2.pack(fill=tk.X, pady=5)
        
        # Filtro por status
        ttk.Label(linha2, text="Status:").pack(side=tk.LEFT, padx=(0, 5))
        self.status_var = tk.StringVar()
        combo_status = ttk.Combobox(linha2, textvariable=self.status_var, width=15,
                                values=["Todos", "autorizada", "rejeitada", "cancelada", "processando"])
        combo_status.set("Todos")
        combo_status.pack(side=tk.LEFT, padx=(0, 15))
        
        # Filtro por forma de pagamento
        ttk.Label(linha2, text="Pagamento:").pack(side=tk.LEFT, padx=(0, 5))
        self.pagamento_var = tk.StringVar()
        combo_pagamento = ttk.Combobox(linha2, textvariable=self.pagamento_var, width=15,
                                    values=["Todos", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", 
                                            "PIX", "Boleto Bancário", "Transferência", "Cheque", "Outros"])
        combo_pagamento.set("Todos")
        combo_pagamento.pack(side=tk.LEFT, padx=(0, 15))
        
        # Filtro por valor
        ttk.Label(linha2, text="Valor mín:").pack(side=tk.LEFT, padx=(0, 5))
        self.valor_min = tk.StringVar()
        ttk.Entry(linha2, textvariable=self.valor_min, width=10).pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Label(linha2, text="Valor máx:").pack(side=tk.LEFT, padx=(0, 5))
        self.valor_max = tk.StringVar()
        ttk.Entry(linha2, textvariable=self.valor_max, width=10).pack(side=tk.LEFT, padx=(0, 15))
        
        # Botões de ação
        ttk.Button(linha2, text="🔍 Filtrar", command=self.aplicar_filtros).pack(side=tk.LEFT, padx=15)
        ttk.Button(linha2, text="🗑️ Limpar", command=self.limpar_filtros).pack(side=tk.LEFT, padx=5)
        ttk.Button(linha2, text="📄 Exportar", command=self.exportar_dados).pack(side=tk.LEFT, padx=5)
        ttk.Button(linha2, text="📁 Importar XMLs", command=self.importar_xmls).pack(side=tk.LEFT, padx=5)
        
        # RestanteTreeView (sem alteração)
        self.setup_treeview()
        # ... resto do código

    def carregar_dados_iniciais(self):
        """Carrega dados iniciais do dashboard - COM EMPRESAS"""

        self.aplicar_filtros()
        self.carregar_empresas()
        self.atualizar_estatisticas()

    def carregar_combo_empresas(self):
        """Carrega combo de empresas para filtro"""
        try:
            empresas = self.db_manager.listar_empresas()
            
            # Lista de valores para combo
            valores_combo = ["Todas as Empresas"]
            self.empresas_dict = {"Todas as Empresas": None}
            
            for empresa in empresas:
                nome_display = f"{empresa['razao_social']} ({empresa['cnpj']})"
                valores_combo.append(nome_display)
                self.empresas_dict[nome_display] = empresa['id']
            
            self.combo_empresa['values'] = valores_combo
            self.combo_empresa.set("Todas as Empresas")
            
            logging.info(f"✅ Carregadas {len(empresas)} empresas no filtro")
            
        except Exception as e:
            logging.error(f"Erro ao carregar empresas: {e}")
            self.combo_empresa['values'] = ["Todas as Empresas"]
            self.combo_empresa.set("Todas as Empresas")

    def aplicar_filtros(self):
        """Aplica filtros e atualiza a TreeView - COM FILTRO EMPRESA"""
        
        # Monta dicionário de filtros
        filtros = {}
        
        # NOVO: Filtro por empresa
        empresa_selecionada = self.empresa_var.get()
        if empresa_selecionada and empresa_selecionada != "Todas as Empresas":
            empresa_id = self.empresas_dict.get(empresa_selecionada)
            if empresa_id:
                filtros['empresa_id'] = empresa_id
        
        # Filtros existentes
        if self.data_inicio.get():
            filtros['data_inicio'] = self.data_inicio.get()
        
        if self.data_fim.get():
            filtros['data_fim'] = self.data_fim.get()
        
        if self.status_var.get() and self.status_var.get() != "Todos":
            filtros['status_sefaz'] = self.status_var.get()
        
        if self.pagamento_var.get() and self.pagamento_var.get() != "Todos":
            filtros['forma_pagamento'] = self.pagamento_var.get()
        
        if self.valor_min.get():
            try:
                filtros['valor_min'] = float(self.valor_min.get())
            except ValueError:
                pass
        
        if self.valor_max.get():
            try:
                filtros['valor_max'] = float(self.valor_max.get())
            except ValueError:
                pass
        
        # Consulta dados
        self.dados_atuais = self.db_manager.consultar_notas_fiscais(filtros)
        
        # Atualiza interface
        self.atualizar_treeview()
        self.atualizar_estatisticas()
        
        # Log do filtro aplicado
        if filtros:
            filtros_str = ", ".join([f"{k}: {v}" for k, v in filtros.items()])
            logging.info(f"🔍 Filtros aplicados: {filtros_str}")
            logging.info(f"📊 Resultados encontrados: {len(self.dados_atuais)}")

    def limpar_filtros(self):
        """Limpa todos os filtros - INCLUINDO EMPRESA"""
        self.empresa_var.set("Todas as Empresas")
        self.data_inicio.set((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
        self.data_fim.set(datetime.now().strftime("%Y-%m-%d"))
        self.status_var.set("Todos")
        self.pagamento_var.set("Todos")
        self.valor_min.set("")
        self.valor_max.set("")
        self.aplicar_filtros()

    def setup_aba_empresas(self):
        """Configura aba de gestão de empresas - VERSÃO COMPLETA"""
        
        # Frame principal dividido
        main_frame = ttk.Frame(self.frame_empresas)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame esquerdo - Lista de empresas
        left_frame = ttk.LabelFrame(main_frame, text="🏢 Empresas Cadastradas", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # TreeView para empresas
        colunas_empresas = ("cnpj", "razao_social", "nome_fantasia", "uf", "total_notas", "valor_total", "criado_em")
        
        self.tree_empresas = ttk.Treeview(left_frame, columns=colunas_empresas, show="headings", height=12)
        
        # Configurar colunas
        self.tree_empresas.heading("cnpj", text="CNPJ")
        self.tree_empresas.column("cnpj", width=120, minwidth=100)
        
        self.tree_empresas.heading("razao_social", text="Razão Social")
        self.tree_empresas.column("razao_social", width=250, minwidth=200)
        
        self.tree_empresas.heading("nome_fantasia", text="Nome Fantasia")
        self.tree_empresas.column("nome_fantasia", width=200, minwidth=150)
        
        self.tree_empresas.heading("uf", text="UF")
        self.tree_empresas.column("uf", width=40, minwidth=40)
        
        self.tree_empresas.heading("total_notas", text="Total NFe")
        self.tree_empresas.column("total_notas", width=80, minwidth=70)
        
        self.tree_empresas.heading("valor_total", text="Valor Total")
        self.tree_empresas.column("valor_total", width=120, minwidth=100)
        
        self.tree_empresas.heading("criado_em", text="Cadastrado em")
        self.tree_empresas.column("criado_em", width=100, minwidth=90)
        
        # Scrollbars para TreeView
        scrollbar_empresas_v = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree_empresas.yview)
        scrollbar_empresas_h = ttk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=self.tree_empresas.xview)
        self.tree_empresas.configure(yscrollcommand=scrollbar_empresas_v.set, xscrollcommand=scrollbar_empresas_h.set)
        
        self.tree_empresas.grid(row=0, column=0, sticky="nsew")
        scrollbar_empresas_v.grid(row=0, column=1, sticky="ns")
        scrollbar_empresas_h.grid(row=1, column=0, sticky="ew")
        
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Botões de ação
        btn_frame_empresas = ttk.Frame(left_frame)
        btn_frame_empresas.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ttk.Button(btn_frame_empresas, text="🔄 Atualizar Lista", command=self.carregar_empresas).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_empresas, text="📊 Ver Notas", command=self.filtrar_por_empresa).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_empresas, text="📈 Estatísticas", command=self.mostrar_stats_empresa).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_empresas, text="🗑️ Excluir", command=self.excluir_empresa).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_empresas, text="🛠️ Gestão Completa", command=self.abrir_gestao_completa).pack(side=tk.LEFT, padx=5)

        # Frame direito - Detalhes e formulário
        right_frame = ttk.LabelFrame(main_frame, text="ℹ️ Detalhes da Empresa", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Área de detalhes
        self.empresa_detalhes = tk.Text(right_frame, width=40, height=20, wrap=tk.WORD, state=tk.DISABLED)
        scrollbar_detalhes = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.empresa_detalhes.yview)
        self.empresa_detalhes.configure(yscrollcommand=scrollbar_detalhes.set)
        
        self.empresa_detalhes.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_detalhes.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Evento de seleção
        self.tree_empresas.bind("<<TreeviewSelect>>", self.on_select_empresa)

    def abrir_gestao_completa(self):
        """Abre gestão completa de empresas"""
        from ui.gestao_empresas import abrir_gestao_empresas
        abrir_gestao_empresas(self, self.db_manager)


    def carregar_empresas(self):
        """Carrega empresas no dashboard"""
        for item in self.tree_empresas.get_children():
            self.tree_empresas.delete(item)
        
        try:
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row  
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT 
                    e.cnpj,
                    e.razao_social, 
                    e.uf,
                    COUNT(nf.id) as total_nfes,
                    COALESCE(SUM(nf.valor_total), 0) as valor_total
                FROM empresas e
                LEFT JOIN empresas_detalhadas ed ON e.id = ed.empresa_id  
                LEFT JOIN notas_fiscais nf ON e.id = nf.empresa_id
                WHERE COALESCE(ed.situacao_cadastral, 'ATIVA') != 'EXCLUIDA'
                GROUP BY e.id, e.cnpj, e.razao_social, e.uf
                ORDER BY e.razao_social
                """)
                
                empresas = cursor.fetchall()
                
                for empresa in empresas:
                    self.tree_empresas.insert('', tk.END, values=(
                        empresa['cnpj'],
                        empresa['razao_social'],
                        empresa['uf'],
                        empresa['total_nfes'], 
                        f"R$ {empresa['valor_total']:,.2f}"
                    ))
                    
        except Exception as e:
            logging.error(f"❌ Erro ao carregar empresas: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar empresas:\n{e}")


    def on_select_empresa(self, event):
        """Evento quando empresa é selecionada"""
        
        selection = self.tree_empresas.selection()
        if not selection:
            return
        
        try:
            # Pega dados da empresa selecionada
            item = self.tree_empresas.item(selection[0])
            cnpj = item['values'][0]
            
            # Busca detalhes da empresa no banco
            empresas = self.db_manager.listar_empresas()
            empresa_detalhada = next((emp for emp in empresas if emp['cnpj'] == cnpj), None)
            
            if empresa_detalhada:
                self.mostrar_detalhes_empresa(empresa_detalhada)
                
        except Exception as e:
            logging.error(f"Erro ao selecionar empresa: {e}")

    def mostrar_detalhes_empresa(self, empresa: Dict[str, Any]):
        """Mostra detalhes da empresa selecionada"""
        
        try:
            # Calcula estatísticas específicas da empresa
            stats_empresa = self.db_manager.obter_estatisticas(empresa['id'])
            
            detalhes = f"""🏢 EMPRESA SELECIONADA

    📋 DADOS CADASTRAIS:
    • CNPJ: {empresa.get('cnpj', 'N/A')}
    • Razão Social: {empresa.get('razao_social', 'N/A')}
    • Nome Fantasia: {empresa.get('nome_fantasia', 'N/A') or 'Não informado'}
    • UF: {empresa.get('uf', 'N/A')}
    • Cadastrado em: {empresa.get('criado_em', 'N/A')[:10] if empresa.get('criado_em') else 'N/A'}

    📊 ESTATÍSTICAS:
    • Total de NFe: {stats_empresa.get('total_notas', 0):,}
    • Valor Total: R$ {stats_empresa.get('valor_total', 0):,.2f}
    • Risco Médio: {stats_empresa.get('risco_medio', 0):.1%}

    📈 STATUS DAS NOTAS:"""

            # Status das notas
            status_counts = stats_empresa.get('status_counts', {})
            for status, count in status_counts.items():
                detalhes += f"\n• {status.title()}: {count}"
            
            # Mostra no text widget
            self.empresa_detalhes.config(state=tk.NORMAL)
            self.empresa_detalhes.delete(1.0, tk.END)
            self.empresa_detalhes.insert(1.0, detalhes)
            self.empresa_detalhes.config(state=tk.DISABLED)
            
        except Exception as e:
            logging.error(f"Erro ao mostrar detalhes da empresa: {e}")

    def mostrar_stats_empresa(self):
        """Mostra estatísticas detalhadas da empresa selecionada"""
        
        selection = self.tree_empresas.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma empresa primeiro")
            return
        
        try:
            item = self.tree_empresas.item(selection[0])
            nome_empresa = item['values'][1]  # Razão social
            
            messagebox.showinfo("Estatísticas Detalhadas", 
                            f"Funcionalidade de estatísticas detalhadas em desenvolvimento\n\n"
                            f"Empresa: {nome_empresa}")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exibir estatísticas: {e}")

    def excluir_empresa(self):
        """Exclui empresa selecionada (com confirmação)"""
        
        selection = self.tree_empresas.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma empresa para excluir")
            return
        
        try:
            item = self.tree_empresas.item(selection[0])
            nome_empresa = item['values'][1]
            total_notas = item['values'][4]
            
            # Confirmação
            resposta = messagebox.askyesno(
                "Confirmar Exclusão",
                f"Deseja realmente excluir a empresa?\n\n"
                f"Empresa: {nome_empresa}\n"
                f"Total de NFe: {total_notas}\n\n"
                f"⚠️ Esta ação NÃO pode ser desfeita!\n"
                f"⚠️ Todas as NFe desta empresa também serão excluídas!"
            )
            
            if resposta:
                messagebox.showinfo("Exclusão", 
                                "Funcionalidade de exclusão em desenvolvimento\n\n"
                                "Por segurança, esta funcionalidade será implementada "
                                "com controles adicionais de segurança.")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir empresa: {e}")