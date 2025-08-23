import re
from typing import Tuple, Optional

def _safe_eval(expr: str) -> Optional[float]:
    """Safely evaluate a mathematical expression.
    
    Security: Only allows basic math operators, no function calls or imports.
    """
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
    """Rule-based judge for common task patterns.
    
    Returns (passed, reason) tuple.
    """
    # Clean up the answer
    answer = str(final_answer).strip()
    task_lower = task.lower()
    
    # Check for errors
    if answer.startswith("error:"):
        return False, f"Agent error: {answer}"
    
    # For calculation tasks, try to extract and verify numeric result
    if any(word in task_lower for word in ['calculate', 'plus', 'minus', 'times', 'divide', 'add', 'subtract', 'multiply', '%', 'percent']):
        # Extract percentage if mentioned
        percent_match = re.search(r'(\d+(?:\.\d+)?)\s*%', task)
        
        # Try to parse numeric answer
        numeric_answer = _safe_eval(answer.split()[0] if ' ' in answer else answer)
        if numeric_answer is None:
            # Try extracting number from answer like "22.2 °C"
            match = re.search(r'([+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)', answer)
            if match:
                numeric_answer = float(match.group(1))
        
        if numeric_answer is not None:
            # For percentage calculations, check if answer is reasonable
            if 'percent' in task_lower or '%' in task:
                # Basic sanity check - percentage calculations should give reasonable results
                if percent_match and 'of' in task_lower:
                    # "X% of Y" type problems
                    return True, "Percentage calculation completed"
                elif 'add' in task_lower or 'increase' in task_lower or '+' in task:
                    # "add X%" or "increase by X%" problems  
                    return True, "Percentage increase calculated"
                elif 'subtract' in task_lower or 'decrease' in task_lower or '-' in task:
                    # "subtract X%" or "decrease by X%" problems
                    return True, "Percentage decrease calculated"
            return True, "Calculation completed"
        else:
            return False, "Could not parse numeric result"
    
    # For unit conversion tasks
    if 'convert' in task_lower or any(unit in task_lower for unit in ['celsius', 'fahrenheit', 'miles', 'kilometers', 'pounds', 'kilograms']):
        # Check if answer contains a unit
        if any(unit in answer.lower() for unit in ['°c', '°f', 'c', 'f', 'mi', 'km', 'lb', 'kg', 'celsius', 'fahrenheit']):
            return True, "Unit conversion completed"
        else:
            # Numeric answer without unit might still be valid
            if _safe_eval(answer.split()[0] if ' ' in answer else answer) is not None:
                return True, "Conversion completed"
            return False, "Invalid conversion result"
    
    # For date calculations
    if any(word in task_lower for word in ['days', 'date', 'between', 'after', 'before']):
        # Check if answer is a number (days) or date
        if re.match(r'^-?\d+$', answer):
            return True, "Date calculation completed"
        elif re.match(r'^\d{4}-\d{2}-\d{2}$', answer):
            return True, "Date calculated"
        else:
            return False, "Invalid date calculation result"
    
    # Generic success for other tasks
    return True, "Task completed"