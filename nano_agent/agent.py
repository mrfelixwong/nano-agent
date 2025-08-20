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
        final_answer = ""
        tokens_input, tokens_output, time_elapsed = 0, 0, 0.0
        
        # --- Main Loop ---
        for step in range(self.max_steps):
            
            # OBSERVE + THINK: LLM decides next action
            prompt = f"{context}\nObservation: {observation}"
            
            # Verbose logging: show what we're sending to LLM
            if self.verbose:
                print(f"\n{'='*60}")
                print(f"STEP {step + 1} - SENDING TO LLM:")
                print(f"{'='*60}")
                print(prompt)
                print(f"{'='*60}")
            
            plan_json = self.model.generate(prompt, format='json').strip()
            
            # Verbose logging: show what LLM responded
            if self.verbose:
                print(f"\nLLM RESPONSE:")
                print(f"{'-'*60}")
                print(plan_json)
                print(f"{'-'*60}")
            
            # Track costs
            trace_log.append(plan_json)
            tokens_input += len(prompt.split())
            tokens_output += len(plan_json.split())
            time_elapsed += self.model.last_duration if hasattr(self.model, 'last_duration') else 0
            
            # Parse LLM's decision
            try:
                plan = json.loads(plan_json)
            except json.JSONDecodeError:
                plan = {"action": "ERROR", "error": "Invalid JSON from LLM"}
            
            # ACT: Execute the chosen action
            if plan.get("action") == "FINAL":
                final_answer = plan.get("answer")
                break
            elif plan.get("action") == "CALL":
                tool_name = plan.get("tool_name")
                arg = plan.get("argument")
                observation = self._execute_tool(tool_name, arg)
            else:
                observation = plan.get("error", "Unknown error")
            
            # Safety check: token budget
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