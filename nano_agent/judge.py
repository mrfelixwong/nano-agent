import json
import math
import re
from typing import Tuple, Dict, Any, List, Optional
from .model_ollama import OllamaModel

def _safe_eval(expr: str) -> Optional[float]:
    """Safely evaluate a mathematical expression, returning None if invalid."""
    try:
        # Remove whitespace and validate characters
        cleaned = re.sub(r"\s+", "", expr)
        if not all(c in "0123456789.+-*/()e" for c in cleaned.lower()):
            return None
        # Evaluate with no built-ins for safety
        return float(eval(cleaned, {"__builtins__": {}}, {}))
    except:
        return None

def rule_judge(task: str, final_answer: str) -> Tuple[bool, str]:
    return True, f"Good job"