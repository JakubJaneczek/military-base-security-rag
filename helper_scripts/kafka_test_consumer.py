from kafka import KafkaConsumer

print("[TEST] Łączenie z Kafka na localhost:29092...")

try:
    consumer = KafkaConsumer(
        'base_security_events',
        bootstrap_servers='localhost:29092',
        auto_offset_reset='earliest',
        enable_auto_commit=True
    )

    print("[TEST] Połączono. Oczekiwanie na wiadomości...")
    for message in consumer:
        print(f"[TEST] Odebrano wiadomość: {message.value}")

except Exception as e:
    print(f"[TEST] ❌ Błąd: {e}")
