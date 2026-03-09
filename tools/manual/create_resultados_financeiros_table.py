import sqlite3

def create_resultados_financeiros_table():
    conn = sqlite3.connect('simulador_operacional/db.sqlite3')
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS RESULTADOS_FINANCEIROS (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        receita DECIMAL(10, 2) DEFAULT 0,
        custos DECIMAL(10, 2) DEFAULT 0,
        despesas DECIMAL(10, 2) DEFAULT 0,
        fluxo_caixa_entrada DECIMAL(10, 2) DEFAULT 0,
        fluxo_caixa_saida DECIMAL(10, 2) DEFAULT 0,
        lucro_liquido DECIMAL(10, 2) DEFAULT 0,
        fluxo_caixa_liquido DECIMAL(10, 2) DEFAULT 0,
        rodada_id INTEGER UNIQUE,
        FOREIGN KEY(rodada_id) REFERENCES RODADAS(id) ON DELETE CASCADE
    )
    """)
    conn.commit()
    conn.close()
    print("Tabela RESULTADOS_FINANCEIROS criada (se não existia).")

if __name__ == "__main__":
    create_resultados_financeiros_table()
