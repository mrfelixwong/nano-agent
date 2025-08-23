from datetime import datetime, timedelta
import re
from typing import Tuple, Dict, Callable


class ToolRegistry:
    """Registry for agent tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tuple[str, Callable]] = {}
    
    def register(self, name: str, desc: str, fn: Callable) -> None:
        """Register a tool with its description and function."""
        self._tools[name] = (desc, fn)
    
    def get(self, name: str) -> Callable:
        """Get the function for a registered tool."""
        return self._tools[name][1]
    
    def spec(self) -> list[Dict[str, str]]:
        """Get specifications of all registered tools."""
        return [{"name": name, "description": desc} for name, (desc, _) in self._tools.items()]


def _calc(arg: str) -> str:
    """Evaluate arithmetic expressions safely.
    
    Handles: +, -, *, /, (), and percentage notation (e.g., '10%' -> 0.1)
    """
    try:
        # REFACTOR: Pre-process the string to handle percentage notation.
        # This makes the tool more robust to the LLM's output.
        processed_arg = re.sub(r"(\d+(\.\d+)?)%", r"(\1/100)", arg)

        expr = re.sub(r"\s+", " ", processed_arg.strip().strip("'\"`"))
        allowed_chars = "0123456789+-*/(). eE"
        
        if any(ch not in allowed_chars for ch in expr):
            return "error: only basic arithmetic allowed"
        
        return str(eval(expr, {"__builtins__": {}}, {}))
    except:
        return "error: invalid expression"


def _unit_convert(arg: str) -> str:
    """Convert between common units."""
    try:
        parts = arg.strip().lower().replace('°','').split()
        value, from_unit, _, to_unit = parts
        value = float(value)
        
        conversions = {
            ('f','c'): lambda v: f"{(v-32)*5/9:.1f} °C",
            ('c','f'): lambda v: f"{v*9/5+32:.1f} °F",
            ('km','mi'): lambda v: f"{v*0.621371:.3f} mi",
            ('mi','km'): lambda v: f"{v/0.621371:.3f} km",
            ('kg','lb'): lambda v: f"{v*2.20462:.3f} lb",
            ('lb','kg'): lambda v: f"{v/2.20462:.3f} kg",
        }
        
        for key, convert_fn in conversions.items():
            if (from_unit, to_unit) == key:
                return convert_fn(value)
        
        return "error: unsupported conversion"
    except:
        return "error: format: '<value> <from_unit> to <to_unit>'"


def _date_calc(arg: str) -> str:
    """Calculate days between dates or add/subtract days from dates."""
    text = arg.strip().lower()
    
    # Pattern: days_between DATE1 DATE2
    if match := re.match(r"days_between\s+(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})", text):
        date1 = datetime.fromisoformat(match.group(1))
        date2 = datetime.fromisoformat(match.group(2))
        return str((date2 - date1).days)
    
    # Pattern: DATE +/- Nd
    if match := re.match(r"(\d{4}-\d{2}-\d{2})\s*([+-])\s*(\d+)d", text):
        base_date = datetime.fromisoformat(match.group(1))
        days = int(match.group(3)) * (1 if match.group(2) == '+' else -1)
        result_date = base_date + timedelta(days=days)
        return result_date.date().isoformat()
    
    # Fallback for natural language date difference
    if match := re.match(r"(\d{4}-\d{2}-\d{2})\s+(?:to|and|between)\s+(\d{4}-\d{2}-\d{2})", text):
        date1 = datetime.fromisoformat(match.group(1))
        date2 = datetime.fromisoformat(match.group(2))
        return str((date2 - date1).days)
    
    return "error: use 'days_between YYYY-MM-DD YYYY-MM-DD' or 'YYYY-MM-DD +/- Nd'"

def register_default_tools(reg: ToolRegistry) -> None:
    """Register the three core educational tools.
    
    Tools demonstrate different capabilities:
    - calculator: Math evaluation with security constraints
    - unit_convert: Pattern matching and conversion logic
    - date_calc: Date parsing and arithmetic
    """
    reg.register("calculator", 
                "Use for ALL math: multiply, divide, add, subtract, percentages.", 
                _calc)
    reg.register("unit_convert", 
                "Convert temperature/distance/weight units ONLY.", 
                _unit_convert)
    reg.register("date_calc", 
                "Calculate days between dates or add/subtract days from dates ONLY.", 
                _date_calc)