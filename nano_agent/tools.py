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
        # Simple approach: Find date patterns directly
        if 'days_between' in text:
            dates_found = []
            
            # Pattern 1: ISO format YYYY-MM-DD
            iso_dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
            for date_str in iso_dates:
                dates_found.append(datetime.fromisoformat(date_str))
            
            # Pattern 2: "Month DD YYYY" like "Jan 1 2024" or "January 1 2024"
            month_dates = re.findall(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*\s+(\d{1,2})\s+(\d{4})', text)
            month_map = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
            for month_str, day, year in month_dates:
                month = month_map[month_str[:3]]
                dates_found.append(datetime(int(year), month, int(day)))
            
            if len(dates_found) >= 2:
                return str(abs((dates_found[1] - dates_found[0]).days))
        
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
                "Use for ALL math: multiply, divide, add, subtract, percentages.", 
                _calc)
    reg.register("unit_convert", 
                "Convert temperature/distance/weight units ONLY.", 
                _unit_convert)
    reg.register("date_calc", 
                "Calculate days between dates or add/subtract days from dates ONLY.", 
                _date_calc)