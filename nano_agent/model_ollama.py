"""Simple Ollama interface for local LLM."""

import requests
from typing import Dict, Any, List

DEFAULT_MODEL = "llama4"
DEFAULT_URL = "http://localhost:11434"
REQUEST_TIMEOUT = 120


class OllamaModel:
    """Local LLM interface via Ollama."""

    def __init__(self, model: str = "auto", url: str = DEFAULT_URL):
        self.url = url
        if model == "auto":
            self.model = self._get_best_available_model()
        else:
            self.model = model
        self.last_duration = 0

    def _get_available_models(self) -> List[str]:
        """Get a list of available models from the Ollama API."""
        try:
            response = requests.get(f"{self.url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get("models", [])
            return [m["name"] for m in models]
        except (requests.exceptions.RequestException, ValueError):
            return []

    def _get_best_available_model(self) -> str:
        """Detect the best available Llama model."""
        available_models = self._get_available_models()
        preferred_models = ["llama4:latest", "llama3.1:latest"]

        for model in preferred_models:
            if model in available_models:
                print(f"Auto-detected model: {model}")
                return model

        print(f"No preferred models found. Using default: {DEFAULT_MODEL}")
        return DEFAULT_MODEL

    def generate(self, prompt: str, format: str = 'json') -> str:
        """Generate JSON response from the model."""
        request_data = {
            "model": self.model,
            "prompt": prompt,
            "format": format,
            "stream": False
        }

        try:
            response = requests.post(f"{self.url}/api/generate", json=request_data, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "\n[ERROR] Cannot connect to Ollama at http://localhost:11434\n"
                "Please ensure Ollama is running:\n"
                "  1. Install Ollama: brew install ollama (or see ollama.ai)\n"
                "  2. Start Ollama: ollama run llama4 (or llama3.1)\n"
                "  3. Try again!"
            )

        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama request timed out after {REQUEST_TIMEOUT}s")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")