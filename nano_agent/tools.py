from datetime import datetime, timedelta
import re, csv, pathlib
from typing import Tuple, Dict, Callable, Optional

class ToolRegistry:
    """Registry for command-line tools with descriptions and functions."""
    
    def __init__(self):
        self._tools: Dict[str, Tuple[str, Callable]] = {}
    
    def register(self, name: str, desc: str, fn: Callable) -> None:
        self._tools[name] = (desc, fn)
    
    def get(self, name: str) -> Callable:
        return self._tools[name][1]
    
    def spec(self) -> list[Tuple[str, str]]:
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
    """Convert between common units (temperature, distance, weight)."""
    try:
        parts = arg.strip().lower().replace('°','').split()
        value, from_unit, _, to_unit = parts
        value = float(value)
        
        # Temperature conversions
        if (from_unit, to_unit) in [('f','c'), ('fahrenheit','celsius')]:
            return f"{(value-32)*5/9:.1f} °C"
        if (from_unit, to_unit) in [('c','f'), ('celsius','fahrenheit')]:
            return f"{value*9/5+32:.1f} °F"
            
        # Distance conversions
        if (from_unit, to_unit) in [('km','mi'), ('km','miles')]:
            return f"{value*0.621371:.3f} mi"
        if (from_unit, to_unit) in [('mi','km'), ('miles','km')]:
            return f"{value/0.621371:.3f} km"
            
        # Weight conversions
        if (from_unit, to_unit) == ('kg','lb'):
            return f"{value*2.20462:.3f} lb"
        if (from_unit, to_unit) == ('lb','kg'):
            return f"{value/2.20462:.3f} kg"
            
        return "error: unsupported conversion"
    except:
        return "error: '<value> <unit_from> to <unit_to>'"

def _date_calc(arg: str) -> str:
    """Calculate days between dates or add/subtract days from a date."""
    text = arg.strip().lower()
    
    # Pattern 1: days_between DATE1 DATE2
    if match := re.match(r"days_between\s+(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})", text):
        date1 = datetime.fromisoformat(match.group(1))
        date2 = datetime.fromisoformat(match.group(2))
        return str((date2 - date1).days)
    
    # Pattern 2: DATE +/- Nd (date arithmetic)
    if match := re.match(r"(\d{4}-\d{2}-\d{2})\s*([+-])\s*(\d+)d", text):
        base_date = datetime.fromisoformat(match.group(1))
        days = int(match.group(3)) * (1 if match.group(2) == '+' else -1)
        result_date = base_date + timedelta(days=days)
        return result_date.date().isoformat()
    
    # Pattern 3: DATE1 to/and/between DATE2 (natural language)
    if match := re.match(r"(\d{4}-\d{2}-\d{2})\s+(?:to|and|between)\s+(\d{4}-\d{2}-\d{2})", text):
        date1 = datetime.fromisoformat(match.group(1))
        date2 = datetime.fromisoformat(match.group(2))
        return str((date2 - date1).days)
    
    # Pattern 4: DATE1 DATE2 (simple pair)
    if match := re.match(r"(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})", text):
        date1 = datetime.fromisoformat(match.group(1))
        date2 = datetime.fromisoformat(match.group(2))
        return str((date2 - date1).days)
    
    return "error: Expected format: 'days_between DATE1 DATE2', 'DATE1 +/- Nd', 'DATE1 to DATE2', or 'DATE1 DATE2'"

def _csv_query(arg: str) -> str:
    """Query CSV files for sum or average of a column with optional filtering."""
    try:
        # Parse arguments
        operation = arg.split()[0] if arg else "sum"
        params = dict(re.findall(r"(\w+)=([^\s]+)", arg))
        
        file_path = params.get("file")
        column = params.get("col")
        
        if not (file_path and column):
            return "error: need file= and col="
        
        # Parse optional filter
        where_clause = params.get("where")
        filter_key, filter_val = (where_clause.split(":", 1) 
                                  if where_clause and ":" in where_clause 
                                  else (None, None))
        
        # Process CSV data
        total, count = 0.0, 0
        with open(pathlib.Path(file_path), newline='') as f:
            for row in csv.DictReader(f):
                # Apply filter if specified
                if filter_key and str(row.get(filter_key, "")) != filter_val:
                    continue
                
                # Try to parse numeric value
                try:
                    value = float(str(row.get(column, "")).replace(',', ''))
                    total += value
                    count += 1
                except ValueError:
                    continue
        
        if count == 0:
            return "0"
        
        if operation == "sum":
            return str(total)
        elif operation == "avg":
            return str(total / count)
        else:
            return "error: op (sum|avg)"
            
    except Exception:
        return "error: invalid csv query"

def register_default_tools(reg: ToolRegistry) -> None:
    """Register all default tools to the registry."""
    reg.register("calculator", 
                "Evaluate arithmetic like '2*(3+4)' or '3.03e12*(1+8.5/100)'.", 
                _calc)
    reg.register("unit_convert", 
                "Convert units (°F↔°C, km↔mi, kg↔lb). e.g. '72 F to C'.", 
                _unit_convert)
    reg.register("date_calc", 
                "Date math: 'days_between DATE1 DATE2', 'DATE1 +/- Nd', 'DATE1 to DATE2', or 'DATE1 DATE2'.", 
                _date_calc)
    reg.register("csv_query", 
                "CSV: 'sum file=... col=... [where=K:V]' or 'avg ...'", 
                _csv_query)