import tkinter as tk
from database.models import DatabaseManager
from ui.dashboard_nfe import DashboardNFe

if __name__ == "__main__":
    db_manager = DatabaseManager()
    root = tk.Tk()
    root.withdraw()
    dashboard = DashboardNFe(root, db_manager)
    root.mainloop()
