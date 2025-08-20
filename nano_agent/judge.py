from typing import Optional, Tuple

def _to_float(text: str) -> Optional[float]:
    """Convert string to float, handling comma separators.
    
    Args:
        text: String to convert, may contain commas as thousands separators
        
    Returns:
        Float value if conversion successful, None otherwise
    """
    try:
        return float(text.replace(',', ''))
    except (ValueError, AttributeError):
        return None

def rule_judge(task: str, final: str) -> Tuple[bool, str]:
    """Judge if a task result meets expected criteria.
    
    Args:
        task: Description of the task to perform
        final: The final result/answer to validate
        
    Returns:
        Tuple of (success: bool, reason: str)
    """
    task_lower = task.lower().strip()
    result = final.strip()
    
    # Rule 1: Percentage addition tasks require numeric result
    if 'add' in task_lower and '%' in task_lower and 'to' in task_lower:
        value = _to_float(result)
        if value is None:
            return (False, 'final not numeric')
        return (True, 'numeric final')
    
    # Rule 2: Calculation tasks require numeric result
    calculation_keywords = ['days_between', 'sum', 'avg', 'csv']
    if any(keyword in task_lower for keyword in calculation_keywords):
        is_numeric = _to_float(result) is not None
        reason = 'numeric' if is_numeric else 'non-numeric'
        return (is_numeric, reason)
    
    # Rule 3: Conversion tasks just need non-empty result
    if 'convert' in task_lower or ' to ' in task_lower:
        is_valid = len(result) > 0
        reason = 'non-empty' if is_valid else 'empty'
        return (is_valid, reason)
    
    # Default rule: Any non-empty result is valid
    is_valid = len(result) > 0
    reason = 'non-empty' if is_valid else 'empty'
    return (is_valid, reason)