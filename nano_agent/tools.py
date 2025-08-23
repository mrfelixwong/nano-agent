"""Simple tools for the educational agent."""

from datetime import datetime, timedelta
import re


def calculator(expr: str) -> str:
    """Basic arithmetic calculator."""
    try:
        # Remove spaces and validate characters
        clean = re.sub(r'\s+', '', expr.strip())
        # Handle percentage notation: 15% -> 0.15
        clean = re.sub(r'(\d+(?:\.\d+)?)%', r'(\1/100)', clean)
        
        if not all(c in '0123456789+-*/().eE*' for c in clean):  # Allow ** for power
            return "error: invalid characters"
        
        return str(eval(clean, {"__builtins__": {}}, {}))
    except:
        return "error: invalid expression"


def unit_convert(arg: str) -> str:
    """Convert temperature/distance/weight units."""
    try:
        parts = arg.strip().lower().replace('°','').split()
        value, from_unit, _, to_unit = parts
        value = float(value)
        
        # Temperature
        if from_unit == 'f' and to_unit == 'c':
            return f"{(value-32)*5/9:.1f} °C"
        if from_unit == 'c' and to_unit == 'f':
            return f"{value*9/5+32:.1f} °F"
        
        # Distance  
        if from_unit == 'km' and to_unit == 'mi':
            return f"{value*0.621371:.3f} mi"
        if from_unit == 'mi' and to_unit == 'km':
            return f"{value/0.621371:.3f} km"
            
        # Weight
        if from_unit == 'kg' and to_unit == 'lb':
            return f"{value*2.20462:.3f} lb"
        if from_unit == 'lb' and to_unit == 'kg':
            return f"{value/2.20462:.3f} kg"
            
        return "error: unsupported conversion"
    except:
        return "error: format: '<value> <from_unit> to <to_unit>'"


def date_calc(arg: str) -> str:
    """Calculate days between dates or add/subtract days."""
    text = arg.strip().lower()
    
    # Pattern: days_between YYYY-MM-DD YYYY-MM-DD
    if text.startswith('days_between'):
        try:
            _, date1_str, date2_str = text.split()
            date1 = datetime.fromisoformat(date1_str)
            date2 = datetime.fromisoformat(date2_str)
            return str((date2 - date1).days)
        except:
            pass
    
    # Pattern: YYYY-MM-DD +/- Nd
    match = re.match(r'(\d{4}-\d{2}-\d{2})\s*([+-])\s*(\d+)d', text)
    if match:
        try:
            base_date = datetime.fromisoformat(match.group(1))
            days = int(match.group(3)) * (1 if match.group(2) == '+' else -1)
            result = base_date + timedelta(days=days)
            return result.date().isoformat()
        except:
            pass
    
    return "error: use 'days_between YYYY-MM-DD YYYY-MM-DD' or 'YYYY-MM-DD +/- Nd'"


# Simple dictionary of tools
TOOLS = {
    "calculator": ("Use for ALL math: multiply, divide, add, subtract, percentages.", calculator),
    "unit_convert": ("Convert temperature/distance/weight units ONLY.", unit_convert),
    "date_calc": ("Calculate days between dates or add/subtract days from dates ONLY.", date_calc)
}


def get_tools_spec():
    """Get tool specifications for the agent prompt."""
    return [{"name": name, "description": desc} for name, (desc, _) in TOOLS.items()]


def execute_tool(name: str, arg: str) -> str:
    """Execute a tool by name."""
    if name not in TOOLS:
        return f"error: unknown tool '{name}'"
    _, func = TOOLS[name]
    return func(arg)