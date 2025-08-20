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
            "stream": False
        }
        
        response = requests.post(self.url, json=request_data, timeout=REQUEST_TIMEOUT)
        result = response.json()
        
        # Track duration for cost metrics
        self.last_duration = result.get("eval_duration", 0) / 1e9  # Convert ns to seconds
        
        return result.get("response", "").strip()