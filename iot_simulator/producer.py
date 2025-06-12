# Simulacja IoT - Kafka producer
import json
import time
import random
from datetime import datetime
from kafka import KafkaProducer
from faker import Faker
import sys

sys.stdout.reconfigure(line_buffering=True)

fake = Faker()
# Konfiguracja Kafka
KAFKA_TOPIC = "base_security_events"
KAFKA_SERVER = "localhost:29092"

producer = KafkaProducer(
    bootstrap_servers=['localhost:29092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(3, 4, 0) 
)

# Możliwe dane wejściowe
event_types = [
    ("motion_detected", True, "Ruch wykryty przy ogrodzeniu"),
    ("gate_opened", True, "Brama została otwarta"),
    ("gate_closed", True, "Brama została zamknięta"),
    ("sound_detected", lambda: round(random.uniform(50.0, 95.0), 1), "Wykryto hałas"),
    ("presence_detected", True, "Wykryto osobę"),
    ("thermal_signature", True, "Wykryto sygnaturę termiczną"),
    ("no_patrol_response", True, "Brak reakcji patrolu")
]

zones = ["sector_A", "sector_B", "sector_C", "gate_north", "gate_south", "gate_west"]
devices = ["sensor_A1", "sensor_B2", "sensor_C3", "motion_sensor_D1", "audio_sensor_G2"]

severities = ["low", "medium", "high"]

print(f"Start symulacji - publikacja na topic '{KAFKA_TOPIC}'", flush=True)

try:
    while True:
        event_type, value, description = random.choice(event_types)
        event_value = value() if callable(value) else value

        message = {
            "timestamp": datetime.utcnow().isoformat(),
            "device_id": random.choice(devices),
            "zone": random.choice(zones),
            "event_type": event_type,
            "event_value": event_value,
            "severity": random.choice(severities),
            "description": description
        }

        producer.send(KAFKA_TOPIC, message)
        print(f"Wysłano zdarzenie: {message['event_type']} ({message['zone']})", flush=True)

        time.sleep(random.uniform(1.0, 3.0))

except KeyboardInterrupt:
    print("Zatrzymano symulację.", flush=True)
finally:
    producer.flush()
    producer.close()
