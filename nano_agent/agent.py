import json
import os
from typing import Dict, List, Any
from .tools import ToolRegistry


class Agent:
    """Agent that uses LLM reasoning and tools to solve tasks."""
    
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4, verbose: bool = False):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps
        self.verbose = verbose or os.environ.get('NANO_AGENT_VERBOSE', '').lower() in ('1', 'true', 'yes')
    
    def _execute_tool(self, tool_name: str, arg: str) -> str:
        """Execute tool and return observation string."""
        try:
            result = self.tools.get(tool_name)(arg)
            # Check if the result is an error from the tool itself
            if isinstance(result, str) and result.startswith("error:"):
                return f"Tool '{tool_name}' returned error: {result[6:].strip()}"
            return f"Tool '{tool_name}' succeeded with result: {result}"
        except Exception as e:
            return f"Tool '{tool_name}' failed with exception: {e}"
    
    def run(self, task: str, token_budget: int = 400) -> Dict[str, Any]:
        """Execute observe-think-act loop until task completes or limits reached."""
        
        # --- Setup ---
        tool_specs = [f"{name}: {desc}" for name, desc in self.tools.spec()]
        context = f"""Task: {task}
Tools: {' | '.join(tool_specs)}

Respond with ONLY a JSON object:
{{
  "action": "CALL" or "FINAL",
  "tool_name": "name_of_tool" or null,
  "argument": "tool_argument" or null,
  "answer": "final_answer" or null
}}"""
        
        observation = "No observation yet. You must decide on the first action."
        trace_log: List[str] = []
        observations: List[str] = []
        final_answer = ""
        tokens_input, tokens_output, time_elapsed = 0, 0, 0.0
        
        # --- Main Loop ---
        for step in range(self.max_steps):
            
            # OBSERVE + THINK: LLM decides next action
            prompt = f"{context}\nObservation: {observation}"
            
            # Verbose logging: show what we're sending to LLM
            if self.verbose:
                print(f"\n[Step {step + 1}]")
                if step == 0:
                    print(f"  THINK: Analyzing task: {task}")
                else:
                    # Extract cleaner observation message
                    if "succeeded with result:" in observation:
                        print(f"  THINK: Previous tool returned: {observation.split('result: ', 1)[1]}")
                    elif "failed" in observation or "error" in observation.lower():
                        print(f"  THINK: Previous tool failed: {observation.split('failed with exception: ', 1)[-1]}")
                    else:
                        print(f"  THINK: {observation}")
            
            plan_json = self.model.generate(prompt, format='json').strip()
            
            # Parse LLM's decision once
            try:
                plan = json.loads(plan_json)
            except json.JSONDecodeError:
                plan = {"action": "ERROR", "error": "Invalid JSON from LLM"}
            
            # Verbose logging: show what LLM decided
            if self.verbose:
                action = plan.get("action", "?")
                if action == "CALL":
                    print(f"  DECIDE: Use {plan.get('tool_name')} tool")
                elif action == "FINAL":
                    print(f"  DECIDE: Return the result")
                elif action == "ERROR":
                    print(f"  ERROR: {plan.get('error', 'Unknown error')}")
                else:
                    print(f"  DECIDE: {action}")
            
            # Track costs
            trace_log.append(plan_json)
            tokens_input += len(prompt.split())
            tokens_output += len(plan_json.split())
            time_elapsed += self.model.last_duration if hasattr(self.model, 'last_duration') else 0
            
            # ACT: Execute the chosen action
            if plan.get("action") == "FINAL":
                final_answer = plan.get("answer")
                observations.append("")  # No observation for final answer
                if self.verbose:
                    print(f"  → RETURN: {final_answer}")
                break
            elif plan.get("action") == "CALL":
                tool_name = plan.get("tool_name")
                arg = plan.get("argument")
                if self.verbose:
                    print(f"  → TOOL: {tool_name}(\"{arg}\")")
                observation = self._execute_tool(tool_name, arg)
                observations.append(observation)
                # Show execution result in verbose mode
                if self.verbose:
                    if "returned error:" in observation:
                        error_msg = observation.split("returned error: ", 1)[1]
                        print(f"  ← ERROR: {error_msg}")
                    elif "succeeded" in observation and "result:" in observation:
                        result = observation.split("result: ", 1)[1]
                        print(f"  ← RESULT: {result}")
                    elif "failed" in observation:
                        error_msg = observation.split("failed with exception: ", 1)[-1]
                        print(f"  ← ERROR: {error_msg}")
                    else:
                        print(f"  ← RESULT: {observation}")
            else:
                observation = f"error: {plan.get('error', 'Unknown error')}"
                observations.append(observation)
                if self.verbose:
                    print(f"  ← ERROR: {observation}")
            
            # Safety check: token budget
            if (tokens_input + tokens_output) > int(token_budget * 1.1):
                final_answer = "error: token budget exceeded"
                break
        
        if not final_answer:
            final_answer = "error: max steps reached"
        
        return {
            "final": final_answer,
            "trace": trace_log,
            "observations": observations,
            "cost": {"ti": tokens_input, "to": tokens_output, "s": time_elapsed}
        }