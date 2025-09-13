# ui/config_reforma.py

import tkinter as tk
from tkinter import ttk, messagebox
from reforma_tributaria.config import ConfigReformaTributaria
from core.config import config_manager  # uso do gerenciador de config existente

class JanelaConfigReforma(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Configuração Reforma Tributária")
        self.resizable(False, False)

        # Ler ano atual
        ano = ConfigReformaTributaria.get_config_por_ano(
            ConfigReformaTributaria.get_config_por_ano.__annotations__['ano']
        ).ano_vigencia
        self.config = ConfigReformaTributaria.get_config_por_ano(ano)

        # Frame para opções
        frame = ttk.Frame(self, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")

        # CBS ativo
        self.var_cbs = tk.BooleanVar(value=self.config.cbs_ativo)
        chk_cbs = ttk.Checkbutton(frame, text="Ativar CBS", variable=self.var_cbs)
        chk_cbs.grid(row=0, column=0, sticky="w", pady=5)

        # IBS ativo
        self.var_ibs = tk.BooleanVar(value=self.config.ibs_ativo)
        chk_ibs = ttk.Checkbutton(frame, text="Ativar IBS", variable=self.var_ibs)
        chk_ibs.grid(row=1, column=0, sticky="w", pady=5)

        # IS ativo
        self.var_is = tk.BooleanVar(value=self.config.is_ativo)
        chk_is = ttk.Checkbutton(frame, text="Ativar IS", variable=self.var_is)
        chk_is.grid(row=2, column=0, sticky="w", pady=5)

        # Alíquota CBS
        ttk.Label(frame, text="Alíquota CBS (%):").grid(row=3, column=0, sticky="w")
        self.ent_cbs = ttk.Entry(frame)
        self.ent_cbs.insert(0, str(self.config.aliquota_cbs * 100))
        self.ent_cbs.grid(row=3, column=1, pady=5)

        # Alíquota IBS
        ttk.Label(frame, text="Alíquota IBS (%):").grid(row=4, column=0, sticky="w")
        self.ent_ibs = ttk.Entry(frame)
        self.ent_ibs.insert(0, str(self.config.aliquota_ibs * 100))
        self.ent_ibs.grid(row=4, column=1, pady=5)

        # Botões
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(10,0))
        ttk.Button(btn_frame, text="Salvar", command=self.salvar).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.destroy).grid(row=0, column=1, padx=5)

    def salvar(self):
        try:
            # Atualiza configurações
            ano = self.config.ano_vigencia
            cbs = self.var_cbs.get()
            ibs = self.var_ibs.get()
            is_ = self.var_is.get()
            aliquota_cbs = float(self.ent_cbs.get()) / 100
            aliquota_ibs = float(self.ent_ibs.get()) / 100

            # Grava no config_manager (arquivo config.ini)
            section = f"REFORMA_{ano}"
            config_manager.set(section, "cbs_ativo", str(cbs))
            config_manager.set(section, "ibs_ativo", str(ibs))
            config_manager.set(section, "is_ativo", str(is_))
            config_manager.set(section, "aliquota_cbs", str(aliquota_cbs))
            config_manager.set(section, "aliquota_ibs", str(aliquota_ibs))
            config_manager.save()

            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso.")
            self.destroy()
        except ValueError:
            messagebox.showerror("Erro", "Informe valores numéricos válidos para alíquotas.")
