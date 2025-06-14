"""
ingestion/consumer.py
Cel: Konsument Apache Kafka – odbiera dane i zapisuje je do PostgreSQL i Qdrant.
"""

import json
import psycopg2
from kafka import KafkaConsumer
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from datetime import datetime
import uuid
import sys

# Buforowanie natychmiastowe dla Windowsa
sys.stdout.reconfigure(line_buffering=True)

# --- Konfiguracja ---
KAFKA_TOPIC = "base_security_events"
KAFKA_SERVER = "localhost:29092"

# Połączenie z PostgreSQL
pg_conn = psycopg2.connect(
    dbname="basedata",
    user="baseuser",
    password="basepass",
    host="localhost",
    port=5432
)
pg_cursor = pg_conn.cursor()

# Połączenie z Qdrant
qdrant = QdrantClient(host="localhost", port=6333)
COLLECTION_NAME = "base_events"

# Załadowanie modelu do generowania embeddingów
model = SentenceTransformer("all-MiniLM-L6-v2")

# Inicjalizacja Kafka consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_SERVER,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="base_ingestor"
)

print(f"Subskrybowanie topicu: {KAFKA_TOPIC}", flush=True)

try:
    for msg in consumer:
        print("Odebrano wiadomość z Kafki...", flush=True)
        data = msg.value
        print(f"Zdarzenie: {data['event_type']} w {data['zone']}", flush=True)

        # --- ZAPIS DO POSTGRESQL (dane strukturalne) ---
        insert_query = """
            INSERT INTO events (timestamp, device_id, zone, event_type, event_value, severity, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        pg_cursor.execute(insert_query, (
            data["timestamp"],
            data["device_id"],
            data["zone"],
            data["event_type"],
            str(data["event_value"]),
            data["severity"],
            data["description"]
        ))
        pg_conn.commit()

        # --- ZAPIS DO QDRANT (embedding + semantyczny payload) ---
        embedding_input = data["description"]
        vector = model.encode(embedding_input).tolist()

        payload = {
            "description": data["description"],
            "event_type": data["event_type"]
        }

        # Wstawienie punktu wektorowego z unikalnym identyfikatorem
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload=payload
        )

        qdrant.upsert(collection_name=COLLECTION_NAME, points=[point])

except Exception as e:
    print(f"Błąd: {e}", flush=True)
