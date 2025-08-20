"""Simple interface to Ollama API for generating agent responses."""

import requests
from typing import Dict, Any

# Model configuration
DEFAULT_MODEL = "llama3.1"
DEFAULT_URL = "http://localhost:11434/api/generate"
REQUEST_TIMEOUT = 120

# Response format instruction
RESPONSE_FORMAT = """Output exactly ONE line: 'CALL: <tool> | <arg>' OR 'FINAL: <answer>'. Do NOT wrap <arg> in quotes."""


class OllamaModel:
    """A minimal Ollama model interface that enforces response format."""
    
    def __init__(self, model: str = DEFAULT_MODEL, url: str = DEFAULT_URL):
        self.model = model
        self.url = url
        
    def generate(self, prompt: str) -> str:
        """Generate a formatted response from the model.
        
        Returns a single line starting with either 'CALL:' or 'FINAL:'.
        Retries once if format is incorrect.
        """
        request_data = {
            "model": self.model,
            "prompt": f"{RESPONSE_FORMAT}\n\n{prompt}",
            "stream": False
        }
        
        # First attempt
        response = self._make_request(request_data)
        
        # Retry if format is wrong
        if not (response.startswith("CALL:") or response.startswith("FINAL:")):
            request_data["prompt"] += "\nRepeat in required format."
            response = self._make_request(request_data)
            
        return response
    
    def _make_request(self, data: Dict[str, Any]) -> str:
        """Make API request and extract response text."""
        r = requests.post(self.url, json=data, timeout=REQUEST_TIMEOUT)
        return r.json().get("response", "").strip()

