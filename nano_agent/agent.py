import time, re
from .tools import ToolRegistry

def _is_numberish(s: str) -> bool:
    return bool(re.match(r"\s*[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s or ""))

def _repair_date_args(task: str, arg: str) -> str:
    if "days_between" in arg: return arg
    m = re.search(r"(\d{4}-\d{2}-\d{2}).*?(\d{4}-\d{2}-\d{2})", task)
    return f"days_between {m.group(1)} {m.group(2)}" if m else arg

class Agent:
    def __init__(self, model, tools: ToolRegistry, max_steps: int = 4):
        self.model, self.tools, self.max_steps = model, tools, max_steps

    def run(self, task: str, token_budget: int = 400) -> dict:
        ctx = f"Task: {task}\nTools: " + " | ".join([f"{n}: {d}" for n, d in self.tools.spec()])

        # Initialize agent state
        observation = ""
        trace_log = []
        evidence_dict = {}

        # Initialize cost tracking
        tokens_input = 0
        tokens_output = 0
        time_elapsed = 0.0

        for _ in range(self.max_steps):
            prompt = f"{ctx}\nObservation: {observation}\nRespond: 'CALL: tool | arg' OR 'FINAL: answer'"
            t0 = time.perf_counter()
            out = self.model.generate(prompt).strip()
            dt = time.perf_counter() - t0
            tokens_input += len(prompt.split()); tokens_output += len(out.split()); time_elapsed += dt
            trace_log.append(out)

            if out.startswith("FINAL:"):
                return {"final": out[6:].strip(), "trace": trace_log, "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}, "evidence": evidence_dict}

            if out.startswith("CALL:"):
                try:
                    tool_name, arg = out[5:].split("|", 1)
                    tool_name, arg = tool_name.strip(), arg.strip()
                    
                    if tool_name == "date_calc":
                        arg = _repair_date_args(task, arg)
                    
                    res = self.tools.get(tool_name)(arg)
                    
                    if tool_name == "calculator":
                        evidence_dict["calculator_result"] = res

                    if tool_name in {"calculator", "date_calc", "csv_query", "unit_convert"} and _is_numberish(res):
                        trace_log.append(f"FINAL: {res.strip()}")
                        return {"final": res.strip(), "trace": trace_log, "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}, "evidence": evidence_dict}

                    observation = f"Tool[{tool_name}] -> {res}"
                except Exception as e:
                    observation = f"error: {e}"
            else:
                observation = "error: expected 'CALL:' or 'FINAL:'"

            if len(trace_log) >= self.max_steps or (tokens_input + tokens_output) > int(token_budget * 1.1):
                return {"final": observation, "trace": trace_log, "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}, "evidence": evidence_dict}

        return {"final": "error: max steps reached", "trace": trace_log, "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}, "evidence": evidence_dict}
