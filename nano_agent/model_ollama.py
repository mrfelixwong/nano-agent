import requests

GRAMMAR = (
    "You must output exactly ONE line:\n"
    "- 'CALL: <tool> | <arg>'  or\n"
    "- 'FINAL: <answer>'\n"
    "Rules:\n"
    "1) Do NOT wrap <arg> in quotes or code fences.\n"
    "2) If an Observation contains the answer you need, respond with FINAL (not CALL).\n"
    "3) Never call the same tool more than once for the same expression.\n"
    "Nothing else."
)

class OllamaModel:
    def __init__(self, model: str = "llama3.1", url: str = "http://localhost:11434/api/generate"):
        self.model = model; self.url = url

    def generate(self, prompt: str) -> str:
        full = f"{GRAMMAR}\n\n{prompt}"
        r = requests.post(self.url, json={"model": self.model, "prompt": full, "stream": False}, timeout=120)
        r.raise_for_status()
        text = r.json().get("response","").strip()
        if not (text.startswith("CALL:") or text.startswith("FINAL:")):
            r = requests.post(self.url, json={"model": self.model,
                                              "prompt": full + "\nRepeat in the required one-line format.",
                                              "stream": False}, timeout=120)
            r.raise_for_status()
            text = r.json().get("response","").strip()
        return text

