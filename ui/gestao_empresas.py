# ui/gestao_empresas.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from typing import Optional
import threading
import sqlite3

from empresa.manager import GerenciadorEmpresas, EmpresaCompleta
from database.models import DatabaseManager

class GestaoEmpresasGUI:
    """Interface gráfica para gestão completa de empresas"""
    
    def __init__(self, parent, db_manager: DatabaseManager):
        self.parent = parent
        self.db_manager = db_manager
        self.gerenciador = GerenciadorEmpresas(db_manager)
        
        self.window = tk.Toplevel(parent)
        self.window.title("🏢 Gestão de Empresas - CRUD Completo")
        self.window.geometry("1200x800")
        
        self.empresa_selecionada = None
        self.setup_interface()
        self.carregar_empresas()
    
    def setup_interface(self):
        """Configura interface principal"""
        
        # Painel principal
        main_paned = ttk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Painel esquerdo - Lista
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)
        
        # Painel direito - Detalhes/Formulário
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        self.setup_painel_lista(left_frame)
        self.setup_painel_detalhes(right_frame)
    
    def setup_painel_lista(self, parent):
        """Painel com lista de empresas"""
        
        # Toolbar
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(toolbar, text="➕ Nova Empresa", 
                  command=self.nova_empresa).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="✏️ Editar", 
                  command=self.editar_empresa).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🗑️ Excluir", 
                  command=self.excluir_empresa).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(toolbar, text="📥 Importar", 
                  command=self.importar_empresas).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="📤 Exportar", 
                  command=self.exportar_empresas).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="🔄 Atualizar", 
                  command=self.carregar_empresas).pack(side=tk.LEFT, padx=5)
        
        # Filtros
        filtros_frame = ttk.LabelFrame(parent, text="🔍 Filtros", padding="10")
        filtros_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(filtros_frame, text="UF:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.filtro_uf = ttk.Combobox(filtros_frame, width=10,
            values=["Todos"] + [f"{uf}" for uf in "AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()])
        self.filtro_uf.set("Todos")
        self.filtro_uf.grid(row=0, column=1, padx=5)
        
        ttk.Label(filtros_frame, text="Status:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.filtro_status = ttk.Combobox(filtros_frame, width=15,
            values=["Todos", "ATIVA", "INATIVA", "SUSPENSA"])
        self.filtro_status.set("Todos")
        self.filtro_status.grid(row=0, column=3, padx=5)
        
        ttk.Button(filtros_frame, text="Filtrar", 
                  command=self.aplicar_filtros).grid(row=0, column=4, padx=10)
        
        # TreeView
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("cnpj", "razao_social", "uf", "cidade", "situacao", "nfes", "valor")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Configurar colunas
        self.tree.heading("cnpj", text="CNPJ")
        self.tree.column("cnpj", width=120, minwidth=100)
        
        self.tree.heading("razao_social", text="Razão Social")
        self.tree.column("razao_social", width=250, minwidth=200)
        
        self.tree.heading("uf", text="UF")
        self.tree.column("uf", width=40, minwidth=40)
        
        self.tree.heading("cidade", text="Cidade")
        self.tree.column("cidade", width=120, minwidth=100)
        
        self.tree.heading("situacao", text="Situação")
        self.tree.column("situacao", width=80, minwidth=70)
        
        self.tree.heading("nfes", text="NFe")
        self.tree.column("nfes", width=60, minwidth=50)
        
        self.tree.heading("valor", text="Valor Total")
        self.tree.column("valor", width=100, minwidth=80)
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_h = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_v.grid(row=0, column=1, sticky="ns")
        scrollbar_h.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Eventos
        self.tree.bind("<<TreeviewSelect>>", self.on_empresa_select)
        self.tree.bind("<Double-1>", lambda e: self.editar_empresa())
    
    def setup_painel_detalhes(self, parent):
        """Painel com detalhes da empresa selecionada"""
        
        # Notebook para abas
        self.notebook_detalhes = ttk.Notebook(parent)
        self.notebook_detalhes.pack(fill=tk.BOTH, expand=True)
        
        # Aba 1: Dados Básicos
        self.tab_dados = ttk.Frame(self.notebook_detalhes)
        self.notebook_detalhes.add(self.tab_dados, text="📋 Dados")
        
        # Aba 2: Estatísticas
        self.tab_stats = ttk.Frame(self.notebook_detalhes)
        self.notebook_detalhes.add(self.tab_stats, text="📊 Estatísticas")
        
        # Aba 3: Histórico
        self.tab_historico = ttk.Frame(self.notebook_detalhes)
        self.notebook_detalhes.add(self.tab_historico, text="📜 Histórico")
        
        self.setup_aba_dados()
        self.setup_aba_estatisticas()
        self.setup_aba_historico()
    
    def setup_aba_dados(self):
        """Aba com dados da empresa"""
        
        # Área de scroll
        canvas = tk.Canvas(self.tab_dados)
        scrollbar = ttk.Scrollbar(self.tab_dados, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Campos de dados
        self.dados_widgets = {}
        
        # Dados básicos
        grupo_basico = ttk.LabelFrame(scrollable_frame, text="Dados Básicos", padding="10")
        grupo_basico.pack(fill=tk.X, pady=5)
        
        self._criar_campo(grupo_basico, "CNPJ:", "cnpj", 0)
        self._criar_campo(grupo_basico, "Razão Social:", "razao_social", 1)
        self._criar_campo(grupo_basico, "Nome Fantasia:", "nome_fantasia", 2)
        self._criar_campo(grupo_basico, "UF:", "uf", 3, width=5)
        
        # Contato
        grupo_contato = ttk.LabelFrame(scrollable_frame, text="Contato", padding="10")
        grupo_contato.pack(fill=tk.X, pady=5)
        
        self._criar_campo(grupo_contato, "Cidade:", "cidade", 0)
        self._criar_campo(grupo_contato, "Endereço:", "endereco", 1)
        self._criar_campo(grupo_contato, "CEP:", "cep", 2)
        self._criar_campo(grupo_contato, "Telefone:", "telefone", 3)
        self._criar_campo(grupo_contato, "Email:", "email", 4)
        
        # Tributário
        grupo_tributario = ttk.LabelFrame(scrollable_frame, text="Dados Tributários", padding="10")
        grupo_tributario.pack(fill=tk.X, pady=5)
        
        self._criar_campo(grupo_tributario, "Inscrição Estadual:", "inscricao_estadual", 0)
        self._criar_campo(grupo_tributario, "Regime Tributário:", "regime_tributario", 1)
        self._criar_campo(grupo_tributario, "Atividade Principal:", "atividade_principal", 2)
        
        # Status e configurações
        grupo_config = ttk.LabelFrame(scrollable_frame, text="Configurações", padding="10")
        grupo_config.pack(fill=tk.X, pady=5)
        
        self._criar_combo(grupo_config, "Situação:", "situacao_cadastral", 0,
                         values=["ATIVA", "INATIVA", "SUSPENSA", "BAIXADA"])
        self._criar_check(grupo_config, "Ativa no sistema", "ativa", 1)
        self._criar_check(grupo_config, "Monitoramento", "monitoramento", 2)
        self._criar_check(grupo_config, "Alertas por email", "alertas", 3)
    
    def setup_aba_estatisticas(self):
        """Aba com estatísticas da empresa"""
        
        self.stats_text = tk.Text(self.tab_stats, wrap=tk.WORD, state=tk.DISABLED,
                                 font=("Consolas", 10))
        stats_scroll = ttk.Scrollbar(self.tab_stats, orient=tk.VERTICAL, 
                                    command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scroll.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_aba_historico(self):
        """Aba com histórico de alterações"""
        
        # TreeView para histórico
        hist_columns = ("data", "campo", "anterior", "novo", "usuario")
        self.tree_historico = ttk.Treeview(self.tab_historico, columns=hist_columns, 
                                          show="headings", height=10)
        
        self.tree_historico.heading("data", text="Data/Hora")
        self.tree_historico.column("data", width=150)
        
        self.tree_historico.heading("campo", text="Campo")
        self.tree_historico.column("campo", width=100)
        
        self.tree_historico.heading("anterior", text="Valor Anterior")
        self.tree_historico.column("anterior", width=150)
        
        self.tree_historico.heading("novo", text="Valor Novo")
        self.tree_historico.column("novo", width=150)
        
        self.tree_historico.heading("usuario", text="Usuário")
        self.tree_historico.column("usuario", width=100)
        
        hist_scroll = ttk.Scrollbar(self.tab_historico, orient=tk.VERTICAL, 
                                   command=self.tree_historico.yview)
        self.tree_historico.configure(yscrollcommand=hist_scroll.set)
        
        self.tree_historico.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        hist_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _criar_campo(self, parent, label, campo, row, width=None):
        """Cria campo de entrada"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
        entry = ttk.Entry(parent, width=width or 50)
        entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        self.dados_widgets[campo] = entry
    
    def _criar_combo(self, parent, label, campo, row, values):
        """Cria combobox"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
        combo = ttk.Combobox(parent, values=values, width=47)
        combo.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        self.dados_widgets[campo] = combo
    
    def _criar_check(self, parent, label, campo, row):
        """Cria checkbox"""
        var = tk.BooleanVar()
        check = ttk.Checkbutton(parent, text=label, variable=var)
        check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=2)
        self.dados_widgets[campo] = var
    
    # === EVENTOS E AÇÕES ===
    
    def carregar_empresas(self):
        """Carrega lista de empresas"""
        try:
            
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # ✅ LEFT JOIN para não perder empresas sem detalhes
            with sqlite3.connect(self.db_manager.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT 
                    e.cnpj,
                    e.razao_social,
                    e.uf,
                    COALESCE(ed.cidade, '') as cidade,
                    COALESCE(ed.situacao_cadastral, 'ATIVA') as situacao_cadastral,
                    COUNT(nf.id) as total_nfes,
                    COALESCE(SUM(nf.valor_total), 0) as valor_total_movimentado
                FROM empresas e
                LEFT JOIN empresas_detalhadas ed ON e.id = ed.empresa_id
                LEFT JOIN notas_fiscais nf ON e.id = nf.empresa_id
                WHERE COALESCE(ed.situacao_cadastral, 'ATIVA') != 'EXCLUIDA'
                GROUP BY e.id, e.cnpj, e.razao_social, e.uf
                ORDER BY e.razao_social
                """)
                
                empresas = cursor.fetchall()
                
                for emp in empresas:
                    self.tree.insert('', tk.END, values=(
                        emp['cnpj'] or '',
                        emp['razao_social'] or '',
                        emp['uf'] or '',
                        emp['cidade'] or '',
                        emp['situacao_cadastral'] or 'ATIVA',
                        emp['total_nfes'] or 0,
                        f"R$ {emp['valor_total_movimentado']:,.2f}"
                    ))            
            self.empresa_selecionada = None
            self.limpar_detalhes()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar empresas:\n{e}")

    
    def aplicar_filtros(self):
        """Aplica filtros na lista"""
        try:
            filtros = {}
            
            if self.filtro_uf.get() != "Todos":
                filtros['uf'] = self.filtro_uf.get()
            
            if self.filtro_status.get() != "Todos":
                filtros['situacao_cadastral'] = self.filtro_status.get()
            
            # Limpa árvore
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # Carrega com filtros
            empresas = self.gerenciador.listar_empresas_completas(filtros)
            
            for emp in empresas:
                self.tree.insert("", tk.END, values=(
                    emp.cnpj, emp.razao_social, emp.uf, emp.cidade,
                    emp.situacao_cadastral, emp.total_nfes,
                    f"R$ {emp.valor_total_movimentado:,.2f}"
                ))
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao aplicar filtros: {e}")
    
    def on_empresa_select(self, event):
        """Evento ao selecionar empresa"""
        selection = self.tree.selection()
        if not selection:
            return
        
        try:
            # Pega CNPJ da empresa selecionada
            item = self.tree.item(selection[0])
            cnpj = item['values'][0]
            
            # Busca empresa completa
            empresas = self.gerenciador.listar_empresas_completas()
            self.empresa_selecionada = next((emp for emp in empresas if emp.cnpj == cnpj), None)
            
            if self.empresa_selecionada:
                self.mostrar_detalhes_empresa()
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar detalhes: {e}")
    
    def mostrar_detalhes_empresa(self):
        """Mostra detalhes da empresa selecionada"""
        if not self.empresa_selecionada:
            return
        
        emp = self.empresa_selecionada
        
        # Preencher campos
        campos_map = {
            'cnpj': emp.cnpj,
            'razao_social': emp.razao_social,
            'nome_fantasia': emp.nome_fantasia or '',
            'uf': emp.uf,
            'cidade': emp.cidade or '',
            'endereco': emp.endereco or '',
            'cep': emp.cep or '',
            'telefone': emp.telefone or '',
            'email': emp.email or '',
            'inscricao_estadual': emp.inscricao_estadual or '',
            'regime_tributario': emp.regime_tributario or '',
            'atividade_principal': emp.atividade_principal or '',
            'situacao_cadastral': emp.situacao_cadastral or 'ATIVA'
        }
        
        for campo, valor in campos_map.items():
            if campo in self.dados_widgets:
                widget = self.dados_widgets[campo]
                if isinstance(widget, tk.BooleanVar):
                    widget.set(valor)
                else:
                    widget.delete(0, tk.END)
                    widget.insert(0, valor)
        
        # Checkboxes
        if 'ativa' in self.dados_widgets:
            self.dados_widgets['ativa'].set(getattr(emp, 'ativa', True))
        if 'monitoramento' in self.dados_widgets:
            self.dados_widgets['monitoramento'].set(getattr(emp, 'monitoramento', True))
        if 'alertas' in self.dados_widgets:
            self.dados_widgets['alertas'].set(getattr(emp, 'alertas', True))
        
        # Atualizar estatísticas
        self.mostrar_estatisticas(emp)
        
        # Carregar histórico
        self.carregar_historico(emp.id)
    
    def mostrar_estatisticas(self, empresa: EmpresaCompleta):
        """Mostra estatísticas da empresa"""
        stats_text = f"""📊 ESTATÍSTICAS DA EMPRESA

🏢 {empresa.razao_social}
📋 CNPJ: {empresa.cnpj}

📈 MOVIMENTAÇÃO:
• Total de NFe processadas: {empresa.total_nfes:,}
• Valor total movimentado: R$ {empresa.valor_total_movimentado:,.2f}
• Último processamento: {empresa.ultimo_processamento or 'Nunca'}

📅 CADASTRO:
• Criado em: {empresa.criado_em[:10] if empresa.criado_em else 'N/A'}
• Atualizado em: {empresa.atualizado_em[:10] if empresa.atualizado_em else 'N/A'}
• Criado por: {empresa.criado_por or 'Sistema'}

⚙️ CONFIGURAÇÕES:
• Status: {'🟢 Ativa' if empresa.ativa else '🔴 Inativa'}
• Monitoramento: {'🟢 Ativo' if empresa.monitoramento else '🔴 Inativo'}
• Alertas: {'🟢 Ativo' if empresa.alertas else '🔴 Inativo'}

🏛️ DADOS OFICIAIS:
• UF: {empresa.uf}
• Cidade: {empresa.cidade or 'Não informado'}
• Situação: {empresa.situacao_cadastral or 'Não informado'}
• Regime: {empresa.regime_tributario or 'Não informado'}
"""
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(1.0, stats_text)
        self.stats_text.config(state=tk.DISABLED)
    
    def carregar_historico(self, empresa_id: int):
        """Carrega histórico de alterações"""
        try:
            # Limpa histórico anterior
            for item in self.tree_historico.get_children():
                self.tree_historico.delete(item)
            
            # Carrega histórico
            historico = self.gerenciador.obter_historico_alteracoes(empresa_id)
            
            for alt in historico:
                data_formatada = alt['alterado_em'][:19].replace('T', ' ')
                
                self.tree_historico.insert("", tk.END, values=(
                    data_formatada,
                    alt['campo_alterado'],
                    alt['valor_anterior'][:50] + "..." if len(alt['valor_anterior']) > 50 else alt['valor_anterior'],
                    alt['valor_novo'][:50] + "..." if len(alt['valor_novo']) > 50 else alt['valor_novo'],
                    alt['alterado_por']
                ))
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar histórico: {e}")
    
    def limpar_detalhes(self):
        """Limpa área de detalhes"""
        for widget in self.dados_widgets.values():
            if isinstance(widget, tk.BooleanVar):
                widget.set(False)
            else:
                widget.delete(0, tk.END)
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.config(state=tk.DISABLED)
        
        for item in self.tree_historico.get_children():
            self.tree_historico.delete(item)
    
    def nova_empresa(self):
        """Abre formulário para nova empresa"""
        FormularioEmpresaDialog(self.window, self.gerenciador, callback=self.carregar_empresas)
    
    def editar_empresa(self):
        """Edita empresa selecionada"""
        if not self.empresa_selecionada:
            messagebox.showwarning("Aviso", "Selecione uma empresa para editar")
            return
        
        FormularioEmpresaDialog(self.window, self.gerenciador, 
                               empresa=self.empresa_selecionada, 
                               callback=self.carregar_empresas)
    
    def excluir_empresa(self):
        """Exclui empresa selecionada"""
        if not self.empresa_selecionada:
            messagebox.showwarning("Aviso", "Selecione uma empresa para excluir")
            return
        
        empresa = self.empresa_selecionada
        
        resposta = messagebox.askyesnocancel(
            "Confirmar Exclusão",
            f"Deseja excluir a empresa?\n\n"
            f"Empresa: {empresa.razao_social}\n"
            f"CNPJ: {empresa.cnpj}\n"
            f"Total de NFe: {empresa.total_nfes}\n\n"
            f"⚠️ Esta ação NÃO pode ser desfeita!\n"
            f"⚠️ Todas as NFe desta empresa também serão excluídas!"
        )
        
        if resposta:
            try:
                self.gerenciador.excluir_empresa(empresa.id, "Usuário GUI")
                messagebox.showinfo("Sucesso", "Empresa excluída com sucesso!")
                self.carregar_empresas()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao excluir empresa:\n\n{e}")
    # No método de exclusão da interface (gestao_empresas.py)
    def excluir_empresa_selecionada(self):
        try:
            # Liberar conexões antes da exclusão
            self.gerenciador.liberar_conexoes_db()
            
            # Prosseguir com exclusão
            resultado = self.gerenciador.excluir_empresa(empresa_id, "Interface")
            
            if resultado:
                messagebox.showinfo("Sucesso", "Empresa excluída com sucesso!")
                self.carregar_empresas()  # Recarregar lista
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao excluir empresa:\n{e}")

    def importar_empresas(self):
        """Importa empresas de arquivo"""
        arquivo = filedialog.askopenfilename(
            title="Importar Empresas",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")]
        )
        
        if arquivo:
            try:
                def importar():
                    resultado = self.gerenciador.importar_empresas(arquivo, "Import GUI")
                    
                    msg = f"""Importação concluída!

Sucessos: {resultado['sucesso']}
Erros: {resultado['erro']}
Duplicadas: {resultado['duplicadas']}"""
                    
                    self.window.after(0, lambda: messagebox.showinfo("Import Concluído", msg))
                    self.window.after(0, self.carregar_empresas)
                
                # Executa em thread para não travar interface
                threading.Thread(target=importar, daemon=True).start()
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro na importação: {e}")
    
    def exportar_empresas(self):
        """Exporta lista de empresas"""
        arquivo = filedialog.asksaveasfilename(
            title="Exportar Empresas",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")]
        )
        
        if arquivo:
            try:
                formato = 'json' if arquivo.endswith('.json') else 'csv'
                conteudo = self.gerenciador.exportar_empresas(formato)
                
                with open(arquivo, 'w', encoding='utf-8') as f:
                    f.write(conteudo)
                
                messagebox.showinfo("Sucesso", f"Empresas exportadas para:\n{arquivo}")
                
            except Exception as e:
                messagebox.showerror("Erro", f"Erro na exportação: {e}")

class FormularioEmpresaDialog:
    """Dialog para criar/editar empresa"""
    
    def __init__(self, parent, gerenciador: GerenciadorEmpresas, 
                 empresa: Optional[EmpresaCompleta] = None, callback=None):
        self.gerenciador = gerenciador
        self.empresa = empresa
        self.callback = callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("✏️ Editar Empresa" if empresa else "➕ Nova Empresa")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.setup_formulario()
        
        if empresa:
            self.preencher_formulario()
    
    def setup_formulario(self):
        """Configura formulário"""
        
        # Área de scroll
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        self.form_frame = ttk.Frame(canvas)
        
        self.form_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.form_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Campos do formulário
        self.fields = {}
        
        # Grupo: Dados Obrigatórios
        grupo_obrig = ttk.LabelFrame(self.form_frame, text="* Campos Obrigatórios", padding="10")
        grupo_obrig.pack(fill=tk.X, pady=5)
        
        self._create_field(grupo_obrig, "CNPJ *:", "cnpj", 0)
        self._create_field(grupo_obrig, "Razão Social *:", "razao_social", 1)
        self._create_field(grupo_obrig, "UF *:", "uf", 2, width=5)
        
        # Botão de consulta CNPJ
        ttk.Button(grupo_obrig, text="🔍 Consultar RF", 
                  command=self.consultar_receita_federal).grid(row=0, column=2, padx=10)
        
        # Grupo: Dados Opcionais
        grupo_opc = ttk.LabelFrame(self.form_frame, text="Dados Opcionais", padding="10")
        grupo_opc.pack(fill=tk.X, pady=5)
        
        self._create_field(grupo_opc, "Nome Fantasia:", "nome_fantasia", 0)
        self._create_field(grupo_opc, "Cidade:", "cidade", 1)
        self._create_field(grupo_opc, "Endereço:", "endereco", 2)
        self._create_field(grupo_opc, "CEP:", "cep", 3)
        self._create_field(grupo_opc, "Telefone:", "telefone", 4)
        self._create_field(grupo_opc, "Email:", "email", 5)
        self._create_field(grupo_opc, "Inscrição Estadual:", "inscricao_estadual", 6)
        self._create_field(grupo_opc, "Regime Tributário:", "regime_tributario", 7)
        
        # Grupo: Configurações
        grupo_config = ttk.LabelFrame(self.form_frame, text="Configurações", padding="10")
        grupo_config.pack(fill=tk.X, pady=5)
        
        self._create_combo(grupo_config, "Situação:", "situacao_cadastral", 0,
                          ["ATIVA", "INATIVA", "SUSPENSA", "BAIXADA"])
        
        self.ativa_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(grupo_config, text="Ativa no sistema", variable=self.ativa_var).grid(
            row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Botões
        btn_frame = ttk.Frame(self.form_frame)
        btn_frame.pack(fill=tk.X, pady=20)
        
        ttk.Button(btn_frame, text="💾 Salvar", 
                  command=self.salvar).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="❌ Cancelar", 
                  command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _create_field(self, parent, label, field, row, width=None):
        """Cria campo de entrada"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
        entry = ttk.Entry(parent, width=width or 40)
        entry.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        self.fields[field] = entry
    
    def _create_combo(self, parent, label, field, row, values):
        """Cria combobox"""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, pady=2)
        combo = ttk.Combobox(parent, values=values, width=37)
        combo.set(values[0])
        combo.grid(row=row, column=1, sticky=tk.W, pady=2, padx=(10, 0))
        self.fields[field] = combo
    
    def preencher_formulario(self):
        """Preenche formulário com dados da empresa"""
        if not self.empresa:
            return
        
        campos = {
            'cnpj': self.empresa.cnpj,
            'razao_social': self.empresa.razao_social,
            'nome_fantasia': self.empresa.nome_fantasia or '',
            'uf': self.empresa.uf,
            'cidade': self.empresa.cidade or '',
            'endereco': self.empresa.endereco or '',
            'cep': self.empresa.cep or '',
            'telefone': self.empresa.telefone or '',
            'email': self.empresa.email or '',
            'inscricao_estadual': self.empresa.inscricao_estadual or '',
            'regime_tributario': self.empresa.regime_tributario or '',
            'situacao_cadastral': self.empresa.situacao_cadastral or 'ATIVA'
        }
        
        for campo, valor in campos.items():
            if campo in self.fields:
                self.fields[campo].delete(0, tk.END)
                self.fields[campo].insert(0, valor)
        
        self.ativa_var.set(getattr(self.empresa, 'ativa', True))
    
    def consultar_receita_federal(self):
        """Consulta dados na Receita Federal"""
        cnpj = self.fields['cnpj'].get().strip()
        if not cnpj:
            messagebox.showwarning("Aviso", "Informe o CNPJ primeiro")
            return
        
        def consultar():
            try:
                cnpj_limpo = ''.join(filter(str.isdigit, cnpj))
                if len(cnpj_limpo) != 14:
                    self.dialog.after(0, lambda: messagebox.showerror("Erro", "CNPJ inválido"))
                    return
                
                # Usa método do gerenciador
                dados = self.gerenciador._consultar_receita_federal(cnpj_limpo)
                
                if dados:
                    # Preenche campos automaticamente
                    def preencher():
                        for campo, valor in dados.items():
                            if campo in self.fields and valor:
                                self.fields[campo].delete(0, tk.END)
                                self.fields[campo].insert(0, valor)
                        
                        messagebox.showinfo("Sucesso", "Dados consultados na Receita Federal!")
                    
                    self.dialog.after(0, preencher)
                else:
                    self.dialog.after(0, lambda: messagebox.showwarning("Aviso", 
                        "Não foi possível consultar os dados.\nVerifique o CNPJ ou tente novamente."))
                    
            except Exception as e:
                self.dialog.after(0, lambda: messagebox.showerror("Erro", f"Erro na consulta: {e}"))
        
        # Executa consulta em thread
        threading.Thread(target=consultar, daemon=True).start()
        messagebox.showinfo("Consultando", "Consultando Receita Federal...\nAguarde...")
    
    def salvar(self):
        """Salva empresa"""
        try:
            # Validações básicas
            cnpj = self.fields['cnpj'].get().strip()
            razao_social = self.fields['razao_social'].get().strip()
            uf = self.fields['uf'].get().strip()
            
            if not cnpj or not razao_social or not uf:
                messagebox.showerror("Erro", "Preencha todos os campos obrigatórios")
                return
            
            # Coleta dados do formulário
            dados = {}
            for campo, widget in self.fields.items():
                dados[campo] = widget.get().strip()
            
            dados['ativa'] = self.ativa_var.get()
            
            if self.empresa:
                # Atualização
                sucesso = self.gerenciador.atualizar_empresa(self.empresa.id, dados, "GUI User")
                if sucesso:
                    messagebox.showinfo("Sucesso", "Empresa atualizada com sucesso!")
                    self.dialog.destroy()
                    if self.callback:
                        self.callback()
                else:
                    messagebox.showerror("Erro", "Falha ao atualizar empresa")
            else:
                # Criação
                empresa_id = self.gerenciador.criar_empresa(dados, "GUI User")
                if empresa_id:
                    messagebox.showinfo("Sucesso", 
                        f"Empresa criada com sucesso!\nID: {empresa_id}")
                    self.dialog.destroy()
                    if self.callback:
                        self.callback()
                else:
                    messagebox.showerror("Erro", "Falha ao criar empresa")
                    
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar empresa: {e}")

def abrir_gestao_empresas(parent, db_manager):
    """Função para abrir gestão de empresas"""
    try:
        GestaoEmpresasGUI(parent, db_manager)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir gestão de empresas: {e}")
