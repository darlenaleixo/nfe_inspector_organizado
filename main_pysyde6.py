# -*- coding: utf-8 -*-
"""
NFe Inspector - Interface PySide6 COMPLETA E INTEGRADA
Versão 2.0 - Totalmente funcional com todos os módulos
"""

import sys
import os
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QProgressBar, QTextEdit,
    QLineEdit, QComboBox, QGroupBox, QFormLayout, QHeaderView,
    QSplitter, QStatusBar, QMenuBar
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QAction, QColor

# Imports dos seus módulos existentes
from processing.processor import NFeProcessorBI


try:
    from core.config import ConfigManager
except:
    ConfigManager = None

try:
    from reports.generator import ReportGenerator
except:
    ReportGenerator = None

try:
    from database.models import Empresa
    from empresa.manager import DatabaseManager
except:
    Empresa = None
    DatabaseManager = None


class ProcessamentoThread(QThread):
    """Thread para processar NFe sem travar a interface"""
    
    progresso = Signal(int)
    mensagem = Signal(str)
    concluido = Signal(dict)
    erro = Signal(str)
    
    def __init__(self, pasta_xml, pasta_saida):
        super().__init__()
        self.pasta_xml = pasta_xml
        self.pasta_saida = pasta_saida
    
    def run(self):
        try:
            self.mensagem.emit("🔍 Iniciando processamento...")
            self.progresso.emit(10)
            
            # Criar processador
            processor = NFeProcessorBI(self.pasta_xml, self.pasta_saida)
            
            self.mensagem.emit("📄 Processando XMLs...")
            self.progresso.emit(30)
            
            # Processar pasta
            processor.processar_pasta()
            
            self.mensagem.emit("📊 Gerando relatórios...")
            self.progresso.emit(70)
            
            # Gerar relatórios se disponível
            if ReportGenerator and processor.dados_processados:
                generator = ReportGenerator(processor.dados_processados)
                
                # CSV
                csv_path = os.path.join(self.pasta_saida, 'relatorio_completo.csv')
                generator.gerar_csv(csv_path)
                
                # Excel se disponível
                if generator.excel_disponivel:
                    excel_path = os.path.join(self.pasta_saida, 'relatorio_completo.xlsx')
                    generator.gerar_excel(excel_path)
            
            self.progresso.emit(100)
            self.mensagem.emit("✅ Concluído!")
            
            # Resultado
            resultado = {
                'total_processadas': len(processor.dados_processados),
                'com_erro': processor.estatisticas.get('arquivos_com_erro', 0),
                'pasta_saida': self.pasta_saida,
                'relatorios_gerados': True if ReportGenerator else False
            }
            
            self.concluido.emit(resultado)
            
        except Exception as e:
            self.erro.emit(str(e))


class NFEInspectorPro(QMainWindow):
    """Janela Principal - Interface Completa Integrada"""
    
    def __init__(self):
        super().__init__()
        
        # Configurações
        self.setWindowTitle("NFe Inspector Pro - Sistema Profissional de Análise")
        self.setMinimumSize(1200, 800)
        
        # Gerenciadores
        self.config = ConfigManager() if ConfigManager else None
        self.db_manager = DatabaseManager() if DatabaseManager else None
        
        # Variáveis
        self.pasta_xml_selecionada = None
        
        # Criar interface
        self.criar_interface()
        self.criar_menubar()
        self.criar_statusbar()
        self.aplicar_tema()
        
        # Carregar dados iniciais
        self.carregar_dados_iniciais()
    
    def criar_interface(self):
        """Cria toda a interface"""
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Header
        header = self.criar_header()
        layout.addWidget(header)
        
        # Abas
        self.tabs = QTabWidget()

        # Aba de Boas-Vindas
        welcome_tab = QWidget()
        wl = QVBoxLayout(welcome_tab)
        lbl_welcome = QLabel("👋 Bem-vindo ao NFe Inspector Pro")
        lbl_welcome.setFont(QFont("Arial", 18, QFont.Bold))
        lbl_welcome.setAlignment(Qt.AlignCenter)
        sub = QLabel(
            "Use as opções acima para acessar:\n"
            "• Processar NFe\n"
            "• Ver Resultados\n"
            "• Gerenciar Empresas\n"
            "• Fazer Download de NFe"
        )
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color: #bdc3c7; font-size: 14px;")
        wl.addStretch()
        wl.addWidget(lbl_welcome)
        wl.addWidget(sub)
        wl.addStretch()
        self.tabs.addTab(welcome_tab, "🏠 Início")
        
        # ABA 1: Processamento
        self.tab_processamento = self.criar_tab_processamento()
        self.tabs.addTab(self.tab_processamento, "📄 Processar NFe")
        
        # ABA 2: Resultados
        self.tab_resultados = self.criar_tab_resultados()
        self.tabs.addTab(self.tab_resultados, "📊 Resultados")
        
        # ABA 3: Empresas
        self.tab_empresas = self.criar_tab_empresas()
        self.tabs.addTab(self.tab_empresas, "🏢 Empresas")
        
        # ABA 4: Download NFe
        self.tab_download = self.criar_tab_download()
        self.tabs.addTab(self.tab_download, "📥 Download NFe")
        
        layout.addWidget(self.tabs)
    
    def criar_header(self):
        """Header com título e botões rápidos"""
        header = QWidget()
        layout = QHBoxLayout(header)
        
        # Título
        titulo = QLabel("🧾 NFe Inspector Pro")
        titulo.setFont(QFont("Arial", 18, QFont.Bold))
        
        # Botões rápidos
        btn_processar_rapido = QPushButton("⚡ Processar Rápido")
        btn_processar_rapido.clicked.connect(self.processar_rapido)
        
        btn_limpar = QPushButton("🗑️ Limpar")
        btn_limpar.clicked.connect(self.limpar_resultados)
        
        layout.addWidget(titulo)
        layout.addStretch()
        layout.addWidget(btn_processar_rapido)
        layout.addWidget(btn_limpar)
        
        return header
    
    def criar_tab_processamento(self):
        """Aba de processamento"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Título
        titulo = QLabel("Processar Notas Fiscais Eletrônicas")
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Seleção de pasta
        grupo_pasta = QGroupBox("📁 Pasta com XMLs")
        grupo_pasta_layout = QVBoxLayout(grupo_pasta)
        
        self.label_pasta = QLabel("Nenhuma pasta selecionada")
        self.label_pasta.setStyleSheet("padding: 10px; background: #34495e; border-radius: 5px;")
        
        btn_selecionar = QPushButton("Selecionar Pasta")
        btn_selecionar.clicked.connect(self.selecionar_pasta_xml)
        
        grupo_pasta_layout.addWidget(self.label_pasta)
        grupo_pasta_layout.addWidget(btn_selecionar)
        layout.addWidget(grupo_pasta)
        
        # Pasta de saída
        grupo_saida = QGroupBox("💾 Pasta de Saída (Relatórios)")
        grupo_saida_layout = QHBoxLayout(grupo_saida)
        
        self.input_pasta_saida = QLineEdit()
        self.input_pasta_saida.setText("relatorios_nfe")
        
        btn_selecionar_saida = QPushButton("...")
        btn_selecionar_saida.setMaximumWidth(50)
        btn_selecionar_saida.clicked.connect(self.selecionar_pasta_saida)
        
        grupo_saida_layout.addWidget(self.input_pasta_saida)
        grupo_saida_layout.addWidget(btn_selecionar_saida)
        layout.addWidget(grupo_saida)
        
        # Status e Progresso
        self.label_status = QLabel("⏸️ Aguardando...")
        self.label_status.setStyleSheet("font-size: 13px; padding: 8px;")
        layout.addWidget(self.label_status)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(30)
        layout.addWidget(self.progress_bar)
        
        # Botão processar
        btn_processar = QPushButton("🚀 PROCESSAR NFe")
        btn_processar.setMinimumHeight(50)
        btn_processar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        btn_processar.clicked.connect(self.processar_nfe)
        layout.addWidget(btn_processar)
        
        # Log
        grupo_log = QGroupBox("📋 Log de Processamento")
        grupo_log_layout = QVBoxLayout(grupo_log)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("background: #1e1e1e; color: #00ff00; font-family: 'Courier New';")
        
        grupo_log_layout.addWidget(self.log_text)
        layout.addWidget(grupo_log)
        
        layout.addStretch()
        return tab
    
    def criar_tab_resultados(self):
        """Aba de resultados"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Cards de resumo
        cards_layout = QHBoxLayout()
        
        self.card_total = self.criar_card("Total Processadas", "0", "NFe")
        self.card_valor = self.criar_card("Valor Total", "R$ 0,00", "")
        self.card_erros = self.criar_card("Com Erro", "0", "arquivos")
        
        cards_layout.addWidget(self.card_total)
        cards_layout.addWidget(self.card_valor)
        cards_layout.addWidget(self.card_erros)
        layout.addLayout(cards_layout)
        
        # Tabela de NFe
        self.tabela_nfe = QTableWidget()
        self.tabela_nfe.setColumnCount(6)
        self.tabela_nfe.setHorizontalHeaderLabels([
            "Chave", "Emitente", "Destinatário", "Valor", "Data", "Status"
        ])
        self.tabela_nfe.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_nfe)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        btn_exportar = QPushButton("📊 Exportar Excel")
        btn_exportar.clicked.connect(self.exportar_excel)
        
        btn_abrir_pasta = QPushButton("📁 Abrir Pasta de Relatórios")
        btn_abrir_pasta.clicked.connect(self.abrir_pasta_relatorios)
        
        btn_layout.addWidget(btn_exportar)
        btn_layout.addWidget(btn_abrir_pasta)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return tab
    
    def criar_tab_empresas(self):
        """Aba de empresas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        titulo = QLabel("🏢 Gestão de Empresas")
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Botões
        btn_layout = QHBoxLayout()
        btn_nova = QPushButton("➕ Nova Empresa")
        btn_editar = QPushButton("✏️ Editar")
        btn_remover = QPushButton("🗑️ Remover")
        
        btn_layout.addWidget(btn_nova)
        btn_layout.addWidget(btn_editar)
        btn_layout.addWidget(btn_remover)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Tabela
        self.tabela_empresas = QTableWidget()
        self.tabela_empresas.setColumnCount(4)
        self.tabela_empresas.setHorizontalHeaderLabels([
            "CNPJ", "Razão Social", "UF", "Total NFe"
        ])
        self.tabela_empresas.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.tabela_empresas)
        
        self.carregar_empresas()
        
        return tab
    
    def criar_tab_download(self):
        """Aba de download NFe"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        titulo = QLabel("📥 Download Automático de NFe")
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        info = QLabel(
            "Sistema de download automático de NFe usando certificados digitais.\n"
            "Configure seus clientes e baixe notas fiscais diretamente da SEFAZ."
        )
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Botão para CLI
        btn_abrir_cli = QPushButton("🖥️ Abrir Interface CLI de Download")
        btn_abrir_cli.setMinimumHeight(50)
        btn_abrir_cli.clicked.connect(self.abrir_cli_download)
        layout.addWidget(btn_abrir_cli)
        
        layout.addStretch()
        return tab
    
    def criar_card(self, titulo, valor, subtitulo):
        """Cria card de estatística"""
        card = QWidget()
        card.setMinimumHeight(100)
        card.setStyleSheet("""
            QWidget {
                background-color: #34495e;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("color: #bdc3c7; font-size: 11px;")
        
        lbl_valor = QLabel(valor)
        lbl_valor.setStyleSheet("color: #ecf0f1; font-size: 24px; font-weight: bold;")
        
        lbl_sub = QLabel(subtitulo)
        lbl_sub.setStyleSheet("color: #95a5a6; font-size: 10px;")
        
        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        layout.addWidget(lbl_sub)
        
        return card
    
    def criar_menubar(self):
        """Cria menu superior"""
        menubar = self.menuBar()
        
        # Menu Arquivo
        menu_arquivo = menubar.addMenu("&Arquivo")
        
        acao_abrir = QAction("📁 Abrir Pasta", self)
        acao_abrir.triggered.connect(self.selecionar_pasta_xml)
        menu_arquivo.addAction(acao_abrir)
        
        menu_arquivo.addSeparator()
        
        acao_sair = QAction("❌ Sair", self)
        acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(acao_sair)
        
        # Menu Ajuda
        menu_ajuda = menubar.addMenu("&Ajuda")
        
        acao_sobre = QAction("ℹ️ Sobre", self)
        acao_sobre.triggered.connect(self.mostrar_sobre)
        menu_ajuda.addAction(acao_sobre)
    
    def criar_statusbar(self):
        """Cria barra de status"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("✅ Pronto")
    
    def aplicar_tema(self):
        """Tema escuro profissional"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Segoe UI', Arial;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5dade2;
            }
            QTabWidget::pane {
                border: 1px solid #34495e;
                background: #2c3e50;
            }
            QTabBar::tab {
                background: #34495e;
                color: #ecf0f1;
                padding: 10px 20px;
                border: 1px solid #2c3e50;
            }
            QTabBar::tab:selected {
                background: #3498db;
            }
            QTableWidget {
                background-color: #34495e;
                gridline-color: #2c3e50;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 5px;
                border: 1px solid #34495e;
            }
            QGroupBox {
                border: 2px solid #34495e;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit, QComboBox {
                background: #34495e;
                border: 1px solid #2c3e50;
                border-radius: 3px;
                padding: 5px;
                color: #ecf0f1;
            }
            QProgressBar {
                background: #34495e;
                border: none;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background: #3498db;
                border-radius: 5px;
            }
        """)
    
    # ========== MÉTODOS DE AÇÃO ==========
    
    def carregar_dados_iniciais(self):
        """Carrega dados ao iniciar"""
        self.adicionar_log("🚀 Sistema iniciado")
        self.adicionar_log(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    def selecionar_pasta_xml(self):
        """Seleciona pasta com XMLs"""
        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta com XMLs de NFe",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if pasta:
            self.pasta_xml_selecionada = pasta
            self.label_pasta.setText(f"✅ {pasta}")
            self.label_pasta.setStyleSheet(
                "padding: 10px; background: #27ae60; border-radius: 5px; color: white;"
            )
            self.statusbar.showMessage(f"Pasta selecionada: {pasta}")
            self.adicionar_log(f"📁 Pasta selecionada: {pasta}")
    
    def selecionar_pasta_saida(self):
        """Seleciona pasta de saída"""
        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta para Relatórios",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if pasta:
            self.input_pasta_saida.setText(pasta)
    
    def processar_nfe(self):
        """Processa NFe em thread"""
        if not self.pasta_xml_selecionada:
            QMessageBox.warning(self, "Atenção", "Selecione uma pasta com XMLs primeiro!")
            return
        
        pasta_saida = self.input_pasta_saida.text() or "relatorios_nfe"
        
        # Mostrar progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.label_status.setText("🔄 Processando...")
        self.statusbar.showMessage("Processando NFe...")
        
        # Thread
        self.thread = ProcessamentoThread(self.pasta_xml_selecionada, pasta_saida)
        self.thread.progresso.connect(self.atualizar_progresso)
        self.thread.mensagem.connect(self.adicionar_log)
        self.thread.mensagem.connect(self.label_status.setText)
        self.thread.concluido.connect(self.processamento_concluido)
        self.thread.erro.connect(self.processamento_erro)
        self.thread.start()
    
    def processar_rapido(self):
        """Processamento rápido"""
        self.selecionar_pasta_xml()
    
    def atualizar_progresso(self, valor):
        """Atualiza barra"""
        self.progress_bar.setValue(valor)
    
    def adicionar_log(self, mensagem):
        """Adiciona mensagem no log"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.append(f"[{timestamp}] {mensagem}")
    
    def processamento_concluido(self, resultado):
        """Callback sucesso"""
        self.progress_bar.setVisible(False)
        self.label_status.setText("✅ Concluído!")
        self.statusbar.showMessage("✅ Processamento concluído!")
        
        # Atualizar cards
        self.atualizar_card(self.card_total, "Total Processadas", str(resultado['total_processadas']), "NFe")
        self.atualizar_card(self.card_erros, "Com Erro", str(resultado['com_erro']), "arquivos")
        
        QMessageBox.information(
            self,
            "Sucesso! 🎉",
            f"Processamento concluído!\n\n"
            f"✅ Total: {resultado['total_processadas']} NFe\n"
            f"❌ Erros: {resultado['com_erro']}\n"
            f"📁 Relatórios: {resultado['pasta_saida']}\n"
            f"📊 Relatórios gerados: {'Sim' if resultado['relatorios_gerados'] else 'Não'}"
        )
        
        
    
    def processamento_erro(self, erro):
        """Callback erro"""
        self.progress_bar.setVisible(False)
        self.label_status.setText("❌ Erro!")
        self.statusbar.showMessage("❌ Erro no processamento")
        
        QMessageBox.critical(self, "Erro", f"Erro durante processamento:\n\n{erro}")
    
    def atualizar_card(self, card, titulo, valor, subtitulo):
        # Encontra o primeiro QLabel dentro do widget 'card'
        label = card.findChild(QLabel)
        if label:
            label.setText(valor)
    
    def limpar_resultados(self):
        """Limpa resultados"""
        self.tabela_nfe.setRowCount(0)
        self.log_text.clear()
        self.label_pasta.setText("Nenhuma pasta selecionada")
        self.label_pasta.setStyleSheet("padding: 10px; background: #34495e; border-radius: 5px;")
        self.pasta_xml_selecionada = None
        self.adicionar_log("🗑️ Resultados limpos")
    
    def exportar_excel(self):
        """Exporta para Excel"""
        QMessageBox.information(self, "Info", "Relatórios já foram gerados na pasta de saída!")
    
    def abrir_pasta_relatorios(self):
        """Abre pasta de relatórios"""
        pasta = self.input_pasta_saida.text() or "relatorios_nfe"
        if os.path.exists(pasta):
            os.startfile(pasta)  # Windows
        else:
            QMessageBox.warning(self, "Atenção", "Pasta não encontrada!")
    
    def carregar_empresas(self):
        """Carrega empresas na tabela, trata lista de dicts ou objetos."""
        try:
            # Limpar tabela antes
            self.tabela_empresas.setRowCount(0)

            # Obter lista de empresas vindas do manager
            empresas = self.db_manager.listar_empresas() if self.db_manager else []

            # Se for dict, converte para lista de dicts; se for objeto, acessa atributos
            rows = []
            for e in empresas:
                if isinstance(e, dict):
                    cnpj = e.get('cnpj', '')
                    razao = e.get('razao_social', '')
                    uf = e.get('uf', '')
                else:
                    cnpj = getattr(e, 'cnpj', '')
                    razao = getattr(e, 'razao_social', '')
                    uf = getattr(e, 'uf', '')
                rows.append((cnpj, razao, uf))

            # Definir número de linhas
            self.tabela_empresas.setRowCount(len(rows))

            # Preencher tabela
            for i, (cnpj, razao, uf) in enumerate(rows):
                self.tabela_empresas.setItem(i, 0, QTableWidgetItem(cnpj))
                self.tabela_empresas.setItem(i, 1, QTableWidgetItem(razao))
                self.tabela_empresas.setItem(i, 2, QTableWidgetItem(uf))
                self.tabela_empresas.setItem(i, 3, QTableWidgetItem("0"))

        except Exception as e:
            # Mostrar no log se der erro
            self.adicionar_log(f"⚠️ Erro ao carregar empresas: {e}")
    
    def abrir_cli_download(self):
        """Abre CLI de download"""
        QMessageBox.information(
            self,
            "CLI de Download",
            "Para usar o sistema de download, execute:\n\n"
            "python nfe_cli.py --help\n\n"
            "No terminal/PowerShell"
        )
    
    def mostrar_sobre(self):
        """Sobre o sistema"""
        QMessageBox.about(
            self,
            "Sobre NFe Inspector Pro",
            "<h2>NFe Inspector Pro</h2>"
            "<p>Sistema Profissional de Análise de NFe</p>"
            "<p><b>Versão:</b> 2.0 - PySide6</p>"
            "<p><b>Recursos:</b></p>"
            "<ul>"
            "<li>Processamento de XMLs NFe</li>"
            "<li>Geração de relatórios</li>"
            "<li>Gestão de empresas</li>"
            "<li>Download automático SEFAZ</li>"
            "<li>Análise com IA Fiscal</li>"
            "</ul>"
            "<p>Desenvolvido com Python e PySide6</p>"
        )


def main():
    """Inicia aplicação"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    janela = NFEInspectorPro()
    janela.showMaximized()

    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()