def _to_float(s: str):
    try: return float(s.replace(',',''))
    except: return None

def rule_judge(task: str, final: str) -> tuple[bool, str]:
    t, f = task.lower().strip(), final.strip()
    
    if 'add' in t and '%' in t and 'to' in t:
        val = _to_float(f)
        if val is None: return (False, 'final not numeric')
        return (True, 'numeric final')
    
    if any(k in t for k in ['days_between', 'sum', 'avg', 'csv']):
        return (_to_float(f) is not None, 'numeric' if _to_float(f) is not None else 'non-numeric')
    
    if 'convert' in t or ' to ' in t:
        return (len(f) > 0, 'non-empty' if len(f) > 0 else 'empty')
    
    return (len(f) > 0, 'non-empty' if len(f) > 0 else 'empty')

