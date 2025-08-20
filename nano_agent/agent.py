# agent.py

import time
import re
from typing import Dict, List, Any, Tuple, Optional
from .tools import ToolRegistry

NUMERICAL_TOOLS = {"calculator", "date_calc", "csv_query", "unit_convert"}

class Agent:
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    def _parse_action(self, llm_output: str) -> Tuple[str, Optional[str], Optional[str]]:
        output = llm_output.strip()
        if output.startswith("FINAL:"):
            return "FINAL", None, output[6:].strip()
        if output.startswith("CALL:"):
            call_content = output[5:].strip()
            parts = call_content.split("|", 1)
            if len(parts) == 2:
                tool_name, arg = parts[0].strip(), parts[1].strip()
                return "CALL", tool_name, arg
            parts = call_content.split(None, 1)
            if len(parts) > 0:
                tool_name = parts[0]
                arg = parts[1] if len(parts) > 1 else ""
                return "CALL", tool_name, arg
        return "ERROR", None, "expected 'CALL:' or 'FINAL:'"

    def _build_context(self, task: str) -> str:
        """Builds the initial context string with the task and tool specs."""
        
        # Step 1: Format each tool's name and description into a list of strings.
        tool_specs = [f"{name}: {desc}" for name, desc in self.tools.spec()]
        
        # Step 2: Join the list of tool specs into a single string.
        tools_string = " | ".join(tool_specs)
        
        # Step 3: Combine everything into the final context string.
        context = f"Task: {task}\nTools: {tools_string}"
        
        return context

    def _execute_tool(self, tool_name: str, arg: str) -> str:
        """Executes a tool and returns the resulting observation string."""
        try:
            # This will now fail gracefully if the tool_name is wrong
            res = self.tools.get(tool_name)(arg)
            return f"Tool[{tool_name}] -> {res}"
        except Exception as e:
            # FIX #1: Ensure this method ALWAYS returns a string
            return f"error: tool '{tool_name}' failed with {e}"
    
    def run(self, task: str, token_budget: int = 400) -> Dict[str, Any]:
        # FIX #2: Use a colon ':' for a clearer prompt to prevent LLM confusion.
        context = self._build_context(task)        
        observation = ""
        trace_log: List[str] = []
        final_answer = ""
        tokens_input, tokens_output, time_elapsed = 0, 0, 0.0

        for step in range(self.max_steps):
            prompt = f"{context}\nObservation: {observation}\nRespond: 'CALL: tool | arg' OR 'FINAL: answer'"
            t0 = time.perf_counter()
            llm_output = self.model.generate(prompt).strip()
            dt = time.perf_counter() - t0
            
            tokens_input += len(prompt.split())
            tokens_output += len(llm_output.split()) 
            time_elapsed += dt
            trace_log.append(llm_output)

            action, tool_name, arg = self._parse_action(llm_output)

            if action == "FINAL":
                final_answer = arg
                break
            
            if action == "CALL":
                observation = self._execute_tool(tool_name, arg)
                
                tool_result = observation.split("->", 1)[-1].strip()
                is_numerical_tool = tool_name in NUMERICAL_TOOLS
                if is_numerical_tool and self._is_numberish(tool_result):
                    final_answer = tool_result
                    trace_log.append(f"FINAL: {final_answer}")
                    break
            else: # ERROR
                observation = arg

            if (tokens_input + tokens_output) > int(token_budget * 1.1):
                final_answer = "error: token budget exceeded"
                break
        
        if not final_answer:
            final_answer = "error: max steps reached"
            
        return {
            "final": final_answer, 
            "trace": trace_log, 
            "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}
        }
        
    @staticmethod
    def _is_numberish(s: str) -> bool:
        return bool(re.match(r"\s*[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s or ""))