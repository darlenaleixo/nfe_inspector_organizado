# -*- coding: utf-8 -*-
"""
Janela Principal do NFe Inspector - PySide6
Interface moderna e profissional
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem,
    QProgressBar, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QAction, QIcon, QFont

# Imports do seu projeto existente
from processing.processor import NFeProcessorBI
from core.config import ConfigManager # Mantido para consistência
from database.models import DatabaseManager, Empresa


class ProcessamentoThread(QThread):
    """Thread para processamento de NFe sem travar a interface"""
    
    progresso = Signal(int)  # Sinal para atualizar barra de progresso
    concluido = Signal(dict)  # Sinal quando concluir
    erro = Signal(str)        # Sinal de erro
    
    def __init__(self, pasta_xml, pasta_saida):
        super().__init__()
        self.pasta_xml = pasta_xml
        self.pasta_saida = pasta_saida
    
    def run(self):
        """Executa processamento em thread separada"""
        try:
            processor = NFeProcessorBI(self.pasta_xml, self.pasta_saida)
            
            # Simular progresso (você pode adaptar o processor para emitir sinais)
            for i in range(0, 101, 10):
                self.progresso.emit(i)
                self.msleep(200)  # Simulação
            
            # Processar e obter estatísticas
            estatisticas = processor.processar_pasta()
            
            # Gerar relatórios (o novo processador já faz isso internamente ou tem um método para isso)
            if hasattr(processor, 'gerar_relatorios'):
                processor.gerar_relatorios()

            # Emitir resultado
            resultado = estatisticas
            resultado['pasta_saida'] = self.pasta_saida
            
            self.concluido.emit(resultado)
            
        except Exception as e:
            self.erro.emit(str(e))


class MainWindow(QMainWindow):
    """Janela Principal do NFe Inspector"""
    
    def __init__(self):
        super().__init__()
        
        self.config = ConfigManager()
        self.setWindowTitle("NFe Inspector - Sistema Profissional de Análise")
        self.setMinimumSize(1200, 800)
        
        # Configurar interface
        self.setup_ui()
        self.setup_menubar()
        self.setup_statusbar()
        self.apply_stylesheet()

        # Carregar dados iniciais
        self.carregar_dados_empresas()
        
    def setup_ui(self):
        """Configura a interface principal"""
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Cabeçalho
        header = self.criar_cabecalho()
        main_layout.addWidget(header)
        
        # Abas principais
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)  # Abas laterais
        
        # Aba 1: Processamento de NFe
        self.tab_processamento = self.criar_tab_processamento()
        self.tabs.addTab(self.tab_processamento, "📄 Processamento")
        
        # Aba 2: Dashboard
        self.tab_dashboard = self.criar_tab_dashboard()
        self.tabs.addTab(self.tab_dashboard, "📊 Dashboard")
        
        # Aba 3: Empresas
        self.tab_empresas = self.criar_tab_empresas()
        self.tabs.addTab(self.tab_empresas, "🏢 Empresas")
        
        # Aba 4: Download NFe
        self.tab_download = self.criar_tab_download()
        self.tabs.addTab(self.tab_download, "📥 Download NFe")
        
        # Aba 5: IA Fiscal
        self.tab_ia = self.criar_tab_ia()
        self.tabs.addTab(self.tab_ia, "🤖 IA Fiscal")
        
        main_layout.addWidget(self.tabs)
        
    def criar_cabecalho(self):
        """Cria cabeçalho da aplicação"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        
        # Logo/Título
        titulo = QLabel("🧾 NFe Inspector Pro")
        titulo_font = QFont("Arial", 18, QFont.Bold)
        titulo.setFont(titulo_font)
        
        # Botões de ação rápida
        btn_processar = QPushButton("⚡ Processar Rápido")
        btn_processar.clicked.connect(self.processar_rapido)
        
        btn_download = QPushButton("📥 Download NFe")
        btn_download.clicked.connect(self.abrir_download)
        
        header_layout.addWidget(titulo)
        header_layout.addStretch()
        header_layout.addWidget(btn_processar)
        header_layout.addWidget(btn_download)
        
        return header
    
    def criar_tab_processamento(self):
        """Aba de processamento de XMLs"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Título
        titulo = QLabel("Processar XMLs de NFe")
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Seleção de pasta
        pasta_layout = QHBoxLayout()
        self.label_pasta = QLabel("Nenhuma pasta selecionada")
        btn_selecionar = QPushButton("📁 Selecionar Pasta XML")
        btn_selecionar.clicked.connect(self.selecionar_pasta_xml)
        pasta_layout.addWidget(self.label_pasta)
        pasta_layout.addWidget(btn_selecionar)
        layout.addLayout(pasta_layout)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Botão processar
        btn_processar = QPushButton("🚀 Processar NFe")
        btn_processar.setMinimumHeight(50)
        btn_processar.clicked.connect(self.processar_nfe)
        layout.addWidget(btn_processar)
        
        # Tabela de resultados
        self.tabela_resultados = QTableWidget()
        self.tabela_resultados.setColumnCount(5)
        self.tabela_resultados.setHorizontalHeaderLabels([
            "Arquivo", "Status", "Chave", "Emitente", "Valor"
        ])
        layout.addWidget(self.tabela_resultados)
        
        layout.addStretch()
        return tab
    
    def criar_tab_dashboard(self):
        """Aba de dashboard com estatísticas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        titulo = QLabel("📊 Dashboard de Análises")
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # Cards de resumo
        cards_layout = QHBoxLayout()
        
        # Card 1: Total processado
        card1 = self.criar_card("Total Processado", "0", "NFe")
        cards_layout.addWidget(card1)
        
        # Card 2: Valor total
        card2 = self.criar_card("Valor Total", "R$ 0,00", "")
        cards_layout.addWidget(card2)
        
        # Card 3: Empresas
        card3 = self.criar_card("Empresas", "0", "Cadastradas")
        cards_layout.addWidget(card3)
        
        layout.addLayout(cards_layout)
        layout.addStretch()
        
        return tab
    
    def criar_card(self, titulo, valor, subtitulo):
        """Cria um card de estatística"""
        card = QWidget()
        card.setMinimumHeight(120)
        card.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        label_titulo = QLabel(titulo)
        label_titulo.setStyleSheet("color: #bdc3c7; font-size: 12px;")
        
        label_valor = QLabel(valor)
        label_valor.setStyleSheet("color: #ecf0f1; font-size: 24px; font-weight: bold;")
        
        label_sub = QLabel(subtitulo)
        label_sub.setStyleSheet("color: #95a5a6; font-size: 10px;")
        
        layout.addWidget(label_titulo)
        layout.addWidget(label_valor)
        layout.addWidget(label_sub)
        
        return card
    
    def criar_tab_empresas(self):
        """Aba de gestão de empresas"""
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
        
        # Tabela de empresas
        self.tabela_empresas = QTableWidget()
        self.tabela_empresas.setColumnCount(5)
        self.tabela_empresas.setHorizontalHeaderLabels([
            "CNPJ", "Razão Social", "UF", "Total NFe", "Valor Total"
        ])
        self.tabela_empresas.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabela_empresas.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabela_empresas.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.tabela_empresas)
        
        return tab

    def carregar_dados_empresas(self):
        """Carrega e exibe os dados das empresas na tabela."""
        try:
            db_manager = DatabaseManager()
            empresas = db_manager.listar_empresas_com_stats() 

            

            self.tabela_empresas.setRowCount(len(empresas))

            for row, empresa in enumerate(empresas):
                self.tabela_empresas.setItem(row, 0, QTableWidgetItem(empresa.get('cnpj', '')))
                self.tabela_empresas.setItem(row, 1, QTableWidgetItem(empresa.get('razao_social', '')))
                self.tabela_empresas.setItem(row, 2, QTableWidgetItem(empresa.get('uf', '')))
                self.tabela_empresas.setItem(row, 3, QTableWidgetItem(str(empresa.get('total_nfes', 0))))
                
                valor_total_str = f"R$ {empresa.get('valor_total', 0):,.2f}"
                self.tabela_empresas.setItem(row, 4, QTableWidgetItem(valor_total_str))

        except Exception as e:
            QMessageBox.critical(self, "Erro ao Carregar Empresas", f"Não foi possível carregar os dados das empresas:\n{e}")
   
       

    def criar_tab_download(self):
        """Aba de download de NFe"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        titulo = QLabel("📥 Download de NFe dos Clientes")
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        info = QLabel("Use esta aba para baixar NFe automaticamente usando certificados dos clientes")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # TODO: Integrar com sistema de download
        layout.addStretch()
        
        return tab
    
    def criar_tab_ia(self):
        """Aba de IA Fiscal"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        titulo = QLabel("🤖 Análise com IA Fiscal")
        titulo.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(titulo)
        
        # TODO: Integrar com módulo de IA
        layout.addStretch()
        
        return tab
    
    def setup_menubar(self):
        """Configura menu superior"""
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
        
        # Menu Ferramentas
        menu_ferramentas = menubar.addMenu("&Ferramentas")
        
        acao_download = QAction("📥 Download NFe", self)
        acao_download.triggered.connect(self.abrir_download)
        menu_ferramentas.addAction(acao_download)
        
        # Menu Ajuda
        menu_ajuda = menubar.addMenu("&Ajuda")
        
        acao_sobre = QAction("ℹ️ Sobre", self)
        acao_sobre.triggered.connect(self.mostrar_sobre)
        menu_ajuda.addAction(acao_sobre)
    
    def setup_statusbar(self):
        """Configura barra de status"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("✅ Pronto")
    
    def apply_stylesheet(self):
        """Aplica tema escuro moderno"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #2d2d30;
                color: #cccccc;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QPushButton:pressed {
                background-color: #0d5689;
            }
            QTabWidget::pane {
                border: 1px solid #3e3e42;
                background: #2d2d30;
            }
            QTabBar::tab {
                background: #252526;
                color: #cccccc;
                padding: 10px 20px;
                border: 1px solid #3e3e42;
            }
            QTabBar::tab:selected {
                background: #0e639c;
                color: white;
            }
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #3e3e42;
                color: #cccccc;
            }
            QHeaderView::section {
                background-color: #252526;
                color: #cccccc;
                padding: 5px;
                border: 1px solid #3e3e42;
            }
        """)
    
    def selecionar_pasta_xml(self):
        """Seleciona pasta com XMLs"""
        pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Pasta com XMLs de NFe",
            "",
            QFileDialog.ShowDirsOnly
        )
        
        if pasta:
            self.label_pasta.setText(f"📁 {pasta}")
            self.pasta_xml_selecionada = pasta
            self.statusbar.showMessage(f"Pasta selecionada: {pasta}")
    
    def processar_nfe(self):
        """Processa NFe em thread separada"""
        if not hasattr(self, 'pasta_xml_selecionada'):
            QMessageBox.warning(
                self,
                "Atenção",
                "Selecione uma pasta com XMLs primeiro!"
            )
            return
        
        # Mostrar progresso
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusbar.showMessage("🔄 Processando...")
        
        # Criar e iniciar thread
        pasta_saida = self.config.get('PADRAO', 'pasta_saida', 'relatorios_nfe')
        self.thread = ProcessamentoThread(self.pasta_xml_selecionada, pasta_saida)
        self.thread.progresso.connect(self.atualizar_progresso)
        self.thread.concluido.connect(self.processamento_concluido)
        self.thread.erro.connect(self.processamento_erro)
        self.thread.start()
    
    def processar_rapido(self):
        """Processamento rápido via botão header"""
        self.tabs.setCurrentIndex(0)  # Mudar para aba processamento
        self.selecionar_pasta_xml()
    
    def abrir_download(self):
        """Abre aba de download"""
        self.tabs.setCurrentIndex(3)  # Aba download
    
    def atualizar_progresso(self, valor):
        """Atualiza barra de progresso"""
        self.progress_bar.setValue(valor)
    
    def processamento_concluido(self, resultado):
        """Callback quando processamento terminar"""
        self.progress_bar.setVisible(False)
        self.statusbar.showMessage(
            f"✅ Processamento concluído: {resultado['total_processadas']} NFe processadas"
        )
        
        QMessageBox.information(
            self,
            "Sucesso",
            f"Processamento concluído!\n\n"
            f"Total processadas: {resultado['total_processadas']}\n"
            f"Com erro: {resultado['com_erro']}\n"
            f"Relatórios salvos em: {resultado['pasta_saida']}"
        )
    
    def processamento_erro(self, erro):
        """Callback quando houver erro"""
        self.progress_bar.setVisible(False)
        self.statusbar.showMessage("❌ Erro no processamento")
        
        QMessageBox.critical(
            self,
            "Erro",
            f"Erro durante o processamento:\n\n{erro}"
        )
    
    def mostrar_sobre(self):
        """Mostra diálogo sobre"""
        QMessageBox.about(
            self,
            "Sobre NFe Inspector",
            "<h2>NFe Inspector Pro</h2>"
            "<p>Sistema profissional de análise de NFe</p>"
            "<p>Versão 2.0 - PySide6</p>"
            "<p>Desenvolvido com ❤️ em Python</p>"
        )


def main():
    """Função principal"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Estilo moderno
    
    # Janela principal
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()