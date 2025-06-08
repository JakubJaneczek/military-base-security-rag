import requests

url = "http://localhost:1234/v1/chat/completions"

payload = {
    "model": "local-model",
    "messages": [
        {
            "role": "user",
            "content": (
                "Jestes wojskowym asystentem analizujacym dane z bazy. "
                "Czy byl ruch w sektorze C o 2 w nocy?"
            )
        }
    ],
    "temperature": 0.7,
    "stream": False
}

response = requests.post(url, json=payload)
if response.status_code == 200:
    print("🧠 Odpowiedz LLM:")
    print(response.json()["choices"][0]["message"]["content"])
else:
    print("❌ Blad:", response.status_code)
    print(response.text)
