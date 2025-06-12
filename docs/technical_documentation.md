# Dokumentacja techniczna: Military Base Security System (IoT + RAG)

## Spis treści
1. Wprowadzenie
2. Architektura systemu
3. Opis komponentów
   - 3.1 Producer (iot_simulator/producer.py)
   - 3.2 Consumer
   - 3.3 Qdrant i PostgreSQL
   - 3.4 LM Studio i LLM
   - 3.5 Query Engine (RAG)
4. Format danych i schemat komunikatów
5. Przepływ danych
6. Technologie i zależności
7. Testowanie i debugowanie
8. Uwagi końcowe

---

## 1. Wprowadzenie

System służy do symulacji i analizy zdarzeń w bazie wojskowej z wykorzystaniem urządzeń IoT, strumieniowania danych (Apache Kafka) oraz asystenta decyzyjnego opartego o LLM (RAG).

## 2. Architektura systemu

System opiera się na architekturze modularnej, w której dane z czujników (symulowanych) są przesyłane przez Kafka do dwóch baz danych (Qdrant, PostgreSQL), a następnie wykorzystywane przez moduł RAG do udzielania odpowiedzi użytkownikowi.

## 3. Opis komponentów

### 3.1 Producer (iot_simulator/producer.py)

**Cel:**  
Symuluje działanie urządzeń IoT rozmieszczonych w bazie. Losowo generuje komunikaty dotyczące wykrytych zdarzeń (ruch, dźwięk, otwarcie bramy, obecność itp.) i publikuje je do brokera Kafka na temat `base_security_events`.

**Mechanizm działania:**
- Losowo wybiera typ zdarzenia, strefę (`zone`), czujnik (`device_id`) i poziom ważności (`severity`).
- Komunikat jest tworzony jako słownik, a następnie serializowany do formatu JSON i wysyłany przez `KafkaProducer`.
- Obsługuje zatrzymanie programu przez `Ctrl+C`.

**Format danych (przykład):**
```json
{
  "timestamp": "2025-06-12T12:34:56.789Z",
  "device_id": "sensor_B2",
  "zone": "sector_C",
  "event_type": "motion_detected",
  "event_value": true,
  "severity": "high",
  "description": "Ruch wykryty przy ogrodzeniu"
}
```

**Technologie:**  
Python 3.10+, `kafka-python`, `faker`, `json`, `datetime`, `random`.

---

(...pozostałe sekcje będą uzupełnione w dalszej części)


### 3.2 Consumer (ingestion/consumer.py)

**Cel:**  
Odbiera wiadomości z Apache Kafka, a następnie zapisuje je do dwóch baz danych:
- PostgreSQL (dane strukturalne)
- Qdrant (embeddingi semantyczne)

**Mechanizm działania:**
- Inicjalizuje połączenia do Kafka, PostgreSQL i Qdrant.
- W pętli oczekuje na wiadomości z topiku `base_security_events`.
- Po odebraniu wiadomości:
  - parsuje dane
  - zapisuje wszystkie pola do tabeli `events` w PostgreSQL
  - generuje embedding na podstawie opisu i zapisuje wektor do Qdrant z odpowiednim payloadem

**Format danych:**  
Taki sam jak generowany przez `producer.py` – dane JSON z 7 polami.

**Wykorzystywane technologie:**  
`kafka-python`, `psycopg2`, `sentence-transformers`, `qdrant-client`, `uuid`, `datetime`.

---


### 3.5 Query Engine (RAG) – rag/query_engine_extended.py

**Cel:**  
Moduł odpowiedzialny za przyjmowanie zapytań użytkownika i generowanie odpowiedzi przy użyciu podejścia RAG (Retrieval-Augmented Generation).

**Mechanizm działania:**
1. Odbiera pytanie użytkownika.
2. Generuje embedding pytania i wyszukuje najbardziej podobne wpisy w bazie Qdrant.
3. Równolegle analizuje pytanie i buduje zapytanie SQL do PostgreSQL na podstawie stref, typów zdarzeń, czasu lub daty.
4. Łączy kontekst z obu baz danych i buduje prompt.
5. Wysyła prompt do lokalnego modelu LLM przez LM Studio API (`http://localhost:1234/v1/chat/completions`).
6. Zwraca odpowiedź modelu i wyświetla ją w terminalu.

**Przetwarzane dane wejściowe:**
- Pytania użytkownika zadawane w języku naturalnym (np. "czy był ruch przy bramie po północy?").

**Wykorzystywane komponenty:**
- QdrantClient do wyszukiwania embeddingów.
- PostgreSQL do analizy danych strukturalnych.
- SentenceTransformer do generowania wektorów pytania.
- LM Studio (API) jako silnik generujący odpowiedź.

**Przykład pytania:**
> Czy wykryto hałas w sektorze B między 1 a 3 w nocy?

---


## 4. Architektura systemu

System składa się z trzech głównych warstw:

1. **Warstwa IoT (Symulacja)**
   - Generuje dane na temat zdarzeń w bazie wojskowej.
   - Publikuje je do Apache Kafka jako wiadomości JSON.

2. **Warstwa przetwarzania danych**
   - `consumer.py` odbiera dane i zapisuje je do dwóch źródeł:
     - PostgreSQL (dane strukturalne)
     - Qdrant (embedding + semantyka opisu)

3. **Warstwa interakcji (RAG)**
   - Użytkownik zadaje pytanie przez GUI lub CLI.
   - `query_engine_extended.py` tworzy embedding pytania, łączy wyniki z Qdrant i PostgreSQL.
   - LLM generuje odpowiedź kontekstową na podstawie danych.

---

## 5. Schemat komunikacji

```
 IoT Simulator
      |
      v
 Apache Kafka  <--- Kafdrop (Monitoring)
      |
      v
 Kafka Consumer (ingestion)
   |               |
   v               v
PostgreSQL      Qdrant
   \              //
    \            //
     \          //
      \        //
       v      v
  Query Engine (RAG)
       |
       v
     LM Studio (LLM)
       |
       v
     Odpowiedź
```

---

