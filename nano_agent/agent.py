import json
import os
import time
from typing import Dict, List, Any
from .tools import ToolRegistry

class Agent:
    """Agent that uses LLM reasoning and tools to solve tasks."""
    
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4, verbose: bool = False):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps
        self.verbose = verbose or os.environ.get('NANO_AGENT_VERBOSE', '').lower() in ('1', 'true', 'yes')

    def _log(self, emoji: str, event_type: str, details: str = ""):
        """Handles all verbose logging if the verbose flag is set."""
        if self.verbose:
            print(f"  {emoji} {event_type}: {details}")
    
    def _execute_tool(self, tool_name: str, arg: str) -> str:
        """Execute tool and return formatted observation string."""
        try:
            result = self.tools.get(tool_name)(arg)
        except Exception as e:
            result = f"error: {e}"
            
        if str(result).startswith("error:"):
            return f"Tool '{tool_name}' returned error: {str(result)[6:].strip()}"
        return f"Tool '{tool_name}' succeeded with result: {result}"

    def _call_model_with_json_retry(self, prompt: str, retry_limit: int = 3):
        # ... (this method is unchanged) ...

    def run(self, task: str, token_budget: int = 400) -> Dict[str, Any]:
        """Execute observe-think-act loop until task completes or limits reached."""
        
        context = f"""Task: {task}
Tools: {' | '.join([f'{n}: {d}' for n, d in self.tools.spec()])}

Respond with ONLY a JSON object with the schema:
{{"action": "PLAN"|"CALL"|"FINAL", "steps":[]|"tool_name"|"answer", ...}}"""
        
        observation = "No observation yet. You must decide on the first action."
        observations: List[str] = []
        trace_log: List[str] = []
        final_answer = ""
        
        plan_state = {"steps": [], "current_step": 0}
        
        for step in range(self.max_steps):
            if self.verbose: print(f"\n[Step {step + 1}]")

            # REFACTOR: Removed the THINK log.

            prompt = f"{context}\nPrevious Observations: {observations}\nObservation: {observation}"
            if plan_state["steps"]:
                plan_context = f"\nPlan: {plan_state['steps']}"
                plan_context += f"\nCurrent Step {plan_state['current_step']+1}: {plan_state['steps'][plan_state['current_step']]}"
                prompt += plan_context
            
            action_dict, raw_response = self._call_model_with_json_retry(prompt)
            trace_log.append(raw_response)
            
            # The only log inside the loop is the raw plan from the LLM.
            self._log("💡", "PLAN", raw_response)

            if action_dict is None:
                final_answer = f"error: Failed to get valid JSON after retries. Last output: {raw_response}"
                break
        
            action = action_dict.get("action", "ERROR")
            
            if action == "PLAN":
                if not plan_state["steps"]:
                    plan_state["steps"] = action_dict.get("steps", [])
                    observation = f"Plan created with {len(plan_state['steps'])} steps. Now use CALL for step 1."
                else:
                    observation = "Already have a plan. Continuing execution."
            
            elif action == "FINAL":
                final_answer = action_dict.get("answer")
                break

            elif action == "CALL":
                tool_name = action_dict.get("tool_name")
                arg = action_dict.get("argument")
                observation = self._execute_tool(tool_name, arg)
                
                if plan_state["steps"]:
                    plan_state["current_step"] += 1
                    if plan_state["current_step"] >= len(plan_state["steps"]):
                        observation += "\nAll plan steps completed. Use FINAL to return the answer."
            else:
                observation = f"error: {action_dict.get('error', 'Unknown error from LLM')}"
            
            # REFACTOR: Removed the OBSERVE log.
            observations.append(observation)
            
        if not final_answer:
            final_answer = "error: max steps reached"
        
        return {
            "final": final_answer,
            "trace": trace_log,
            "observations": observations,
        }