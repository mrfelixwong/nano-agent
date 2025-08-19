from datetime import datetime, timedelta
import re, csv, pathlib

class ToolRegistry:
    def __init__(self): self._tools = {}
    def register(self, name: str, desc: str, fn): self._tools[name] = (desc, fn)
    def get(self, name: str): return self._tools[name][1]
    def spec(self): return [(n, d) for n, (d, _) in self._tools.items()]

def _calc(arg: str) -> str:
    try:
        s = re.sub(r"\s+", " ", arg.strip().strip("'\"`"))
        if any(ch not in "0123456789+-*/(). eE" for ch in s):
            return "error: only basic arithmetic allowed"
        return str(eval(s, {"__builtins__": {}}, {}))
    except: return "error: invalid expression"

def _unit_convert(arg: str) -> str:
    try:
        val, u1, _, u2 = arg.strip().lower().replace('°','').split()
        val = float(val)
        if (u1,u2) in [('f','c'),('fahrenheit','celsius')]: return f"{(val-32)*5/9:.1f} °C"
        if (u1,u2) in [('c','f'),('celsius','fahrenheit')]: return f"{val*9/5+32:.1f} °F"
        if (u1,u2) in [('km','mi'),('km','miles')]: return f"{val*0.621371:.3f} mi"
        if (u1,u2) in [('mi','km'),('miles','km')]: return f"{val/0.621371:.3f} km"
        if (u1,u2) in [('kg','lb')]: return f"{val*2.20462:.3f} lb"
        if (u1,u2) in [('lb','kg')]: return f"{val/2.20462:.3f} kg"
        return "error: unsupported conversion"
    except: return "error: '<value> <unit_from> to <unit_to>'"

def _date_calc(arg: str) -> str:
    s = arg.strip().lower()
    if m := re.match(r"days_between\s+(\d{4}-\d{2}-\d{2})\s+(\d{4}-\d{2}-\d{2})", s):
        d1, d2 = datetime.fromisoformat(m.group(1)), datetime.fromisoformat(m.group(2))
        return str((d2-d1).days)
    if m := re.match(r"(\d{4}-\d{2}-\d{2})\s*([+-])\s*(\d+)d", s):
        d, sign, n = datetime.fromisoformat(m.group(1)), 1 if m.group(2)=='+' else -1, int(m.group(3))
        return (d + timedelta(days=sign*n)).date().isoformat()
    return "error: 'days_between A B' or 'YYYY-MM-DD +/- Nd'"

def _csv_query(arg: str) -> str:
    try:
        op = arg.split()[0] if arg else "sum"
        kv = dict(re.findall(r"(\w+)=([^\s]+)", arg))
        file, col = kv.get("file"), kv.get("col")
        if not (file and col): return "error: need file= and col="
        
        p = pathlib.Path(file)
        where = kv.get("where")
        key, val = where.split(":",1) if where and ":" in where else (None, None)
        
        total = count = 0.0
        with open(p, newline='') as f:
            for row in csv.DictReader(f):
                if key and str(row.get(key,"")) != val: continue
                try: 
                    x = float(str(row.get(col,"")).replace(',',''))
                    total += x; count += 1
                except: continue
        
        if count == 0: return "0"
        return str(total if op=="sum" else total/count if op=="avg" else "error: op (sum|avg)")
    except: return "error: invalid csv query"

def register_default_tools(reg: ToolRegistry):
    reg.register("calculator", "Evaluate arithmetic like '2*(3+4)' or '3.03e12*(1+8.5/100)'.", _calc)
    reg.register("unit_convert", "Convert units (°F↔°C, km↔mi, kg↔lb). e.g. '72 F to C'.", _unit_convert)
    reg.register("date_calc", "Date math: 'days_between A B' or 'YYYY-MM-DD +/- Nd'.", _date_calc)
    reg.register("csv_query", "CSV: 'sum file=... col=... [where=K:V]' or 'avg ...'", _csv_query)

