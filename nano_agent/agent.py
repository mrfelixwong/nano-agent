import time
import re
import json
from typing import Dict, List, Any, Tuple, Optional
from .tools import ToolRegistry


class Agent:
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    def _build_context(self, task: str) -> str:
        """Builds the initial context string with the task and tool specs."""
        tool_specs = [f"{name}: {desc}" for name, desc in self.tools.spec()]
        tools_string = " | ".join(tool_specs)
        
        json_instructions = """
Respond with ONLY a JSON object with the following schema:
{
  "action": "CALL" or "FINAL",
  "tool_name": "name_of_tool_to_call" or null,
  "argument": "argument_for_the_tool" or null,
  "answer": "final_answer_to_the_user" or null
}"""
        
        context = f"Task: {task}\nTools: {tools_string}\n{json_instructions}"
        return context

    def _execute_tool(self, tool_name: str, arg: str) -> str:
        """Executes a tool and returns the resulting observation string."""
        try:
            res = self.tools.get(tool_name)(arg)
            # Make successful tool results more explicit
            if not str(res).startswith('error:'):
                return f"Tool '{tool_name}' succeeded with result: {res}"
            return f"Tool '{tool_name}' failed with error: {res}"
        except Exception as e:
            return f"Tool '{tool_name}' failed with exception: {e}"
    
    def run(self, task: str, token_budget: int = 400) -> Dict[str, Any]:
        context = self._build_context(task)
        observation = ""
        trace_log: List[str] = []
        final_answer = ""
        tokens_input, tokens_output, time_elapsed = 0, 0, 0.0

        for step in range(self.max_steps):
            prompt = f"{context}\nObservation: {observation}"
            t0 = time.perf_counter()
            
            llm_output = self.model.generate(prompt, format='json').strip()
            dt = time.perf_counter() - t0
            
            tokens_input += len(prompt.split())
            tokens_output += len(llm_output.split()) 
            time_elapsed += dt
            trace_log.append(llm_output)

            # Parse LLM's JSON output or return error action if invalid
            action_data = json.loads(llm_output) if llm_output else {"action": "ERROR", "error": "Empty output"}
            action = action_data.get("action")

            if action == "FINAL":
                final_answer = action_data.get("answer")
                break
            
            if action == "CALL":
                tool_name = action_data.get("tool_name")
                arg = action_data.get("argument")
                observation = self._execute_tool(tool_name, arg)
                
            else: # ERROR
                observation = action_data.get("error", "Unknown error")

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