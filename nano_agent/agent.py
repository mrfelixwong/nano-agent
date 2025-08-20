"""
A lightweight agent that can solve tasks using a language model and tools.
The agent follows a simple loop of observing, planning, and acting until it reaches
a final answer or hits execution limits.
"""

import time
import re
from typing import Dict, List, Any
from .tools import ToolRegistry


# Set of tools that can directly return a final numerical answer
NUMERICAL_TOOLS = {"calculator", "date_calc", "csv_query", "unit_convert"}


class Agent:
    """An agent that uses a language model and tools to solve tasks.
    
    The agent operates in a loop where it:
    1. Observes the current state
    2. Plans the next action using the language model
    3. Executes the action using available tools
    4. Repeats until reaching a final answer or hitting limits
    """
    
    @staticmethod
    def _is_numberish(s: str) -> bool:
        """Check if a string represents a numeric value."""
        return bool(re.match(r"\s*[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s or ""))
        
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    def run(self, task: str, token_budget: int = 400) -> Dict[str, Any]:
        ctx = f"Task: {task}\nTools: " + " | ".join([f"{n}: {d}" for n, d in self.tools.spec()])
        observation = ""
        trace_log: List[str] = []
        tokens_input = 0
        tokens_output = 0
        time_elapsed = 0.0

        for _ in range(self.max_steps):
            # Generate next action using the model
            prompt = f"{ctx}\nObservation: {observation}\nRespond: 'CALL: tool | arg' OR 'FINAL: answer'"
            t0 = time.perf_counter()
            out = self.model.generate(prompt).strip()
            dt = time.perf_counter() - t0
            
            # Update costs
            tokens_input += len(prompt.split())
            tokens_output += len(out.split()) 
            time_elapsed += dt
            trace_log.append(out)

            if out.startswith("FINAL:"):
                return {"final": out[6:].strip(), "trace": trace_log, "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}}

            if out.startswith("CALL:"):
                try:
                    # More robust parsing for the 'CALL' command.
                    # Handles cases with or without the '|' separator.
                    call_content = out[5:].strip()
                    parts = call_content.split("|", 1)
                    
                    if len(parts) == 2:
                        tool_name, arg = parts[0].strip(), parts[1].strip()
                    else:
                        # Fallback for when the '|' is missing
                        parts = call_content.split(None, 1)
                        tool_name = parts[0]
                        arg = parts[1] if len(parts) > 1 else ""
                    res = self.tools.get(tool_name)(arg)

                    # Check if we got a numerical result from a numerical tool
                    if tool_name in NUMERICAL_TOOLS and Agent._is_numberish(res):
                        trace_log.append(f"FINAL: {res.strip()}")
                        return {
                            "final": res.strip(), 
                            "trace": trace_log, 
                            "cost": {
                                "ti": tokens_input, 
                                "to": tokens_output, 
                                "s": time_elapsed
                            }
                        }

                    observation = f"Tool[{tool_name}] -> {res}"
                except Exception as e:
                    observation = f"error: {e}"
            else:
                observation = "error: expected 'CALL:' or 'FINAL:'"

            if len(trace_log) >= self.max_steps or (tokens_input + tokens_output) > int(token_budget * 1.1):
                return {"final": observation, "trace": trace_log, "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}}

        return {"final": "error: max steps reached", "trace": trace_log, "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}}