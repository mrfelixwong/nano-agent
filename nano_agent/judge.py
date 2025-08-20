import json
from typing import Optional, Tuple, Dict, Any
from .model_ollama import OllamaModel

def _to_float(text: str) -> Optional[float]:
    """Convert string to float, handling comma separators."""
    try: return float(text.replace(',', ''))
    except (ValueError, AttributeError): return None

def llm_judge(model: OllamaModel, task: str, result: Dict[str, Any]) -> Tuple[bool, str]:
    """Judges an agent's work using an LLM to evaluate its reasoning trace."""
    # The judge LLM needs to see the agent's reasoning process (trace) to evaluate if:
    # 1. The agent used appropriate tools for the task (e.g., calculator for math)
    # 2. The tools were used correctly (right arguments, valid operations)
    # 3. The sequence of steps makes logical sense for solving the task
    # 4. The final answer follows from the steps taken
    # Without traces, the judge would only see input/output and miss reasoning errors
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
    You are an AI agent evaluator. Judge the agent's success based on its trace and final answer in relation to the original task.
    Task: "{task}"
    Trace:
    ---
    {"\n".join(trace_lines)}
    ---
    Final Answer: "{result.get('final', 'None')}"

    Respond ONLY with a JSON object: {{"success": boolean, "reason": "one-sentence explanation"}}
    """
    
    try:
        response_str = model.generate(judge_prompt, format='json')
        output = json.loads(response_str)
        return output.get('success', False), output.get('reason', 'Invalid JSON response.')
    except Exception as e:
        return False, f"LLM Judge error: {e}"

