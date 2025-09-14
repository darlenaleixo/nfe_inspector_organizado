# listar_pagamentos.py

import sqlite3

def listar_formas():
    conn = sqlite3.connect("nfe_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT forma_pagamento FROM notas_fiscais")
    formas = [row[0] or "<vazio>" for row in cursor.fetchall()]
    conn.close()
    print("Valores distintos de forma_pagamento no banco:")
    for f in formas:
        print(f"- {f}")

if __name__ == "__main__":
    listar_formas()
