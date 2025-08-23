import re
from typing import Tuple

def rule_judge(task: str, answer: str) -> Tuple[bool, str]:
    """Check if agent's answer looks reasonable for the task."""
    answer = str(answer).strip()
    task_lower = task.lower()
    
    if answer.startswith("error:"): return False, answer
    
    number_match = re.search(r'[+-]?\d+(?:\.\d+)?', answer)
    
    if any(word in task_lower for word in ['calculate', 'add', 'subtract', 'multiply', 'divide', '%', 'percent']):
        return (True, "Calculation completed") if number_match else (False, "No numeric result")
    
    if 'convert' in task_lower or any(unit in task_lower for unit in ['celsius', 'fahrenheit', 'miles', 'kilometers']):
        return (True, "Conversion completed") if number_match else (False, "No numeric result")
    
    if any(word in task_lower for word in ['days', 'date', 'between']):
        return (True, "Date completed") if (number_match or re.search(r'\d{4}-\d{2}-\d{2}', answer)) else (False, "No result")
    return True, "Task completed"