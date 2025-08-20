# agent.py

import time
import re
import json # Import the json library
from typing import Dict, List, Any, Tuple, Optional
from .tools import ToolRegistry

NUMERICAL_TOOLS = {"calculator", "date_calc", "csv_query", "unit_convert"}

class Agent:
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    def _parse_json_action(self, llm_output: str) -> Dict[str, str]:
        """Parses the LLM's JSON output into a dictionary."""
        try:
            return json.loads(llm_output)
        except json.JSONDecodeError:
            return {"action": "ERROR", "error": "Invalid JSON output from LLM."}

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
            return f"Tool[{tool_name}] -> {res}"
        except Exception as e:
            return f"error: tool '{tool_name}' failed with {e}"
    
    def run(self, task: str, token_budget: int = 400) -> Dict[str, Any]:
        context = self._build_context(task)
        observation = ""
        trace_log: List[str] = []
        final_answer = ""
        tokens_input, tokens_output, time_elapsed = 0, 0, 0.0

        for step in range(self.max_steps):
            prompt = f"{context}\nObservation: {observation}"
            t0 = time.perf_counter()            

            # WHY: We force the LLM to output JSON and use the Ollama 'format' parameter.
            # This is a reliability pattern. It prevents the agent from crashing due
            # to malformed LLM output and removes the need for brittle string parsing.
            llm_output = self.model.generate(prompt, format='json').strip()
            dt = time.perf_counter() - t0
            
            tokens_input += len(prompt.split())
            tokens_output += len(llm_output.split()) 
            time_elapsed += dt
            trace_log.append(llm_output)

            action_data = self._parse_json_action(llm_output)
            action = action_data.get("action")

            if action == "FINAL":
                final_answer = action_data.get("answer")
                break
            
            if action == "CALL":
                tool_name = action_data.get("tool_name")
                arg = action_data.get("argument")
                observation = self._execute_tool(tool_name, arg)
                
                tool_result = observation.split("->", 1)[-1].strip()
                is_numerical_tool = tool_name in NUMERICAL_TOOLS

                # WHY: This is the "numerical shortcut," a pragmatic optimization.
                # 1. Optimization: It saves a final, unnecessary LLM call just to
                #    wrap a number in a FINAL tag, reducing cost and latency.
                # 2. Guardrail: It provides a reliable, hard-coded rule for simple,
                #    deterministic tasks, improving the agent's overall reliability.
                if is_numerical_tool and self._is_numberish(tool_result):
                    final_answer = tool_result
                    trace_log.append(json.dumps({"action": "FINAL", "answer": final_answer}))
                    break
            else: # ERROR
                observation = action_data.get("error", "Unknown error")

            # WHY: Agents can sometimes get stuck in loops. These limits act as
            # safety mechanisms to prevent runaway execution and costs.
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