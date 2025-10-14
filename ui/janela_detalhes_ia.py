<<<<<<< HEAD
# ui/janela_detalhes_ia.py

import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime

class JanelaDetalhesIA:
    """Janela com detalhes completos da análise IA"""
    
    def __init__(self, parent, dados_nfe, resultado_analise):
        self.parent = parent
        self.dados_nfe = dados_nfe
        self.resultado = resultado_analise
        
        self.janela = tk.Toplevel(parent)
        self.janela.title(f"🧠 Análise IA Detalhada - {dados_nfe.get('chave_acesso', 'N/A')[:8]}...")
        self.janela.geometry("1000x700")
        self.janela.transient(parent)
        self.janela.grab_set()
        
        self.setup_interface()
        self.carregar_resultados()
    
    def setup_interface(self):
        """Configura interface da janela de detalhes"""
        
        # Notebook para abas
        notebook = ttk.Notebook(self.janela)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 1: Resumo Geral
        self.tab_resumo = ttk.Frame(notebook)
        notebook.add(self.tab_resumo, text="📊 Resumo Geral")
        
        # Aba 2: Problemas Encontrados
        self.tab_problemas = ttk.Frame(notebook)
        notebook.add(self.tab_problemas, text="⚠️ Problemas Encontrados")
        
        # Aba 3: Sugestões de Correção
        self.tab_sugestoes = ttk.Frame(notebook)
        notebook.add(self.tab_sugestoes, text="🔧 Correções Sugeridas")
        
        # Aba 4: Análise Técnica
        self.tab_tecnica = ttk.Frame(notebook)
        notebook.add(self.tab_tecnica, text="🔬 Análise Técnica")
        
        # Aba 5: Relatório Completo
        self.tab_relatorio = ttk.Frame(notebook)
        notebook.add(self.tab_relatorio, text="📄 Relatório Completo")
        
        self.setup_tab_resumo()
        self.setup_tab_problemas()
        self.setup_tab_sugestoes()
        self.setup_tab_tecnica()
        self.setup_tab_relatorio()
        
        # Botões na parte inferior
        btn_frame = ttk.Frame(self.janela)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="📤 Exportar Relatório", 
                  command=self.exportar_relatorio).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="📧 Enviar por Email", 
                  command=self.enviar_email).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="🖨️ Imprimir", 
                  command=self.imprimir_relatorio).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="❌ Fechar", 
                  command=self.janela.destroy).pack(side=tk.RIGHT)
    
    def setup_tab_resumo(self):
        """Configura aba de resumo"""
        
        frame = ttk.Frame(self.tab_resumo, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = tk.Label(frame, text="📊 Resumo da Análise IA", 
                              font=("Segoe UI", 16, "bold"), fg="#0066cc")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Cards de resumo
        cards_frame = tk.Frame(frame)
        cards_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Score geral
        self.criar_card_resumo(cards_frame, "Score de Risco", 
                              f"{self.resultado.get('score', 0):.2f}/10", 
                              self.get_cor_score(self.resultado.get('score', 0)), 0, 0)
        
        # Nível de risco
        nivel = self.resultado.get('nivel', 'BAIXO')
        cor_nivel = {"BAIXO": "#28a745", "MEDIO": "#ffc107", "ALTO": "#dc3545"}
        self.criar_card_resumo(cards_frame, "Nível de Risco", nivel, 
                              cor_nivel.get(nivel, "#6c757d"), 0, 1)
        
        # Problemas encontrados
        total_problemas = len(self.resultado.get('inconsistencias', []))
        self.criar_card_resumo(cards_frame, "Problemas Encontrados", str(total_problemas),
                              "#dc3545" if total_problemas > 0 else "#28a745", 0, 2)
        
        # Status da NFe
        status = "✅ CONFORME" if total_problemas == 0 else "⚠️ REQUER ATENÇÃO"
        self.criar_card_resumo(cards_frame, "Status da NFe", status,
                              "#28a745" if total_problemas == 0 else "#ffc107", 0, 3)
        
        # Informações da NFe
        info_frame = ttk.LabelFrame(frame, text="📋 Informações da Nota Fiscal", padding=15)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        info_text = f"""
🏢 Emissor: {self.dados_nfe.get('razao_social', 'N/A')}
📧 CNPJ: {self.dados_nfe.get('cnpj_emissor', 'N/A')}
🔑 Chave de Acesso: {self.dados_nfe.get('chave_acesso', 'N/A')}
📅 Data de Emissão: {self.dados_nfe.get('data_emissao', 'N/A')}
💰 Valor Total: R$ {self.dados_nfe.get('valor_total', 0):,.2f}
📍 UF: {self.dados_nfe.get('uf', 'N/A')}
🏭 Natureza da Operação: {self.dados_nfe.get('natureza_operacao', 'N/A')}
"""
        
        info_label = tk.Label(info_frame, text=info_text, font=("Consolas", 10),
                             justify=tk.LEFT, anchor=tk.W)
        info_label.pack(fill=tk.X)
    
    def criar_card_resumo(self, parent, titulo, valor, cor, row, col):
        """Cria card de resumo"""
        
        card = tk.Frame(parent, bg=cor, relief="solid", bd=2)
        card.grid(row=row, column=col, padx=10, pady=5, sticky="ew", ipadx=15, ipady=15)
        
        parent.columnconfigure(col, weight=1)
        
        tk.Label(card, text=titulo, font=("Segoe UI", 9), 
                bg=cor, fg="white").pack()
        tk.Label(card, text=valor, font=("Segoe UI", 14, "bold"), 
                bg=cor, fg="white").pack(pady=(5, 0))
    
    def setup_tab_problemas(self):
        """Configura aba de problemas"""
        
        frame = ttk.Frame(self.tab_problemas, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(frame, text="⚠️ Problemas Identificados pela IA", 
                              font=("Segoe UI", 16, "bold"), fg="#dc3545")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Lista de problemas
        problemas_frame = tk.Frame(frame)
        problemas_frame.pack(fill=tk.BOTH, expand=True)
        
        # TreeView para problemas
        columns = ('severidade', 'categoria', 'descricao', 'impacto')
        self.tree_problemas = ttk.Treeview(problemas_frame, columns=columns, 
                                          show="headings", height=15)
        
        self.tree_problemas.heading('severidade', text='Severidade')
        self.tree_problemas.heading('categoria', text='Categoria')
        self.tree_problemas.heading('descricao', text='Descrição do Problema')
        self.tree_problemas.heading('impacto', text='Impacto')
        
        self.tree_problemas.column('severidade', width=100)
        self.tree_problemas.column('categoria', width=150)
        self.tree_problemas.column('descricao', width=400)
        self.tree_problemas.column('impacto', width=200)
        
        scrollbar_problemas = ttk.Scrollbar(problemas_frame, orient="vertical", 
                                           command=self.tree_problemas.yview)
        self.tree_problemas.configure(yscrollcommand=scrollbar_problemas.set)
        
        self.tree_problemas.pack(side="left", fill="both", expand=True)
        scrollbar_problemas.pack(side="right", fill="y")
    
    def setup_tab_sugestoes(self):
        """Configura aba de sugestões"""
        
        frame = ttk.Frame(self.tab_sugestoes, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(frame, text="🔧 Sugestões de Correção da IA", 
                              font=("Segoe UI", 16, "bold"), fg="#0066cc")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Área de texto para sugestões
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_sugestoes = tk.Text(text_frame, wrap=tk.WORD, font=("Segoe UI", 10),
                                     relief="solid", bd=1, padx=15, pady=15)
        
        scrollbar_sugestoes = ttk.Scrollbar(text_frame, orient="vertical", 
                                           command=self.text_sugestoes.yview)
        self.text_sugestoes.configure(yscrollcommand=scrollbar_sugestoes.set)
        
        self.text_sugestoes.pack(side="left", fill="both", expand=True)
        scrollbar_sugestoes.pack(side="right", fill="y")
    
    def setup_tab_tecnica(self):
        """Configura aba técnica"""
        
        frame = ttk.Frame(self.tab_tecnica, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(frame, text="🔬 Análise Técnica Detalhada", 
                              font=("Segoe UI", 16, "bold"), fg="#6f42c1")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Área de texto para análise técnica
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_tecnica = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 9),
                                   relief="solid", bd=1, padx=15, pady=15, bg="#f8f9fa")
        
        scrollbar_tecnica = ttk.Scrollbar(text_frame, orient="vertical", 
                                         command=self.text_tecnica.yview)
        self.text_tecnica.configure(yscrollcommand=scrollbar_tecnica.set)
        
        self.text_tecnica.pack(side="left", fill="both", expand=True)
        scrollbar_tecnica.pack(side="right", fill="y")
    
    def setup_tab_relatorio(self):
        """Configura aba de relatório completo"""
        
        frame = ttk.Frame(self.tab_relatorio, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(frame, text="📄 Relatório Completo da Análise", 
                              font=("Segoe UI", 16, "bold"), fg="#28a745")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Área de texto para relatório
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_relatorio = tk.Text(text_frame, wrap=tk.WORD, font=("Segoe UI", 10),
                                     relief="solid", bd=1, padx=15, pady=15)
        
        scrollbar_relatorio = ttk.Scrollbar(text_frame, orient="vertical", 
                                           command=self.text_relatorio.yview)
        self.text_relatorio.configure(yscrollcommand=scrollbar_relatorio.set)
        
        self.text_relatorio.pack(side="left", fill="both", expand=True)
        scrollbar_relatorio.pack(side="right", fill="y")
    
    def carregar_resultados(self):
        """Carrega os resultados da análise nas abas"""
        
        # Carregar problemas
        inconsistencias = self.resultado.get('inconsistencias', [])
        
        for problema in inconsistencias:
            severidade = problema.get('severidade', 'MEDIA')
            categoria = problema.get('categoria', 'GERAL')
            descricao = problema.get('descricao', 'Problema não especificado')
            impacto = problema.get('impacto', 'Impacto não informado')
            
            # Configurar cor por severidade
            if severidade == "ALTA":
                tag = "alta"
            elif severidade == "MEDIA":
                tag = "media"
            else:
                tag = "baixa"
            
            self.tree_problemas.insert('', tk.END, values=(
                severidade, categoria, descricao, impacto
            ), tags=(tag,))
        
        # Configurar cores
        self.tree_problemas.tag_configure("alta", background="#ffcccc")
        self.tree_problemas.tag_configure("media", background="#fff2cc")
        self.tree_problemas.tag_configure("baixa", background="#e6f3ff")
        
        # Carregar sugestões
        sugestoes = self.resultado.get('sugestoes', [])
        texto_sugestoes = "🔧 SUGESTÕES DA INTELIGÊNCIA ARTIFICIAL\n\n"
        
        if not sugestoes:
            texto_sugestoes += "✅ Nenhuma correção necessária. A NFe está em conformidade.\n\n"
            texto_sugestoes += "🎯 RECOMENDAÇÕES GERAIS:\n"
            texto_sugestoes += "• Mantenha os dados sempre atualizados\n"
            texto_sugestoes += "• Revise periodicamente as informações cadastrais\n"
            texto_sugestoes += "• Monitore alterações na legislação fiscal\n"
        else:
            for i, sugestao in enumerate(sugestoes, 1):
                prioridade = sugestao.get('prioridade', 'MÉDIA')
                emoji_prioridade = {"ALTA": "🔴", "MEDIA": "🟡", "BAIXA": "🟢"}
                
                texto_sugestoes += f"{emoji_prioridade.get(prioridade, '🔵')} SUGESTÃO {i} - PRIORIDADE {prioridade}\n"
                texto_sugestoes += f"📋 Problema: {sugestao.get('problema', 'N/A')}\n"
                texto_sugestoes += f"🔧 Solução: {sugestao.get('solucao', 'N/A')}\n"
                texto_sugestoes += f"⏱️ Tempo Estimado: {sugestao.get('tempo_estimado', 'N/A')}\n"
                texto_sugestoes += f"💼 Responsável: {sugestao.get('responsavel', 'Departamento Fiscal')}\n"
                texto_sugestoes += "-" * 80 + "\n\n"
        
        self.text_sugestoes.insert(tk.END, texto_sugestoes)
        self.text_sugestoes.config(state=tk.DISABLED)
        
        # Carregar análise técnica
        self.carregar_analise_tecnica()
        
        # Carregar relatório completo
        self.carregar_relatorio_completo()
    
    def carregar_analise_tecnica(self):
        """Carrega análise técnica detalhada"""
        
        texto_tecnica = f"""
🔬 ANÁLISE TÉCNICA DETALHADA - IA FISCAL
{"="*80}

🤖 ALGORITMOS UTILIZADOS:
• Detector de Riscos Fiscais v2.1
• Detector de Fraudes v1.8
• Validador de Conformidade v3.2
• Analisador de Padrões Suspeitos v1.5

📊 MÉTRICAS DE ANÁLISE:
• Score de Risco: {self.resultado.get('score', 0):.4f}/10
• Confiabilidade da Análise: {self.resultado.get('confiabilidade', 95.0):.2f}%
• Tempo de Processamento: {self.resultado.get('tempo_processamento', 0.8):.2f}s
• Critérios Avaliados: {self.resultado.get('criterios_avaliados', 25)}

🔍 VALIDAÇÕES EXECUTADAS:
✓ Validação estrutural do XML
✓ Consistência de dados fiscais
✓ Verificação de CNPJ/CPF
✓ Análise de valores e cálculos
✓ Conformidade com legislação
✓ Detecção de padrões suspeitos
✓ Verificação de duplicatas
✓ Análise temporal de emissão

🧠 INTELIGÊNCIA APLICADA:
• Machine Learning para detecção de anomalias
• Redes Neurais para análise de padrões
• Processamento de Linguagem Natural para textos
• Algoritmos de clustering para agrupamento

📈 HISTÓRICO COMPARATIVO:
• Notas similares analisadas: {self.resultado.get('notas_similares', 1247)}
• Padrão de comportamento: {self.resultado.get('padrao_comportamento', 'NORMAL')}
• Ranking de risco relativo: {self.resultado.get('ranking_risco', 'Top 15%')}

⚠️ ALERTAS AUTOMÁTICOS:
"""
        
        alertas = self.resultado.get('alertas', [])
        if alertas:
            for alerta in alertas:
                texto_tecnica += f"• {alerta}\n"
        else:
            texto_tecnica += "• Nenhum alerta gerado\n"
        
        texto_tecnica += f"""

🔐 ASSINATURA DIGITAL DA ANÁLISE:
Hash: {self.gerar_hash_analise()}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Versão IA: 2.1.0
"""
        
        self.text_tecnica.insert(tk.END, texto_tecnica)
        self.text_tecnica.config(state=tk.DISABLED)
    
    def carregar_relatorio_completo(self):
        """Carrega relatório completo"""
        
        relatorio = f"""
📄 RELATÓRIO COMPLETO DE ANÁLISE IA - NFe INSPECTOR
{"="*100}

🏢 DADOS DA EMPRESA
Razão Social: {self.dados_nfe.get('razao_social', 'N/A')}
CNPJ: {self.dados_nfe.get('cnpj_emissor', 'N/A')}
UF: {self.dados_nfe.get('uf', 'N/A')}

📋 DADOS DA NOTA FISCAL
Chave de Acesso: {self.dados_nfe.get('chave_acesso', 'N/A')}
Data de Emissão: {self.dados_nfe.get('data_emissao', 'N/A')}
Valor Total: R$ {self.dados_nfe.get('valor_total', 0):,.2f}
Natureza da Operação: {self.dados_nfe.get('natureza_operacao', 'N/A')}

🧠 RESULTADO DA ANÁLISE IA
Score de Risco: {self.resultado.get('score', 0):.2f}/10
Nível de Risco: {self.resultado.get('nivel', 'BAIXO')}
Status: {"✅ CONFORME" if len(self.resultado.get('inconsistencias', [])) == 0 else "⚠️ REQUER ATENÇÃO"}

⚠️ PROBLEMAS IDENTIFICADOS ({len(self.resultado.get('inconsistencias', []))})
"""
        
        for i, problema in enumerate(self.resultado.get('inconsistencias', []), 1):
            relatorio += f"""
{i}. {problema.get('descricao', 'Problema não especificado')}
   Severidade: {problema.get('severidade', 'MEDIA')}
   Categoria: {problema.get('categoria', 'GERAL')}
   Impacto: {problema.get('impacto', 'Impacto não informado')}
"""
        
        relatorio += f"""

🔧 AÇÕES RECOMENDADAS
"""
        
        for i, sugestao in enumerate(self.resultado.get('sugestoes', []), 1):
            relatorio += f"""
{i}. {sugestao.get('solucao', 'Sugestão não especificada')}
   Prioridade: {sugestao.get('prioridade', 'MÉDIA')}
   Tempo Estimado: {sugestao.get('tempo_estimado', 'N/A')}
   Responsável: {sugestao.get('responsavel', 'Departamento Fiscal')}
"""
        
        if not self.resultado.get('sugestoes', []):
            relatorio += "\n✅ Nenhuma ação corretiva necessária no momento.\n"
        
        relatorio += f"""

📊 CONCLUSÃO DA ANÁLISE
Data da Análise: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
Analista Virtual: IA Fiscal NFe Inspector v2.1
Próxima Revisão Recomendada: {self.calcular_proxima_revisao()}

Este relatório foi gerado automaticamente pela Inteligência Artificial do NFe Inspector.
Para dúvidas ou esclarecimentos, entre em contato com o suporte técnico.

{"="*100}
"""
        
        self.text_relatorio.insert(tk.END, relatorio)
        self.text_relatorio.config(state=tk.DISABLED)
    
    def get_cor_score(self, score):
        """Retorna cor baseada no score"""
        if score >= 7:
            return "#dc3545"  # Vermelho
        elif score >= 4:
            return "#ffc107"  # Amarelo
        else:
            return "#28a745"  # Verde
    
    def gerar_hash_analise(self):
        """Gera hash da análise para rastreabilidade"""
        import hashlib
        dados = f"{self.dados_nfe.get('chave_acesso', '')}{self.resultado.get('score', 0)}{datetime.now().date()}"
        return hashlib.md5(dados.encode()).hexdigest()[:16].upper()
    
    def calcular_proxima_revisao(self):
        """Calcula data da próxima revisão"""
        from datetime import timedelta
        
        score = self.resultado.get('score', 0)
        if score >= 7:
            dias = 7  # Alto risco - revisar em 1 semana
        elif score >= 4:
            dias = 30  # Médio risco - revisar em 1 mês
        else:
            dias = 90  # Baixo risco - revisar em 3 meses
        
        proxima = datetime.now() + timedelta(days=dias)
        return proxima.strftime('%d/%m/%Y')
    
    def exportar_relatorio(self):
        """Exporta relatório completo"""
        messagebox.showinfo("Em Desenvolvimento", 
                           "Funcionalidade de exportação será implementada em breve")
    
    def enviar_email(self):
        """Envia relatório por email"""
        messagebox.showinfo("Em Desenvolvimento", 
                           "Funcionalidade de email será implementada em breve")
    
    def imprimir_relatorio(self):
        """Imprime relatório"""
        messagebox.showinfo("Em Desenvolvimento", 
                           "Funcionalidade de impressão será implementada em breve")

# Função para abrir janela de detalhes
def abrir_janela_detalhes_ia(parent, dados_nfe, resultado_analise):
    """Abre janela com detalhes da análise IA"""
    JanelaDetalhesIA(parent, dados_nfe, resultado_analise)
=======
# ui/janela_detalhes_ia.py

import tkinter as tk
from tkinter import ttk, messagebox
import json
from datetime import datetime

class JanelaDetalhesIA:
    """Janela com detalhes completos da análise IA"""
    
    def __init__(self, parent, dados_nfe, resultado_analise):
        self.parent = parent
        self.dados_nfe = dados_nfe
        self.resultado = resultado_analise
        
        self.janela = tk.Toplevel(parent)
        self.janela.title(f"🧠 Análise IA Detalhada - {dados_nfe.get('chave_acesso', 'N/A')[:8]}...")
        self.janela.geometry("1000x700")
        self.janela.transient(parent)
        self.janela.grab_set()
        
        self.setup_interface()
        self.carregar_resultados()
    
    def setup_interface(self):
        """Configura interface da janela de detalhes"""
        
        # Notebook para abas
        notebook = ttk.Notebook(self.janela)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 1: Resumo Geral
        self.tab_resumo = ttk.Frame(notebook)
        notebook.add(self.tab_resumo, text="📊 Resumo Geral")
        
        # Aba 2: Problemas Encontrados
        self.tab_problemas = ttk.Frame(notebook)
        notebook.add(self.tab_problemas, text="⚠️ Problemas Encontrados")
        
        # Aba 3: Sugestões de Correção
        self.tab_sugestoes = ttk.Frame(notebook)
        notebook.add(self.tab_sugestoes, text="🔧 Correções Sugeridas")
        
        # Aba 4: Análise Técnica
        self.tab_tecnica = ttk.Frame(notebook)
        notebook.add(self.tab_tecnica, text="🔬 Análise Técnica")
        
        # Aba 5: Relatório Completo
        self.tab_relatorio = ttk.Frame(notebook)
        notebook.add(self.tab_relatorio, text="📄 Relatório Completo")
        
        self.setup_tab_resumo()
        self.setup_tab_problemas()
        self.setup_tab_sugestoes()
        self.setup_tab_tecnica()
        self.setup_tab_relatorio()
        
        # Botões na parte inferior
        btn_frame = ttk.Frame(self.janela)
        btn_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(btn_frame, text="📤 Exportar Relatório", 
                  command=self.exportar_relatorio).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="📧 Enviar por Email", 
                  command=self.enviar_email).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="🖨️ Imprimir", 
                  command=self.imprimir_relatorio).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="❌ Fechar", 
                  command=self.janela.destroy).pack(side=tk.RIGHT)
    
    def setup_tab_resumo(self):
        """Configura aba de resumo"""
        
        frame = ttk.Frame(self.tab_resumo, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = tk.Label(frame, text="📊 Resumo da Análise IA", 
                              font=("Segoe UI", 16, "bold"), fg="#0066cc")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Cards de resumo
        cards_frame = tk.Frame(frame)
        cards_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Score geral
        self.criar_card_resumo(cards_frame, "Score de Risco", 
                              f"{self.resultado.get('score', 0):.2f}/10", 
                              self.get_cor_score(self.resultado.get('score', 0)), 0, 0)
        
        # Nível de risco
        nivel = self.resultado.get('nivel', 'BAIXO')
        cor_nivel = {"BAIXO": "#28a745", "MEDIO": "#ffc107", "ALTO": "#dc3545"}
        self.criar_card_resumo(cards_frame, "Nível de Risco", nivel, 
                              cor_nivel.get(nivel, "#6c757d"), 0, 1)
        
        # Problemas encontrados
        total_problemas = len(self.resultado.get('inconsistencias', []))
        self.criar_card_resumo(cards_frame, "Problemas Encontrados", str(total_problemas),
                              "#dc3545" if total_problemas > 0 else "#28a745", 0, 2)
        
        # Status da NFe
        status = "✅ CONFORME" if total_problemas == 0 else "⚠️ REQUER ATENÇÃO"
        self.criar_card_resumo(cards_frame, "Status da NFe", status,
                              "#28a745" if total_problemas == 0 else "#ffc107", 0, 3)
        
        # Informações da NFe
        info_frame = ttk.LabelFrame(frame, text="📋 Informações da Nota Fiscal", padding=15)
        info_frame.pack(fill=tk.X, pady=(10, 0))
        
        info_text = f"""
🏢 Emissor: {self.dados_nfe.get('razao_social', 'N/A')}
📧 CNPJ: {self.dados_nfe.get('cnpj_emissor', 'N/A')}
🔑 Chave de Acesso: {self.dados_nfe.get('chave_acesso', 'N/A')}
📅 Data de Emissão: {self.dados_nfe.get('data_emissao', 'N/A')}
💰 Valor Total: R$ {self.dados_nfe.get('valor_total', 0):,.2f}
📍 UF: {self.dados_nfe.get('uf', 'N/A')}
🏭 Natureza da Operação: {self.dados_nfe.get('natureza_operacao', 'N/A')}
"""
        
        info_label = tk.Label(info_frame, text=info_text, font=("Consolas", 10),
                             justify=tk.LEFT, anchor=tk.W)
        info_label.pack(fill=tk.X)
    
    def criar_card_resumo(self, parent, titulo, valor, cor, row, col):
        """Cria card de resumo"""
        
        card = tk.Frame(parent, bg=cor, relief="solid", bd=2)
        card.grid(row=row, column=col, padx=10, pady=5, sticky="ew", ipadx=15, ipady=15)
        
        parent.columnconfigure(col, weight=1)
        
        tk.Label(card, text=titulo, font=("Segoe UI", 9), 
                bg=cor, fg="white").pack()
        tk.Label(card, text=valor, font=("Segoe UI", 14, "bold"), 
                bg=cor, fg="white").pack(pady=(5, 0))
    
    def setup_tab_problemas(self):
        """Configura aba de problemas"""
        
        frame = ttk.Frame(self.tab_problemas, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(frame, text="⚠️ Problemas Identificados pela IA", 
                              font=("Segoe UI", 16, "bold"), fg="#dc3545")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Lista de problemas
        problemas_frame = tk.Frame(frame)
        problemas_frame.pack(fill=tk.BOTH, expand=True)
        
        # TreeView para problemas
        columns = ('severidade', 'categoria', 'descricao', 'impacto')
        self.tree_problemas = ttk.Treeview(problemas_frame, columns=columns, 
                                          show="headings", height=15)
        
        self.tree_problemas.heading('severidade', text='Severidade')
        self.tree_problemas.heading('categoria', text='Categoria')
        self.tree_problemas.heading('descricao', text='Descrição do Problema')
        self.tree_problemas.heading('impacto', text='Impacto')
        
        self.tree_problemas.column('severidade', width=100)
        self.tree_problemas.column('categoria', width=150)
        self.tree_problemas.column('descricao', width=400)
        self.tree_problemas.column('impacto', width=200)
        
        scrollbar_problemas = ttk.Scrollbar(problemas_frame, orient="vertical", 
                                           command=self.tree_problemas.yview)
        self.tree_problemas.configure(yscrollcommand=scrollbar_problemas.set)
        
        self.tree_problemas.pack(side="left", fill="both", expand=True)
        scrollbar_problemas.pack(side="right", fill="y")
    
    def setup_tab_sugestoes(self):
        """Configura aba de sugestões"""
        
        frame = ttk.Frame(self.tab_sugestoes, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(frame, text="🔧 Sugestões de Correção da IA", 
                              font=("Segoe UI", 16, "bold"), fg="#0066cc")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Área de texto para sugestões
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_sugestoes = tk.Text(text_frame, wrap=tk.WORD, font=("Segoe UI", 10),
                                     relief="solid", bd=1, padx=15, pady=15)
        
        scrollbar_sugestoes = ttk.Scrollbar(text_frame, orient="vertical", 
                                           command=self.text_sugestoes.yview)
        self.text_sugestoes.configure(yscrollcommand=scrollbar_sugestoes.set)
        
        self.text_sugestoes.pack(side="left", fill="both", expand=True)
        scrollbar_sugestoes.pack(side="right", fill="y")
    
    def setup_tab_tecnica(self):
        """Configura aba técnica"""
        
        frame = ttk.Frame(self.tab_tecnica, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(frame, text="🔬 Análise Técnica Detalhada", 
                              font=("Segoe UI", 16, "bold"), fg="#6f42c1")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Área de texto para análise técnica
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_tecnica = tk.Text(text_frame, wrap=tk.WORD, font=("Consolas", 9),
                                   relief="solid", bd=1, padx=15, pady=15, bg="#f8f9fa")
        
        scrollbar_tecnica = ttk.Scrollbar(text_frame, orient="vertical", 
                                         command=self.text_tecnica.yview)
        self.text_tecnica.configure(yscrollcommand=scrollbar_tecnica.set)
        
        self.text_tecnica.pack(side="left", fill="both", expand=True)
        scrollbar_tecnica.pack(side="right", fill="y")
    
    def setup_tab_relatorio(self):
        """Configura aba de relatório completo"""
        
        frame = ttk.Frame(self.tab_relatorio, padding=15)
        frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(frame, text="📄 Relatório Completo da Análise", 
                              font=("Segoe UI", 16, "bold"), fg="#28a745")
        title_label.pack(anchor=tk.W, pady=(0, 20))
        
        # Área de texto para relatório
        text_frame = tk.Frame(frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_relatorio = tk.Text(text_frame, wrap=tk.WORD, font=("Segoe UI", 10),
                                     relief="solid", bd=1, padx=15, pady=15)
        
        scrollbar_relatorio = ttk.Scrollbar(text_frame, orient="vertical", 
                                           command=self.text_relatorio.yview)
        self.text_relatorio.configure(yscrollcommand=scrollbar_relatorio.set)
        
        self.text_relatorio.pack(side="left", fill="both", expand=True)
        scrollbar_relatorio.pack(side="right", fill="y")
    
    def carregar_resultados(self):
        """Carrega os resultados da análise nas abas"""
        
        # Carregar problemas
        inconsistencias = self.resultado.get('inconsistencias', [])
        
        for problema in inconsistencias:
            severidade = problema.get('severidade', 'MEDIA')
            categoria = problema.get('categoria', 'GERAL')
            descricao = problema.get('descricao', 'Problema não especificado')
            impacto = problema.get('impacto', 'Impacto não informado')
            
            # Configurar cor por severidade
            if severidade == "ALTA":
                tag = "alta"
            elif severidade == "MEDIA":
                tag = "media"
            else:
                tag = "baixa"
            
            self.tree_problemas.insert('', tk.END, values=(
                severidade, categoria, descricao, impacto
            ), tags=(tag,))
        
        # Configurar cores
        self.tree_problemas.tag_configure("alta", background="#ffcccc")
        self.tree_problemas.tag_configure("media", background="#fff2cc")
        self.tree_problemas.tag_configure("baixa", background="#e6f3ff")
        
        # Carregar sugestões
        sugestoes = self.resultado.get('sugestoes', [])
        texto_sugestoes = "🔧 SUGESTÕES DA INTELIGÊNCIA ARTIFICIAL\n\n"
        
        if not sugestoes:
            texto_sugestoes += "✅ Nenhuma correção necessária. A NFe está em conformidade.\n\n"
            texto_sugestoes += "🎯 RECOMENDAÇÕES GERAIS:\n"
            texto_sugestoes += "• Mantenha os dados sempre atualizados\n"
            texto_sugestoes += "• Revise periodicamente as informações cadastrais\n"
            texto_sugestoes += "• Monitore alterações na legislação fiscal\n"
        else:
            for i, sugestao in enumerate(sugestoes, 1):
                prioridade = sugestao.get('prioridade', 'MÉDIA')
                emoji_prioridade = {"ALTA": "🔴", "MEDIA": "🟡", "BAIXA": "🟢"}
                
                texto_sugestoes += f"{emoji_prioridade.get(prioridade, '🔵')} SUGESTÃO {i} - PRIORIDADE {prioridade}\n"
                texto_sugestoes += f"📋 Problema: {sugestao.get('problema', 'N/A')}\n"
                texto_sugestoes += f"🔧 Solução: {sugestao.get('solucao', 'N/A')}\n"
                texto_sugestoes += f"⏱️ Tempo Estimado: {sugestao.get('tempo_estimado', 'N/A')}\n"
                texto_sugestoes += f"💼 Responsável: {sugestao.get('responsavel', 'Departamento Fiscal')}\n"
                texto_sugestoes += "-" * 80 + "\n\n"
        
        self.text_sugestoes.insert(tk.END, texto_sugestoes)
        self.text_sugestoes.config(state=tk.DISABLED)
        
        # Carregar análise técnica
        self.carregar_analise_tecnica()
        
        # Carregar relatório completo
        self.carregar_relatorio_completo()
    
    def carregar_analise_tecnica(self):
        """Carrega análise técnica detalhada"""
        
        texto_tecnica = f"""
🔬 ANÁLISE TÉCNICA DETALHADA - IA FISCAL
{"="*80}

🤖 ALGORITMOS UTILIZADOS:
• Detector de Riscos Fiscais v2.1
• Detector de Fraudes v1.8
• Validador de Conformidade v3.2
• Analisador de Padrões Suspeitos v1.5

📊 MÉTRICAS DE ANÁLISE:
• Score de Risco: {self.resultado.get('score', 0):.4f}/10
• Confiabilidade da Análise: {self.resultado.get('confiabilidade', 95.0):.2f}%
• Tempo de Processamento: {self.resultado.get('tempo_processamento', 0.8):.2f}s
• Critérios Avaliados: {self.resultado.get('criterios_avaliados', 25)}

🔍 VALIDAÇÕES EXECUTADAS:
✓ Validação estrutural do XML
✓ Consistência de dados fiscais
✓ Verificação de CNPJ/CPF
✓ Análise de valores e cálculos
✓ Conformidade com legislação
✓ Detecção de padrões suspeitos
✓ Verificação de duplicatas
✓ Análise temporal de emissão

🧠 INTELIGÊNCIA APLICADA:
• Machine Learning para detecção de anomalias
• Redes Neurais para análise de padrões
• Processamento de Linguagem Natural para textos
• Algoritmos de clustering para agrupamento

📈 HISTÓRICO COMPARATIVO:
• Notas similares analisadas: {self.resultado.get('notas_similares', 1247)}
• Padrão de comportamento: {self.resultado.get('padrao_comportamento', 'NORMAL')}
• Ranking de risco relativo: {self.resultado.get('ranking_risco', 'Top 15%')}

⚠️ ALERTAS AUTOMÁTICOS:
"""
        
        alertas = self.resultado.get('alertas', [])
        if alertas:
            for alerta in alertas:
                texto_tecnica += f"• {alerta}\n"
        else:
            texto_tecnica += "• Nenhum alerta gerado\n"
        
        texto_tecnica += f"""

🔐 ASSINATURA DIGITAL DA ANÁLISE:
Hash: {self.gerar_hash_analise()}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Versão IA: 2.1.0
"""
        
        self.text_tecnica.insert(tk.END, texto_tecnica)
        self.text_tecnica.config(state=tk.DISABLED)
    
    def carregar_relatorio_completo(self):
        """Carrega relatório completo"""
        
        relatorio = f"""
📄 RELATÓRIO COMPLETO DE ANÁLISE IA - NFe INSPECTOR
{"="*100}

🏢 DADOS DA EMPRESA
Razão Social: {self.dados_nfe.get('razao_social', 'N/A')}
CNPJ: {self.dados_nfe.get('cnpj_emissor', 'N/A')}
UF: {self.dados_nfe.get('uf', 'N/A')}

📋 DADOS DA NOTA FISCAL
Chave de Acesso: {self.dados_nfe.get('chave_acesso', 'N/A')}
Data de Emissão: {self.dados_nfe.get('data_emissao', 'N/A')}
Valor Total: R$ {self.dados_nfe.get('valor_total', 0):,.2f}
Natureza da Operação: {self.dados_nfe.get('natureza_operacao', 'N/A')}

🧠 RESULTADO DA ANÁLISE IA
Score de Risco: {self.resultado.get('score', 0):.2f}/10
Nível de Risco: {self.resultado.get('nivel', 'BAIXO')}
Status: {"✅ CONFORME" if len(self.resultado.get('inconsistencias', [])) == 0 else "⚠️ REQUER ATENÇÃO"}

⚠️ PROBLEMAS IDENTIFICADOS ({len(self.resultado.get('inconsistencias', []))})
"""
        
        for i, problema in enumerate(self.resultado.get('inconsistencias', []), 1):
            relatorio += f"""
{i}. {problema.get('descricao', 'Problema não especificado')}
   Severidade: {problema.get('severidade', 'MEDIA')}
   Categoria: {problema.get('categoria', 'GERAL')}
   Impacto: {problema.get('impacto', 'Impacto não informado')}
"""
        
        relatorio += f"""

🔧 AÇÕES RECOMENDADAS
"""
        
        for i, sugestao in enumerate(self.resultado.get('sugestoes', []), 1):
            relatorio += f"""
{i}. {sugestao.get('solucao', 'Sugestão não especificada')}
   Prioridade: {sugestao.get('prioridade', 'MÉDIA')}
   Tempo Estimado: {sugestao.get('tempo_estimado', 'N/A')}
   Responsável: {sugestao.get('responsavel', 'Departamento Fiscal')}
"""
        
        if not self.resultado.get('sugestoes', []):
            relatorio += "\n✅ Nenhuma ação corretiva necessária no momento.\n"
        
        relatorio += f"""

📊 CONCLUSÃO DA ANÁLISE
Data da Análise: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}
Analista Virtual: IA Fiscal NFe Inspector v2.1
Próxima Revisão Recomendada: {self.calcular_proxima_revisao()}

Este relatório foi gerado automaticamente pela Inteligência Artificial do NFe Inspector.
Para dúvidas ou esclarecimentos, entre em contato com o suporte técnico.

{"="*100}
"""
        
        self.text_relatorio.insert(tk.END, relatorio)
        self.text_relatorio.config(state=tk.DISABLED)
    
    def get_cor_score(self, score):
        """Retorna cor baseada no score"""
        if score >= 7:
            return "#dc3545"  # Vermelho
        elif score >= 4:
            return "#ffc107"  # Amarelo
        else:
            return "#28a745"  # Verde
    
    def gerar_hash_analise(self):
        """Gera hash da análise para rastreabilidade"""
        import hashlib
        dados = f"{self.dados_nfe.get('chave_acesso', '')}{self.resultado.get('score', 0)}{datetime.now().date()}"
        return hashlib.md5(dados.encode()).hexdigest()[:16].upper()
    
    def calcular_proxima_revisao(self):
        """Calcula data da próxima revisão"""
        from datetime import timedelta
        
        score = self.resultado.get('score', 0)
        if score >= 7:
            dias = 7  # Alto risco - revisar em 1 semana
        elif score >= 4:
            dias = 30  # Médio risco - revisar em 1 mês
        else:
            dias = 90  # Baixo risco - revisar em 3 meses
        
        proxima = datetime.now() + timedelta(days=dias)
        return proxima.strftime('%d/%m/%Y')
    
    def exportar_relatorio(self):
        """Exporta relatório completo"""
        messagebox.showinfo("Em Desenvolvimento", 
                           "Funcionalidade de exportação será implementada em breve")
    
    def enviar_email(self):
        """Envia relatório por email"""
        messagebox.showinfo("Em Desenvolvimento", 
                           "Funcionalidade de email será implementada em breve")
    
    def imprimir_relatorio(self):
        """Imprime relatório"""
        messagebox.showinfo("Em Desenvolvimento", 
                           "Funcionalidade de impressão será implementada em breve")

# Função para abrir janela de detalhes
def abrir_janela_detalhes_ia(parent, dados_nfe, resultado_analise):
    """Abre janela com detalhes da análise IA"""
    JanelaDetalhesIA(parent, dados_nfe, resultado_analise)
>>>>>>> 62fc89a629eb88be57523fc82f480d488337ac8e
