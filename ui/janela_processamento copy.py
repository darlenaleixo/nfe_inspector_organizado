# ui/janela_processamento.py

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any

# Imports seguros
try:
    from processing.processor import NFeProcessorBI
except ImportError:
    try:
        from processing.processor import NFeProcessor as NFeProcessorBI
    except ImportError:
        NFeProcessorBI = None

class JanelaProcessamento:
    """Janela completa de processamento de XMLs com interface visual"""
    
    def __init__(self, parent):
        self.parent = parent
        self.processing_thread = None
        self.processamento_ativo = False
        self.processamento_pausado = False
        self.deve_parar = False
        
        # Variáveis de controle
        self.pasta_xml = tk.StringVar()
        self.pasta_saida = tk.StringVar(value="relatorios")
        self.arquivos_total = 0
        self.arquivos_processados = 0
        self.arquivos_com_erro = 0
        self.tempo_inicio = None
        
        # Configurações de cores
        self.cores = {
            'fundo_principal': "#F8F9FA",
            'fundo_secundario': "#FFFFFF",
            'azul_primario': '#0056B3',
            'verde_sucesso': '#28A745',
            'vermelho_erro': '#DC3545',
            'amarelo_aviso': '#FFC107',
            'texto_principal': "#212529",
            'texto_secundario': "#6C757D"
        }
        
        self.criar_janela()
        self.setup_interface()
        
    def criar_janela(self):
        """Cria a janela de processamento"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("🚀 Processamento de XMLs NFe")
        self.window.geometry("800x600")
        self.window.configure(bg=self.cores['fundo_principal'])
        
        # Centralizar janela
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Impedir fechamento durante processamento
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_interface(self):
        """Configura interface da janela"""
        
        # Container principal
        main_frame = tk.Frame(self.window, bg=self.cores['fundo_principal'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Cabeçalho
        self.setup_header(main_frame)
        
        # Seção de configuração
        self.setup_config_section(main_frame)
        
        # Seção de controles
        self.setup_controls_section(main_frame)
        
        # Seção de progresso
        self.setup_progress_section(main_frame)
        
        # Seção de log
        self.setup_log_section(main_frame)
        
        # Barra de status
        self.setup_status_bar(main_frame)
        
    def setup_header(self, parent):
        """Cabeçalho da janela"""
        header_frame = tk.Frame(parent, bg=self.cores['fundo_principal'])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        title_label = tk.Label(header_frame,
                              text="🚀 Processamento de Notas Fiscais",
                              font=("Segoe UI", 18, "bold"),
                              bg=self.cores['fundo_principal'],
                              fg=self.cores['azul_primario'])
        title_label.pack(anchor=tk.W)
        
        subtitle_label = tk.Label(header_frame,
                                 text="Importe e analise arquivos XML de NFe/NFCe com IA e Business Intelligence",
                                 font=("Segoe UI", 10),
                                 bg=self.cores['fundo_principal'],
                                 fg=self.cores['texto_secundario'])
        subtitle_label.pack(anchor=tk.W, pady=(5, 0))
        
    def setup_config_section(self, parent):
        """Seção de configuração de pastas"""
        config_frame = tk.LabelFrame(parent,
                                    text="📁 Configuração de Pastas",
                                    font=("Segoe UI", 11, "bold"),
                                    bg=self.cores['fundo_secundario'],
                                    fg=self.cores['texto_principal'],
                                    padx=15,
                                    pady=15)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Pasta XML
        xml_frame = tk.Frame(config_frame, bg=self.cores['fundo_secundario'])
        xml_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(xml_frame,
                text="Pasta com arquivos XML:",
                font=("Segoe UI", 10),
                bg=self.cores['fundo_secundario'],
                fg=self.cores['texto_principal']).pack(anchor=tk.W)
        
        xml_path_frame = tk.Frame(xml_frame, bg=self.cores['fundo_secundario'])
        xml_path_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.xml_entry = tk.Entry(xml_path_frame,
                                 textvariable=self.pasta_xml,
                                 font=("Segoe UI", 10),
                                 width=60)
        self.xml_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.btn_selecionar_xml = tk.Button(xml_path_frame,
                                           text="📂 Selecionar",
                                           command=self.selecionar_pasta_xml,
                                           bg=self.cores['azul_primario'],
                                           fg='white',
                                           font=("Segoe UI", 9, "bold"),
                                           relief="flat",
                                           padx=15,
                                           pady=5,
                                           cursor="hand2")
        self.btn_selecionar_xml.pack(side=tk.RIGHT)
        
        # Pasta Saída
        saida_frame = tk.Frame(config_frame, bg=self.cores['fundo_secundario'])
        saida_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(saida_frame,
                text="Pasta para relatórios:",
                font=("Segoe UI", 10),
                bg=self.cores['fundo_secundario'],
                fg=self.cores['texto_principal']).pack(anchor=tk.W)
        
        saida_path_frame = tk.Frame(saida_frame, bg=self.cores['fundo_secundario'])
        saida_path_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.saida_entry = tk.Entry(saida_path_frame,
                                   textvariable=self.pasta_saida,
                                   font=("Segoe UI", 10),
                                   width=60)
        self.saida_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.btn_selecionar_saida = tk.Button(saida_path_frame,
                                             text="📂 Selecionar",
                                             command=self.selecionar_pasta_saida,
                                             bg=self.cores['azul_primario'],
                                             fg='white',
                                             font=("Segoe UI", 9, "bold"),
                                             relief="flat",
                                             padx=15,
                                             pady=5,
                                             cursor="hand2")
        self.btn_selecionar_saida.pack(side=tk.RIGHT)
        
    def setup_controls_section(self, parent):
        """Seção de controles de processamento"""
        controls_frame = tk.LabelFrame(parent,
                                      text="⚙️ Controles de Processamento",
                                      font=("Segoe UI", 11, "bold"),
                                      bg=self.cores['fundo_secundario'],
                                      fg=self.cores['texto_principal'],
                                      padx=15,
                                      pady=15)
        controls_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Botões de controle
        buttons_frame = tk.Frame(controls_frame, bg=self.cores['fundo_secundario'])
        buttons_frame.pack(fill=tk.X)
        
        # Botão Processar
        self.btn_processar = tk.Button(buttons_frame,
                                      text="🚀 Processar XMLs",
                                      command=self.iniciar_processamento,
                                      bg=self.cores['verde_sucesso'],
                                      fg='white',
                                      font=("Segoe UI", 11, "bold"),
                                      relief="flat",
                                      padx=20,
                                      pady=10,
                                      cursor="hand2")
        self.btn_processar.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botão Pausar
        self.btn_pausar = tk.Button(buttons_frame,
                                   text="⏸️ Pausar",
                                   command=self.pausar_processamento,
                                   bg=self.cores['amarelo_aviso'],
                                   fg='white',
                                   font=("Segoe UI", 11, "bold"),
                                   relief="flat",
                                   padx=20,
                                   pady=10,
                                   cursor="hand2",
                                   state="disabled")
        self.btn_pausar.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botão Parar
        self.btn_parar = tk.Button(buttons_frame,
                                  text="⏹️ Parar",
                                  command=self.parar_processamento,
                                  bg=self.cores['vermelho_erro'],
                                  fg='white',
                                  font=("Segoe UI", 11, "bold"),
                                  relief="flat",
                                  padx=20,
                                  pady=10,
                                  cursor="hand2",
                                  state="disabled")
        self.btn_parar.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botão Fechar
        self.btn_fechar = tk.Button(buttons_frame,
                                   text="❌ Fechar",
                                   command=self.fechar_janela,
                                   bg=self.cores['texto_secundario'],
                                   fg='white',
                                   font=("Segoe UI", 11, "bold"),
                                   relief="flat",
                                   padx=20,
                                   pady=10,
                                   cursor="hand2")
        self.btn_fechar.pack(side=tk.RIGHT)
        
    def setup_progress_section(self, parent):
        """Seção de progresso visual"""
        progress_frame = tk.LabelFrame(parent,
                                      text="📊 Progresso do Processamento",
                                      font=("Segoe UI", 11, "bold"),
                                      bg=self.cores['fundo_secundario'],
                                      fg=self.cores['texto_principal'],
                                      padx=15,
                                      pady=15)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Informações de progresso
        info_frame = tk.Frame(progress_frame, bg=self.cores['fundo_secundario'])
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Grid de informações
        info_frame.columnconfigure(0, weight=1)
        info_frame.columnconfigure(1, weight=1)
        info_frame.columnconfigure(2, weight=1)
        info_frame.columnconfigure(3, weight=1)
        
        # Cards de informação
        self.criar_info_card(info_frame, "Total", "0", "total_label", 0)
        self.criar_info_card(info_frame, "Processados", "0", "processados_label", 1)
        self.criar_info_card(info_frame, "Erros", "0", "erros_label", 2)
        self.criar_info_card(info_frame, "Tempo", "00:00", "tempo_label", 3)
        
        # Barra de progresso
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame,
                                           variable=self.progress_var,
                                           maximum=100,
                                           length=400,
                                           mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 5))
        
        # Label de percentual
        self.progress_label = tk.Label(progress_frame,
                                      text="0%",
                                      font=("Segoe UI", 10, "bold"),
                                      bg=self.cores['fundo_secundario'],
                                      fg=self.cores['azul_primario'])
        self.progress_label.pack()
        
    def criar_info_card(self, parent, titulo, valor, var_name, col):
        """Cria card de informação"""
        card_frame = tk.Frame(parent,
                             bg='white',
                             relief="solid",
                             bd=1)
        card_frame.grid(row=0, column=col, padx=5, pady=5, sticky="ew", ipadx=10, ipady=10)
        
        tk.Label(card_frame,
                text=titulo,
                font=("Segoe UI", 9),
                bg='white',
                fg=self.cores['texto_secundario']).pack()
        
        label = tk.Label(card_frame,
                        text=valor,
                        font=("Segoe UI", 14, "bold"),
                        bg='white',
                        fg=self.cores['texto_principal'])
        label.pack()
        
        # Armazenar referência do label
        setattr(self, var_name, label)
        
    def setup_log_section(self, parent):
        """Seção de log de atividades"""
        log_frame = tk.LabelFrame(parent,
                                 text="📋 Log de Atividades",
                                 font=("Segoe UI", 11, "bold"),
                                 bg=self.cores['fundo_secundario'],
                                 fg=self.cores['texto_principal'],
                                 padx=15,
                                 pady=15)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Área de texto com scroll
        log_container = tk.Frame(log_frame, bg=self.cores['fundo_secundario'])
        log_container.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = tk.Text(log_container,
                               height=10,
                               bg='white',
                               fg=self.cores['texto_principal'],
                               font=("Consolas", 9),
                               relief="solid",
                               bd=1,
                               wrap=tk.WORD,
                               state=tk.DISABLED)
        
        log_scrollbar = ttk.Scrollbar(log_container,
                                     orient="vertical",
                                     command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scrollbar.pack(side="right", fill="y")
        
        # Log inicial
        self.adicionar_log("Sistema de processamento iniciado")
        self.adicionar_log("Selecione uma pasta com arquivos XML para começar")
        
    def setup_status_bar(self, parent):
        """Barra de status"""
        status_frame = tk.Frame(parent,
                               bg=self.cores['azul_primario'],
                               height=30)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame,
                                    text="Pronto para processar",
                                    bg=self.cores['azul_primario'],
                                    fg='white',
                                    font=("Segoe UI", 9))
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
    # === MÉTODOS DE AÇÃO ===
    
    def selecionar_pasta_xml(self):
        """Seleciona pasta com arquivos XML"""
        pasta = filedialog.askdirectory(
            title="Selecione a pasta com arquivos XML",
            parent=self.window
        )
        
        if pasta:
            self.pasta_xml.set(pasta)
            self.adicionar_log(f"Pasta XML selecionada: {pasta}")
            self.atualizar_status("Pasta XML selecionada")
            
            # Contar arquivos XML
            try:
                xml_files = [f for f in os.listdir(pasta) if f.lower().endswith('.xml')]
                self.arquivos_total = len(xml_files)
                self.total_label.config(text=str(self.arquivos_total))
                self.adicionar_log(f"Encontrados {self.arquivos_total} arquivos XML")
            except Exception as e:
                self.adicionar_log(f"Erro ao contar arquivos: {e}", "ERROR")
    
    def selecionar_pasta_saida(self):
        """Seleciona pasta de saída"""
        pasta = filedialog.askdirectory(
            title="Selecione a pasta para relatórios",
            parent=self.window
        )
        
        if pasta:
            self.pasta_saida.set(pasta)
            self.adicionar_log(f"Pasta de saída selecionada: {pasta}")
            self.atualizar_status("Pasta de saída selecionada")
    
    def iniciar_processamento(self):
        """Inicia processamento de XMLs"""
        # Validações
        if not self.pasta_xml.get():
            messagebox.showwarning("Aviso", "Selecione a pasta com arquivos XML primeiro")
            return
            
        if not os.path.exists(self.pasta_xml.get()):
            messagebox.showerror("Erro", "Pasta de XMLs não existe")
            return
            
        if NFeProcessorBI is None:
            messagebox.showerror("Erro", "Módulo de processamento não disponível")
            return
        
        # Preparar interface
        self.processamento_ativo = True
        self.processamento_pausado = False
        self.deve_parar = False
        self.arquivos_processados = 0
        self.arquivos_com_erro = 0
        self.tempo_inicio = time.time()
        
        # Atualizar botões
        self.btn_processar.config(state="disabled")
        self.btn_pausar.config(state="normal")
        self.btn_parar.config(state="normal")
        self.btn_selecionar_xml.config(state="disabled")
        self.btn_selecionar_saida.config(state="disabled")
        
        # Iniciar thread de processamento
        self.processing_thread = threading.Thread(target=self.executar_processamento, daemon=True)
        self.processing_thread.start()
        
        # Iniciar timer de atualização
        self.atualizar_timer()
        
        self.adicionar_log("Processamento iniciado!")
        self.atualizar_status("Processando...")
    
    def executar_processamento(self):
        """Executa processamento em thread separada"""
        try:
            processor = NFeProcessorBI(self.pasta_xml.get(), self.pasta_saida.get())
            
            # Simular processamento com callback de progresso
            self.window.after(0, self.adicionar_log, "Criando instância do processador...")
            
            # Processar arquivos
            estatisticas = processor.processar_pasta()
            
            # Finalizar processamento
            self.window.after(0, self.processamento_finalizado, True, estatisticas)
            
        except Exception as e:
            self.window.after(0, self.processamento_finalizado, False, str(e))
    
    def pausar_processamento(self):
        """Pausa/retoma processamento"""
        if self.processamento_pausado:
            self.processamento_pausado = False
            self.btn_pausar.config(text="⏸️ Pausar")
            self.adicionar_log("Processamento retomado")
            self.atualizar_status("Processando...")
        else:
            self.processamento_pausado = True
            self.btn_pausar.config(text="▶️ Retomar")
            self.adicionar_log("Processamento pausado")
            self.atualizar_status("Processamento pausado")
    
    def parar_processamento(self):
        """Para processamento"""
        resposta = messagebox.askyesno(
            "Confirmar",
            "Deseja realmente parar o processamento?",
            parent=self.window
        )
        
        if resposta:
            self.deve_parar = True
            self.processamento_ativo = False
            self.adicionar_log("Processamento interrompido pelo usuário")
            self.atualizar_status("Processamento interrompido")
            self.resetar_interface()
    
    def processamento_finalizado(self, sucesso, resultado):
        """Callback quando processamento termina"""
        self.processamento_ativo = False
        
        if sucesso:
            self.adicionar_log("✅ Processamento concluído com sucesso!")
            self.atualizar_status("Processamento concluído")
            
            if isinstance(resultado, dict):
                for chave, valor in resultado.items():
                    self.adicionar_log(f"• {chave.replace('_', ' ').title()}: {valor}")
            
            # Atualizar progress bar para 100%
            self.progress_var.set(100)
            self.progress_label.config(text="100%")
            
            messagebox.showinfo("Sucesso", "Processamento concluído com sucesso!", parent=self.window)
        else:
            self.adicionar_log(f"❌ Erro no processamento: {resultado}", "ERROR")
            self.atualizar_status("Erro no processamento")
            messagebox.showerror("Erro", f"Erro no processamento:\n\n{resultado}", parent=self.window)
        
        self.resetar_interface()
    
    def resetar_interface(self):
        """Reseta interface após processamento"""
        self.btn_processar.config(state="normal")
        self.btn_pausar.config(state="disabled", text="⏸️ Pausar")
        self.btn_parar.config(state="disabled")
        self.btn_selecionar_xml.config(state="normal")
        self.btn_selecionar_saida.config(state="normal")
    
    def atualizar_timer(self):
        """Atualiza timer de processamento"""
        if self.processamento_ativo and self.tempo_inicio:
            tempo_decorrido = time.time() - self.tempo_inicio
            minutos = int(tempo_decorrido // 60)
            segundos = int(tempo_decorrido % 60)
            self.tempo_label.config(text=f"{minutos:02d}:{segundos:02d}")
            
            # Simular progresso (substitua pela lógica real)
            if self.arquivos_total > 0:
                progresso = (self.arquivos_processados / self.arquivos_total) * 100
                self.progress_var.set(progresso)
                self.progress_label.config(text=f"{progresso:.1f}%")
            
            # Continuar atualizando se ainda estiver processando
            if self.processamento_ativo:
                self.window.after(1000, self.atualizar_timer)
    
    def adicionar_log(self, mensagem, tipo="INFO"):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Cores por tipo
        cor_map = {
            "INFO": "black",
            "SUCCESS": "green",
            "WARNING": "orange",
            "ERROR": "red"
        }
        
        self.log_text.config(state=tk.NORMAL)
        
        # Inserir timestamp
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        
        # Inserir mensagem com cor
        self.log_text.insert(tk.END, f"{mensagem}\n", tipo.lower())
        
        # Configurar tags de cor
        self.log_text.tag_config("timestamp", foreground="blue", font=("Consolas", 9, "bold"))
        self.log_text.tag_config("info", foreground=cor_map.get("INFO", "black"))
        self.log_text.tag_config("success", foreground=cor_map.get("SUCCESS", "green"))
        self.log_text.tag_config("warning", foreground=cor_map.get("WARNING", "orange"))
        self.log_text.tag_config("error", foreground=cor_map.get("ERROR", "red"))
        
        # Auto-scroll
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def atualizar_status(self, mensagem):
        """Atualiza barra de status"""
        self.status_label.config(text=mensagem)
    
    def fechar_janela(self):
        """Fecha janela"""
        if self.processamento_ativo:
            resposta = messagebox.askyesno(
                "Confirmar",
                "Processamento em andamento. Deseja interromper e fechar?",
                parent=self.window
            )
            
            if resposta:
                self.deve_parar = True
                self.processamento_ativo = False
                self.window.destroy()
        else:
            self.window.destroy()
    
    def on_closing(self):
        """Evento de fechamento da janela"""
        self.fechar_janela()

# Função para abrir janela de processamento
def abrir_janela_processamento(parent):
    """Abre janela de processamento"""
    try:
        janela = JanelaProcessamento(parent)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir janela de processamento:\n{e}")
