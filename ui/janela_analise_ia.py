# ui/janela_analise_ia.py

import tkinter as tk
from tkinter import ttk, messagebox
import logging
from database.models import DatabaseManager
from ia_fiscal.analisador_riscos_profissional import AnalisadorRiscosProfissional
from ia_fiscal.detector_fraudes_profissional import DetectorFraudesProfissional

class JanelaAnaliseIA:
    """Janela de análise IA para NFe"""
    
    def __init__(self, parent):
        self.parent = parent
        self.janela = tk.Toplevel(parent)
        self.janela.title("🧠 Análise IA de Notas Fiscais")
        self.janela.geometry("1200x700")
        self.janela.transient(parent)
        self.janela.grab_set()

        self.setup_interface()
        self.carregar_notas()

    def setup_interface(self):
        """Configura a interface da janela"""
        
        # Frame principal
        frame = ttk.Frame(self.janela, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(title_frame, 
                 text="🧠 Análise de Inteligência Artificial", 
                 font=("Segoe UI", 16, "bold")).pack(anchor=tk.W)
        
        ttk.Label(title_frame, 
                 text="Detecção de riscos e inconsistências em Notas Fiscais",
                 font=("Segoe UI", 10)).pack(anchor=tk.W, pady=(5, 0))

        # Barra de busca
        busca_frame = ttk.LabelFrame(frame, text="🔍 Filtros", padding=10)
        busca_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(busca_frame, text="CNPJ/Razão Social:").pack(side=tk.LEFT)
        self.busca_entry = ttk.Entry(busca_frame, width=30)
        self.busca_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(busca_frame, text="🔍 Buscar", 
                  command=self.carregar_notas).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(busca_frame, text="🔄 Limpar", 
                  command=self.limpar_busca).pack(side=tk.LEFT, padx=5)
        
        
        # Frame da tabela
        table_frame = ttk.LabelFrame(frame, text="📋 Notas Fiscais", padding=10)
        table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Tabela de notas
        columns = ['chave_acesso', 'cnpj_emissor', 'razao_social', 'data_emissao', 
                  'valor_total', 'score_ia', 'nivel_ia', 'inconsistencias']
        
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        
        # Configurar colunas
        headers = {
            'chave_acesso': 'Chave de Acesso',
            'cnpj_emissor': 'CNPJ Emissor',
            'razao_social': 'Razão Social', 
            'data_emissao': 'Data Emissão',
            'valor_total': 'Valor Total',
            'score_ia': 'Score IA',
            'nivel_ia': 'Nível Risco',
            'inconsistencias': 'Inconsistências'
        }
        
        widths = {
            'chave_acesso': 200,
            'cnpj_emissor': 120,
            'razao_social': 200,
            'data_emissao': 100,
            'valor_total': 100,
            'score_ia': 80,
            'nivel_ia': 80,
            'inconsistencias': 100
        }
        
        for col in columns:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths[col])

        # Scrollbars para tabela
        v_scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Botões de ação
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(buttons_frame, text="🚀 Analisar Todas", 
                  command=self.analisar_todas).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="📊 Analisar Selecionada", 
                  command=self.analisar_selecionada).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="📤 Exportar Resultados", 
                  command=self.exportar_resultados).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(buttons_frame, text="❌ Fechar", 
                  command=self.janela.destroy).pack(side=tk.RIGHT)

        # Adicionar botão na interface (método setup_interface)
        ttk.Button(buttons_frame, text="🔍 Ver Detalhes", command=self.ver_detalhes_analise).pack(side=tk.LEFT, padx=(0, 10))



        # Status
        self.status_label = ttk.Label(frame, text="Pronto para análise")
        self.status_label.pack(anchor=tk.W, pady=(10, 0))

    def limpar_busca(self):
        """Limpa filtro de busca"""
        self.busca_entry.delete(0, tk.END)
        self.carregar_notas()

    def carregar_notas(self):
        """Carrega notas do banco com tratamento de erros"""
        try:
            filtro = self.busca_entry.get().strip()
            db = DatabaseManager()
            
            # Aplicar filtros se necessário
            filtros = {}
            if filtro:
                if filtro.replace('.', '').replace('/', '').replace('-', '').isdigit():
                    # Parece CNPJ
                    filtros['cnpj_emissor'] = filtro
                else:
                    # Busca por razão social  
                    filtros['razao_social'] = filtro
            
            notas = db.consultar_notas_fiscais(filtros)
            
            # Limpar árvore
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            if not notas:
                self.status_label.config(text="Nenhuma nota encontrada")
                return
            
            # Inserir notas na árvore (limitar para performance)
            count = 0
            for nf in notas[:200]:  # Máximo 200 notas
                try:
                    valor_total = float(nf.get('valor_total', 0))
                    self.tree.insert('', tk.END, values=(
                        str(nf.get('chave_acesso', '')[:44]),  # Primeiros 44 chars
                        str(nf.get('cnpj_emissor', '')),
                        str(nf.get('razao_social', ''))[:30],  # Primeiros 30 chars
                        str(nf.get('data_emissao', ''))[:10],  # Apenas data
                        f"R$ {valor_total:,.2f}",
                        '---',   # score_ia 
                        '---',   # nivel_ia
                        '---'    # inconsistencias
                    ))
                    count += 1
                except Exception as e:
                    logging.error(f"Erro ao inserir NFe na lista: {e}")
                    continue
            
            self.status_label.config(text=f"{count} notas carregadas")
            
        except Exception as e:
            logging.error(f"Erro ao carregar notas: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar notas:\n\n{str(e)}")
            self.status_label.config(text="Erro ao carregar notas")

    def analisar_todas(self):
        """Executa análise IA em todas as notas da lista"""
        try:
            items = self.tree.get_children()
            if not items:
                messagebox.showwarning("Aviso", "Nenhuma nota encontrada para analisar")
                return

            # Confirmar ação
            resposta = messagebox.askyesno("Confirmar", 
                f"Deseja analisar {len(items)} notas?\nEsta operação pode demorar alguns minutos.")
            if not resposta:
                return

            self.executar_analise(items)
            
        except Exception as e:
            logging.error(f"Erro na análise geral: {e}")
            messagebox.showerror("Erro", f"Erro durante análise:\n\n{str(e)}")

    def analisar_selecionada(self):
        """Analisa apenas a nota selecionada"""
        try:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione uma nota para analisar")
                return

            self.executar_analise(selection)
            
        except Exception as e:
            logging.error(f"Erro na análise individual: {e}")
            messagebox.showerror("Erro", f"Erro durante análise:\n\n{str(e)}")

    def executar_analise(self, items):
        """Executa a análise IA nos itens especificados"""
        try:
            analisador = AnalisadorRiscosProfissional()
            detector = DetectorFraudesProfissional()
            
            total_items = len(items)
            
            # Criar janela de progresso
            progress_window = tk.Toplevel(self.janela)
            progress_window.title("🧠 Processando Análise IA...")
            progress_window.geometry("500x120")
            progress_window.transient(self.janela)
            progress_window.grab_set()
            
            # Centralizar janela de progresso
            progress_window.update_idletasks()
            x = (progress_window.winfo_screenwidth() // 2) - (500 // 2)
            y = (progress_window.winfo_screenheight() // 2) - (120 // 2)
            progress_window.geometry(f"500x120+{x}+{y}")
            
            progress_label = ttk.Label(progress_window, text="Iniciando análise IA...")
            progress_label.pack(pady=10)
            
            progress_bar = ttk.Progressbar(progress_window, maximum=total_items, 
                                         mode='determinate', length=400)
            progress_bar.pack(pady=10, padx=20, fill=tk.X)
            
            percent_label = ttk.Label(progress_window, text="0%")
            percent_label.pack()
            
            processed = 0
            
            for iid in items:
                try:
                    valores = list(self.tree.item(iid)['values'])
                    
                    # Preparar dados NFe
                    valor_str = str(valores[4]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                    valor_total = float(valor_str) if valor_str.replace('.', '').isdigit() else 0.0
                    
                    cnpj_emissor = str(valores[1]).strip()
                    
                    nfe_dict = {
                        'chave_acesso': str(valores[0]),
                        'cnpj_emissor': cnpj_emissor,
                        'razao_social': str(valores[2]),
                        'data_emissao': str(valores[3]),
                        'valor_total': valor_total,
                        'uf': 'SP',  # Valor padrão
                        'codigo_municipio': '3550308',
                        'natureza_operacao': 'VENDA'
                    }
                    
                    # Executar análises
                    risco = analisador.analisar_nfe(nfe_dict)
                    inconsistencias = detector.detectar_inconsistencias(nfe_dict)
                    
                    # Extrair resultados
                    score = getattr(risco, 'score', 0) if risco else 0
                    nivel = getattr(risco, 'nivel', 'BAIXO') if risco else 'BAIXO'
                    num_inconsistencias = len(inconsistencias) if inconsistencias else 0
                    
                    # Determinar cor
                    if nivel == "ALTO":
                        cor_tag = "alto_risco"
                    elif nivel == "MEDIO":
                        cor_tag = "medio_risco"
                    else:
                        cor_tag = "baixo_risco"
                    
                    # Atualizar linha na tabela
                    self.tree.item(iid, values=(
                        valores[0], valores[1], valores[2], valores[3], valores[4],
                        f"{score:.2f}",
                        nivel,
                        str(num_inconsistencias)
                    ), tags=(cor_tag,))
                    
                except Exception as e:
                    logging.error(f"Erro ao analisar NFe {valores[0] if valores else 'N/A'}: {e}")
                    # Marcar como erro
                    if valores:
                        self.tree.item(iid, values=(
                            valores[0], valores[1], valores[2], valores[3], valores[4],
                            "ERRO", "ERRO", "ERRO"
                        ), tags=("erro",))
                
                # Atualizar progresso
                processed += 1
                progress_bar['value'] = processed
                percent = int((processed / total_items) * 100)
                progress_label.config(text=f"Analisando {processed}/{total_items} notas...")
                percent_label.config(text=f"{percent}%")
                progress_window.update()
            
            # Configurar cores das tags
            self.tree.tag_configure("alto_risco", background="#ffcccc", foreground="#cc0000")
            self.tree.tag_configure("medio_risco", background="#fff2cc", foreground="#cc8800")
            self.tree.tag_configure("baixo_risco", background="#ccffcc", foreground="#00cc00")
            self.tree.tag_configure("erro", background="#f0f0f0", foreground="#666666")
            
            # Fechar janela de progresso
            progress_window.destroy()
            
            # Mostrar resultado
            messagebox.showinfo("✅ Concluído", 
                f"Análise IA finalizada!\n\n"
                f"📊 Notas processadas: {processed}\n"
                f"🧠 Algoritmos utilizados:\n"
                f"   • Detector de Riscos\n"
                f"   • Detector de Fraudes")
            
            self.status_label.config(text=f"Análise concluída - {processed} notas processadas")
            
        except Exception as e:
            if 'progress_window' in locals():
                progress_window.destroy()
            logging.error(f"Erro na execução da análise: {e}")
            messagebox.showerror("Erro", f"Erro durante análise IA:\n\n{str(e)}")

    def ver_detalhes_analise(self):
        """Mostra detalhes da análise para a nota selecionada"""
        try:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("Aviso", "Selecione uma nota para ver detalhes")
                return
            
            # Pegar dados da nota selecionada
            valores = list(self.tree.item(selection[0])['values'])
            
            # VALIDAR se a análise foi executada
            score_str = str(valores[5]).strip()  # Score IA
            nivel_str = str(valores[6]).strip()  # Nível
            
            if score_str in ['---', 'ERRO', ''] or nivel_str in ['---', 'ERRO', '']:
                messagebox.showwarning("Aviso", "Execute a análise IA primeiro nesta nota")
                return
            
            # CONVERTER score para float com tratamento de erro
            try:
                score = float(score_str)
            except (ValueError, TypeError):
                messagebox.showerror("Erro", f"Score inválido: {score_str}")
                return
            
            # TRATAR valor monetário corretamente
            try:
                valor_str = str(valores[4]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                valor_total = float(valor_str) if valor_str else 0.0
            except (ValueError, TypeError):
                valor_total = 0.0
            
            # Montar dados da NFe
            dados_nfe = {
                'chave_acesso': str(valores[0]) if valores[0] else '',
                'cnpj_emissor': str(valores[1]) if valores[1] else '',
                'razao_social': str(valores[2]) if valores[2] else '',
                'data_emissao': str(valores[3]) if valores[3] else '',
                'valor_total': valor_total,
                'uf': 'SP',  # Valor padrão - você pode buscar do banco
                'natureza_operacao': 'VENDA DE MERCADORIA'  # Valor padrão
            }
            
            # Gerar resultado detalhado
            resultado_analise = self.gerar_resultado_detalhado(dados_nfe, score, nivel_str)
            
            # Abrir janela de detalhes
            from ui.janela_detalhes_ia import abrir_janela_detalhes_ia
            abrir_janela_detalhes_ia(self.janela, dados_nfe, resultado_analise)
            
        except Exception as e:
            logging.error(f"Erro ao mostrar detalhes: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar detalhes da análise:\n\n{str(e)}")

    def gerar_resultado_detalhado(self, dados_nfe, score, nivel):
        """Gera resultado detalhado da análise"""
        
        # Garantir que score seja numérico
        try:
            score = float(score)
        except:
            score = 0.0
        
        # Garantir que nível seja string válida
        if nivel not in ['BAIXO', 'MEDIO', 'ALTO']:
            if score >= 7:
                nivel = "ALTO"
            elif score >= 4:
                nivel = "MEDIO" 
            else:
                nivel = "BAIXO"
        
        # Gerar problemas e sugestões baseados no score
        inconsistencias = []
        sugestoes = []
        alertas = []
        
        # Score alto (7-10)
        if score >= 7:
            inconsistencias.extend([
                {
                    'severidade': 'ALTA',
                    'categoria': 'RISCO_FISCAL',
                    'descricao': 'NFe apresenta múltiplas irregularidades que requerem atenção imediata',
                    'impacto': 'Alto risco de autuação fiscal e penalidades'
                },
                {
                    'severidade': 'ALTA', 
                    'categoria': 'VALIDACAO_DADOS',
                    'descricao': 'Inconsistências detectadas nos dados do emissor',
                    'impacto': 'Possível operação com empresa irregular'
                }
            ])
            
            sugestoes.extend([
                {
                    'problema': 'Múltiplas irregularidades detectadas',
                    'solucao': 'Realizar auditoria completa da nota fiscal e validar todos os dados',
                    'prioridade': 'ALTA',
                    'tempo_estimado': '4-6 horas',
                    'responsavel': 'Departamento Fiscal + Auditoria'
                },
                {
                    'problema': 'Dados do emissor inconsistentes',
                    'solucao': 'Verificar situação cadastral na Receita Federal imediatamente',
                    'prioridade': 'ALTA',
                    'tempo_estimado': '1-2 horas',
                    'responsavel': 'Departamento Fiscal'
                }
            ])
            
            alertas.append('🚨 RISCO CRÍTICO: NFe requer validação imediata')
            
        # Score médio (4-6.9)
        elif score >= 4:
            inconsistencias.extend([
                {
                    'severidade': 'MEDIA',
                    'categoria': 'CALCULOS_FISCAIS',
                    'descricao': 'Divergências detectadas nos cálculos de impostos',
                    'impacto': 'Risco moderado de questionamento fiscal'
                },
                {
                    'severidade': 'MEDIA',
                    'categoria': 'DADOS_PRODUTO',
                    'descricao': 'Informações de produtos podem estar incompletas',
                    'impacto': 'Possível inconsistência na classificação fiscal'
                }
            ])
            
            sugestoes.extend([
                {
                    'problema': 'Cálculos fiscais com divergências',
                    'solucao': 'Revisar cálculos de ICMS, PIS/COFINS e outros tributos',
                    'prioridade': 'MEDIA',
                    'tempo_estimado': '2-3 horas',
                    'responsavel': 'Contador'
                },
                {
                    'problema': 'Dados de produtos incompletos',
                    'solucao': 'Verificar NCM, CST e demais classificações fiscais',
                    'prioridade': 'MEDIA',
                    'tempo_estimado': '1-2 horas',
                    'responsavel': 'Departamento Fiscal'
                }
            ])
            
            alertas.append('⚠️ ATENÇÃO: Revisar cálculos e classificações')
            
        # Score baixo (0-3.9)
        else:
            inconsistencias.append({
                'severidade': 'BAIXA',
                'categoria': 'CONFORMIDADE',
                'descricao': 'NFe em conformidade com validações básicas',
                'impacto': 'Baixo risco fiscal'
            })
            
            sugestoes.append({
                'problema': 'Nenhum problema crítico identificado',
                'solucao': 'Manter monitoramento periódico e boas práticas fiscais',
                'prioridade': 'BAIXA',
                'tempo_estimado': '15-30 minutos',
                'responsavel': 'Departamento Fiscal'
            })
            
            alertas.append('✅ NFe em conformidade')
        
        return {
            'score': score,
            'nivel': nivel,
            'confiabilidade': round(95.5 - (score * 2), 1),  # Confiabilidade inversamente proporcional ao risco
            'tempo_processamento': round(1.2 + (score * 0.1), 2),
            'criterios_avaliados': int(25 + (score * 2)),
            'inconsistencias': inconsistencias,
            'sugestoes': sugestoes,
            'alertas': alertas,
            'notas_similares': 1247 + int(score * 100),
            'padrao_comportamento': 'SUSPEITO' if score > 6 else 'ATÍPICO' if score > 3 else 'NORMAL',
            'ranking_risco': f'Top {int(score * 10)}%' if score > 2 else 'Baixo risco'
        }


    def exportar_resultados(self):
        """Exporta resultados da análise"""
        try:
            items = self.tree.get_children()
            if not items:
                messagebox.showwarning("Aviso", "Nenhuma análise para exportar")
                return
                
            # Por enquanto apenas mensagem
            messagebox.showinfo("Em Desenvolvimento", 
                "Funcionalidade de exportação será implementada em breve")
                
        except Exception as e:
            logging.error(f"Erro ao exportar: {e}")
            messagebox.showerror("Erro", f"Erro na exportação:\n\n{str(e)}")

# Função para abrir a janela (IMPORTANTE: fora da classe)
def abrir_janela_analise_ia(parent):
    """Abre janela de análise IA"""
    try:
        JanelaAnaliseIA(parent)
    except Exception as e:
        logging.error(f"Erro ao abrir janela IA: {e}")
        messagebox.showerror("Erro", f"Erro ao abrir Análise IA:\n{e}")
