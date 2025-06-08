from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance

def create_qdrant_collection():
    client = QdrantClient(host="localhost", port=6333)

    client.recreate_collection(
        collection_name="base_events",
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )
    print("✅ Kolekcja 'base_events' w Qdrant utworzona.")

if __name__ == "__main__":
    create_qdrant_collection()
