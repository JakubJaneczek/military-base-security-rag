# Military Base Security System (IoT + RAG)

Projekt systemu monitorowania bezpieczeństwa bazy wojskowej, wykorzystujący:
- Symulację urządzeń IoT (Kafka producer)
- Apache Kafka jako pośrednik wiadomości
- PostgreSQL (baza strukturalna)
- Qdrant (baza wektorowa)
- Local LLM (LM Studio) jako asystent decyzyjny (RAG)
- GUI do uruchamiania systemu

---

## 📦 Wymagania

- Windows 11 / Linux
- Python 3.10 (nie działa na 3.13, inne wersje nietestowane)
- Docker + Docker Compose
- [LM Studio](https://lmstudio.ai) z załadowanym modelem wspierającym OpenAI API (w projekcie wykorzystany mistral-7b-instruct-v0.2)

---

## 🛠 Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/JakubJaneczek/military-base-security-rag.git
cd military-base-security-rag
```

2. Stwórz środowisko i zainstaluj zależności:
```bash
python3.10 -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

3. Uruchom Docker Desktop i stwórz kontenery:
```bash
cd docker
docker compose up -d
```

4. Stwórz wymagane bazy:
```bash
cd ..
python helper_scripts/create_postgres_table.py
python helper_scripts/create_qdrant_collection.py
```

5. Uruchom LM Studio i załaduj model (mistral-7b-instruct-v0.2), włącz tryb OpenAI-compatible API (`http://localhost:1234/v1/chat/completions`)

---

## ▶️ Uruchomienie systemu

Uruchom aplikację graficzną:
```bash
python gui_launcher.py
```
Po uruchoieniu aplikacji mogą pobierać się dodatkowe zależności, należy poczekać na ich zakończenie.

Dostępne zakładki:
- **Symulacja** – uruchamia producer (publikuje zdarzenia do Kafki); powinna wyświetlać informacje o zapisie zdarzenia.
- **Ingestor** – uruchamia consumer (zapisuje do PostgreSQL i Qdrant); powinna wyświetlac informacje o odebraniu zdarzenia.
- **RAG** – zadajesz pytanie → model generuje odpowiedź na podstawie danych; powinien zachęcać użytkownika do zadania pytania i wyświetlać uzyskaną odpowiedź.

---

## ❓ Przykładowe pytania

- Czy wykryto ruch przy bramie zachodniej po północy?
- Czy były jakiekolwiek zdarzenia w sektorze A między 2 a 5 w nocy?
- Czy dzisiaj wykryto dźwięk w sektorze C?

---

## 🧠 Architektura RAG

Równoległe zapytania:
- 🔹 Semantyczne (embedding pytania → Qdrant)
- 🔸 Strukturalne (parsowanie pytania → SQL do PostgreSQL)

Połączone wyniki → prompt → odpowiedź z modelu LLM

---

## 📂 Struktura katalogów

```
.
├── docker/               # docker-compose.yml i konfiguracje
├── iot_simulator/        # producer.py – generowanie danych
├── ingestion/            # consumer.py – zapis do baz
├── rag/                  # query_engine_extended.py
├── helper_scripts/       # inicjalizacja baz, testy
├── gui_launcher.py       # interfejs graficzny
├── requirements.txt
└── README.md
```

---

## 📄 Licencja

Projekt demonstracyjny do celów edukacyjnych.
