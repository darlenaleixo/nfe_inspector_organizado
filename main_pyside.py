# ui/main_pyside.py

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QStackedWidget, QLabel, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NFe Inspector Pro - PySide6")
        self.resize(1400, 900)

        # Container principal
        container = QWidget()
        layout = QHBoxLayout(container)
        self.setCentralWidget(container)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFrameShape(QFrame.StyledPanel)
        sidebar.setFixedWidth(250)
        vbox = QVBoxLayout(sidebar)
        vbox.setContentsMargins(10, 20, 10, 20)
        vbox.setSpacing(20)

        logo = QLabel("NFe Inspector")
        logo.setAlignment(Qt.AlignCenter)
        logo.setStyleSheet("font-size: 20px; font-weight: bold;")
        vbox.addWidget(logo)

        btn_process = QPushButton("📁 Processar XMLs")
        btn_companies = QPushButton("🏢 Gestão Empresas")
        btn_dashboard = QPushButton("📊 Dashboard BI")
        btn_settings = QPushButton("⚙️ Configurações")

        for btn in (btn_process, btn_companies, btn_dashboard, btn_settings):
            btn.setFixedHeight(40)
            btn.setStyleSheet("text-align: left; padding-left: 10px;")
            vbox.addWidget(btn)
        vbox.addStretch()

        # Área de conteúdo
        self.stack = QStackedWidget()
        self.stack.addWidget(self.page_process())
        self.stack.addWidget(self.page_companies())
        self.stack.addWidget(self.page_dashboard())
        self.stack.addWidget(self.page_settings())

        # Conectar botões
        btn_process.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_companies.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_dashboard.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        btn_settings.clicked.connect(lambda: self.stack.setCurrentIndex(3))

        layout.addWidget(sidebar)
        layout.addWidget(self.stack)

    def page_process(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.addWidget(QLabel("Página de Processamento"), alignment=Qt.AlignCenter)
        # Aqui entraria formulário e botões de filtro
        return page

    def page_companies(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.addWidget(QLabel("Gestão de Empresas"), alignment=Qt.AlignCenter)

        table = QTableWidget(0, 5)
        table.setHorizontalHeaderLabels([
            "CNPJ", "Razão Social", "UF", "Total NFe", "Valor Total"
        ])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        v.addWidget(table)
        return page

    def page_dashboard(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.addWidget(QLabel("Dashboard BI"), alignment=Qt.AlignCenter)

        # Exemplo de estatísticas
        stats = QHBoxLayout()
        for label in ("Arquivos: 931", "NF-e: 931", "Empresas: 1"):
            lbl = QLabel(label)
            lbl.setStyleSheet("font-size: 16px;")
            stats.addWidget(lbl)
        stats.addStretch()
        v.addLayout(stats)

        return page

    def page_settings(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.addWidget(QLabel("Configurações"), alignment=Qt.AlignCenter)
        return page

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
