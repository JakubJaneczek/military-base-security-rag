import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import subprocess
import threading
import requests
import time
import queue

PREDEFINED_CATEGORIES = {
    "Lokalizacja": [
        "Czy wykryto ruch przy bramie zachodniej po północy?",
        "Czy była obecność w sektorze C w ciągu ostatnich 2 godzin?",
        "Czy uruchomił się alarm w sektorze A dziś rano?",
        "Co działo się przy bramie północnej?"
    ],
    "Typ zdarzenia": [
        "Czy wykryto dźwięki w okolicach ogrodzenia?",
        "Czy brama była otwierana w nocy?",
        "Czy ktoś wykrył sygnaturę termiczną dziś po południu?",
        "Czy którykolwiek czujnik zgłosił brak odpowiedzi patrolu?"
    ],
    "Czas": [
        "Czy po godzinie 22:00 pojawiły się jakiekolwiek zdarzenia?",
        "Czy między 1:00 a 3:00 rano wykryto coś podejrzanego?",
        "Czy były jakieś zdarzenia o dużej ważności w nocy?"
    ],
    "Złożone": [
        "Czy doszło do otwarcia bramy bez wykrycia obecności?",
        "Czy wykryto jednocześnie ruch i dźwięk w tej samej strefie?",
        "Czy w sektorze B pojawiły się sygnały bez reakcji patrolu?"
    ],
    "Ogólne": [
        "Czy dzisiejsza noc była spokojna?",
        "Czy baza była bezpieczna w ciągu ostatnich 24 godzin?",
        "Jakie były najważniejsze zdarzenia w sektorze A?"
    ]
}

class LauncherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Military Base Security System Launcher")
        self.geometry("1100x750")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.outputs = {}
        self.processes = {}
        self.rag_input_queue = queue.Queue()

        for name in ["Producer", "Consumer", "RAG"]:
            frame = ttk.Frame(self.tabs)

            text_widget = ScrolledText(frame, wrap=tk.WORD, height=30)
            text_widget.pack(fill=tk.BOTH, expand=True)

            if name == "RAG":
                entry_frame = ttk.Frame(frame)
                entry_frame.pack(fill=tk.X, pady=5)

                self.rag_entry = ttk.Entry(entry_frame)
                self.rag_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                self.rag_entry.bind("<Return>", self.send_rag_input)

                submit_btn = ttk.Button(entry_frame, text="Wyślij", command=self.send_rag_input)
                submit_btn.pack(side=tk.RIGHT, padx=5)

                preset_tabs = ttk.Notebook(frame)
                preset_tabs.pack(fill=tk.BOTH, pady=5)

                for category, questions in PREDEFINED_CATEGORIES.items():
                    tab = ttk.Frame(preset_tabs)
                    preset_tabs.add(tab, text=category)
                    for q in questions:
                        btn = ttk.Button(tab, text=q, command=lambda txt=q: self.set_and_send(txt))
                        btn.pack(anchor="w", fill=tk.X, padx=10, pady=1)

            self.outputs[name] = text_widget
            self.tabs.add(frame, text=name)

        self.after(100, self.launch_all)

    def log(self, label, text):
        widget = self.outputs.get(label)
        if widget:
            widget.insert(tk.END, text + "\n")
            widget.see(tk.END)

    def run_command(self, cmd, label, stdin_queue=None):
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, shell=True, text=True, bufsize=1)
            self.processes[label] = process

            def reader():
                for line in iter(process.stdout.readline, ''):
                    self.log(label, line.strip())
                process.wait()

            def writer():
                while True:
                    user_input = stdin_queue.get()
                    if user_input is None:
                        break
                    try:
                        process.stdin.write(user_input + '\n')
                        process.stdin.flush()
                    except:
                        break

            threading.Thread(target=reader, daemon=True).start()
            if stdin_queue:
                threading.Thread(target=writer, daemon=True).start()

        except Exception as e:
            self.log(label, f"[ERROR] {e}")

    def launch_all(self):
        threading.Thread(target=self._launch_sequence).start()

    def _launch_sequence(self):
        self.log("Producer", "Uruchamianie kontenerów Docker...")
        self.run_command("docker-compose -f docker/docker-compose.yml up -d", "Producer")

        self.log("Producer", "Sprawdzanie LM Studio API...")
        for _ in range(15):
            try:
                r = requests.get("http://localhost:1234/v1/models")
                if r.status_code == 200:
                    self.log("Producer", "LM Studio API gotowe.")
                    break
            except:
                pass
            time.sleep(2)
        else:
            self.log("Producer", "Nie znaleziono LM Studio API.")
            return

        self.log("Producer", "Uruchamianie iot_simulator/producer.py")
        threading.Thread(target=self.run_command, args=("python iot_simulator/producer.py", "Producer")).start()

        self.log("Consumer", "Uruchamianie ingestion/consumer.py")
        threading.Thread(target=self.run_command, args=("python ingestion/consumer.py", "Consumer")).start()

        self.log("RAG", "Uruchamianie rag/query_engine_extended.py")
        threading.Thread(target=self.run_command, args=("python rag/query_engine_extended.py", "RAG", self.rag_input_queue)).start()

    def send_rag_input(self, event=None):
        question = self.rag_entry.get().strip()
        if question:
            self.rag_input_queue.put(question)
            self.log("RAG", f"> {question}")
            self.rag_entry.delete(0, tk.END)

    def set_and_send(self, question):
        self.rag_entry.delete(0, tk.END)
        self.rag_entry.insert(0, question)
        self.send_rag_input()

if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
