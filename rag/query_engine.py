# Logika RAG - łączenie Qdrant + SQL + LLM
import json
import psycopg2
import requests
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from qdrant_client.http.models import Filter, SearchRequest
from datetime import datetime

# --- Konfiguracja ---
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
QDRANT_COLLECTION = "base_events"

PG_CONFIG = {
    "dbname": "basedata",
    "user": "baseuser",
    "password": "basepass",
    "host": "localhost",
    "port": 5432
}

LLM_API_URL = "http://localhost:1234/v1/chat/completions"

# --- Inicjalizacja ---
model = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
pg_conn = psycopg2.connect(**PG_CONFIG)
pg_cursor = pg_conn.cursor()

# --- Pobierz pytanie użytkownika ---
print("🧠 Zadaj pytanie:")
user_input = input("> ").strip()

# --- Krok 1: embedding pytania ---
query_vector = model.encode(user_input).tolist()

# --- Krok 2: wyszukiwanie w Qdrant ---
hits = qdrant.search(
    collection_name=QDRANT_COLLECTION,
    query_vector=query_vector,
    limit=5
)

# --- Krok 3: kontekst z Qdrant ---
context_lines = []
for hit in hits:
    payload = hit.payload
    context_lines.append(f"- [{payload.get('event_type')}] {payload.get('description')}")

context_text = "\n".join(context_lines)

# --- Krok 4: budowa promptu dla LLM ---
prompt = f"""
Dane z monitoringu bazy wojskowej:

{context_text}

Na podstawie powyższych danych odpowiedz na pytanie:
"{user_input}"
"""

# --- Krok 5: zapytanie do LLM Studio ---
response = requests.post(LLM_API_URL, json={
    "model": "local-model",
    "messages": [
        {"role": "user", "content": prompt}
    ],
    "temperature": 0.7,
    "stream": False
})

# --- Wyświetlenie odpowiedzi ---
if response.status_code == 200:
    answer = response.json()["choices"][0]["message"]["content"]
    print("\nOdpowiedź modelu:")
    print(answer)
else:
    print(f"Błąd {response.status_code}: {response.text}")
