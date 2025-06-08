import psycopg2
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

# --- PostgreSQL ---
def clear_postgres():
    try:
        conn = psycopg2.connect(
            dbname="basedata",
            user="baseuser",
            password="basepass",
            host="localhost",
            port=5432
        )
        cur = conn.cursor()
        cur.execute("DELETE FROM events;")
        conn.commit()
        cur.close()
        conn.close()
        print("🧹 PostgreSQL: tabela 'events' została wyczyszczona.")
    except Exception as e:
        print(f"❌ PostgreSQL błąd: {e}")

# --- Qdrant ---
def clear_qdrant():
    try:
        client = QdrantClient(host="localhost", port=6333)
        client.recreate_collection(
            collection_name="base_events",
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
        print("🧹 Qdrant: kolekcja 'base_events' została wyczyszczona (recreated).")
    except Exception as e:
        print(f"❌ Qdrant błąd: {e}")

if __name__ == "__main__":
    print("🧹 Czyszczenie baz danych...")
    clear_postgres()
    clear_qdrant()
