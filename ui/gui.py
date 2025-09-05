# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import webbrowser

from processing.processor import NFeProcessor
from core.config import config_manager # <-- Importa o gestor de configuração

def iniciar_gui():
    """Inicia a interface gráfica (GUI) para seleção de pastas e processamento."""
    root = tk.Tk()
    root.title("Analisador de NFe/NFCe")
    root.geometry("600x450")
    root.minsize(500, 400)

    # --- Variáveis de Estado ---
    xml_folder = tk.StringVar(value=config_manager.get('PADRAO', 'pasta_xml'))
    output_folder = tk.StringVar(value=config_manager.get('PADRAO', 'pasta_saida'))
    processor_instance = None

    # --- Funções ---
    def select_folder(variable, title):
        path = filedialog.askdirectory(title=title)
        if path:
            variable.set(path)

    def run_processing_thread():
        nonlocal processor_instance
        if not xml_folder.get() or not output_folder.get():
            messagebox.showwarning("Atenção", "Por favor, selecione a pasta de XMLs e a pasta de saída.")
            return
        
        # Salva os caminhos no config.ini para a próxima vez
        config_manager.set('PADRAO', 'pasta_xml', xml_folder.get())
        config_manager.set('PADRAO', 'pasta_saida', output_folder.get())
        config_manager.save()

        # Desabilita botões e mostra progresso
        btn_processar.config(state=tk.DISABLED)
        btn_dashboard.config(state=tk.DISABLED)
        progress_bar.start(10)

        try:
            processor_instance = NFeProcessor(xml_folder.get(), output_folder.get())
            processor_instance.processar_pasta()
            processor_instance.calcular_resumos()
            processor_instance.gerar_relatorios()
            
            # Mostra resultados no log
            log_text.config(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            log_text.insert(tk.END, "--- Processamento Concluído ---\n\n")
            for key, value in processor_instance.estatisticas.items():
                log_text.insert(tk.END, f"{key.replace('_', ' ').title()}: {value}\n")
            log_text.config(state=tk.DISABLED)

            messagebox.showinfo("Sucesso", f"Processamento concluído!\nRelatórios salvos em: {output_folder.get()}")
            btn_dashboard.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
        finally:
            # Reabilita botões e para progresso
            progress_bar.stop()
            btn_processar.config(state=tk.NORMAL)

    def run_processing():
        # Inicia o processamento em uma nova thread para não bloquear a GUI
        threading.Thread(target=run_processing_thread, daemon=True).start()

    def open_dashboard():
        if processor_instance:
            # Lógica para abrir o dashboard web
            from ui.web import iniciar_dashboard_web
            threading.Thread(target=iniciar_dashboard_web, args=(processor_instance,), daemon=True).start()
            webbrowser.open_new("http://127.0.0.1:5000")

    # --- Layout da GUI ---
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Seleção de Pastas
    folder_frame = ttk.LabelFrame(main_frame, text="Configuração de Pastas", padding="10")
    folder_frame.pack(fill=tk.X, pady=(0, 20))

    ttk.Label(folder_frame, text="Pasta dos XMLs:").grid(row=0, column=0, sticky=tk.W, pady=2)
    entry_xml = ttk.Entry(folder_frame, textvariable=xml_folder)
    entry_xml.grid(row=0, column=1, sticky=tk.EW, padx=5)
    btn_select_xml = ttk.Button(folder_frame, text="Selecionar...", command=lambda: select_folder(xml_folder, "Selecione a pasta com os XMLs"))
    btn_select_xml.grid(row=0, column=2)

    ttk.Label(folder_frame, text="Pasta de Saída:").grid(row=1, column=0, sticky=tk.W, pady=2)
    entry_output = ttk.Entry(folder_frame, textvariable=output_folder)
    entry_output.grid(row=1, column=1, sticky=tk.EW, padx=5)
    btn_select_output = ttk.Button(folder_frame, text="Selecionar...", command=lambda: select_folder(output_folder, "Selecione a pasta para salvar os relatórios"))
    btn_select_output.grid(row=1, column=2)

    folder_frame.columnconfigure(1, weight=1)

    # Botões de Ação
    action_frame = ttk.Frame(main_frame)
    action_frame.pack(fill=tk.X, pady=10)
    btn_processar = ttk.Button(action_frame, text="▶ Iniciar Processamento", command=run_processing, style="Accent.TButton")
    btn_processar.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
    btn_dashboard = ttk.Button(action_frame, text="🚀 Abrir Dashboard Web", state=tk.DISABLED, command=open_dashboard)
    btn_dashboard.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))
    
    # Barra de Progresso
    progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
    progress_bar.pack(fill=tk.X, pady=10)

    # Log
    log_frame = ttk.LabelFrame(main_frame, text="Resultados do Processamento", padding="10")
    log_frame.pack(fill=tk.BOTH, expand=True)
    log_text = tk.Text(log_frame, height=8, state=tk.DISABLED, bg="#f0f0f0", relief=tk.SUNKEN, borderwidth=1)
    log_text.pack(fill=tk.BOTH, expand=True)

    # Estilo
    style = ttk.Style(root)
    style.configure("Accent.TButton", foreground="white", background="#0078d4")

    root.mainloop()

