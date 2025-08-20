# judge_improved.py - More robust judging system

import json
import re
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

class TaskType(Enum):
    """Enumeration of recognized task types."""
    PERCENTAGE = "percentage"
    CONVERSION = "conversion"
    DATE_CALC = "date_calculation"
    ARITHMETIC = "arithmetic"
    CSV_QUERY = "csv_query"
    UNKNOWN = "unknown"

@dataclass
class ValidationRule:
    """Represents a validation rule for a specific task type."""
    task_type: TaskType
    patterns: List[str]  # Regex patterns to identify task type
    validator: callable  # Function to validate the result
    expected_format: str  # Description of expected format

class RobustJudge:
    """A more robust rule-based judge with better pattern matching and validation."""
    
    def __init__(self):
        self.rules = self._initialize_rules()
    
    def _initialize_rules(self) -> Dict[TaskType, ValidationRule]:
        """Initialize validation rules for each task type."""
        return {
            TaskType.PERCENTAGE: ValidationRule(
                task_type=TaskType.PERCENTAGE,
                patterns=[
                    r'add\s+\d+(?:\.\d+)?%\s+to',
                    r'increase.*by\s+\d+(?:\.\d+)?%',
                    r'calculate.*\d+(?:\.\d+)?%\s+of'
                ],
                validator=self._validate_percentage,
                expected_format="numeric value"
            ),
            TaskType.CONVERSION: ValidationRule(
                task_type=TaskType.CONVERSION,
                patterns=[
                    r'convert.*\d+.*(?:to|into)',
                    r'\d+\s*(?:f|c|fahrenheit|celsius|km|mi|miles|kg|lb|pounds)',
                    r'(?:temperature|distance|weight).*conversion'
                ],
                validator=self._validate_conversion,
                expected_format="number with unit"
            ),
            TaskType.DATE_CALC: ValidationRule(
                task_type=TaskType.DATE_CALC,
                patterns=[
                    r'days[\s_]between',
                    r'\d{4}-\d{2}-\d{2}.*(?:to|and|between)',
                    r'date.*(?:add|subtract|difference)'
                ],
                validator=self._validate_date_calc,
                expected_format="integer (days) or date (YYYY-MM-DD)"
            ),
            TaskType.CSV_QUERY: ValidationRule(
                task_type=TaskType.CSV_QUERY,
                patterns=[
                    r'(?:sum|average|avg).*(?:csv|file)',
                    r'query.*csv',
                    r'csv.*(?:sum|avg|average)'
                ],
                validator=self._validate_csv_query,
                expected_format="numeric value"
            ),
            TaskType.ARITHMETIC: ValidationRule(
                task_type=TaskType.ARITHMETIC,
                patterns=[
                    r'calculate\s+[\d\+\-\*/\(\)\s]+',
                    r'what\s+is\s+[\d\+\-\*/\(\)\s]+',
                    r'evaluate.*expression'
                ],
                validator=self._validate_arithmetic,
                expected_format="numeric value"
            )
        }
    
    def identify_task_type(self, task: str) -> TaskType:
        """Identify the type of task based on patterns."""
        task_lower = task.lower().strip()
        
        for task_type, rule in self.rules.items():
            for pattern in rule.patterns:
                if re.search(pattern, task_lower):
                    return task_type
        
        return TaskType.UNKNOWN
    
    def _validate_percentage(self, task: str, result: str) -> Tuple[bool, str]:
        """Validate percentage calculation results."""
        # Extract expected calculation from task
        match = re.search(r'(\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*\*?\s*\(?\s*1?\s*\+?\s*(\d+(?:\.\d+)?)\s*%', task.lower())
        if not match:
            # Try simpler pattern
            match = re.search(r'add\s+(\d+(?:\.\d+)?)%\s+to\s+(\d+(?:\.\d+)?(?:e[+-]?\d+)?)', task.lower())
            if match:
                percentage = float(match.group(1))
                base = float(match.group(2))
                expected = base * (1 + percentage / 100)
            else:
                # Can't extract values, just check if numeric
                try:
                    float(result.replace(',', ''))
                    return (True, "Result is numeric (cannot verify exact value)")
                except:
                    return (False, "Expected numeric result for percentage calculation")
        else:
            base = float(match.group(1))
            percentage = float(match.group(2))
            expected = base * (1 + percentage / 100)
        
        try:
            actual = float(result.replace(',', ''))
            tolerance = abs(expected * 0.0001)  # 0.01% tolerance
            if abs(actual - expected) <= tolerance:
                return (True, f"Correct: {actual} ≈ {expected}")
            else:
                return (False, f"Incorrect: got {actual}, expected {expected}")
        except:
            return (False, f"Invalid number format: {result}")
    
    def _validate_conversion(self, task: str, result: str) -> Tuple[bool, str]:
        """Validate unit conversion results."""
        # Check if result contains a number and unit
        patterns = [
            r'[-+]?\d+(?:\.\d+)?\s*°?[CFcf]',  # Temperature
            r'[-+]?\d+(?:\.\d+)?\s*(?:km|mi|miles|kilometers)',  # Distance
            r'[-+]?\d+(?:\.\d+)?\s*(?:kg|lb|pounds|kilograms)'  # Weight
        ]
        
        for pattern in patterns:
            if re.search(pattern, result, re.IGNORECASE):
                return (True, "Valid conversion format with unit")
        
        # Check if at least numeric
        try:
            float(re.sub(r'[^\d\.\-+]', '', result))
            return (True, "Numeric result (missing unit)")
        except:
            return (False, "Expected number with unit for conversion")
    
    def _validate_date_calc(self, task: str, result: str) -> Tuple[bool, str]:
        """Validate date calculation results."""
        # Check for date format (YYYY-MM-DD)
        if re.match(r'\d{4}-\d{2}-\d{2}', result.strip()):
            return (True, "Valid date format")
        
        # Check for integer (days)
        try:
            days = int(result.strip())
            if 'days_between' in task.lower() or 'between' in task.lower():
                return (True, f"Valid day count: {days}")
            return (True, "Valid numeric result")
        except:
            return (False, "Expected integer (days) or date (YYYY-MM-DD)")
    
    def _validate_csv_query(self, task: str, result: str) -> Tuple[bool, str]:
        """Validate CSV query results."""
        try:
            value = float(result.replace(',', ''))
            if 'avg' in task.lower() or 'average' in task.lower():
                return (True, f"Valid average: {value}")
            elif 'sum' in task.lower():
                return (True, f"Valid sum: {value}")
            return (True, "Valid numeric result")
        except:
            return (False, "Expected numeric result for CSV query")
    
    def _validate_arithmetic(self, task: str, result: str) -> Tuple[bool, str]:
        """Validate arithmetic calculation results."""
        try:
            float(result.replace(',', ''))
            return (True, "Valid numeric calculation")
        except:
            return (False, "Expected numeric result for arithmetic")
    
    def judge(self, task: str, result: str) -> Tuple[bool, str]:
        """Main judging method."""
        if not result or result.startswith("error:"):
            return (False, f"Agent error: {result}")
        
        task_type = self.identify_task_type(task)
        
        if task_type == TaskType.UNKNOWN:
            # Fallback: check if non-empty
            is_valid = len(result.strip()) > 0
            return (is_valid, "Unknown task type - checking non-empty" if is_valid else "Empty result")
        
        rule = self.rules[task_type]
        return rule.validator(task, result)


class HybridJudge:
    """
    Combines rule-based and LLM-based judging for robustness.
    Uses rules for known patterns, falls back to LLM for complex cases.
    """
    
    def __init__(self, model=None):
        self.rule_judge = RobustJudge()
        self.model = model
    
    def judge(self, task: str, result: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Judge using rules first, then LLM if needed.
        
        Args:
            task: The original task
            result: Full agent output dictionary
        """
        final_answer = result.get("final", "")
        
        # First try rule-based judgment
        task_type = self.rule_judge.identify_task_type(task)
        
        if task_type != TaskType.UNKNOWN:
            # Use rule-based for known types
            return self.rule_judge.judge(task, final_answer)
        
        # Fall back to LLM for unknown/complex tasks
        if self.model:
            return self._llm_judge(task, result)
        
        # No LLM available, use basic validation
        is_valid = len(final_answer.strip()) > 0 and not final_answer.startswith("error:")
        return (is_valid, "Basic validation only" if is_valid else "Invalid or error result")
    
    def _llm_judge(self, task: str, result: Dict[str, Any]) -> Tuple[bool, str]:
        """LLM-based judgment with improved prompting."""
        final_answer = result.get("final", "NO FINAL ANSWER")
        trace = result.get("trace", [])
        
        # More structured prompt
        judge_prompt = f"""Evaluate if this agent completed the task correctly.

TASK: {task}

AGENT'S PROCESS:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(trace))}

FINAL ANSWER: {final_answer}

Respond with JSON: {{"success": true/false, "reason": "one sentence"}}"""
        
        try:
            response = self.model.generate(judge_prompt, format='json')
            output = json.loads(response)
            return (output.get('success', False), output.get('reason', 'Invalid response'))
        except Exception as e:
            # Fallback to rule-based
            return self.rule_judge.judge(task, final_answer)


# Convenience functions for backward compatibility
def robust_judge(task: str, final: str) -> Tuple[bool, str]:
    """Drop-in replacement for rule_judge with better validation."""
    judge = RobustJudge()
    return judge.judge(task, final)

def hybrid_judge(model, task: str, result: Dict[str, Any]) -> Tuple[bool, str]:
    """Drop-in replacement for llm_judge with fallback to rules."""
    judge = HybridJudge(model)
    return judge.judge(task, result)