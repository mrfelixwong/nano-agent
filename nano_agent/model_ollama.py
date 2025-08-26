"""Ollama API interface for local LLM generation."""

import requests
import os
from typing import Dict, Any

# Models in order of preference (best to fallback)
PREFERRED_MODELS = [
    "gpt-oss:20b",
    "qwen3:30b", 
    "gemma3:27b-it-qat",
    "llama3.1:latest"
]

DEFAULT_URL = "http://localhost:11434/api/generate"
REQUEST_TIMEOUT = 120


def get_available_models(url: str = DEFAULT_URL) -> list:
    """Get list of available models from Ollama."""
    try:
        response = requests.get(url.replace('/api/generate', '/api/tags'), timeout=10)
        response.raise_for_status()
        models = response.json().get('models', [])
        return [model['name'] for model in models]
    except:
        return []


def detect_best_model() -> str:
    """Auto-detect the best available model from our preferred list."""
    # Check environment variable first
    if 'OLLAMA_MODEL' in os.environ:
        return os.environ['OLLAMA_MODEL']
    
    available = get_available_models()
    
    for preferred in PREFERRED_MODELS:
        if preferred in available:
            return preferred
    
    # Fallback to first available or llama3.1
    return available[0] if available else "llama3.1"


class OllamaModel:
    """Local LLM interface via Ollama with auto-detection."""
    
    def __init__(self, model: str = "auto", url: str = DEFAULT_URL):
        if model == "auto":
            model = detect_best_model()
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