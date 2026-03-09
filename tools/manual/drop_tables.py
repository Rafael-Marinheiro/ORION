import sqlite3

def drop_table_if_exists(table_name):
    conn = sqlite3.connect('simulador_operacional/db.sqlite3')
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    result = c.fetchone()
    if result:
        c.execute(f"DROP TABLE {table_name}")
        print(f"Dropped table {table_name}")
    else:
        print(f"Table {table_name} does not exist")
    conn.commit()
    conn.close()

def main():
    tables = [
        "RODADAS",
        "RESULTADOS_FINANCEIROS",
        "GRUPOS",
        "GRUPOS_membros"
    ]
    for table in tables:
        drop_table_if_exists(table)

if __name__ == "__main__":
    main()
