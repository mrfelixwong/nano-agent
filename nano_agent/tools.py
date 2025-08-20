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
    
    def spec(self) -> list[Tuple[str, str]]:
        """Get specifications of all registered tools."""
        return [(name, desc) for name, (desc, _) in self._tools.items()]


def _calc(arg: str) -> str:
    """Evaluate arithmetic expressions safely."""
    try:
        expr = re.sub(r"\s+", " ", arg.strip().strip("'\"`"))
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
    """Calculate date differences or arithmetic."""
    text = arg.strip().lower().replace("'", "").replace('"', "")
    
    try:
        # Try "days_between DATE1 DATE2" or "DATE1 to DATE2" patterns
        if 'days_between' in text or ' to ' in text or re.match(r'\d{4}-\d{2}-\d{2}\s+\d{4}-\d{2}-\d{2}', text):
            # Extract two dates
            dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
            if len(dates) == 2:
                date1 = datetime.fromisoformat(dates[0])
                date2 = datetime.fromisoformat(dates[1])
                return str((date2 - date1).days)
        
        # Try "DATE +/- Nd" pattern
        match = re.match(r'(\d{4}-\d{2}-\d{2})\s*([+-])\s*(\d+)d', text)
        if match:
            base_date = datetime.fromisoformat(match.group(1))
            days = int(match.group(3)) * (1 if match.group(2) == '+' else -1)
            result = base_date + timedelta(days=days)
            return result.date().isoformat()
        
        return "error: use 'days_between DATE1 DATE2' or 'DATE +/- Nd'"
    except Exception as e:
        return f"error: {e}"


def register_default_tools(reg: ToolRegistry) -> None:
    """Register all default tools."""
    reg.register("calculator", 
                "Evaluate arithmetic like '2*(3+4)' or '3.03e12*(1+8.5/100)'.", 
                _calc)
    reg.register("unit_convert", 
                "Convert units (°F↔°C, km↔mi, kg↔lb). e.g. '72 F to C'.", 
                _unit_convert)
    reg.register("date_calc", 
                "Date math: 'days_between DATE1 DATE2' or 'DATE +/- Nd'.", 
                _date_calc)