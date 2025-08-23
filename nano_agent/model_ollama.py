"""Ollama API interface for local LLM generation."""

import requests
from typing import Dict, Any

DEFAULT_MODEL = "llama3.1"
DEFAULT_URL = "http://localhost:11434/api/generate"
REQUEST_TIMEOUT = 120


class OllamaModel:
    """Local LLM interface via Ollama."""
    
    def __init__(self, model: str = DEFAULT_MODEL, url: str = DEFAULT_URL):
        self.model = model
        self.url = url
        self.last_duration = 0
    
    def generate(self, prompt: str, format: str = 'json') -> str:
        """Generate JSON response from the model."""
        request_data = {
            "model": self.model,
            "prompt": prompt,
            "format": format,
            "stream": False,
            "temperature": 0.0,  # Zero temperature for completely deterministic responses
            "top_p": 1.0        # Take the most likely token at each step
        }
        
        try:
            response = requests.post(self.url, json=request_data, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            result = response.json()
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "\n[ERROR] Cannot connect to Ollama at http://localhost:11434\n"
                "Please ensure Ollama is running:\n"
                "  1. Install Ollama: brew install ollama (or see ollama.ai)\n"
                "  2. Start Ollama: ollama run llama3.1\n"
                "  3. Try again!"
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Ollama request timed out after {REQUEST_TIMEOUT}s")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")
        
        # Track duration for cost metrics
        self.last_duration = result.get("eval_duration", 0) / 1e9  # Convert ns to seconds
        
        return result.get("response", "").strip()