# judge.py

import json
from typing import Optional, Tuple, Dict, Any

# You need to import the model to pass it to the judge
from .model_ollama import OllamaModel

def _to_float(text: str) -> Optional[float]:
    """Convert string to float, handling comma separators."""
    try:
        return float(text.replace(',', ''))
    except (ValueError, AttributeError):
        return None

def llm_judge(model: OllamaModel, task: str, result: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Judges an agent's work using an LLM to evaluate its reasoning trace.
    
    Args:
        model: An instance of the OllamaModel to use for judging.
        task: The original task description given to the agent.
        result: The full output dictionary from the agent's run().
        
    Returns:
        A tuple of (success: bool, reason: str).
    """
    final_answer = result.get("final", "NO FINAL ANSWER")
    trace = "\n".join(result.get("trace", []))

    # This prompt asks the LLM to act as a strict evaluator,
    # looking at the whole process.
    judge_prompt = f"""
    You are a strict but fair AI evaluator. Your goal is to determine if the AI agent successfully completed the task by analyzing its execution trace.

    THE ORIGINAL TASK:
    "{task}"

    THE AGENT'S EXECUTION TRACE:
    ---
    {trace}
    ---

    THE AGENT'S FINAL ANSWER:
    "{final_answer}"

    EVALUATION CRITERIA:
    1.  Correctness: Is the final answer factually and logically correct for the task?
    2.  Efficiency: Did the agent use the correct tool(s) without unnecessary steps?
    3.  Process: Does the trace show a logical path to the answer?

    INSTRUCTIONS:
    Respond ONLY with a JSON object containing two keys:
    - "success": a boolean (true if the agent met all criteria, otherwise false).
    - "reason": a brief, one-sentence explanation for your decision.
    """
    
    try:
        # We will add a 'format' parameter to the generate method for reliability
        response_str = model.generate(judge_prompt, format='json')
        
        output = json.loads(response_str)
        
        success = output.get('success', False)
        reason = output.get('reason', 'Judge LLM returned invalid JSON.')
        
        return (success, reason)
        
    except Exception as e:
        return (False, f"An error occurred during LLM judgment: {e}")

def rule_judge(task: str, final: str) -> Tuple[bool, str]:
    """
    (Original baseline judge)
    Judge if a task result meets expected criteria based on keywords.
    """
    task_lower = task.lower().strip()
    result = final.strip()
    
    if 'add' in task_lower and '%' in task_lower and 'to' in task_lower:
        return (True, 'numeric final') if _to_float(result) is not None else (False, 'final not numeric')
    
    calc_keywords = ['days_between', 'sum', 'avg', 'csv']
    if any(k in task_lower for k in calc_keywords):
        is_numeric = _to_float(result) is not None
        return (is_numeric, 'numeric' if is_numeric else 'non-numeric')
    
    if 'convert' in task_lower or ' to ' in task_lower:
        is_valid = len(result) > 0
        return (is_valid, 'non-empty' if is_valid else 'empty')
    
    is_valid = len(result) > 0
    return (is_valid, 'non-empty' if is_valid else 'empty')