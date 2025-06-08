import psycopg2

def create_postgres_table():
    conn = psycopg2.connect(
        dbname="basedata",
        user="baseuser",
        password="basepass",
        host="localhost",
        port=5432
    )
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMPTZ NOT NULL,
            device_id TEXT NOT NULL,
            zone TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_value TEXT,
            severity TEXT,
            description TEXT
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Tabela 'events' w PostgreSQL utworzona.")

if __name__ == "__main__":
    create_postgres_table()
