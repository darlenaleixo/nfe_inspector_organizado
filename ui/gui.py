# ui/gui.py - VERSÃO CORRIGIDA COM TEMA APLICADO

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import logging
from datetime import datetime
from database.models import DatabaseManager
from ui.gestao_empresas import abrir_gestao_empresas

# Imports seguros
try:
    from processing.processor import NFeProcessorBI
except ImportError:
    try:
        from processing.processor import NFeProcessor as NFeProcessorBI
    except ImportError:
        logging.error("Módulo de processamento não disponível")
        NFeProcessorBI = None

def aplicar_tema(root):
    """Aplica tema azul, branco e preto"""
    
    style = ttk.Style(root)
    root.configure(bg="#0D1B2A")  # Fundo geral preto-azulado
    
    # Escolha o tema base
    style.theme_use("clam")
    
    # Configurações de cores
    style.configure("TFrame", background="#1B263B")  # Azul escuro
    style.configure("TLabelframe", 
                   background="#1B263B", 
                   foreground="#E0E1DD",
                   borderwidth=2,
                   relief="groove")
    style.configure("TLabelframe.Label", 
                   background="#1B263B", 
                   foreground="#E0E1DD", 
                   font=("Arial", 11, "bold"))
    
    style.configure("TLabel", 
                   background="#1B263B", 
                   foreground="#E0E1DD", 
                   font=("Arial", 10))
    style.configure("Header.TLabel", 
                   background="#1B263B", 
                   foreground="#E0E1DD", 
                   font=("Arial", 18, "bold"))
    
    # Botões com efeito hover
    style.configure("TButton",
                   background="#415A77",
                   foreground="#E0E1DD",
                   font=("Arial", 10, "bold"),
                   padding=8,
                   relief="raised")
    style.map("TButton",
              background=[("active", "#1F4287"), ("pressed", "#0F3460")],
              foreground=[("active", "#FFFFFF"), ("pressed", "#FFFFFF")],
              relief=[("pressed", "sunken"), ("active", "raised")])
    
    # Campos de entrada
    style.configure("TEntry", 
                   fieldbackground="#E0E1DD", 
                   foreground="#0D1B2A",
                   borderwidth=2,
                   relief="sunken")
    style.configure("TCombobox", 
                   fieldbackground="#E0E1DD", 
                   foreground="#0D1B2A",
                   arrowcolor="#415A77")
    
    # Scrollbars
    style.configure("Vertical.TScrollbar", 
                   background="#415A77", 
                   troughcolor="#1B263B", 
                   arrowcolor="#E0E1DD",
                   borderwidth=1)
    style.configure("Horizontal.TScrollbar", 
                   background="#415A77", 
                   troughcolor="#1B263B", 
                   arrowcolor="#E0E1DD",
                   borderwidth=1)
    
    # TreeView (para Dashboard)
    style.configure("Treeview",
                   background="#E0E1DD",
                   foreground="#0D1B2A",
                   fieldbackground="#E0E1DD",
                   font=("Arial", 9),
                   rowheight=25)
    style.configure("Treeview.Heading",
                   background="#415A77",
                   foreground="#E0E1DD",
                   font=("Arial", 10, "bold"),
                   relief="raised")
    style.map("Treeview",
              background=[("selected", "#1F4287")],
              foreground=[("selected", "#FFFFFF")])
    
    # Barra de progresso
    style.configure("TProgressbar", 
                   troughcolor="#1B263B", 
                   background="#1F4287", 
                   lightcolor="#4A90E2",
                   darkcolor="#1F4287",
                   borderwidth=1,
                   relief="sunken")

class AppGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚀 NFe Inspector - Business Intelligence")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Variáveis de controle
        self.pasta_xml = tk.StringVar()
        self.pasta_saida = tk.StringVar()
        self.processing_thread = None
        
        self.setup_interface()
        
    def setup_interface(self):
        """Configura a interface principal"""
        
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título com estilo personalizado
        title_label = ttk.Label(main_frame, 
                               text="🚀 NFe Inspector - Business Intelligence", 
                               style="Header.TLabel")
        title_label.pack(pady=(0, 25))
        
        # Frame para seleção de pastas
        pastas_frame = ttk.LabelFrame(main_frame, text="📁 Configurações de Pasta", padding="15")
        pastas_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Pasta XML
        ttk.Label(pastas_frame, text="Pasta com arquivos XML:").grid(row=0, column=0, sticky=tk.W, pady=8)
        ttk.Entry(pastas_frame, textvariable=self.pasta_xml, width=65).grid(row=0, column=1, padx=10, pady=8)
        ttk.Button(pastas_frame, text="📂 Selecionar", command=self.selecionar_pasta_xml).grid(row=0, column=2, pady=8)
        
        # Pasta Saída
        ttk.Label(pastas_frame, text="Pasta para relatórios:").grid(row=1, column=0, sticky=tk.W, pady=8)
        ttk.Entry(pastas_frame, textvariable=self.pasta_saida, width=65).grid(row=1, column=1, padx=10, pady=8)
        ttk.Button(pastas_frame, text="📂 Selecionar", command=self.selecionar_pasta_saida).grid(row=1, column=2, pady=8)
        
        # Configurar grid
        pastas_frame.columnconfigure(1, weight=1)
        
        # Frame para botões principais
        botoes_frame = ttk.LabelFrame(main_frame, text="🛠️ Ações Disponíveis", padding="15")
        botoes_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Container para botões em grid
        botoes_container = ttk.Frame(botoes_frame)
        botoes_container.pack(expand=True)
        
        # Botões principais em grid 2x2
        ttk.Button(botoes_container, text="🚀 Processar XMLs",
                command=self.iniciar_processamento, width=20).grid(row=0, column=0, padx=8, pady=5)

        ttk.Button(botoes_container, text="📊 Dashboard BI",
                command=self.abrir_dashboard, width=20).grid(row=0, column=1, padx=8, pady=5)

        ttk.Button(botoes_container, text="🛠️ Gestão Completa",
                command=self.abrir_gestao_completa,
                width=20).grid(row=0, column=2, padx=8, pady=5)

        ttk.Button(botoes_container, text="🔧 Teste IA Fiscal",
                command=self.testar_ia, width=20).grid(row=1, column=0, padx=8, pady=5)

        ttk.Button(botoes_container, text="📈 Reforma Tributária",
                command=self.testar_reforma, width=20).grid(row=1, column=1, padx=8, pady=5)

        ttk.Button(botoes_container, text="❓ Ajuda",
                command=self.mostrar_ajuda, width=20).grid(row=1, column=2, padx=8, pady=5)
        
        # Área de log com estilo personalizado
        log_frame = ttk.LabelFrame(main_frame, text="📋 Log de Execução", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Text widget com cores personalizadas
        self.log_text = tk.Text(log_frame, 
                               wrap=tk.WORD, 
                               state=tk.DISABLED,
                               bg="#E0E1DD",          # Fundo claro
                               fg="#0D1B2A",          # Texto escuro
                               insertbackground="#1F4287",  # Cursor
                               selectbackground="#415A77",   # Seleção
                               selectforeground="#FFFFFF",   # Texto selecionado
                               font=("Consolas", 9),
                               relief="sunken",
                               borderwidth=2)
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Barra de progresso estilizada
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(10, 5))
        
        # Status com cor
        self.status_label = ttk.Label(main_frame, text="✅ Pronto para processar")
        self.status_label.pack(pady=(5, 0))
        
        # Log inicial
        self.log("🚀 NFe Inspector iniciado com sucesso!")
        self.log("💡 Selecione as pastas e clique em 'Processar XMLs' para começar")
    
    def mostrar_ajuda(self):
        """Exibe informações de ajuda sobre a interface."""
        messagebox.showinfo(
            "Ajuda - NFe Inspector",
            "🚀 Processar XMLs: importa e analisa notas.\n"
            "📊 Dashboard BI: exibirá filtros e gráficos.\n"
            "🛠️ Gestão Completa: CRUD de empresas.\n"
            "🔧 Teste IA Fiscal: valida módulos de IA.\n"
            "📈 Reforma Tributária: valida módulos de reforma."
        )

    def log(self, mensagem):
        """Adiciona mensagem ao log com cores"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Insere timestamp em cor diferente
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"{mensagem}\n")
        
        # Configura tags de cor
        self.log_text.tag_config("timestamp", foreground="#415A77", font=("Consolas", 9, "bold"))
        
        # Auto scroll
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
        
    def selecionar_pasta_xml(self):
        """Seleciona pasta com arquivos XML"""
        pasta = filedialog.askdirectory(title="Selecione a pasta com arquivos XML")
        if pasta:
            self.pasta_xml.set(pasta)
            self.log(f"📁 Pasta XML selecionada: {pasta}")
            
    def selecionar_pasta_saida(self):
        """Seleciona pasta para relatórios"""
        pasta = filedialog.askdirectory(title="Selecione a pasta para relatórios")
        if pasta:
            self.pasta_saida.set(pasta)
            self.log(f"📁 Pasta de saída selecionada: {pasta}")
    
    def iniciar_processamento(self):
        """Inicia processamento em thread separada"""
        
        # Validações
        if not self.pasta_xml.get():
            messagebox.showwarning("Aviso", "Selecione a pasta com arquivos XML")
            return
            
        if not self.pasta_saida.get():
            messagebox.showwarning("Aviso", "Selecione a pasta para relatórios")
            return
            
        if not os.path.exists(self.pasta_xml.get()):
            messagebox.showerror("Erro", "Pasta de XMLs não existe")
            return
        
        # Verifica se processador está disponível
        if NFeProcessorBI is None:
            messagebox.showerror("Erro",
                               "Módulo de processamento não disponível.\n\n"
                               "Verifique se todos os módulos estão instalados corretamente.")
            return
        
        # Inicia thread de processamento
        self.processing_thread = threading.Thread(
            target=self.run_processing_thread, 
            daemon=True
        )
        self.processing_thread.start()
        
        # Atualiza interface
        self.progress.start()
        self.status_label.config(text="⏳ Processando...")
        
    def run_processing_thread(self):
        """Executa processamento em thread separada"""
        
        try:
            self.log("🚀 Iniciando processamento de NFe...")
            
            # Criar instância do processador
            pasta_xml = self.pasta_xml.get()
            pasta_saida = self.pasta_saida.get()
            
            self.log(f"📁 Pasta XML: {pasta_xml}")
            self.log(f"📁 Pasta saída: {pasta_saida}")
            
            if NFeProcessorBI is None:
                raise Exception("Módulo NFeProcessorBI não está disponível")
            
            self.log("⚙️ Criando instância do processador...")
            processor_instance = NFeProcessorBI(pasta_xml, pasta_saida)
            
            if processor_instance is None:
                raise Exception("Falha ao criar instância do processador")
            
            self.log("✅ Processador criado com sucesso")
            
            # Verifica arquivos XML
            xml_files = [f for f in os.listdir(pasta_xml) if f.lower().endswith('.xml')]
            if not xml_files:
                raise Exception(f"Nenhum arquivo XML encontrado em: {pasta_xml}")
            
            self.log(f"📄 Encontrados {len(xml_files)} arquivos XML")
            
            # Processa
            self.log("🔄 Iniciando processamento...")
            
            if hasattr(processor_instance, 'processar_pasta'):
                estatisticas = processor_instance.processar_pasta()
            else:
                raise Exception("Método 'processar_pasta' não disponível")
            
            # Métodos de compatibilidade
            if hasattr(processor_instance, 'calcular_resumos'):
                self.log("📊 Calculando resumos...")
                processor_instance.calcular_resumos()
            
            if hasattr(processor_instance, 'gerar_relatorios'):
                self.log("📑 Gerando relatórios...")
                processor_instance.gerar_relatorios()
            
            # Mostra estatísticas
            if estatisticas:
                self.log("\n=== ✅ PROCESSAMENTO CONCLUÍDO ===")
                for chave, valor in estatisticas.items():
                    self.log(f"• {chave.replace('_', ' ').title()}: {valor}")
                    
                self.log(f"\n💾 Dados salvos no banco de dados")
                self.log(f"🎯 Use o Dashboard BI para visualizar os resultados")
            
            # Atualiza interface
            self.root.after(0, self.processamento_concluido, True, "Processamento concluído com sucesso!")
            
        except Exception as e:
            error_msg = str(e)
            self.log(f"❌ ERRO: {error_msg}")
            logging.error(f"Erro no processamento: {error_msg}", exc_info=True)
            
            self.root.after(0, self.processamento_concluido, False, error_msg)
    
    def processamento_concluido(self, sucesso, mensagem):
        """Chamado quando processamento termina"""
        
        self.progress.stop()
        
        if sucesso:
            self.status_label.config(text="✅ Processamento concluído")
            messagebox.showinfo("✅ Sucesso", mensagem)
        else:
            self.status_label.config(text="❌ Erro no processamento")
            messagebox.showerror("❌ Erro", f"Erro no processamento:\n\n{mensagem}")
    
    def abrir_dashboard(self):
        """Abre Dashboard BI"""
        try:
            from database.models import DatabaseManager
            from ui.dashboard_nfe import DashboardNFe
            
            self.log("🚀 Abrindo Dashboard BI...")
            
            db_manager = DatabaseManager()
            dashboard = DashboardNFe(self.root, db_manager)
            
            self.log("✅ Dashboard BI aberto")
            
        except ImportError as e:
            error_msg = f"Módulo de Dashboard BI não disponível: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("Erro", error_msg)
        except Exception as e:
            error_msg = f"Erro ao abrir Dashboard BI: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("Erro", error_msg)
    
    def testar_ia(self):
        """Testa módulos de IA"""
        try:
            from ia_fiscal.analisador_riscos import AnalisadorRiscos
            from ia_fiscal.detector_fraudes import DetectorFraudes
            
            self.log("🧠 Testando módulos de IA...")
            
            nfe_teste = {
                'cnpj_emissor': '11222333000181',
                'valor_total': 50000.00,
                'data_emissao': '2025-09-13'
            }
            
            analisador = AnalisadorRiscos()
            detector = DetectorFraudes()
            
            risco = analisador.analisar_nfe(nfe_teste)
            inconsistencias = detector.detectar_inconsistencias(nfe_teste)
            
            self.log(f"✅ Teste IA - Risco: {risco.nivel}, Score: {risco.score:.2f}")
            self.log(f"✅ Teste IA - Inconsistências: {len(inconsistencias)}")
            
            messagebox.showinfo("✅ Teste IA", "Módulos de IA funcionando corretamente!")
            
        except ImportError as e:
            error_msg = f"Módulos de IA não disponíveis: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showwarning("⚠️ Aviso", error_msg)
        except Exception as e:
            error_msg = f"Erro no teste de IA: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("❌ Erro", error_msg)
    
    def testar_reforma(self):
        """Testa módulos da Reforma Tributária"""
        try:
            from reforma_tributaria.config import ConfigReformaTributaria
            from reforma_tributaria.calculadora import CalculadoraReformaTributaria
            
            self.log("📊 Testando Reforma Tributária...")
            
            config = ConfigReformaTributaria.get_config_por_ano(2025)
            calc = CalculadoraReformaTributaria(config)
            
            cbs = calc.calcular_cbs(1000.0, {})
            ibs = calc.calcular_ibs(1000.0, {})
            
            self.log(f"✅ Teste Reforma - CBS: R$ {cbs['valor']:.2f}")
            self.log(f"✅ Teste Reforma - IBS: R$ {ibs['valor']:.2f}")
            
            messagebox.showinfo("✅ Teste Reforma", "Módulos da Reforma Tributária funcionando!")
            
        except ImportError as e:
            error_msg = f"Módulos da Reforma Tributária não disponíveis: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showwarning("⚠️ Aviso", error_msg)
        except Exception as e:
            error_msg = f"Erro no teste da Reforma: {e}"
            self.log(f"❌ {error_msg}")
            messagebox.showerror("❌ Erro", error_msg)

    def abrir_gestao_completa(self):
        """Abre janela de Gestão Completa de Empresas"""
        try:
            db_manager = DatabaseManager()
            abrir_gestao_empresas(self.root, db_manager)
        except Exception as e:
            logging.error(f"Erro ao abrir Gestão Completa: {e}")
            messagebox.showerror("Erro", f"Erro ao abrir Gestão Completa:\n{e}")
            
def iniciar_gui():
    """Função principal para iniciar a GUI"""
    
    root = tk.Tk()
    
    # ✅ APLICAR TEMA ANTES DE CRIAR A GUI
    aplicar_tema(root)
    
    app = AppGUI(root)
    root.mainloop()

if __name__ == "__main__":
    iniciar_gui()
