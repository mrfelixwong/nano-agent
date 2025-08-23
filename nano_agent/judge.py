"""Simple judge for validating agent outputs."""

import re
from typing import Tuple


def rule_judge(task: str, answer: str) -> Tuple[bool, str]:
    """Check if agent's answer looks reasonable for the task."""
    answer = str(answer).strip()
    task_lower = task.lower()
    
    # Check for errors
    if answer.startswith("error:"):
        return False, answer
    
    # Extract any number from answer
    number_match = re.search(r'[+-]?\d+(?:\.\d+)?', answer)
    
    # Math tasks need a number
    if any(word in task_lower for word in ['calculate', 'add', 'subtract', 'multiply', 'divide', '%', 'percent']):
        if number_match:
            return True, "Calculation completed"
        return False, "No numeric result"
    
    # Conversion tasks need a number  
    if 'convert' in task_lower or any(unit in task_lower for unit in ['celsius', 'fahrenheit', 'miles', 'kilometers']):
        if number_match:
            return True, "Conversion completed"
        return False, "No numeric result"
    
    # Date tasks need a number or date
    if any(word in task_lower for word in ['days', 'date', 'between']):
        if number_match or re.search(r'\d{4}-\d{2}-\d{2}', answer):
            return True, "Date calculation completed"
        return False, "No date or number result"
    
    # Default: pass if no error
    return True, "Task completed"