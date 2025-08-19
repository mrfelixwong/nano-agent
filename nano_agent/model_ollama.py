import requests

GRAMMAR = "Output exactly ONE line: 'CALL: <tool> | <arg>' OR 'FINAL: <answer>'. Do NOT wrap <arg> in quotes."

class OllamaModel:
    def __init__(self, model: str = "llama3.1", url: str = "http://localhost:11434/api/generate"):
        self.model, self.url = model, url

    def generate(self, prompt: str) -> str:
        full = f"{GRAMMAR}\n\n{prompt}"
        r = requests.post(self.url, json={"model": self.model, "prompt": full, "stream": False}, timeout=120)
        text = r.json().get("response","").strip()
        if not (text.startswith("CALL:") or text.startswith("FINAL:")):
            r = requests.post(self.url, json={"model": self.model, "prompt": full + "\nRepeat in required format.", "stream": False}, timeout=120)
            text = r.json().get("response","").strip()
        return text

