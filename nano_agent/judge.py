def _to_float(s: str):
    try: return float(s.replace(',',''))
    except: return None

def rule_judge(task: str, final: str, evidence: dict) -> tuple[bool, str]:
    t, f = task.lower().strip(), final.strip()
    
    if 'add' in t and '%' in t and 'to' in t:
        val = _to_float(f)
        if val is None: return (False, 'final not numeric')
        calc = evidence.get('calculator_result')
        if calc and abs(float(calc) - val) <= abs(float(calc))*0.01 + 1e-9:
            return (True, 'within 1% of calculator')
        return (True, 'numeric final (no calc evidence)')
    
    if any(k in t for k in ['days_between', 'sum', 'avg', 'csv']):
        return (_to_float(f) is not None, 'numeric' if _to_float(f) is not None else 'non-numeric')
    
    if 'convert' in t or ' to ' in t:
        return (len(f) > 0, 'non-empty' if len(f) > 0 else 'empty')
    
    return (len(f) > 0, 'non-empty' if len(f) > 0 else 'empty')

