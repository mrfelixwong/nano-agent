import json
import os
import time
from typing import Dict, List, Any, Optional
from .tools import ToolRegistry

class Agent:
    """Agent that uses LLM reasoning and tools to solve tasks."""
    
    def __init__(self, model: Any, tools: ToolRegistry, max_steps: int = 4, verbose: bool = False):
        self.model = model
        self.tools = tools
        self.max_steps = max_steps
        self.verbose = verbose or os.environ.get('NANO_AGENT_VERBOSE', '').lower() in ('1', 'true', 'yes')
 
    def _execute_tool(self, tool_name: str, arg: str) -> str:
        """Execute tool and return formatted observation string."""
        try:
            result = self.tools.get(tool_name)(arg)
            return f"Tool '{tool_name}' succeeded with result: {result}"
        except Exception as e:
            return f"Tool '{tool_name}' failed with exception: {e}"

    def _call_model(self, prompt: str, retry_limit: int = 3) -> Optional[Dict[str, Any]]:
        """Calls the model, handling JSON decoding errors with a retry mechanism."""
        current_prompt = prompt
        
        for retry_attempt in range(retry_limit):
            response = self.model.generate(current_prompt, format='json').strip()
            
            try:
                parsed_action = json.loads(response)
                return parsed_action
            except json.JSONDecodeError:
                if self.verbose:
                    print(f"  - Invalid JSON, retrying ({retry_attempt + 1}/{retry_limit})...")
                current_prompt = f"{prompt}\n\nError: LLM returned invalid JSON. Please re-format your response as a valid JSON object."
        return None
        
    def run(self, task: str) -> Dict[str, Any]:
        """Execute observe-think-act loop until task completes or limits reached."""
        
        base_context = f"""Tools: {json.dumps(self.tools.spec())}

Decide on your next action. You can either:
1. Use the "CALL" action to invoke a tool.
2. Use the "FINAL" action when you have the answer.

Respond with ONLY a JSON object:
- For CALL: {{"action": "CALL", "tool_name": "tool_name", "argument": "argument"}}
- For FINAL: {{"action": "FINAL", "answer": "the final result"}}"""
        
        observation = "No observation yet. You must decide on the first action."
        observations: List[str] = []
        trace_log: List[str] = []
        final_answer = ""
        
        for step in range(self.max_steps):
            if self.verbose: print(f"\n[Step {step + 1}]")

            prompt = ""
            # FIX: Make the condition more specific. It should only trigger on
            # a success that does NOT contain an error message.
            if "succeeded with result" in observation and "error:" not in observation.lower():
                prompt = f"""Observation: {observation}
Task is complete. Your only valid action is to use "FINAL" to return the answer from the observation.
Respond with ONLY a JSON object: {{"action": "FINAL", "answer": "the result from the observation"}}"""
            else:
                prompt = f"Task: {task}\n{base_context}\nPrevious Observations: {observations}\nObservation: {observation}"

            if self.verbose:
                print("\nPROMPT:\n--------\n" + prompt + "\n--------")
            
            action_dict = self._call_model(prompt)
            
            if action_dict:
                trace_log.append(json.dumps(action_dict))
            
            if self.verbose:
                print("\nLLM Response:\n--------\n" + json.dumps(action_dict, indent=2) + "\n--------")

            if action_dict is None:
                final_answer = "error: Failed to get valid JSON after retries."
                break
                        
            action = action_dict.get("action", "ERROR")
            
            if action == "FINAL":
                final_answer = action_dict.get("answer")
                break

            elif action == "CALL":
                tool_name = action_dict.get("tool_name")
                arg = action_dict.get("argument")
                if self.verbose:
                    print(f"Triggering TOOL: {tool_name}(\"{arg}\")")
                observation = self._execute_tool(tool_name, arg)
                if self.verbose:
                    print(f"TOOL Result: {observation}")
            else:
                observation = f"error: {action_dict.get('error', 'Unknown action from LLM')}"
            
            observations.append(observation)
            
        if not final_answer:
            final_answer = "error: max steps reached"
        
        return {
            "final": final_answer,
            "trace": trace_log,
            "observations": observations,
            "cost": {"ti": 0, "to": 0, "s": 0}
        }