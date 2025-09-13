# -*- coding: utf-8 -*-
import tkinter as tk
from cert.manager import CertificateManager
from cert.config import PFX_PATH, PFX_PASSWORD
from tkinter import filedialog, messagebox, ttk, simpledialog
import threading
import webbrowser
import logging
import os
# ui/gui.py
from cert.notifier import start_scheduler
from processing.processor import NFeProcessor
from core.config import config_manager
from sefaz_integration.client import SefazClient


def atualizar_status(label):
    mgr = CertificateManager(PFX_PATH, PFX_PASSWORD)
    dias = mgr.days_until_expiration()
    expira_em = mgr.get_expiration_date().strftime("%d/%m/%Y")
    if dias <= 0:
        cor, texto = "red", f"Certificado vencido em {-dias} dias!"
    elif dias <= 15:
        cor, texto = "orange", f"Vence em {dias} dias ({expira_em})"
    else:
        cor, texto = "green", f"Vence em {dias} dias ({expira_em})"
    label.config(text=texto, fg=cor)
    label.after(24*60*60*1000, lambda: atualizar_status(label))  # 24h

def criar_status_certificado(parent):
    mgr = CertificateManager(PFX_PATH, PFX_PASSWORD)
    label = tk.Label(parent)
    atualizar_status(label)
    frame = tk.Frame(parent, bd=1, relief="solid", padx=5, pady=5)
    label.pack(in_=frame)
    return frame


def iniciar_gui():
    """Inicia a interface gráfica (GUI) para seleção de pastas e processamento."""
    start_scheduler()
    root = tk.Tk()
    root.title("NFe Inspector")
    root.geometry("600x550") # Aumenta a altura para os novos campos
    root.minsize(500, 500)
     # Painel de status do certificado
    status_frame = criar_status_certificado(root)
    status_frame.pack(anchor="ne", pady=10, padx=10)

    # --- Variáveis de Estado ---
    xml_folder = tk.StringVar(value=config_manager.get('PADRAO', 'pasta_xml'))
    output_folder = tk.StringVar(value=config_manager.get('PADRAO', 'pasta_saida'))
    cert_path = tk.StringVar(value=config_manager.get('SEFAZ', 'caminho_certificado_a1'))
    cert_pass = tk.StringVar() # Senha nunca é guardada
    processor_instance = None

    # --- Funções ---
    def select_folder(variable, title):
        path = filedialog.askdirectory(title=title)
        if path:
            variable.set(path)

    def select_cert_file():
        path = filedialog.askopenfilename(
            title="Selecione o Certificado Digital A1",
            filetypes=[("Arquivos PFX", "*.pfx")]
        )
        if path:
            cert_path.set(path)

    def run_processing_thread():
        # Lógica de processamento... (sem alterações)
        nonlocal processor_instance
        if not xml_folder.get() or not output_folder.get():
            messagebox.showwarning("Atenção", "Por favor, selecione a pasta de XMLs e a pasta de saída.")
            return
        
        config_manager.set('PADRAO', 'pasta_xml', xml_folder.get())
        config_manager.set('PADRAO', 'pasta_saida', output_folder.get())
        config_manager.set('SEFAZ', 'caminho_certificado_a1', cert_path.get())
        config_manager.save()

        btn_processar.config(state=tk.DISABLED)
        btn_dashboard.config(state=tk.DISABLED)
        btn_consultar_sefaz.config(state=tk.DISABLED)
        progress_bar.start(10)

        try:
            processor_instance = NFeProcessor(xml_folder.get(), output_folder.get())
            processor_instance.processar_pasta()
            processor_instance.calcular_resumos()
            processor_instance.gerar_relatorios()
            
            log_text.config(state=tk.NORMAL)
            log_text.delete(1.0, tk.END)
            log_text.insert(tk.END, "--- Processamento Concluído ---\n\n")
            for key, value in processor_instance.estatisticas.items():
                log_text.insert(tk.END, f"{key.replace('_', ' ').title()}: {value}\n")
            log_text.config(state=tk.DISABLED)

            messagebox.showinfo("Sucesso", f"Processamento concluído!\nRelatórios salvos em: {output_folder.get()}")
            btn_dashboard.config(state=tk.NORMAL)
            btn_consultar_sefaz.config(state=tk.NORMAL)

        except Exception as e:
            messagebox.showerror("Erro", f"Ocorreu um erro: {e}")
            logging.error(f"Erro no processamento: {e}", exc_info=True)
        finally:
            progress_bar.stop()
            btn_processar.config(state=tk.NORMAL)

    def run_processing():
        threading.Thread(target=run_processing_thread, daemon=True).start()

    def open_dashboard():
        if processor_instance:
            from ui.web import iniciar_dashboard_web
            threading.Thread(target=iniciar_dashboard_web, args=(processor_instance,), daemon=True).start()
            webbrowser.open_new("http://127.0.0.1:5000")

    def run_sefaz_consult_thread(chave):
        """Thread para consultar a SEFAZ sem bloquear a GUI."""
        # Validações antes de iniciar
        caminho_certificado = cert_path.get()
        senha_certificado = cert_pass.get()
        
        if not caminho_certificado or not os.path.exists(caminho_certificado):
            messagebox.showerror("Erro de Configuração", "O caminho para o certificado digital é inválido ou não foi preenchido.")
            return
        if not senha_certificado:
            messagebox.showerror("Erro de Configuração", "A senha do certificado digital é obrigatória.")
            return

        try:
            messagebox.showinfo("Consultando...", "A contactar a SEFAZ. Por favor, aguarde...", parent=root)
            client = SefazClient(certificado_path=caminho_certificado, senha_certificado=senha_certificado)
            resultado = client.consultar_chave(chave)
            
            resultado_formatado = "\n".join([f"{key.replace('_', ' ').title()}: {value}" for key, value in resultado.items()])
            messagebox.showinfo("Resultado da Consulta SEFAZ", resultado_formatado)

        except Exception as e:
            messagebox.showerror("Erro na Consulta SEFAZ", f"Não foi possível consultar a chave:\n{e}")
            logging.error(f"Erro na consulta SEFAZ: {e}", exc_info=True)

    def consultar_sefaz():
        """Pede uma chave de acesso ao utilizador e consulta na SEFAZ."""
        chave = simpledialog.askstring("Consulta de NFe", "Digite a chave de acesso da NFe (apenas números):", parent=root)
        if chave and chave.isdigit() and len(chave) == 44:
            threading.Thread(target=run_sefaz_consult_thread, args=(chave,), daemon=True).start()
        elif chave:
            messagebox.showwarning("Chave Inválida", "A chave de acesso deve conter 44 números.")

    # --- Layout da GUI ---
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)

    # Frame de Pastas
    folder_frame = ttk.LabelFrame(main_frame, text="Configuração de Pastas", padding="10")
    folder_frame.pack(fill=tk.X, pady=(0, 10))
    # ... (código dos campos de pasta sem alteração) ...
    ttk.Label(folder_frame, text="Pasta dos XMLs:").grid(row=0, column=0, sticky=tk.W, pady=2)
    ttk.Entry(folder_frame, textvariable=xml_folder).grid(row=0, column=1, sticky=tk.EW, padx=5)
    ttk.Button(folder_frame, text="Selecionar...", command=lambda: select_folder(xml_folder, "Selecione a pasta com os XMLs")).grid(row=0, column=2)
    ttk.Label(folder_frame, text="Pasta de Saída:").grid(row=1, column=0, sticky=tk.W, pady=2)
    ttk.Entry(folder_frame, textvariable=output_folder).grid(row=1, column=1, sticky=tk.EW, padx=5)
    ttk.Button(folder_frame, text="Selecionar...", command=lambda: select_folder(output_folder, "Selecione a pasta para salvar os relatórios")).grid(row=1, column=2)
    folder_frame.columnconfigure(1, weight=1)

    # --- NOVA SECÇÃO PARA O CERTIFICADO ---
    sefaz_frame = ttk.LabelFrame(main_frame, text="Configuração SEFAZ", padding="10")
    sefaz_frame.pack(fill=tk.X, pady=10)

    ttk.Label(sefaz_frame, text="Certificado A1 (.pfx):").grid(row=0, column=0, sticky=tk.W, pady=2)
    ttk.Entry(sefaz_frame, textvariable=cert_path).grid(row=0, column=1, sticky=tk.EW, padx=5)
    ttk.Button(sefaz_frame, text="Selecionar...", command=select_cert_file).grid(row=0, column=2)
    
    ttk.Label(sefaz_frame, text="Senha do Certificado:").grid(row=1, column=0, sticky=tk.W, pady=2)
    ttk.Entry(sefaz_frame, textvariable=cert_pass, show="*").grid(row=1, column=1, columnspan=2, sticky=tk.EW, padx=5)

    sefaz_frame.columnconfigure(1, weight=1)

    # Botões de Ação
    action_frame = ttk.Frame(main_frame)
    action_frame.pack(fill=tk.X, pady=10)
    btn_processar = ttk.Button(action_frame, text="▶ Iniciar Processamento", command=run_processing, style="Accent.TButton")
    btn_processar.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
    btn_dashboard = ttk.Button(action_frame, text="🚀 Abrir Dashboard Web", state=tk.DISABLED, command=open_dashboard)
    btn_dashboard.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))
    
    btn_consultar_sefaz = ttk.Button(main_frame, text="🔍 Consultar Chave na SEFAZ", command=consultar_sefaz)
    btn_consultar_sefaz.pack(fill=tk.X, pady=5)

    progress_bar = ttk.Progressbar(main_frame, mode='indeterminate')
    progress_bar.pack(fill=tk.X, pady=10)

    log_frame = ttk.LabelFrame(main_frame, text="Resultados do Processamento", padding="10")
    log_frame.pack(fill=tk.BOTH, expand=True)
    log_text = tk.Text(log_frame, height=5, state=tk.DISABLED, bg="#f0f0f0", relief=tk.SUNKEN, borderwidth=1)
    log_text.pack(fill=tk.BOTH, expand=True)

    style = ttk.Style(root)
    style.configure("Accent.TButton", foreground="white", background="#0078d4")

    root.mainloop()

