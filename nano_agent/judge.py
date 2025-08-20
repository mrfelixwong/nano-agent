import json
from typing import Tuple, Dict, Any
from .model_ollama import OllamaModel


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