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

def rule_judge(task: str, final_answer: str, trace: List[str]) -> Tuple[bool, str]:
    """
    (Default Judge) A deterministic judge that verifies the agent's final answer
    by re-computing the result from its tool calls.
    """
    # Find the last tool call in the trace to evaluate.
    last_call = None
    for step_str in reversed(trace):
        try:
            step_data = json.loads(step_str)
            if step_data.get("action") == "CALL":
                last_call = step_data
                break
        except (json.JSONDecodeError, TypeError):
            continue

    if not last_call:
        return False, "FAIL: Could not find a valid tool call in the trace."

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

def llm_judge(model: OllamaModel, task: str, result: Dict[str, Any]) -> Tuple[bool, str]:
    """Judge if agent successfully completed the task by examining its trace."""
    
    # Parse trace into readable format
    trace_lines = []
    for step in result.get("trace", []):
        try:
            data = json.loads(step)
            action = data.get("action")
            if action == "CALL":
                trace_lines.append(f'CALL: {data.get("tool_name")} | {data.get("argument")}')
            elif action == "FINAL":
                trace_lines.append(f'FINAL: {data.get("answer")}')
        except (json.JSONDecodeError, TypeError):
            trace_lines.append(str(step))
    
    judge_prompt = f"""
You are an AI agent evaluator. Judge the agent's success based on its trace and final answer.
Task: "{task}"
Trace:
---
{chr(10).join(trace_lines)}
---
Final Answer: "{result.get('final', 'None')}"

Respond ONLY with JSON: {{"success": boolean, "reason": "one-sentence explanation"}}
"""
    
    try:
        response_str = model.generate(judge_prompt, format='json')
        output = json.loads(response_str)
        return output.get('success', False), output.get('reason', 'Invalid response')
    except Exception as e:
        return False, f"Judge error: {e}"