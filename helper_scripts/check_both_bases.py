import psycopg2
from qdrant_client import QdrantClient

# --- PostgreSQL ---
def check_postgres():
    try:
        conn = psycopg2.connect(
            dbname="basedata",
            user="baseuser",
            password="basepass",
            host="localhost",
            port=5432
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM events;")
        count = cur.fetchone()[0]
        print(f"✅ PostgreSQL: {count} rekordów w tabeli 'events'")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL błąd: {e}")

# --- Qdrant ---
def check_qdrant():
    try:
        client = QdrantClient(host="localhost", port=6333)
        count = client.count(collection_name="base_events", exact=True)
        print(f"✅ Qdrant: {count.count} wektorów w kolekcji 'base_events'")
    except Exception as e:
        print(f"❌ Qdrant błąd: {e}")

if __name__ == "__main__":
    print("🔍 Sprawdzanie zawartości baz danych...")
    check_postgres()
    check_qdrant()
