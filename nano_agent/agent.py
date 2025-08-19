from dataclasses import dataclass
from typing import Optional, List, Dict
import time
from .tools import ToolRegistry
import re

@dataclass
class Cost:
    tokens_in: int = 0
    tokens_out: int = 0
    seconds: float = 0.0
    def add(self, ti=0, to=0, s=0.0):
        self.tokens_in += ti; self.tokens_out += to; self.seconds += s

def should_continue(trace, cost: Cost, max_steps: int, token_budget: int) -> bool:
    if len(trace) >= max_steps: return False
    if (cost.tokens_in + cost.tokens_out) > int(token_budget * 1.1): return False
    return True

class Agent:
    """
    Model must return exactly one line per step:
      CALL: <tool> | <arg>
      FINAL: <answer>
    """
    def __init__(self, model, tools: ToolRegistry, max_steps: int = 4):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    def run(self, task: str, token_budget: int = 400) -> dict:
        tool_lines = "\n".join([f"- {n}: {d}" for (n,d) in self.tools.spec()])
        ctx = f"Task: {task}\nAvailable tools:\n{tool_lines}"
        obs = ""
        trace: List[str] = []
        evidence: Dict[str, str] = {}
        cost = Cost()

        for _ in range(self.max_steps):
            prompt = f"""{ctx}
Observation: {obs}
Respond with exactly ONE line:
- 'CALL: tool_name | arg'  OR
- 'FINAL: answer'
"""
            t0 = time.perf_counter()
            out = self.model.generate(prompt).strip()
            dt = time.perf_counter() - t0
            cost.add(ti=len(prompt.split()), to=len(out.split()), s=dt)
            trace.append(out)

            if out.startswith("FINAL:"):
                return {"final": out[len("FINAL:"):].strip(), "trace": trace, "cost": cost, "evidence": evidence}

            if out.startswith("CALL:"):
                try:
                    head, arg = out[len("CALL:"):].split("|", 1)
                    tool_name = head.strip(); arg = arg.strip()
                    res = self.tools.get(tool_name)(arg)

                    # stash evidence for the judge
                    if tool_name == "calculator":
                        evidence["calculator_result"] = res
                        # If the calculator returned a clean number, finalize immediately.
                        if re.fullmatch(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", res.strip()):
                            trace.append(f"FINAL: {res.strip()}")
                            return {"final": res.strip(), "trace": trace, "cost": cost, "evidence": evidence}

                    # otherwise continue as before
                    obs = f"Tool[{tool_name}] -> {res}"

                except Exception as e:
                    obs = f"error: {e}"
            else:
                obs = "error: expected 'CALL:' or 'FINAL:'"

            if not should_continue(trace, cost, self.max_steps, token_budget):
                return {"final": obs, "trace": trace, "cost": cost, "evidence": evidence}

        return {"final": "error: max steps reached", "trace": trace, "cost": cost, "evidence": evidence}

