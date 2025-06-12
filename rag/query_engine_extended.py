import json
import re
import psycopg2
import requests
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from datetime import datetime, timedelta
import sys

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

ZONE_MAP = {
    "brama zachodnia": "gate_west",
    "brama południowa": "gate_south",
    "brama północna": "gate_north",
    "sektor a": "sector_A",
    "sektor b": "sector_B",
    "sektor c": "sector_C",
    "ogrodzenie": "sector_C"
}

TIME_KEYWORDS = {
    "o 0 w nocy": "00:00:00",
    "po 0 w nocy": "00:00:00",
    "o 1 w nocy": "01:00:00",
    "po 1 w nocy": "01:00:00",
    "o 2 w nocy": "02:00:00",
    "po 2 w nocy": "02:00:00",
    "o 3 w nocy": "03:00:00",
    "po 3 w nocy": "03:00:00",
    "o 4 w nocy": "04:00:00",
    "po 4 w nocy": "04:00:00",
    "o 5 w nocy": "05:00:00",
    "po 5 w nocy": "05:00:00",
    "o 6": "06:00:00", "po 6": "06:00:00", "o 7": "07:00:00", "po 7": "07:00:00",
    "o 8": "08:00:00", "po 8": "08:00:00", "o 9": "09:00:00", "po 9": "09:00:00",
    "o 10": "10:00:00", "po 10": "10:00:00", "o 11": "11:00:00", "po 11": "11:00:00",
    "o 12": "12:00:00", "po 12": "12:00:00", "o 13": "13:00:00", "po 13": "13:00:00",
    "o 14": "14:00:00", "po 14": "14:00:00", "o 15": "15:00:00", "po 15": "15:00:00",
    "o 16": "16:00:00", "po 16": "16:00:00", "o 17": "17:00:00", "po 17": "17:00:00",
    "o 18": "18:00:00", "po 18": "18:00:00", "o 19": "19:00:00", "po 19": "19:00:00",
    "o 20": "20:00:00", "po 20": "20:00:00", "o 21": "21:00:00", "po 21": "21:00:00",
    "o 22": "22:00:00", "po 22": "22:00:00", "o 23": "23:00:00", "po 23": "23:00:00"
}

EVENT_TYPE_KEYWORDS = {
    "ruch": "motion_detected",
    "dźwięk": "sound_detected",
    "otwarcie": "door_opened",
    "zamknięcie": "door_closed",
    "obecność": "presence_detected",
    "osoba": "thermal_signature"
}

MONTHS = {
    "stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4,
    "maja": 5, "czerwca": 6, "lipca": 7, "sierpnia": 8,
    "września": 9, "października": 10, "listopada": 11, "grudnia": 12
}

# --- Inicjalizacja ---
model = SentenceTransformer("all-MiniLM-L6-v2")
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
pg_conn = psycopg2.connect(**PG_CONFIG)
pg_cursor = pg_conn.cursor()

print("Zadaj pytanie:", flush=True)

for line in sys.stdin:
    user_input = line.strip().lower()
    if not user_input:
        continue

    print(f"Zapytanie: {user_input}", flush=True)

    query_vector = model.encode(user_input).tolist()
    hits = qdrant.search(
        collection_name=QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=5
    )

    context_lines = []
    for hit in hits:
        payload = hit.payload
        context_lines.append(f"- [{payload.get('event_type')}] {payload.get('description')}")
    context_text = "\n".join(context_lines)

    zone_filter = time_filter = event_filter = date_filter = None
    time_range = None

    for phrase, zone in ZONE_MAP.items():
        if phrase in user_input:
            zone_filter = zone
            break

    for phrase, time_str in TIME_KEYWORDS.items():
        if phrase in user_input:
            time_filter = time_str
            break

    range_match = re.search(r"między (\d+) a (\d+) w nocy", user_input)
    if range_match:
        t1, t2 = int(range_match.group(1)), int(range_match.group(2))
        time_range = (f"{t1:02d}:00:00", f"{t2:02d}:00:00")

    for phrase, etype in EVENT_TYPE_KEYWORDS.items():
        if phrase in user_input:
            event_filter = etype
            break

    today = datetime.now().date()
    if "dzisiaj" in user_input:
        date_filter = today
    elif "wczoraj" in user_input:
        date_filter = today - timedelta(days=1)
    else:
        match = re.search(r"(\d{1,2})\.?\s*(czerwca|maja|lipca|sierpnia)", user_input)
        if match:
            day = int(match.group(1))
            month = MONTHS.get(match.group(2), None)
            if month:
                date_filter = datetime(datetime.now().year, month, day).date()

    pg_context_lines = []
    sql = "SELECT timestamp, zone, event_type, description FROM events WHERE TRUE"
    params = []

    if zone_filter:
        sql += " AND zone = %s"
        params.append(zone_filter)

    if time_filter:
        sql += " AND timestamp::time >= %s"
        params.append(time_filter)

    if time_range:
        sql += " AND timestamp::time BETWEEN %s AND %s"
        params.extend(time_range)

    if event_filter:
        sql += " AND event_type = %s"
        params.append(event_filter)

    if date_filter:
        sql += " AND timestamp::date = %s"
        params.append(date_filter)

    sql += " ORDER BY timestamp DESC LIMIT 5"
    pg_cursor.execute(sql, tuple(params))
    results = pg_cursor.fetchall()

    for ts, zone, etype, desc in results:
        pg_context_lines.append(f"- [{etype}] {desc} @ {ts.strftime('%Y-%m-%d %H:%M:%S')} ({zone})")

    pg_context_text = "\n".join(pg_context_lines)

    prompt = "Dane z monitoringu bazy wojskowej:\n\n"
    if context_lines:
        prompt += "🔹 Wyniki semantyczne (Qdrant):\n" + context_text + "\n\n"
    if pg_context_lines:
        prompt += "🔸 Wyniki strukturalne (PostgreSQL):\n" + pg_context_text + "\n\n"
    prompt += f"Na podstawie powyższych danych odpowiedz na pytanie:\n\"{user_input}\""

    response = requests.post(LLM_API_URL, json={
        "model": "local-model",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "stream": False
    })

    if response.status_code == 200:
        answer = response.json()["choices"][0]["message"]["content"]
        print("\nOdpowiedź modelu:\n")
        print(answer, flush=True)
    else:
        print(f"Błąd {response.status_code}: {response.text}", flush=True)

    print("\nZadaj pytanie:", flush=True)
