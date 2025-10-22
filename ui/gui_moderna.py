# ui/gui_moderna.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import logging
from datetime import datetime

# Imports seguros
try:
    from processing.processor import NFeProcessorBI
except ImportError:
    try:
        from processing.processor import NFeProcessor as NFeProcessorBI
    except ImportError:
        logging.error("Módulo de processamento não disponível")
        NFeProcessorBI = None

try:
    from database.models import DatabaseManager
    from ui.dashboard_nfe import DashboardNFe
    from ui.gestao_empresas import abrir_gestao_empresas
except ImportError as e:
    logging.warning(f"Alguns módulos não disponíveis: {e}")

class MenuModerno:
    """Menu superior moderno estilo ERP"""
    
    
    # === SISTEMA ===
  
    # ... resto do menu sistema ...
    
   

    def __init__(self, parent, app_instance):
        self.parent = parent
        self.app = app_instance
        self.setup_menu()

    def setup_menu(self):
        """Cria menu superior"""
        
        # Barra de menu principal
        menubar = tk.Menu(self.parent)
        self.parent.config(menu=menubar)

        # === SISTEMA ===
        menu_sistema = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sistema", menu=menu_sistema)
        
        menu_sistema.add_command(label="🏠 Início", command=self.app.ir_para_inicio)
        menu_sistema.add_separator()
        menu_sistema.add_command(label="⚙️ Configurações", command=self.app.abrir_configuracoes)
        menu_sistema.add_command(label="🔑 Sobre", command=self.app.mostrar_sobre)
        menu_sistema.add_separator()
        menu_sistema.add_command(label="❌ Sair", command=self.parent.quit)

         # === PROCESSAMENTO === (SUBSTITUIR ESTE BLOCO)
        menu_processamento = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Processamento", menu=menu_processamento)
        
        # NOVA OPÇÃO ÚNICA:
        menu_processamento.add_command(label="🚀 Processamento de XMLs", command=self.app.abrir_janela_processamento)
        
        # === EMPRESAS ===
        menu_empresas = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Empresas", menu=menu_empresas)
                
        menu_empresas.add_command(label="🏢 Gestão Completa",
                                command=self.app.abrir_gestao_empresas)
        menu_empresas.add_command(label="➕ Nova Empresa",
                                command=self.app.nova_empresa)
        menu_empresas.add_separator()
        menu_empresas.add_command(label="📥 Importar Lista",
                                command=self.app.importar_empresas)
        menu_empresas.add_command(label="📤 Exportar Lista",
                                command=self.app.exportar_empresas)

        # === ANÁLISES ===
        menu_analises = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Análises", menu=menu_analises)
        
        menu_analises.add_command(label="📊 Dashboard BI",
                                command=self.app.abrir_dashboard)
        menu_analises.add_command(label="📈 Relatórios",
                                command=self.app.abrir_relatorios)
        menu_analises.add_separator()
        menu_analises.add_command(label="🧠 Análise IA",
                                command=self.app.executar_analise_ia)
        menu_analises.add_command(label="⚠️ Detecção de Riscos",
                                command=self.app.detectar_riscos)

        # === TRIBUTÁRIO ===
        menu_tributario = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tributário", menu=menu_tributario)
        
        menu_tributario.add_command(label="📋 Reforma Tributária",
                                  command=self.app.testar_reforma)
        menu_tributario.add_command(label="🧮 Calculadora CBS/IBS",
                                  command=self.app.abrir_calculadora)
        menu_tributario.add_separator()
        menu_tributario.add_command(label="📜 Legislação",
                                  command=self.app.mostrar_legislacao)

        # === FERRAMENTAS ===
        menu_ferramentas = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ferramentas", menu=menu_ferramentas)
        
        menu_ferramentas.add_command(label="🔍 Validador CNPJ",
                                   command=self.app.validar_cnpj)
        menu_ferramentas.add_command(label="🏛️ Consulta Receita Federal",
                                   command=self.app.consultar_rf)
        menu_ferramentas.add_separator()
        menu_ferramentas.add_command(label="🔧 Teste Módulos",
                                   command=self.app.testar_modulos)
        menu_ferramentas.add_command(label="📋 Log do Sistema",
                                   command=self.app.mostrar_log)

        # === AJUDA ===
        menu_ajuda = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ajuda", menu=menu_ajuda)
        
        menu_ajuda.add_command(label="📚 Manual do Usuário",
                             command=self.app.abrir_manual)
        menu_ajuda.add_command(label="🎥 Tutoriais",
                             command=self.app.abrir_tutoriais)
        menu_ajuda.add_separator()
        menu_ajuda.add_command(label="🐛 Reportar Bug",
                             command=self.app.reportar_bug)
        menu_ajuda.add_command(label="ℹ️ Sobre o Sistema",
                             command=self.app.mostrar_sobre)

class AppModerna:
    """Interface principal moderna estilo ERP"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🚀 NFe Inspector - Sistema de Análise Fiscal")
        
        # Maximiza janela independente da resolução
        self.root.state('zoomed')  # Windows
        # Para Linux/Mac: self.root.attributes('-zoomed', True)
        
        # Variáveis de controle
        self.pasta_xml = tk.StringVar()
        self.pasta_saida = tk.StringVar(value="relatorios")
        self.processamento_ativo = False
        self.processing_thread = None
        
        # Configurações visuais
        self.configurar_tema()
        
        # Menu superior
        self.menu = MenuModerno(self.root, self)
        
        # Interface principal
        self.setup_interface_principal()
        
        # Status inicial
        self.atualizar_status("Sistema iniciado - Pronto para usar")
    
    def configurar_tema(self):
        """Configura tema visual moderno"""
        
        style = ttk.Style()
        
        # Cores principais
        self.cores = {
            'fundo_principal': "#C0C0C0",
            'fundo_secundario': "#FFFFFF",
            'azul_primario': '#0056B3',
            'azul_claro': '#CCE7FF',
            'verde_sucesso': '#28A745',
            'vermelho_erro': '#DC3545',
            'amarelo_aviso': '#FFC107',
            'texto_principal': "#000000",
            'texto_secundario': "#000000"
        }
        
        self.root.configure(bg=self.cores['fundo_principal'])
        
        try:
            style.theme_use('clam')
        except:
            pass
        
        # Configurações do tema
        style.configure("Title.TLabel", 
                       font=("Segoe UI", 24, "bold"),
                       background=self.cores['fundo_principal'],
                       foreground=self.cores['azul_primario'])
        
        style.configure("Subtitle.TLabel",
                       font=("Segoe UI", 12),
                       background=self.cores['fundo_principal'],
                       foreground=self.cores['texto_secundario'])
        
        style.configure("Card.TFrame",
                       background=self.cores['fundo_secundario'],
                       relief="solid",
                       borderwidth=1)
        
        style.configure("Success.TLabel",
                       foreground=self.cores['verde_sucesso'],
                       font=("Segoe UI", 10, "bold"))
        
        style.configure("Error.TLabel",
                       foreground=self.cores['vermelho_erro'],
                       font=("Segoe UI", 10, "bold"))
    
    def setup_interface_principal(self):
        """Cria interface principal limpa"""
        
        # Container principal com padding
        main_container = tk.Frame(self.root, bg=self.cores['fundo_principal'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Área de cabeçalho
        self.setup_header(main_container)
        
        # Área de conteúdo central
        self.setup_content_area(main_container)
        
        # Barra de status
        self.setup_status_bar(main_container)
    
    def setup_header(self, parent):
        """Área de cabeçalho com título e informações"""
        
        header_frame = tk.Frame(parent, bg=self.cores['fundo_principal'])
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Lado esquerdo - Título e subtítulo
        left_frame = tk.Frame(header_frame, bg=self.cores['fundo_principal'])
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        title_label = ttk.Label(left_frame, 
                               text="NFe Inspector",
                               style="Title.TLabel")
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(left_frame,
                                  text="Sistema Avançado de Análise Fiscal com IA e Business Intelligence",
                                  style="Subtitle.TLabel")
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
        # Lado direito - Informações rápidas
        right_frame = tk.Frame(header_frame, bg=self.cores['fundo_principal'])
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Cards de informação
        self.criar_info_card(right_frame, "Data/Hora", 
                           datetime.now().strftime("%d/%m/%Y %H:%M"), 0, 0)
        
        self.criar_info_card(right_frame, "Módulos", "IA, BI, Reforma", 0, 1)
    
    def criar_info_card(self, parent, titulo, valor, row, col):
        """Cria card de informação"""
        
        card = tk.Frame(parent, 
                       bg=self.cores['fundo_secundario'],
                       relief="solid", 
                       bd=1)
        card.grid(row=row, column=col, padx=5, pady=2, ipadx=10, ipady=5)
        
        tk.Label(card, text=titulo, 
                font=("Segoe UI", 8),
                bg=self.cores['fundo_secundario'],
                fg=self.cores['texto_secundario']).pack()
        
        tk.Label(card, text=valor,
                font=("Segoe UI", 10, "bold"),
                bg=self.cores['fundo_secundario'],
                fg=self.cores['texto_principal']).pack()
    
    def setup_content_area(self, parent):
        """Área de conteúdo central"""
        
        # Frame de conteúdo com scroll
        canvas = tk.Canvas(parent, bg=self.cores['fundo_principal'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        self.content_frame = tk.Frame(canvas, bg=self.cores['fundo_principal'])
        
        self.content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Conteúdo inicial - Dashboard de Início
        self.mostrar_tela_inicial()
    
    def setup_status_bar(self, parent):
        """Barra de status na parte inferior"""
        
        status_frame = tk.Frame(parent, 
                               bg=self.cores['azul_primario'],
                               height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(20, 0))
        status_frame.pack_propagate(False)
        
        # Status text
        self.status_text = tk.Label(status_frame,
                                   text="Pronto",
                                   bg=self.cores['azul_primario'],
                                   fg='white',
                                   font=("Segoe UI", 9))
        self.status_text.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Progress bar (oculta inicialmente)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame,
                                          variable=self.progress_var,
                                          length=200,
                                          mode='indeterminate')
    
    def mostrar_tela_inicial(self):
        """Mostra tela inicial com dashboard limpo"""
        
        # Limpa conteúdo anterior
        for widget in self.content_frame.winfo_children():
            widget.destroy()
          
    def criar_botao_acao(self, parent, texto, comando, cor, posicao):
        """Cria botão de ação estilizado"""
        
        btn_frame = tk.Frame(parent, 
                           bg=cor,
                           relief="solid",
                           bd=2,
                           cursor="hand2")
        btn_frame.grid(row=0, column=posicao, padx=10, pady=5, sticky="ew")
        
        # Label com texto
        label = tk.Label(btn_frame, 
                        text=texto,
                        bg=cor,
                        fg='white',
                        font=("Segoe UI", 12, "bold"),
                        cursor="hand2",
                        padx=20,
                        pady=15)
        label.pack(expand=True)
        
        # Eventos de hover e clique
        def on_enter(e):
            btn_frame.configure(relief="raised")
            
        def on_leave(e):
            btn_frame.configure(relief="solid")
        
        def on_click(e):
            comando()
        
        for widget in [btn_frame, label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", on_click)
    
    def criar_secao_estatisticas(self, parent):
        """Seção com estatísticas do sistema"""
        
        # Título
        titulo_frame = tk.Frame(parent, bg=self.cores['fundo_principal'])
        titulo_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(titulo_frame, text="📊 Estatísticas do Sistema",
                font=("Segoe UI", 16, "bold"),
                bg=self.cores['fundo_principal'],
                fg=self.cores['azul_primario']).pack(anchor=tk.W)
        
        # Cards de estatísticas
        stats_frame = tk.Frame(parent, bg=self.cores['fundo_principal'])
        stats_frame.pack(fill=tk.X, pady=(0, 30))
        
        for i in range(4):
            stats_frame.columnconfigure(i, weight=1)
        
        # Obter estatísticas reais (simulado por enquanto)
        try:
            db_manager = DatabaseManager()
            stats = self.obter_estatisticas_sistema(db_manager)
        except:
            stats = {
                'total_empresas': 0,
                'total_nfes': 0,
                'valor_total': 0.0,
                'ultimo_processamento': 'Nunca'
            }
        
        # Cards de estatísticas
        self.criar_card_stat(stats_frame, "🏢 Empresas", str(stats['total_empresas']), 0)
        self.criar_card_stat(stats_frame, "📄 NFe Processadas", str(stats['total_nfes']), 1)
        self.criar_card_stat(stats_frame, "💰 Valor Total", f"R$ {stats['valor_total']:,.2f}", 2)
        self.criar_card_stat(stats_frame, "📅 Último Processo", stats['ultimo_processamento'], 3)
    
    def criar_card_stat(self, parent, titulo, valor, posicao):
        """Cria card de estatística"""
        
        card = tk.Frame(parent,
                       bg=self.cores['fundo_secundario'],
                       relief="solid",
                       bd=1)
        card.grid(row=0, column=posicao, padx=10, pady=5, sticky="ew", ipadx=15, ipady=15)
        
        # Título
        tk.Label(card, text=titulo,
                font=("Segoe UI", 10),
                bg=self.cores['fundo_secundario'],
                fg=self.cores['texto_secundario']).pack()
        
        # Valor
        tk.Label(card, text=valor,
                font=("Segoe UI", 14, "bold"),
                bg=self.cores['fundo_secundario'],
                fg=self.cores['texto_principal']).pack(pady=(5, 0))
    
    def criar_secao_atividades(self, parent):
        """Seção com atividades recentes"""
        
        # Título
        titulo_frame = tk.Frame(parent, bg=self.cores['fundo_principal'])
        titulo_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(titulo_frame, text="📋 Atividades Recentes",
                font=("Segoe UI", 16, "bold"),
                bg=self.cores['fundo_principal'],
                fg=self.cores['azul_primario']).pack(anchor=tk.W)
        
        # Lista de atividades
        atividades_frame = tk.Frame(parent,
                                   bg=self.cores['fundo_secundario'],
                                   relief="solid",
                                   bd=1)
        atividades_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # Área de scroll para atividades
        atividades_text = tk.Text(atividades_frame,
                                 height=8,
                                 bg=self.cores['fundo_secundario'],
                                 fg=self.cores['texto_principal'],
                                 font=("Segoe UI", 10),
                                 relief="flat",
                                 padx=15,
                                 pady=15)
        
        scrollbar_ativ = ttk.Scrollbar(atividades_frame, orient="vertical", command=atividades_text.yview)
        atividades_text.configure(yscrollcommand=scrollbar_ativ.set)
        
        atividades_text.pack(side="left", fill="both", expand=True)
        scrollbar_ativ.pack(side="right", fill="y")
        
        # Conteúdo inicial
        atividades_iniciais = f"""🚀 Sistema iniciado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}

📋 Bem-vindo ao NFe Inspector!
   Sistema pronto para processamento de notas fiscais

💡 Dicas de uso:
   • Use o menu "Processamento" para importar XMLs
   • Acesse "Dashboard BI" para análises avançadas
   • Gerencie empresas pelo menu "Empresas"
   • Explore análises de IA em "Análises"

🔧 Sistema atualizado com:
   ✓ Análise de riscos com IA
   ✓ Suporte à Reforma Tributária
   ✓ Dashboard Business Intelligence
   ✓ CRUD completo de empresas
   ✓ Interface moderna e responsiva"""
        
        atividades_text.insert(tk.END, atividades_iniciais)
        atividades_text.config(state=tk.DISABLED)
    
    def obter_estatisticas_sistema(self, db_manager):
        """Obtém estatísticas reais do sistema"""
        try:
            stats = db_manager.obter_estatisticas()
            empresas = db_manager.listar_empresas()
            
            return {
                'total_empresas': len(empresas),
                'total_nfes': stats.get('total_notas', 0),
                'valor_total': stats.get('valor_total', 0.0),
                'ultimo_processamento': stats.get('ultimo_processamento', 'Nunca')[:10] if stats.get('ultimo_processamento') else 'Nunca'
            }
        except Exception as e:
            logging.error(f"Erro ao obter estatísticas: {e}")
            return {
                'total_empresas': 0,
                'total_nfes': 0, 
                'valor_total': 0.0,
                'ultimo_processamento': 'Erro'
            }
    
    def atualizar_status(self, mensagem, mostrar_progress=False):
        """Atualiza barra de status"""
        self.status_text.config(text=mensagem)
        
        if mostrar_progress:
            self.progress_bar.pack(side=tk.RIGHT, padx=10, pady=5)
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.pack_forget()
    
    # === MÉTODOS DE AÇÃO DO MENU ===
    def ir_para_inicio(self):
        """Volta para tela inicial"""
        self.mostrar_tela_inicial()
        self.atualizar_status("Tela inicial carregada")
    
    def iniciar_processamento_rapido(self):
        """Inicia processamento rápido (seletor de pasta)"""
        pasta = filedialog.askdirectory(title="Selecione pasta com XMLs para processamento rápido")
        if pasta:
            self.pasta_xml.set(pasta)
            self.iniciar_processamento()
    
    def selecionar_pasta_xml(self):
        """Seleciona pasta XML"""
        pasta = filedialog.askdirectory(title="Selecione pasta com arquivos XML")
        if pasta:
            self.pasta_xml.set(pasta)
            self.atualizar_status(f"Pasta XML selecionada: {pasta}")
            messagebox.showinfo("Pasta Selecionada", f"Pasta XML definida:\n{pasta}")

    # ui/gui_moderna.py - Atualizar método no menu
    def abrir_janela_processamento(self):
        """Abre janela dedicada de processamento"""
        try:
            from ui.janela_processamento import abrir_janela_processamento
            abrir_janela_processamento(self.root)
            self.atualizar_status("Janela de processamento aberta")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir processamento:\n{e}")

    def iniciar_processamento(self):
        """Inicia processamento de XMLs"""
        if not self.pasta_xml.get():
            messagebox.showwarning("Aviso", "Selecione uma pasta com arquivos XML primeiro")
            self.selecionar_pasta_xml()
            return
        
        if not os.path.exists(self.pasta_xml.get()):
            messagebox.showerror("Erro", "Pasta selecionada não existe")
            return
        
        if NFeProcessorBI is None:
            messagebox.showerror("Erro", "Módulo de processamento não disponível")
            return
        
        self.processamento_ativo = True
        self.atualizar_status("Iniciando processamento...", True)
        
        def processar():
            try:
                processor = NFeProcessorBI(self.pasta_xml.get(), self.pasta_saida.get())
                estatisticas = processor.processar_pasta()
                
                # Atualiza interface
                self.root.after(0, self.processamento_concluido, True, estatisticas)
                
            except Exception as e:
                self.root.after(0, self.processamento_concluido, False, str(e))
        
        self.processing_thread = threading.Thread(target=processar, daemon=True)
        self.processing_thread.start()
    
    def processamento_concluido(self, sucesso, resultado):
        """Callback quando processamento termina"""
        self.processamento_ativo = False
        self.atualizar_status("Processamento concluído" if sucesso else "Erro no processamento", False)
        
        if sucesso:
            msg = "Processamento concluído com sucesso!\n\n"
            if isinstance(resultado, dict):
                for chave, valor in resultado.items():
                    msg += f"• {chave.replace('_', ' ').title()}: {valor}\n"
            
            messagebox.showinfo("Sucesso", msg)
            
            # Atualizar tela inicial com novas estatísticas
            self.mostrar_tela_inicial()
        else:
            messagebox.showerror("Erro", f"Erro no processamento:\n\n{resultado}")
    
    def pausar_processamento(self):
        """Pausa processamento (funcionalidade futura)"""
        messagebox.showinfo("Info", "Funcionalidade de pausa em desenvolvimento")
    
    def parar_processamento(self):
        """Para processamento"""
        if self.processamento_ativo:
            resposta = messagebox.askyesno("Confirmar", "Deseja interromper o processamento?")
            if resposta:
                self.processamento_ativo = False
                self.atualizar_status("Processamento interrompido pelo usuário")
        else:
            messagebox.showinfo("Info", "Nenhum processamento em andamento")
    
    def abrir_dashboard(self):
        """Abre Dashboard BI"""
        try:
            db_manager = DatabaseManager()
            dashboard = DashboardNFe(self.root, db_manager)
            self.atualizar_status("Dashboard BI aberto")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir Dashboard:\n{e}")
    
    def abrir_gestao_empresas(self):
        """Abre gestão completa de empresas"""
        try:
            db_manager = DatabaseManager()
            abrir_gestao_empresas(self.root, db_manager)
            self.atualizar_status("Gestão de empresas aberta")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir gestão de empresas:\n{e}")
    
    def nova_empresa(self):
        """Abre formulário para nova empresa"""
        self.abrir_gestao_empresas()  # Por enquanto abre gestão completa
    
    def importar_empresas(self):
        """Importa lista de empresas"""
        messagebox.showinfo("Em Desenvolvimento", "Funcionalidade de importação em desenvolvimento")
    
    def exportar_empresas(self):
        """Exporta lista de empresas"""
        messagebox.showinfo("Em Desenvolvimento", "Funcionalidade de exportação em desenvolvimento")
    
    def abrir_relatorios(self):
        """Abre módulo de relatórios"""
        messagebox.showinfo("Em Desenvolvimento", "Módulo de relatórios em desenvolvimento")
    
    def executar_analise_ia(self):
        """Executa análise de IA"""
        try:
            from ui.janela_analise_ia import abrir_janela_analise_ia
            abrir_janela_analise_ia(self.root)
            self.atualizar_status("Análise IA aberta")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir Análise IA:\n{e}")

    
    def detectar_riscos(self):
        """Executa detecção de riscos"""
        messagebox.showinfo("Em Desenvolvimento", "Detecção de riscos em desenvolvimento")
    
    def testar_reforma(self):
        """Testa módulos da Reforma Tributária"""
        try:
            from reforma_tributaria.config import ConfigReformaTributaria
            from reforma_tributaria.calculadora import CalculadoraReformaTributaria
            
            config = ConfigReformaTributaria.get_config_por_ano(2025)
            calc = CalculadoraReformaTributaria(config)
            
            # Teste rápido
            cbs = calc.calcular_cbs(1000.0, {})
            ibs = calc.calcular_ibs(1000.0, {})
            
            msg = f"Teste da Reforma Tributária:\n\n"
            msg += f"Produto R$ 1.000,00:\n"
            msg += f"• CBS: R$ {cbs['valor']:.2f}\n"
            msg += f"• IBS: R$ {ibs['valor']:.2f}"
            
            messagebox.showinfo("Teste Reforma", msg)
            self.atualizar_status("Teste da Reforma Tributária executado")
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro no teste da Reforma:\n{e}")
    
    def abrir_calculadora(self):
        """Abre calculadora CBS/IBS"""
        messagebox.showinfo("Em Desenvolvimento", "Calculadora CBS/IBS em desenvolvimento")
    
    def mostrar_legislacao(self):
        """Mostra informações sobre legislação"""
        messagebox.showinfo("Em Desenvolvimento", "Módulo de legislação em desenvolvimento")
    
    def validar_cnpj(self):
        """Abre validador de CNPJ"""
        messagebox.showinfo("Em Desenvolvimento", "Validador de CNPJ em desenvolvimento")
    
    def consultar_rf(self):
        """Consulta Receita Federal"""
        messagebox.showinfo("Em Desenvolvimento", "Consulta à RF em desenvolvimento")
    
    def testar_modulos(self):
        """Testa todos os módulos"""
        messagebox.showinfo("Em Desenvolvimento", "Teste de módulos em desenvolvimento")
    
    def mostrar_log(self):
        """Mostra log do sistema"""
        messagebox.showinfo("Em Desenvolvimento", "Visualizador de log em desenvolvimento")
    
    def abrir_configuracoes(self):
        """Abre configurações"""
        messagebox.showinfo("Em Desenvolvimento", "Configurações em desenvolvimento")
    
    def mostrar_sobre(self):
        """Mostra informações sobre o sistema"""
        sobre_texto = """🚀 NFe Inspector - Sistema de Análise Fiscal

📍 Versão: 2.0 Beta
📅 Data: Setembro 2025
👨‍💻 Desenvolvido por: Sua Equipe

🎯 Funcionalidades:
• Processamento avançado de NFe/NFCe
• Análise de riscos com Inteligência Artificial
• Suporte completo à Reforma Tributária
• Dashboard Business Intelligence
• Gestão completa de empresas
• Interface moderna e intuitiva

🛠️ Tecnologias:
• Python 3.11+
• Tkinter (Interface)
• SQLite (Banco de dados)
• Machine Learning (IA)
• APIs Governo (Integração)

📞 Suporte: support@nfeinspector.com
🌐 Site: www.nfeinspector.com"""
        
        messagebox.showinfo("Sobre o Sistema", sobre_texto)
    
    def abrir_manual(self):
        """Abre manual do usuário"""
        messagebox.showinfo("Em Desenvolvimento", "Manual do usuário em desenvolvimento")
    
    def abrir_tutoriais(self):
        """Abre tutoriais"""
        messagebox.showinfo("Em Desenvolvimento", "Tutoriais em desenvolvimento")
    
    def reportar_bug(self):
        """Reporta bug"""
        messagebox.showinfo("Reportar Bug", "Envie bugs para: bugs@nfeinspector.com")
    
    def executar(self):
        """Inicia aplicação"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            print("Aplicação interrompida pelo usuário")
        except Exception as e:
            logging.error(f"Erro na aplicação: {e}")

# Função para iniciar nova interface
def iniciar_gui_moderna():
    """Inicia interface moderna"""
    app = AppModerna()
    app.executar()

if __name__ == "__main__":
    iniciar_gui_moderna()

