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
    """
    (Default Judge) A deterministic judge that verifies the agent's final answer
    by re-computing the result from its tool calls.
    """
    tool_name = last_call.get("tool_name")
    argument = last_call.get("argument")

    # --- Verification logic for each tool ---
    if tool_name == "calculator":
        try:
            expected_val = _safe_eval(argument)
            actual_val = float(final_answer)
            if expected_val is None:
                 return False, f"FAIL: Could not parse calculator argument '{argument}'."
            
            if math.isclose(expected_val, actual_val):
                return True, f"PASS: Final answer {actual_val} matches re-calculated value."
            else:
                return False, f"FAIL: Expected ≈{expected_val}, but got {actual_val}."
        except (ValueError, TypeError):
            return False, f"FAIL: Could not compare final answer '{final_answer}' with expected number."
    
    # For complex tools like unit_converter and date_calculator, we rely on the LLM judge
    # since rule-based verification would require extensive parsing and domain knowledge.
    # This ensures flexibility while maintaining verification capabilities.
    # Default for unknown tools
    return False, f"UNVERIFIED: Rule judge cannot verify tool '{tool_name}'."