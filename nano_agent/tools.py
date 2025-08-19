from typing import Callable, Dict
from datetime import datetime, timedelta
import re, csv, pathlib

# --- Registry ---
class Tool:
    def __init__(self, name: str, desc: str, fn: Callable[[str], str]):
        self.name = name; self.desc = desc; self.fn = fn
    def __call__(self, arg: str) -> str: return self.fn(arg)

class ToolRegistry:
    def __init__(self): self._tools: Dict[str, Tool] = {}
    def register(self, tool: Tool): self._tools[tool.name] = tool
    def get(self, name: str) -> Tool: return self._tools[name]
    def names(self): return list(self._tools.keys())
    def spec(self):  # [(name, desc), ...]
        return [(t.name, t.desc) for t in self._tools.values()]

# 1) calculator
_WS = re.compile(r"\s+")
def _sanitize_expr(expr: str) -> str:
    s = expr.strip()
    # strip one pair of matching quotes/backticks if present
    if (s.startswith("'") and s.endswith("'")) or \
       (s.startswith('"') and s.endswith('"')) or \
       (s.startswith("`") and s.endswith("`")):
        s = s[1:-1].strip()
    # collapse all whitespace (turns \n, \t into single spaces)
    s = _WS.sub(" ", s)
    return s

def _calc(arg: str) -> str:
    try:
        s = _sanitize_expr(arg)
        allowed = set("0123456789+-*/(). eE")
        if any(ch not in allowed for ch in s):
            return "error: only basic arithmetic allowed"
        return str(eval(s, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"error: {e}"

calculator = Tool("calculator", "Evaluate arithmetic like '2*(3+4)' or '3.03e12*(1+8.5/100)'.", _calc)

# 2) unit_convert
def _unit_convert(arg: str) -> str:
    parts = arg.strip().lower().replace('°','').split()
    try:
        val = float(parts[0]); u1 = parts[1]; assert parts[2] == 'to'; u2 = parts[3]
    except Exception:
        return "error: '<value> <unit_from> to <unit_to>'"
    km_mi=0.621371; kg_lb=2.20462
    if (u1,u2) in [('f','c'),('fahrenheit','celsius')]: return f"{(val-32)*5/9:.1f} °C"
    if (u1,u2) in [('c','f'),('celsius','fahrenheit')]: return f"{val*9/5+32:.1f} °F"
    if (u1,u2) in [('km','mi'),('km','miles')]: return f"{val*km_mi:.3f} mi"
    if (u1,u2) in [('mi','km'),('miles','km')]: return f"{val/km_mi:.3f} km"
    if (u1,u2) in [('kg','lb')]: return f"{val*kg_lb:.3f} lb"
    if (u1,u2) in [('lb','kg')]: return f"{val/kg_lb:.3f} kg"
    return "error: unsupported conversion"
unit_convert = Tool("unit_convert", "Convert units (°F↔°C, km↔mi, kg↔lb). e.g. '72 F to C'.", _unit_convert)

# 3) date_calc
def _date_calc(arg: str) -> str:
    s = arg.strip().lower()
    m = re.match(r"days_between\s+(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})", s)
    if m:
        d1 = datetime.fromisoformat(m.group(1)); d2 = datetime.fromisoformat(m.group(2))
        return f"{(d2-d1).days}"
    m = re.match(r"(\d{4}-\d{2}-\d{2})\s*([+-])\s*(\d+)d", s)
    if m:
        d = datetime.fromisoformat(m.group(1)); sign = 1 if m.group(2)=='+' else -1; n=int(m.group(3))
        return (d + timedelta(days=sign*n)).date().isoformat()
    return "error: 'days_between A B' or 'YYYY-MM-DD +/- Nd'"
date_calc = Tool("date_calc", "Date math: 'days_between A B' or 'YYYY-MM-DD +/- Nd'.", _date_calc)

# 4) csv_query
def _csv_query(arg: str) -> str:
    # "sum file=path col=amount where=region:west"  or  "avg file=... col=..."
    s = arg.strip()
    op = s.split()[0] if s else "sum"
    kv = dict(re.findall(r"(\w+)=([^\s]+)", s))
    file = kv.get("file"); col = kv.get("col")
    if not (file and col): return "error: need file= and col="
    p = pathlib.Path(file)
    if not (p.exists() and p.is_file()): return "error: file not found"
    where = kv.get("where"); key=None; val=None
    if where and ":" in where: key,val = where.split(":",1)
    total=0.0; count=0
    with open(p, newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            if key and str(row.get(key,"")) != val: continue
            try: x = float(str(row.get(col,"")).replace(',',''))
            except: continue
            total += x; count += 1
    if count==0: return "0"
    if op=="sum": return f"{total}"
    if op=="avg": return f"{total/count}"
    return "error: op (sum|avg)"
csv_query = Tool("csv_query", "CSV: 'sum file=... col=... [where=K:V]' or 'avg ...'", _csv_query)

def register_default_tools(reg: ToolRegistry):
    for t in [calculator, unit_convert, date_calc, csv_query]:
        reg.register(t)

