import json
import os
import time
from typing import Dict, List, Any, Tuple, Optional
from .tools import ToolRegistry

class Agent:
    """Agent that uses LLM reasoning and tools to solve tasks."""
    
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4, verbose: bool = False):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps
        self.verbose = verbose or os.environ.get('NANO_AGENT_VERBOSE', '').lower() in ('1', 'true', 'yes')

    def _log_llm_response(self, action_dict: Optional[Dict[str, Any]], raw_response: str):
        """A single function to log the LLM's response in verbose mode."""
        if not self.verbose:
            return

        if action_dict is None:
            # This logs the final error when parsing failed after retries
            print(f"  → ABORT: Failed to get valid JSON. Last output: {raw_response}")
            return

        action = action_dict.get("action", "?")
        if action == "PLAN":
            print(f"  DECISION: Create plan with {len(action_dict.get('steps', []))} steps")
        elif action == "CALL":
            print(f"  DECISION: Use {action_dict.get('tool_name')} tool")
        elif action == "FINAL":
            print(f"  DECISION: Return the result")
        else:
            print(f"  DECISION: {action}")
    
    def _execute_tool(self, tool_name: str, arg: str) -> str:
        """Execute tool and return formatted observation string."""
        try:
            result = self.tools.get(tool_name)(arg)
        except Exception as e:
            result = f"error: {e}"
            
        if str(result).startswith("error:"):
            return f"Tool '{tool_name}' returned error: {str(result)[6:].strip()}"
        return f"Tool '{tool_name}' succeeded with result: {result}"

    def _call_model(self, prompt: str, retry_limit: int = 3) -> Tuple[Optional[Dict[str, Any]]]:
        """
        Calls the model, handling JSON decoding errors with a retry mechanism.
        Returns: tuple of (parsed_action, raw_response)
        """
        current_prompt = prompt
        
        for retry_attempt in range(retry_limit):
            response = self.model.generate(current_prompt, format='json').strip()

            try:
                parsed_action = json.loads(response)
                # Success, log and return
                #self._log_llm_response(parsed_action, response)
                return (parsed_action)
            except json.JSONDecodeError:
                if self.verbose:
                    print(f"  - Invalid JSON, retrying ({retry_attempt + 1}/{retry_limit})...")
                
                if retry_attempt == 0:
                    current_prompt = f"{prompt}\n\nError: LLM returned invalid JSON. Please re-format your response as a valid JSON object."
                else:
                    current_prompt = f"{prompt}\n\nI repeat: Respond ONLY with a JSON object. Do NOT include any other text."

        # Failure after all retries
        #self._log_llm_response(None, response)
        return (None)
    def run(self, task: str) -> Dict[str, Any]:
        """Execute observe-think-act loop until task completes or limits reached."""
        
        context = f"""Task: {task}
Tools: {' | '.join([f'{n}: {d}' for n, d in self.tools.spec()])}

For simple tasks: Use CALL directly.
For multi-step tasks: Use PLAN first.

Respond with ONLY a JSON object:
- For PLAN: {{"action": "PLAN", "steps": ["step 1 description", "step 2 description"]}}
- For CALL: {{"action": "CALL", "tool_name": "calculator", "argument": "2*50"}}
- For FINAL: {{"action": "FINAL", "answer": "the result"}}"""
        
        observation = "No observation yet. You must decide on the first action."
        observations: List[str] = []
        final_answer = ""
        
        plan_state = {"steps": [], "current_step": 0}
        
        for step in range(self.max_steps):
            if self.verbose: print(f"\n[Step {step + 1}]")

            # REFACTOR: Removed the THINK log.

            prompt = f"{context}\nPrevious Observations: {observations}\nObservation: {observation}"
            if plan_state["steps"] and plan_state["current_step"] < len(plan_state["steps"]):
                # Handle plan steps that might be strings or dicts
                current_step_data = plan_state['steps'][plan_state['current_step']]
                if isinstance(current_step_data, dict):
                    step_desc = str(current_step_data)
                else:
                    step_desc = current_step_data
                plan_context = f"\nPlan: {plan_state['steps']}"
                plan_context += f"\nCurrent Step {plan_state['current_step']+1}: {step_desc}"
                prompt += plan_context
            
            if self.verbose:
                print("\nPROMPT:")
                print("--------")
                print(prompt)
                print("--------")
            
            action_dict = self._call_model(prompt)
            
            if self.verbose:
                print("\nRESPONSE:")
                print("--------")
                print(json.dumps(action_dict, indent=2))
                print("--------")
        
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
            "observations": observations,
            "cost": {"ti": 0, "to": 0, "s": 0}  # Placeholder for cost tracking
        }