"""Simple Ollama interface for local LLM."""

import requests


class OllamaModel:
    """Minimal Ollama wrapper."""
    
    def __init__(self, model: str = "llama3.1"):
        self.model = model
    
    def generate(self, prompt: str, format: str = 'json') -> str:
        """Generate response from local Ollama."""
        try:
            request_data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.0
            }
            # Only add format if it's json
            if format == 'json':
                request_data["format"] = "json"
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=request_data,
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            raise ConnectionError("Ollama not running. Try: ollama run llama3.1")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")